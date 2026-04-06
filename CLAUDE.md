# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full implementation of **Ticket to Ride: Europe** with:
1. A complete Python game engine (ported from the original C++ data)
2. A PettingZoo `AECEnv` + RLlib `MultiAgentEnv` for reinforcement learning
3. A FastAPI + WebSocket server for human multiplayer
4. A Ray RLlib PPO training script with action masking and self-play

The original C++ code in `TTR_Europe_info/` and `TTR_Europe_code/` is superseded by the Python implementation in `ttr_game/`.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest ttr_game/tests/ -v

# Run a single test
pytest ttr_game/tests/test_game_engine.py::test_random_game_completes -v

# Start the multiplayer web server
uvicorn ttr_game.server.app:app --reload

# Train the RL agent (requires ray[rllib])
python -m ttr_game.agents.train --num-players 4 --num-iters 500

# Evaluate a checkpoint
python -m ttr_game.agents.train --eval ./checkpoints/<checkpoint> --num-players 4
```

## Architecture

### `ttr_game/game/` — Game engine (pure Python, no dependencies)
- **`info.py`**: Constants (45 trains, 3 stations, 110 cards, train scoring table, card colors)
- **`board.py`**: Europe map as an adjacency list. Each `RouteSegment` has `(city1, city2, length, color, ferries, tunnel, parallel_index)`. Double routes in the C++ source (two-letter color codes like `"KW"`) are expanded into two separate `RouteSegment` objects at load time.
- **`routes.py`**: 101 `DestinationTicket` objects across all editions. `TICKETS` = 46 base-game tickets used as the RL observation universe. Each ticket has `in_base`, `in_1912`, `in_big_cities` flags. `get_ticket_set(expansion)` returns `(long_tickets, regular_tickets)` for 5 expansion variants: `base`, `1912`, `europe_expanded`, `big_cities`, `mega`.
- **`state.py`**: `GameState` and `PlayerState` dataclasses + `setup_game()`. Mutable; use `copy.deepcopy()` to snapshot.
- **`actions.py`**: Flat integer action space. `ActionSpace(board)` maps integer indices ↔ `Action` objects. Layout: `[0–4]` draw face-up, `[5]` draw deck, `[6]` draw tickets, `[7–11]` second draw face-up, `[12]` second draw deck, `[13–27]` KEEP_TICKETS (masks 1–15, up to 4 drawn tickets), `[28–59]` KEEP_INIT_TICKETS (masks 0–31, up to 5 initial tickets; mask=0=keep none for Mega), `[60+]` claim route × 9 colors, then place station × 9 colors. Total ~1400+ actions.
- **`rules.py`**: `legal_actions()`, `step()` (mutates state, returns reward), `final_scores()`, `is_terminal()`

### `ttr_game/env/ttr_env.py` — PettingZoo / RLlib environment
- `TicketToRideEnv`: PettingZoo `AECEnv` (sequential turn-based). Observation dict has `"observations"` (float32 array) + `"action_mask"` (int8 array) for RLlib native action masking.
- `TTRMultiAgentEnv`: RLlib `MultiAgentEnv` shim wrapping the above.
- Supports 2–5 players; observations are padded to `MAX_PLAYERS=5` so observation shape is constant.

### `ttr_game/server/` — Web multiplayer
- `session.py`: `SessionManager` (in-memory) creates/manages `GameSession` objects; `to_dict()` serializes public state, `player_private_view(n)` returns private hand/tickets.
- `app.py`: FastAPI app. REST endpoints for create/list/get/delete games. WebSocket at `/ws/{session_id}/{player_idx}` — send `{"action": <int>}`, receive `{"type": "state", "public": {...}, "private": {...}}`. AI players take moves automatically.

### `ttr_game/agents/train.py` — RL training
- `ActionMaskedModel`: PyTorch custom model that adds `log(action_mask)` to logits (sets invalid actions to −∞).
- `build_ppo_config()`: RLlib PPO with shared policy across all agents (parameter-sharing self-play).
- All players share `"shared_policy"` — training is self-play by default.

## Key Design Decisions

- **Action masking is essential**: TTR has ~1320 total actions but most are invalid at any step. Without masking, RL training diverges.
- **Cards discarded on use**: When routes are claimed, cards go to `state.discard`, which is reshuffled into `state.deck` when depleted.
- **Tunnel mechanic (simplified)**: Tunnel resolution draws 3 cards; if the player can't pay the extra cost, the claim fails and their original cards are returned.
- **Double routes**: In 2–3 player games, once one route of a city pair is claimed, the parallel route is masked out for ALL players. In 4–5 player games, both parallel routes can be claimed by different players.
- **Expansion variants**: `setup_game(n, expansion=...)` supports `base` (1L+3R initial deal), `1912`/`europe_expanded` (same deal, expanded ticket pool), `big_cities` (0L+5R initial deal, draw 4 per turn), `mega` (2-phase initial: pick 0–1 long in `MEGA_LONG_SELECTION`, then pick ≥2 or ≥3 regular from 5 in `INITIAL_TICKET_SELECTION`).
- **`GamePhase.MEGA_LONG_SELECTION`**: New initial phase for Mega Europe. `KEEP_INIT_TICKETS` with mask=0 means "keep none". After selection, `state.mega_long_kept` controls whether regular min_keep is 2 (kept a long) or 3 (kept none).
- **C++ typos fixed in Python**: `"Bacelona"` → `"Barcelona"`, `"Zabreb"` → `"Zagrab"`, `"Bucresti"` → `"Bucuresti"`, `numCards` corrected to 110, `numRoutes` corrected to 50.
