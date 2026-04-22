import type { PlayerPublicInfo } from "../types";
import { PLAYER_COLORS } from "../types";

interface Props {
  players: PlayerPublicInfo[];
  currentPlayer: number;
  myPlayerIdx: number;
}

export function Scoreboard({ players, currentPlayer, myPlayerIdx }: Props) {
  return (
    <div className="scoreboard">
      <h3>Players</h3>
      {players.map((p, i) => (
        <div
          key={i}
          className={`player-row ${currentPlayer === i ? "active-player" : ""} ${myPlayerIdx === i ? "my-player" : ""}`}
          style={{ borderLeft: `4px solid ${PLAYER_COLORS[i]}` }}
        >
          <div className="player-name">
            {p.name}
            {p.is_ai && <span className="ai-badge">AI</span>}
            {myPlayerIdx === i && <span className="you-badge">You</span>}
            {currentPlayer === i && <span className="turn-badge">▶ Turn</span>}
          </div>
          <div className="player-stats">
            <span title="Score">🏆 {p.score}</span>
            <span title="Trains remaining">🚂 {p.trains}</span>
            <span title="Stations remaining">🏠 {p.stations}</span>
            <span title="Cards in hand">🃏 {p.hand_total}</span>
            <span title="Tickets">🎫 {p.ticket_count}</span>
          </div>
          {p.station_cities.length > 0 && (
            <div className="station-cities">
              Stations: {p.station_cities.join(", ")}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
