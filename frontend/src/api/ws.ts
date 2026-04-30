import { useCallback, useEffect, useRef, useState } from "react";
import type { PublicState, PrivateState, ServerMessage, PlayerScoreBreakdown } from "../types";

const WS_BASE = `ws://${window.location.hostname}:8000`;

interface GameWSState {
  publicState: PublicState | null;
  privateState: PrivateState | null;
  gameOver: { scores: number[]; players: string[]; breakdown: PlayerScoreBreakdown[] } | null;
  error: string | null;
  connected: boolean;
}

interface UseGameWSReturn extends GameWSState {
  sendAction: (actionIdx: number) => void;
}

export function useGameWS(sessionId: string, playerIdx: number): UseGameWSReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [state, setState] = useState<GameWSState>({
    publicState: null,
    privateState: null,
    gameOver: null,
    error: null,
    connected: false,
  });

  useEffect(() => {
    if (!sessionId) return;

    const url = `${WS_BASE}/ws/${sessionId}/${playerIdx}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setState(s => ({ ...s, connected: true, error: null }));
    };

    ws.onclose = () => {
      setState(s => ({ ...s, connected: false }));
    };

    ws.onerror = () => {
      setState(s => ({ ...s, error: "WebSocket connection failed", connected: false }));
    };

    ws.onmessage = (event) => {
      let msg: ServerMessage;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }

      if (msg.type === "state") {
        setState(s => ({
          ...s,
          publicState: msg.type === "state" ? msg.public : s.publicState,
          privateState: msg.type === "state" ? msg.private : s.privateState,
          error: null,
        }));
      } else if (msg.type === "error") {
        setState(s => ({ ...s, error: msg.message }));
      } else if (msg.type === "game_over") {
        setState(s => ({
          ...s,
          gameOver: { scores: msg.scores, players: msg.players, breakdown: msg.breakdown },
        }));
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sessionId, playerIdx]);

  const sendAction = useCallback((actionIdx: number) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: actionIdx }));
    }
  }, []);

  return { ...state, sendAction };
}
