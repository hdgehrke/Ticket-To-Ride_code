import { COLOR_HEX, COLOR_NAMES, COLORS, LOCO } from "../types";

interface Props {
  hand: Record<string, number>;
}

export function PlayerHand({ hand }: Props) {
  const allColors = [...COLORS, LOCO];
  return (
    <div className="player-hand">
      <h3>Your Hand</h3>
      <div className="hand-row">
        {allColors.map(c => {
          const count = hand[c] ?? 0;
          if (count === 0) return null;
          return (
            <div
              key={c}
              className="hand-card"
              style={{ background: COLOR_HEX[c], color: c === "W" ? "#111" : "#fff" }}
              title={COLOR_NAMES[c]}
            >
              <span className="card-color">{c}</span>
              <span className="card-count">×{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
