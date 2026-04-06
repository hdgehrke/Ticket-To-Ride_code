"""
Game session manager.  Each active game is a GameSession object identified
by a UUID string.  Sessions are stored in memory (no persistence).
"""
from __future__ import annotations
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..game.actions import ActionSpace, Action
from ..game.rules import final_scores, is_terminal, legal_actions, step
from ..game.state import GameState, GamePhase, setup_game
from ..env.ttr_env import _board_singleton, _action_space_singleton


@dataclass
class Player:
    player_id: int
    name: str
    is_ai: bool = False
    # WebSocket connection is stored by the server layer, not here


@dataclass
class GameSession:
    session_id: str
    players: List[Player]
    state: GameState
    asp: ActionSpace
    rng: random.Random
    log: List[str] = field(default_factory=list)

    def current_player_name(self) -> str:
        return self.players[self.state.current_player].name

    def legal_action_indices(self) -> List[int]:
        return legal_actions(self.state, self.asp)

    def apply_action(self, action_idx: int) -> float:
        reward = step(self.state, action_idx, self.asp, self.rng)
        action = self.asp.decode(action_idx)
        self.log.append(
            f"Player {self.state.players[(self.state.current_player - 1) % len(self.players)].name} "
            f"played: {action}"
        )
        return reward

    def is_over(self) -> bool:
        return is_terminal(self.state)

    def final_scores(self) -> List[int]:
        return final_scores(self.state)

    def to_dict(self) -> dict:
        """Serialise game state to JSON-safe dict for the frontend."""
        state = self.state
        board = state.board

        return {
            "session_id": self.session_id,
            "phase": state.phase.name,
            "current_player": state.current_player,
            "players": [
                {
                    "id": p.player_id,
                    "name": p.name,
                    "is_ai": p.is_ai,
                    "trains": state.players[i].trains,
                    "stations": state.players[i].stations,
                    "score": state.players[i].score,
                    "hand_total": state.players[i].hand_total(),
                    "ticket_count": len(state.players[i].tickets),
                    "station_cities": state.players[i].station_cities,
                }
                for i, p in enumerate(self.players)
            ],
            "face_up": state.face_up,
            "deck_size": len(state.deck),
            "discard_size": len(state.discard),
            "claimed_routes": {
                str(route_idx): owner
                for route_idx, owner in state.claimed_routes.items()
            },
            "routes": [
                {
                    "index": i,
                    "city1": r.city1,
                    "city2": r.city2,
                    "length": r.length,
                    "color": r.color,
                    "ferries": r.ferries,
                    "tunnel": r.tunnel,
                    "parallel_index": r.parallel_index,
                }
                for i, r in enumerate(board.routes)
            ],
        }

    def player_private_view(self, player_idx: int) -> dict:
        """Private data only visible to a specific player."""
        player = self.state.players[player_idx]
        return {
            "hand": dict(player.hand),
            "tickets": [
                {
                    "city1": t.city1,
                    "city2": t.city2,
                    "points": t.points,
                    "is_long": t.is_long,
                }
                for t in player.tickets
            ],
            "pending_tickets": [
                {
                    "city1": t.city1,
                    "city2": t.city2,
                    "points": t.points,
                    "is_long": t.is_long,
                }
                for t in self.state.pending_tickets
            ] if self.state.current_player == player_idx else [],
            "legal_actions": self.legal_action_indices(),
        }


class SessionManager:
    """In-memory store of active game sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, GameSession] = {}

    def create(self, player_names: List[str], ai_players: Optional[List[int]] = None,
               seed: Optional[int] = None) -> GameSession:
        """
        Create a new game session.

        player_names: list of display names (2–5 entries)
        ai_players:   list of player indices that should be AI-controlled
        """
        if not (2 <= len(player_names) <= 5):
            raise ValueError("Need 2–5 players")

        ai_players = ai_players or []
        session_id = str(uuid.uuid4())
        rng = random.Random(seed)
        board = _board_singleton()
        asp = _action_space_singleton()
        state = setup_game(len(player_names), seed=seed)
        players = [
            Player(player_id=i, name=name, is_ai=(i in ai_players))
            for i, name in enumerate(player_names)
        ]
        session = GameSession(
            session_id=session_id,
            players=players,
            state=state,
            asp=asp,
            rng=rng,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[GameSession]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_sessions(self) -> List[dict]:
        return [
            {
                "session_id": sid,
                "players": [p.name for p in s.players],
                "phase": s.state.phase.name,
                "current_player": s.current_player_name(),
            }
            for sid, s in self._sessions.items()
        ]
