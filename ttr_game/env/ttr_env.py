"""
PettingZoo AECEnv wrapper for Ticket to Ride: Europe.

Observation dict per agent:
  "observations": flat float32 array (see _encode_observation)
  "action_mask":  int8 array of shape (total_actions,) — 1 = valid, 0 = invalid

Action space: Discrete(total_actions) — flat integer encoding defined by ActionSpace.

Supports 2–5 players.  Padded to MAX_PLAYERS=5 in observation encoding so the
observation shape is constant regardless of actual player count.

Usage:
    env = TicketToRideEnv(num_players=4, seed=42)
    env.reset()
    for agent in env.agent_iter():
        obs, reward, terminated, truncated, info = env.last()
        if terminated or truncated:
            action = None
        else:
            action = policy(obs)
        env.step(action)

RLlib compatibility:
    The env is also exposed as a RLlib MultiAgentEnv via TTRMultiAgentEnv below.
"""
from __future__ import annotations
import copy
import random
from typing import Dict, Iterator, List, Optional

import numpy as np
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector
from gymnasium import spaces

from ..game.actions import ActionSpace
from ..game.board import Board
from ..game.info import COLORS, LOCO, NUM_TRAINS, NUM_STATIONS
from ..game.routes import (
    TICKETS,
    EXPANSION_BASE, EXPANSION_1912, EXPANSION_EUROPE_EXPANDED,
    EXPANSION_BIG_CITIES, EXPANSION_MEGA,
)
from ..game.rules import final_scores, is_terminal, legal_actions, step
from ..game.state import GamePhase, GameState, setup_game


MAX_PLAYERS = 5
NUM_TICKETS = len(TICKETS)
NUM_CARD_TYPES = len(COLORS) + 1  # 8 colors + loco
NUM_FACE_UP = 5
# One-hot encoding for a card slot: 9 card types + 1 empty = 10
CARD_SLOT_SIZE = NUM_CARD_TYPES + 1
# Game phase one-hot: 5 phases (INITIAL_TICKET_SELECTION, MAIN_TURN, SECOND_DRAW, TICKET_SELECTION, FINAL_ROUND/GAME_OVER)
NUM_PHASES = 5

# All supported expansion variants in a fixed order (used for one-hot encoding)
ALL_EXPANSIONS: List[str] = [
    EXPANSION_BASE,
    EXPANSION_1912,
    EXPANSION_EUROPE_EXPANDED,
    EXPANSION_BIG_CITIES,
    EXPANSION_MEGA,
]
NUM_EXPANSIONS = len(ALL_EXPANSIONS)


def _board_singleton() -> Board:
    """Shared board instance (data is read-only)."""
    if not hasattr(_board_singleton, "_instance"):
        _board_singleton._instance = Board()
    return _board_singleton._instance


def _action_space_singleton() -> ActionSpace:
    if not hasattr(_action_space_singleton, "_instance"):
        _action_space_singleton._instance = ActionSpace(_board_singleton())
    return _action_space_singleton._instance


def _obs_size(board: Board) -> int:
    num_routes = len(board.routes)
    return (
        NUM_CARD_TYPES                          # own hand
        + NUM_TICKETS                           # own tickets (binary)
        + NUM_FACE_UP * CARD_SLOT_SIZE          # face-up cards (one-hot each)
        + num_routes * (MAX_PLAYERS + 1)        # route ownership (one-hot per route: unclaimed + MAX_PLAYERS)
        + 3                                     # own trains, stations, score (normalized)
        + (MAX_PLAYERS - 1) * 3                 # opponents' trains, stations, score
        + NUM_PHASES                            # game phase (one-hot)
        + 1                                     # deck size (normalized)
        + NUM_EXPANSIONS                        # active expansion (one-hot)
    )


class TicketToRideEnv(AECEnv):
    """PettingZoo AECEnv for Ticket to Ride: Europe."""

    metadata = {"render_modes": ["human"], "name": "ticket_to_ride_europe_v0"}

    def __init__(self, num_players: int = 4, seed: Optional[int] = None,
                 render_mode: Optional[str] = None,
                 expansion: Optional[str] = None,
                 expansions: Optional[List[str]] = None) -> None:
        super().__init__()
        if not (2 <= num_players <= MAX_PLAYERS):
            raise ValueError(f"num_players must be 2–{MAX_PLAYERS}")

        self.num_players = num_players
        self._seed = seed
        self.render_mode = render_mode
        # Expansion pool: if expansions list given, sample one per episode reset.
        # expansions takes priority; expansion sets a single fixed variant.
        if expansions is not None:
            self._expansion_pool = list(expansions)
        elif expansion is not None:
            self._expansion_pool = [expansion]
        else:
            self._expansion_pool = [EXPANSION_BASE]
        self._current_expansion: str = self._expansion_pool[0]
        self._expansion_rng = random.Random(seed)

        self._board = _board_singleton()
        self._asp = _action_space_singleton()
        self._obs_size = _obs_size(self._board)

        # PettingZoo required attributes
        self.possible_agents = [f"player_{i}" for i in range(num_players)]
        self.agents: List[str] = []

        obs_space = spaces.Dict({
            "observations": spaces.Box(
                low=-1.0, high=1.0,
                shape=(self._obs_size,),
                dtype=np.float32,
            ),
            "action_mask": spaces.Box(
                low=0, high=1,
                shape=(self._asp.total,),
                dtype=np.int8,
            ),
        })
        act_space = spaces.Discrete(self._asp.total)

        self.observation_spaces = {a: obs_space for a in self.possible_agents}
        self.action_spaces = {a: act_space for a in self.possible_agents}

        self._state: Optional[GameState] = None
        self._rng = random.Random(seed)
        self._cumulative_rewards: Dict[str, float] = {}
        self._rewards: Dict[str, float] = {}
        self._terminations: Dict[str, bool] = {}
        self._truncations: Dict[str, bool] = {}
        self._infos: Dict[str, dict] = {}
        self._agent_selector: Optional[agent_selector] = None

    # ------------------------------------------------------------------
    # PettingZoo API
    # ------------------------------------------------------------------

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        if seed is not None:
            self._seed = seed
            self._rng = random.Random(seed)
            self._expansion_rng = random.Random(seed)

        # Pick an expansion for this episode
        self._current_expansion = self._expansion_rng.choice(self._expansion_pool)
        self._state = setup_game(self.num_players, seed=self._seed,
                                 expansion=self._current_expansion)
        self.agents = self.possible_agents[:]
        self._cumulative_rewards = {a: 0.0 for a in self.agents}
        self._rewards = {a: 0.0 for a in self.agents}
        self._terminations = {a: False for a in self.agents}
        self._truncations = {a: False for a in self.agents}
        self._infos = {a: {} for a in self.agents}

        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self.agents[self._state.current_player]

        return self.observe(self.agent_selection), self._infos[self.agent_selection]

    def step(self, action: Optional[int]) -> None:
        if self._state is None:
            raise RuntimeError("Call reset() before step()")

        current_agent = self.agent_selection
        player_idx = int(current_agent.split("_")[1])

        if self._terminations[current_agent] or self._truncations[current_agent]:
            self._was_dead_step(action)
            return

        # Reset rewards
        self._rewards = {a: 0.0 for a in self.agents}

        if action is None:
            action = 0  # fallback; shouldn't happen in normal play

        # Apply action
        reward = step(self._state, action, self._asp, self._rng)
        self._rewards[current_agent] = reward
        self._cumulative_rewards[current_agent] += reward

        # Check terminal
        if is_terminal(self._state):
            scores = final_scores(self._state)
            # Distribute final rewards
            for i, agent in enumerate(self.possible_agents):
                final_r = float(scores[i])
                self._rewards[agent] += final_r
                self._cumulative_rewards[agent] += final_r
                self._terminations[agent] = True
        else:
            # Advance agent selector to match current_player in game state
            self.agent_selection = self.possible_agents[self._state.current_player]

        self._accumulate_rewards()

    def observe(self, agent: str) -> dict:
        player_idx = int(agent.split("_")[1])
        obs = self._encode_observation(player_idx)
        mask = self._compute_mask(player_idx)
        return {"observations": obs, "action_mask": mask}

    def observation_space(self, agent: str) -> spaces.Space:
        return self.observation_spaces[agent]

    def action_space(self, agent: str) -> spaces.Space:
        return self.action_spaces[agent]

    def render(self) -> None:
        if self.render_mode == "human" and self._state is not None:
            _render_text(self._state, self._board)

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Observation encoding
    # ------------------------------------------------------------------

    def _encode_observation(self, player_idx: int) -> np.ndarray:
        state = self._state
        player = state.players[player_idx]
        board = self._board
        asp = self._asp
        obs = np.zeros(self._obs_size, dtype=np.float32)
        ptr = 0

        # Own hand (normalized by max possible cards)
        for color in COLORS:
            obs[ptr] = player.hand.get(color, 0) / 12.0
            ptr += 1
        obs[ptr] = player.hand.get(LOCO, 0) / 14.0
        ptr += 1

        # Own destination tickets (binary)
        held_tickets = {(t.city1, t.city2) for t in player.tickets}
        for ticket in TICKETS:
            obs[ptr] = 1.0 if (ticket.city1, ticket.city2) in held_tickets else 0.0
            ptr += 1

        # Face-up cards (one-hot per slot, 10 values: 9 card types + empty)
        card_to_idx = {c: i for i, c in enumerate(COLORS + [LOCO])}
        for slot_card in state.face_up:
            slot_enc = np.zeros(CARD_SLOT_SIZE, dtype=np.float32)
            if slot_card is None:
                slot_enc[NUM_CARD_TYPES] = 1.0  # empty
            else:
                slot_enc[card_to_idx.get(slot_card, NUM_CARD_TYPES)] = 1.0
            obs[ptr:ptr + CARD_SLOT_SIZE] = slot_enc
            ptr += CARD_SLOT_SIZE

        # Route ownership (one-hot per route: 0=unclaimed, 1..MAX_PLAYERS=owned by player i-1)
        num_routes = len(board.routes)
        for route_idx in range(num_routes):
            slot = np.zeros(MAX_PLAYERS + 1, dtype=np.float32)
            owner = state.claimed_routes.get(route_idx)
            if owner is None:
                slot[0] = 1.0
            else:
                # Encode relative to this player: player_idx → position 1, others → 2..
                if owner == player_idx:
                    slot[1] = 1.0
                else:
                    # Map other players to positions 2..MAX_PLAYERS in order
                    others = [i for i in range(self.num_players) if i != player_idx]
                    rel = others.index(owner) + 2 if owner in others else MAX_PLAYERS
                    slot[min(rel, MAX_PLAYERS)] = 1.0
            obs[ptr:ptr + MAX_PLAYERS + 1] = slot
            ptr += MAX_PLAYERS + 1

        # Own stats
        obs[ptr] = player.trains / NUM_TRAINS
        obs[ptr + 1] = player.stations / NUM_STATIONS
        obs[ptr + 2] = player.score / 200.0  # rough normalization
        ptr += 3

        # Other players' visible stats (trains, stations, score) — padded to MAX_PLAYERS-1
        others = [state.players[i] for i in range(self.num_players) if i != player_idx]
        for i in range(MAX_PLAYERS - 1):
            if i < len(others):
                p = others[i]
                obs[ptr] = p.trains / NUM_TRAINS
                obs[ptr + 1] = p.stations / NUM_STATIONS
                obs[ptr + 2] = p.score / 200.0
            ptr += 3

        # Game phase (one-hot)
        phase_map = {
            GamePhase.MEGA_LONG_SELECTION: 0,
            GamePhase.INITIAL_TICKET_SELECTION: 0,
            GamePhase.MAIN_TURN: 1,
            GamePhase.SECOND_DRAW: 2,
            GamePhase.TICKET_SELECTION: 3,
            GamePhase.FINAL_ROUND: 4,
            GamePhase.GAME_OVER: 4,
        }
        phase_enc = np.zeros(NUM_PHASES, dtype=np.float32)
        phase_enc[phase_map.get(state.phase, 4)] = 1.0
        obs[ptr:ptr + NUM_PHASES] = phase_enc
        ptr += NUM_PHASES

        # Deck size (normalized)
        obs[ptr] = len(state.deck) / 110.0
        ptr += 1

        # Active expansion (one-hot)
        exp_enc = np.zeros(NUM_EXPANSIONS, dtype=np.float32)
        exp_idx = ALL_EXPANSIONS.index(state.expansion) if state.expansion in ALL_EXPANSIONS else 0
        exp_enc[exp_idx] = 1.0
        obs[ptr:ptr + NUM_EXPANSIONS] = exp_enc
        ptr += NUM_EXPANSIONS

        return obs

    def _compute_mask(self, player_idx: int) -> np.ndarray:
        state = self._state
        asp = self._asp
        # Only compute mask for the current player; others get all-zero mask
        mask = np.zeros(asp.total, dtype=np.int8)
        if state.current_player != player_idx:
            return mask
        for idx in legal_actions(state, asp):
            mask[idx] = 1
        return mask

    # ------------------------------------------------------------------
    # agent_iter (AECEnv requirement)
    # ------------------------------------------------------------------

    def agent_iter(self) -> Iterator[str]:
        """Yield the current agent until the episode ends."""
        while self.agents:
            yield self.agent_selection
            if all(self._terminations.values()) or all(self._truncations.values()):
                break

    def last(self, observe: bool = True):
        agent = self.agent_selection
        obs = self.observe(agent) if observe else None
        return (
            obs,
            self._cumulative_rewards[agent],
            self._terminations[agent],
            self._truncations[agent],
            self._infos[agent],
        )

    def _was_dead_step(self, action) -> None:
        if self.agents:
            self.agent_selection = self._agent_selector.next()
        self._clear_rewards()

    def _clear_rewards(self) -> None:
        self._rewards = {a: 0.0 for a in self.agents}

    def _accumulate_rewards(self) -> None:
        for agent in self.agents:
            self._cumulative_rewards[agent] += self._rewards[agent]


# ---------------------------------------------------------------------------
# Simple text rendering
# ---------------------------------------------------------------------------

def _render_text(state: GameState, board: Board) -> None:
    print(f"\n{'='*60}")
    print(f"Phase: {state.phase.name}  |  Current player: {state.current_player}")
    for i, p in enumerate(state.players):
        marker = "→ " if i == state.current_player else "  "
        hand_str = " ".join(f"{c}:{n}" for c, n in p.hand.items() if n > 0)
        print(f"{marker}Player {i}: score={p.score} trains={p.trains} stations={p.stations} | {hand_str}")
    face_up_str = " ".join(c if c else "_" for c in state.face_up)
    print(f"Face-up: [{face_up_str}]  Deck: {len(state.deck)}  Discard: {len(state.discard)}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# RLlib MultiAgentEnv shim
# ---------------------------------------------------------------------------

try:
    from ray.rllib.env.multi_agent_env import MultiAgentEnv

    class TTRMultiAgentEnv(MultiAgentEnv):
        """
        RLlib MultiAgentEnv adapter wrapping TicketToRideEnv.

        Observation dict includes "action_mask" for native RLlib action masking:
          config["model"]["custom_model_config"]["use_action_mask"] = True
        """

        def __init__(self, config: Optional[dict] = None) -> None:
            config = config or {}
            self._env = TicketToRideEnv(
                num_players=config.get("num_players", 4),
                seed=config.get("seed", None),
                expansion=config.get("expansion", None),
                expansions=config.get("expansions", None),
            )
            self._asp = self._env._asp
            self._agents = self._env.possible_agents

            # New RLlib 2.x API: use plural dicts keyed by agent ID
            self.observation_spaces = {a: self._env.observation_spaces[a] for a in self._agents}
            self.action_spaces      = {a: self._env.action_spaces[a]      for a in self._agents}
            # Keep singular forms for backward compat with older callers
            self.observation_space = self._env.observation_spaces[self._agents[0]]
            self.action_space      = self._env.action_spaces[self._agents[0]]

            self.possible_agents = self._agents[:]
            self.agents = self._agents[:]
            super().__init__()

        def reset(self, *, seed=None, options=None):
            obs, infos = self._env.reset(seed=seed, options=options)
            return {self._env.agent_selection: obs}, infos

        def step(self, action_dict: dict):
            current = self._env.agent_selection
            action = action_dict.get(current, 0)
            self._env.step(action)

            rewards, terminations, truncations, infos, obs_dict = {}, {}, {}, {}, {}
            current_next = self._env.agent_selection
            obs_dict[current_next] = self._env.observe(current_next)
            rewards[current] = self._env._rewards.get(current, 0.0)

            done = all(self._env._terminations.values())
            terminations["__all__"] = done
            truncations["__all__"] = False

            for agent in self._env.agents:
                terminations[agent] = self._env._terminations[agent]
                truncations[agent] = self._env._truncations[agent]
                infos[agent] = self._env._infos[agent]

            if done:
                for agent in self._env.possible_agents:
                    obs_dict[agent] = self._env.observe(agent)

            return obs_dict, rewards, terminations, truncations, infos

        def render(self):
            self._env.render()

except ImportError:
    pass  # RLlib not installed; TTRMultiAgentEnv not available
