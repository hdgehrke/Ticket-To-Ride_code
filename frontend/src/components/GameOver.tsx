import { useState } from "react";
import { PLAYER_COLORS } from "../types";
import type { PlayerScoreBreakdown } from "../types";

interface Props {
  scores: number[];
  players: string[];
  breakdown: PlayerScoreBreakdown[];
  onNewGame: () => void;
}

function sign(n: number): string {
  return n >= 0 ? `+${n}` : `${n}`;
}

function BreakdownTable({ bd }: { bd: PlayerScoreBreakdown }) {
  return (
    <table className="score-breakdown-table">
      <tbody>
        <tr>
          <td>Routes claimed</td>
          <td className="score-cell positive">+{bd.route_score}</td>
        </tr>

        <tr>
          <td>
            Unused stations
            {bd.unused_stations > 0 && (
              <span className="score-detail"> ({bd.unused_stations} × 4)</span>
            )}
          </td>
          <td className={`score-cell ${bd.station_bonus > 0 ? "positive" : "neutral"}`}>
            {sign(bd.station_bonus)}
          </td>
        </tr>

        {bd.tickets.length > 0 && (
          <>
            <tr className="score-section-header">
              <td colSpan={2}>Destination Tickets</td>
            </tr>
            {bd.tickets.map((t, i) => (
              <tr key={i} className={t.completed ? "ticket-done" : "ticket-fail"}>
                <td>
                  <span className="ticket-check">{t.completed ? "✓" : "✗"}</span>
                  {" "}{t.city1} → {t.city2}
                </td>
                <td className={`score-cell ${t.completed ? "positive" : "negative"}`}>
                  {sign(t.completed ? t.points : -t.points)}
                </td>
              </tr>
            ))}
            <tr className="score-subtotal">
              <td>Ticket total</td>
              <td className={`score-cell ${bd.ticket_total >= 0 ? "positive" : "negative"}`}>
                {sign(bd.ticket_total)}
              </td>
            </tr>
          </>
        )}

        {bd.longest_route_bonus > 0 && (
          <tr className="ticket-done">
            <td>
              Longest route
              <span className="score-detail"> ({bd.longest_route_length} segments)</span>
            </td>
            <td className="score-cell positive">+{bd.longest_route_bonus}</td>
          </tr>
        )}
      </tbody>
      <tfoot>
        <tr className="score-total-row">
          <td>Total</td>
          <td className="score-cell">{bd.total}</td>
        </tr>
      </tfoot>
    </table>
  );
}

export function GameOver({ scores, players, breakdown, onNewGame }: Props) {
  const [expanded, setExpanded] = useState<number | null>(0);

  const ranked = players
    .map((name, i) => ({ name, score: scores[i], idx: i }))
    .sort((a, b) => b.score - a.score);

  return (
    <div className="game-over-overlay">
      <div className="game-over-box">
        <h2>Game Over!</h2>

        <ol className="final-rankings">
          {ranked.map((p, rank) => (
            <li key={p.idx}>
              <button
                className={`ranking-row ${rank === 0 ? "winner" : ""} ${expanded === p.idx ? "open" : ""}`}
                onClick={() => setExpanded(expanded === p.idx ? null : p.idx)}
              >
                <span className="player-dot" style={{ background: PLAYER_COLORS[p.idx] }} />
                <span className="ranking-name">
                  {rank + 1}. <strong>{p.name}</strong>
                </span>
                <span className="ranking-score">
                  {p.score} pts{rank === 0 ? " 🏆" : ""}
                </span>
                <span className="expand-arrow">{expanded === p.idx ? "▲" : "▼"}</span>
              </button>

              {expanded === p.idx && breakdown[p.idx] && (
                <div className="breakdown-panel">
                  <BreakdownTable bd={breakdown[p.idx]} />
                </div>
              )}
            </li>
          ))}
        </ol>

        <button onClick={onNewGame} className="btn-primary new-game-btn">New Game</button>
      </div>
    </div>
  );
}
