import { PLAYER_COLORS } from "../types";

interface Props {
  scores: number[];
  players: string[];
  onNewGame: () => void;
}

export function GameOver({ scores, players, onNewGame }: Props) {
  const ranked = players
    .map((name, i) => ({ name, score: scores[i], idx: i }))
    .sort((a, b) => b.score - a.score);

  return (
    <div className="game-over-overlay">
      <div className="game-over-box">
        <h2>Game Over!</h2>
        <ol className="final-scores">
          {ranked.map((p, rank) => (
            <li key={p.idx} className={rank === 0 ? "winner" : ""}>
              <span
                className="player-dot"
                style={{ background: PLAYER_COLORS[p.idx] }}
              />
              <strong>{p.name}</strong>: {p.score} pts
              {rank === 0 && " 🏆"}
            </li>
          ))}
        </ol>
        <button onClick={onNewGame} className="btn-primary">New Game</button>
      </div>
    </div>
  );
}
