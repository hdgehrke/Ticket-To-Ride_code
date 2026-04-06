"""
FastAPI server for Ticket to Ride: Europe multiplayer.

REST endpoints:
  POST /games                  — create a new game session
  GET  /games                  — list active sessions
  GET  /games/{id}             — get public game state
  GET  /games/{id}/player/{n}  — get player n's private view (hand, tickets)
  DELETE /games/{id}           — end and remove session

WebSocket:
  WS /ws/{session_id}/{player_id}
    Client → server:  {"action": <int>}
    Server → client:  {"type": "state", "public": {...}, "private": {...}}
                      {"type": "error", "message": "..."}
                      {"type": "game_over", "scores": [...]}

Run with:
  uvicorn ttr_game.server.app:app --reload
"""
from __future__ import annotations
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .session import GameSession, SessionManager
from ..game.state import GamePhase

logger = logging.getLogger(__name__)

app = FastAPI(title="Ticket to Ride: Europe", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()

# WebSocket connection registry: session_id → {player_id → WebSocket}
_connections: Dict[str, Dict[int, WebSocket]] = {}


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

class CreateGameRequest(BaseModel):
    player_names: List[str]
    ai_players: Optional[List[int]] = []
    seed: Optional[int] = None


@app.post("/games")
async def create_game(req: CreateGameRequest):
    try:
        session = session_manager.create(
            player_names=req.player_names,
            ai_players=req.ai_players,
            seed=req.seed,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"session_id": session.session_id}


@app.get("/games")
async def list_games():
    return {"sessions": session_manager.list_sessions()}


@app.get("/games/{session_id}")
async def get_game(session_id: str):
    session = _get_session_or_404(session_id)
    return session.to_dict()


@app.get("/games/{session_id}/player/{player_idx}")
async def get_player_view(session_id: str, player_idx: int):
    session = _get_session_or_404(session_id)
    if not (0 <= player_idx < len(session.players)):
        raise HTTPException(status_code=400, detail="Invalid player index")
    return session.player_private_view(player_idx)


@app.delete("/games/{session_id}")
async def delete_game(session_id: str):
    _get_session_or_404(session_id)
    _connections.pop(session_id, None)
    session_manager.delete(session_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/{session_id}/{player_idx}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_idx: int):
    session = session_manager.get(session_id)
    if session is None:
        await websocket.close(code=4004, reason="Session not found")
        return
    if not (0 <= player_idx < len(session.players)):
        await websocket.close(code=4004, reason="Invalid player index")
        return

    await websocket.accept()
    _connections.setdefault(session_id, {})[player_idx] = websocket
    logger.info(f"Player {player_idx} connected to session {session_id}")

    try:
        # Send current state on connect
        await _broadcast_state(session_id, session)

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            action_idx = msg.get("action")
            if action_idx is None:
                await websocket.send_text(json.dumps({"type": "error", "message": "Missing 'action' field"}))
                continue

            current = session.state.current_player
            if current != player_idx and not session.players[player_idx].is_ai:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Not your turn (current player: {current})"
                }))
                continue

            legal = session.legal_action_indices()
            if action_idx not in legal:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Action {action_idx} is not legal"
                }))
                continue

            session.apply_action(action_idx)

            if session.is_over():
                scores = session.final_scores()
                await _broadcast(session_id, {
                    "type": "game_over",
                    "scores": scores,
                    "players": [p.name for p in session.players],
                })
            else:
                await _broadcast_state(session_id, session)
                # If next player is AI, trigger AI move
                await _maybe_play_ai(session_id, session)

    except WebSocketDisconnect:
        logger.info(f"Player {player_idx} disconnected from session {session_id}")
    finally:
        conns = _connections.get(session_id, {})
        conns.pop(player_idx, None)


async def _broadcast_state(session_id: str, session: GameSession) -> None:
    """Send public state + private views to all connected players."""
    public = session.to_dict()
    conns = _connections.get(session_id, {})
    for pid, ws in list(conns.items()):
        private = session.player_private_view(pid)
        msg = json.dumps({"type": "state", "public": public, "private": private})
        try:
            await ws.send_text(msg)
        except Exception:
            conns.pop(pid, None)


async def _broadcast(session_id: str, payload: dict) -> None:
    conns = _connections.get(session_id, {})
    text = json.dumps(payload)
    for pid, ws in list(conns.items()):
        try:
            await ws.send_text(text)
        except Exception:
            conns.pop(pid, None)


async def _maybe_play_ai(session_id: str, session: GameSession) -> None:
    """If the current player is AI, automatically select a random legal action."""
    import random as _random
    while not session.is_over():
        current = session.state.current_player
        if not session.players[current].is_ai:
            break
        legal = session.legal_action_indices()
        if not legal:
            break
        action_idx = _random.choice(legal)
        session.apply_action(action_idx)
        if session.is_over():
            scores = session.final_scores()
            await _broadcast(session_id, {
                "type": "game_over",
                "scores": scores,
                "players": [p.name for p in session.players],
            })
        else:
            await _broadcast_state(session_id, session)
        await asyncio.sleep(0.1)  # small delay so frontend can track AI moves


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session_or_404(session_id: str) -> GameSession:
    session = session_manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
