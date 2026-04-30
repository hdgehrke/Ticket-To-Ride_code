import { COLOR_HEX, COLOR_NAMES } from "../types";

interface Props {
  revealedCards: string[];
  extraCost: number;
  payAction: number;
  declineAction: number;
  isMyTurn: boolean;
  onAction: (actionIdx: number) => void;
}

function CardBadge({ color }: { color: string }) {
  const bg = COLOR_HEX[color] ?? "#9CA3AF";
  const label = COLOR_NAMES[color] ?? color;
  const textColor = color === "W" ? "#111" : "#fff";
  return (
    <span
      className="tunnel-card-badge"
      style={{ background: bg, color: textColor }}
      title={label}
    >
      {color}
    </span>
  );
}

export function TunnelModal({ revealedCards, extraCost, payAction, declineAction, isMyTurn, onAction }: Props) {
  return (
    <div className="tunnel-overlay">
      <div className="tunnel-modal">
        <h3>Tunnel Resolution</h3>
        <p>Three cards were revealed:</p>
        <div className="tunnel-cards-row">
          {revealedCards.map((c, i) => <CardBadge key={i} color={c} />)}
        </div>
        {extraCost === 0 ? (
          <p className="tunnel-free">No match — no extra cost! Route claimed for free.</p>
        ) : (
          <p>
            <strong>{extraCost}</strong> matching card{extraCost > 1 ? "s" : ""} revealed.
            {isMyTurn
              ? ` Pay ${extraCost} extra card${extraCost > 1 ? "s" : ""} to complete the claim?`
              : " Waiting for the current player to decide…"}
          </p>
        )}
        {isMyTurn && (
          <div className="tunnel-actions">
            <button
              className="btn-primary"
              onClick={() => onAction(payAction)}
            >
              {extraCost === 0 ? "Claim Route" : `Pay ${extraCost} Extra`}
            </button>
            {extraCost > 0 && (
              <button
                className="btn-secondary"
                onClick={() => onAction(declineAction)}
              >
                Abandon
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
