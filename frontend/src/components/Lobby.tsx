import { useState } from "react";

const API_BASE = `http://${window.location.hostname}:8000`;

interface LobbyProps {
  onJoin: (sessionId: string, playerIdx: number) => void;
}

interface SessionInfo {
  session_id: string;
  player_count: number;
  phase: string;
}

export function Lobby({ onJoin }: LobbyProps) {
  const [numPlayers, setNumPlayers] = useState(2);
  const [names, setNames] = useState(["Player 1", "Player 2", "Player 3", "Player 4", "Player 5"]);
  const [aiSlots, setAiSlots] = useState<boolean[]>([false, true, true, true, true]);
  const [humanSlot, setHumanSlot] = useState(0);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchSessions() {
    try {
      const res = await fetch(`${API_BASE}/games`);
      const data = await res.json();
      setSessions(data.sessions ?? []);
    } catch {
      setSessions([]);
    }
  }

  async function createGame() {
    setLoading(true);
    setError(null);
    const playerNames = names.slice(0, numPlayers);
    const ai: number[] = [];
    for (let i = 0; i < numPlayers; i++) {
      if (i !== humanSlot && aiSlots[i]) ai.push(i);
    }
    try {
      const res = await fetch(`${API_BASE}/games`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_names: playerNames, ai_players: ai }),
      });
      if (!res.ok) {
        const err = await res.json();
        setError(err.detail ?? "Failed to create game");
        return;
      }
      const data = await res.json();
      onJoin(data.session_id, humanSlot);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  function updateName(i: number, val: string) {
    setNames(n => { const a = [...n]; a[i] = val; return a; });
  }

  function toggleAI(i: number) {
    setAiSlots(a => { const b = [...a]; b[i] = !b[i]; return b; });
  }

  return (
    <div className="lobby">
      <h1>Ticket to Ride: Europe</h1>
      <div className="lobby-create">
        <h2>New Game</h2>
        <label>
          Players:&nbsp;
          <select value={numPlayers} onChange={e => setNumPlayers(Number(e.target.value))}>
            {[2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <p className="hint">Select your seat (human player):</p>
        <div className="player-slots">
          {Array.from({ length: numPlayers }).map((_, i) => (
            <div key={i} className={`slot ${humanSlot === i ? "human-slot" : ""}`}>
              <input
                type="radio"
                name="human"
                checked={humanSlot === i}
                onChange={() => setHumanSlot(i)}
              />
              <input
                value={names[i]}
                onChange={e => updateName(i, e.target.value)}
                className="name-input"
              />
              {humanSlot !== i && (
                <label>
                  <input
                    type="checkbox"
                    checked={aiSlots[i]}
                    onChange={() => toggleAI(i)}
                  />&nbsp;AI
                </label>
              )}
              {humanSlot === i && <span className="you-badge">You</span>}
            </div>
          ))}
        </div>
        {error && <p className="error">{error}</p>}
        <button onClick={createGame} disabled={loading} className="btn-primary">
          {loading ? "Creating…" : "Start Game"}
        </button>
      </div>

      <div className="lobby-existing">
        <h2>
          Existing Games&nbsp;
          <button onClick={fetchSessions} className="btn-small">Refresh</button>
        </h2>
        {sessions.length === 0 && <p>No active sessions. Start a game above.</p>}
        <ul>
          {sessions.map(s => (
            <li key={s.session_id}>
              <strong>{s.session_id.slice(0, 8)}</strong> — {s.player_count} players — {s.phase}
              {Array.from({ length: s.player_count }).map((_, i) => (
                <button key={i} onClick={() => onJoin(s.session_id, i)} className="btn-small join-btn">
                  Join as P{i}
                </button>
              ))}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
