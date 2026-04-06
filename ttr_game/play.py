"""
Hot-seat CLI for Ticket to Ride: Europe.

Any combination of human and CPU players can share one computer.
Between turns the screen clears so the current player can't see the
previous player's hand or tickets.

Usage:
    python -m ttr_game.play                        # 4 humans
    python -m ttr_game.play --players 3            # 3 humans
    python -m ttr_game.play --players 4 --ai 3     # 3 humans + 1 CPU
    python -m ttr_game.play --players 2 --ai 0 1   # 2 CPUs (watch mode)
    python -m ttr_game.play --players 4 --ai 2 3 --seed 42
"""
from __future__ import annotations
import argparse
import os
import random
import sys
import time
from typing import List, Optional

from .game.actions import Action, ActionSpace, ActionType
from .game.board import Board
from .game.info import COLORS, LOCO
from .game.routes import TICKETS
from .game.rules import final_scores, is_terminal, legal_actions, step
from .game.routes import (
    EXPANSION_BASE, EXPANSION_1912, EXPANSION_BIG_CITIES,
    EXPANSION_EUROPE_EXPANDED, EXPANSION_MEGA,
)
from .game.state import GamePhase, GameState, PlayerState, setup_game


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

CARD_COLOR_NAMES = {
    "P": "Purple", "W": "White", "B": "Blue", "Y": "Yellow",
    "O": "Orange", "K": "Black", "R": "Red",  "G": "Green", "L": "Loco",
}
CARD_COLOR_DISPLAY = {
    "P": "\033[35mPurple\033[0m",
    "W": "\033[37mWhite\033[0m",
    "B": "\033[34mBlue\033[0m",
    "Y": "\033[33mYellow\033[0m",
    "O": "\033[93mOrange\033[0m",
    "K": "\033[90mBlack\033[0m",
    "R": "\033[31mRed\033[0m",
    "G": "\033[32mGreen\033[0m",
    "L": "\033[96mLoco\033[0m",
    "X": "Any",
    None: "---",
}


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def card_str(color: Optional[str]) -> str:
    return CARD_COLOR_DISPLAY.get(color, str(color))


def hand_str(player: PlayerState) -> str:
    parts = []
    for c in COLORS + [LOCO]:
        n = player.hand.get(c, 0)
        if n:
            parts.append(f"{n}×{card_str(c)}")
    return "  ".join(parts) if parts else "(empty)"


def print_header(state: GameState, player_names: List[str]) -> None:
    print("=" * 62)
    print("  TICKET TO RIDE: EUROPE")
    print("=" * 62)
    for i, p in enumerate(state.players):
        marker = "▶ " if i == state.current_player else "  "
        tickets_done = _count_completed(p, state)
        print(
            f"{marker}Player {i+1} ({player_names[i]}): "
            f"score={p.score}  trains={p.trains}  stations={p.stations}  "
            f"tickets={len(p.tickets)}({tickets_done}✓)"
        )
    print("-" * 62)
    face_up = "  ".join(
        f"[{i}] {card_str(c)}" for i, c in enumerate(state.face_up)
    )
    print(f"Face-up cards:  {face_up}")
    print(f"Deck: {len(state.deck)} cards   Discard: {len(state.discard)}")
    print("=" * 62)


def _count_completed(player: PlayerState, state: GameState) -> int:
    from .game.rules import _ticket_completed
    return sum(1 for t in player.tickets if _ticket_completed(t, player, state))


def print_tickets(player: PlayerState, state: GameState) -> None:
    if not player.tickets:
        print("  (no tickets)")
        return
    from .game.rules import _ticket_completed
    for t in player.tickets:
        done = "✓" if _ticket_completed(t, player, state) else "✗"
        star = "★" if t.is_long else " "
        print(f"  {done}{star} {t.city1} ↔ {t.city2}  ({t.points} pts)")


# ---------------------------------------------------------------------------
# Grouped legal action menus
# ---------------------------------------------------------------------------

def group_actions(legal: List[int], asp: ActionSpace,
                  state: GameState) -> dict:
    """Return a dict of category → [(display_str, action_idx)]."""
    groups: dict = {
        "draw_first": [],
        "draw_second": [],
        "claim": [],
        "tickets": [],
        "keep": [],
        "station": [],
    }
    for idx in legal:
        a = asp.decode(idx)
        if a.action_type == ActionType.DRAW_FACE_UP:
            card = state.face_up[a.slot]
            groups["draw_first"].append((f"Draw face-up [{a.slot}] {card_str(card)}", idx))
        elif a.action_type == ActionType.DRAW_DECK:
            groups["draw_first"].append(("Draw 2 from deck", idx))
        elif a.action_type == ActionType.DRAW_TICKETS:
            groups["tickets"].append(("Draw destination tickets", idx))
        elif a.action_type == ActionType.DRAW_FACE_UP_SECOND:
            card = state.face_up[a.slot]
            groups["draw_second"].append((f"Take face-up [{a.slot}] {card_str(card)}", idx))
        elif a.action_type == ActionType.DRAW_DECK_SECOND:
            groups["draw_second"].append(("Draw from deck", idx))
        elif a.action_type == ActionType.KEEP_TICKETS or a.action_type == ActionType.KEEP_INIT_TICKETS:
            pending = state.pending_tickets
            kept = [pending[i].city1 + "↔" + pending[i].city2
                    for i in range(len(pending)) if a.slot & (1 << i)]
            groups["keep"].append((f"Keep: {', '.join(kept)}", idx))
        elif a.action_type == ActionType.CLAIM_ROUTE:
            route = state.board.routes[a.slot]
            color_label = card_str(a.color) if route.color == "X" else card_str(route.color)
            extras = []
            if route.tunnel:
                extras.append("tunnel")
            if route.ferries:
                extras.append(f"ferry×{route.ferries}")
            extra = f" ({','.join(extras)})" if extras else ""
            label = (f"Claim {route.city1}↔{route.city2}  "
                     f"len={route.length}  color={color_label}{extra}")
            groups["claim"].append((label, idx))
        elif a.action_type == ActionType.PLACE_STATION:
            city = state.board.cities[a.slot]
            groups["station"].append((f"Place station at {city} using {card_str(a.color)}", idx))
    return groups


def prompt_action(state: GameState, asp: ActionSpace,
                  player_name: str, player: PlayerState) -> int:
    """Show the action menu and return the chosen action index."""
    legal = legal_actions(state, asp)
    phase = state.phase

    # Mega Europe: choose 0 or 1 long route from 2 dealt
    if phase == GamePhase.MEGA_LONG_SELECTION:
        print("\nMega Europe — choose at most one long route to keep (or none):")
        for i, t in enumerate(state.pending_tickets):
            print(f"  [{i}] ★ {t.city1} ↔ {t.city2}  ({t.points} pts)")
        print()
        groups = group_actions(legal, asp, state)
        options = groups["keep"]
        for n, (label, _) in enumerate(options, 1):
            print(f"  {n}. {label}")
        return _pick(options, player_name)

    # During ticket keep phases, just show keep options directly
    if phase in (GamePhase.INITIAL_TICKET_SELECTION, GamePhase.TICKET_SELECTION):
        print("\nDestination tickets drawn:")
        for i, t in enumerate(state.pending_tickets):
            star = "★" if t.is_long else " "
            print(f"  [{i}] {star} {t.city1} ↔ {t.city2}  ({t.points} pts)")
        print()
        groups = group_actions(legal, asp, state)
        options = groups["keep"]
        for n, (label, _) in enumerate(options, 1):
            print(f"  {n}. {label}")
        return _pick(options, player_name)

    # During second draw, only show second-draw options
    if phase == GamePhase.SECOND_DRAW:
        print(f"\n{player_name}, pick your second card:")
        groups = group_actions(legal, asp, state)
        options = groups["draw_second"]
        for n, (label, _) in enumerate(options, 1):
            print(f"  {n}. {label}")
        return _pick(options, player_name)

    # Main turn: show categorized menu
    groups = group_actions(legal, asp, state)
    options = []
    section_headers = []

    def add_section(title: str, items) -> None:
        if items:
            section_headers.append((len(options), title))
            options.extend(items)

    add_section("── Draw cards ──────────────────────", groups["draw_first"])
    add_section("── Claim a route ───────────────────", groups["claim"])
    add_section("── Destination tickets ─────────────", groups["tickets"])
    add_section("── Place a station ─────────────────", groups["station"])

    print()
    header_set = {h[0] for h in section_headers}
    header_map = {h[0]: h[1] for h in section_headers}
    n = 1
    for i, (label, _) in enumerate(options):
        if i in header_set:
            print(f"\n  {header_map[i]}")
        print(f"    {n}. {label}")
        n += 1
    return _pick(options, player_name)


def _pick(options: list, player_name: str) -> int:
    while True:
        try:
            raw = input(f"\n{player_name}, enter choice (1–{len(options)}): ").strip()
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1][1]
        except (ValueError, EOFError):
            pass
        print("  Invalid choice, try again.")


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def _load_algo(model_path: str):
    """Load a trained RLlib checkpoint. Returns algo or None on failure."""
    try:
        import ray
        from ray.rllib.algorithms.ppo import PPOConfig
        from ray.rllib.core.rl_module.rl_module import RLModuleSpec
        from ray.rllib.examples.rl_modules.classes.action_masking_rlm import (
            ActionMaskingTorchRLModule,
        )
        from .env.ttr_env import TTRMultiAgentEnv

        ray.init(ignore_reinit_error=True)
        cfg = (
            PPOConfig()
            .environment(env=TTRMultiAgentEnv, env_config={"num_players": 5})
            .framework("torch")
            .env_runners(num_env_runners=0)
            .learners(num_learners=0)
            .rl_module(rl_module_spec=RLModuleSpec(module_class=ActionMaskingTorchRLModule))
            .multi_agent(
                policies={"shared_policy"},
                policy_mapping_fn=lambda agent_id, *args, **kwargs: "shared_policy",
                policies_to_train=["shared_policy"],
            )
        )
        cfg.train_batch_size_per_learner = 512
        cfg.minibatch_size = 128
        cfg.num_epochs = 3
        algo = cfg.build_algo()
        algo.restore(model_path)
        return algo
    except Exception as e:
        print(f"  Warning: could not load model from {model_path!r}: {e}")
        print("  Falling back to random CPU play.")
        return None


def play(num_players: int = 4, ai_players: Optional[List[int]] = None,
         seed: Optional[int] = None, model_path: Optional[str] = None,
         expansion: str = EXPANSION_BASE) -> None:
    rng = random.Random(seed)
    board = Board()
    asp = ActionSpace(board)
    state = setup_game(num_players, seed=seed, expansion=expansion)
    ai_players = set(ai_players or [])

    algo = None
    if model_path and ai_players:
        print(f"Loading trained model from: {model_path}")
        algo = _load_algo(model_path)
        if algo:
            print("  Model loaded — CPU players will use the trained policy.")

    # Collect player names
    player_names = []
    clear()
    print("TICKET TO RIDE: EUROPE — Hot Seat Setup")
    print("=" * 42)
    for i in range(num_players):
        if i in ai_players:
            player_names.append(f"CPU {i+1}")
        else:
            name = input(f"Enter name for Player {i+1}: ").strip()
            player_names.append(name or f"Player {i+1}")

    # Main loop
    while not is_terminal(state):
        pid = state.current_player
        player = state.players[pid]
        name = player_names[pid]

        if pid in ai_players:
            legal = legal_actions(state, asp)
            if not legal:
                break
            if algo is not None:
                from .env.ttr_env import TicketToRideEnv
                # Build a minimal env just to encode the observation
                _obs_env = TicketToRideEnv(num_players=num_players, seed=seed)
                _obs_env._state = state
                obs = _obs_env.observe(f"player_{pid}")
                action_idx = algo.compute_single_action(obs, policy_id="shared_policy")
                if action_idx not in legal:
                    action_idx = rng.choice(legal)  # safety fallback
            else:
                action_idx = rng.choice(legal)
            action = asp.decode(action_idx)
            reward = step(state, action_idx, asp, rng)
            clear()
            print_header(state, player_names)
            print(f"\n  CPU ({name}) played: {action}")
            time.sleep(0.4)
        else:
            # Human turn
            clear()
            print_header(state, player_names)

            phase = state.phase
            if phase in (GamePhase.MAIN_TURN, GamePhase.FINAL_ROUND):
                print(f"\n  ► It's {name}'s turn  (other players, look away!)")
                input("  Press Enter to see your hand...")
                clear()
                print_header(state, player_names)

            # Show current player's private info
            print(f"\n  YOUR HAND:")
            print(f"    {hand_str(player)}")
            if player.tickets:
                print(f"\n  YOUR TICKETS:")
                print_tickets(player, state)
            if state.pending_tickets and state.current_player == pid:
                pass  # shown inside prompt_action

            if phase == GamePhase.FINAL_ROUND:
                print("\n  *** FINAL ROUND — each player gets one last turn ***")
            if phase == GamePhase.MEGA_LONG_SELECTION:
                print("\n  *** MEGA EUROPE — choose 0 or 1 long route from the 2 dealt ***")

            action_idx = prompt_action(state, asp, name, player)
            reward = step(state, action_idx, asp, rng)

    # Game over
    clear()
    print("=" * 62)
    print("  GAME OVER")
    print("=" * 62)
    scores = final_scores(state)
    print("\nFinal Scores:")
    ranked = sorted(enumerate(scores), key=lambda x: -x[1])
    for rank, (pid, score) in enumerate(ranked, 1):
        marker = "🏆 " if rank == 1 else "   "
        print(f"  {marker}{rank}. {player_names[pid]}: {score} pts")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ticket to Ride: Europe — hot seat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--players", type=int, default=4,
                        help="Number of players (2–5, default 4)")
    parser.add_argument("--ai", type=int, nargs="*", default=[],
                        help="Player indices (0-based) to control as CPU")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--model", type=str, default=None, metavar="CHECKPOINT",
                        help="Path to a trained RLlib checkpoint directory for CPU players")
    parser.add_argument("--expansion", type=str, default=EXPANSION_BASE,
                        choices=[EXPANSION_BASE, EXPANSION_1912, EXPANSION_BIG_CITIES,
                                 EXPANSION_EUROPE_EXPANDED, EXPANSION_MEGA],
                        help="Ticket expansion: base, 1912, big_cities, europe_expanded, mega")
    args = parser.parse_args()

    if not (2 <= args.players <= 5):
        print("Error: --players must be between 2 and 5")
        sys.exit(1)

    invalid_ai = [i for i in (args.ai or []) if not (0 <= i < args.players)]
    if invalid_ai:
        print(f"Error: --ai indices {invalid_ai} out of range for {args.players} players")
        sys.exit(1)

    play(num_players=args.players, ai_players=args.ai, seed=args.seed,
         model_path=args.model, expansion=args.expansion)


if __name__ == "__main__":
    main()
