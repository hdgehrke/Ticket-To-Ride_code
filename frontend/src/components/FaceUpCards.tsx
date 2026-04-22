import { COLOR_HEX, COLOR_NAMES } from "../types";

interface Props {
  faceUp: (string | null)[];
  deckSize: number;
  discardSize: number;
  legalActions: number[];
  isMyTurn: boolean;
  phase: string;
  onDrawFaceUp: (slot: number) => void;
  onDrawDeck: () => void;
}

// Action index layout from actions.py
const FACE_UP_FIRST_START = 0;
const DRAW_DECK_FIRST = 5;
const FACE_UP_SECOND_START = 7;
const DRAW_DECK_SECOND = 12;

export function FaceUpCards({
  faceUp, deckSize, discardSize, legalActions, isMyTurn, phase,
  onDrawFaceUp, onDrawDeck,
}: Props) {
  const isSecondDraw = phase === "SECOND_DRAW";

  function canDrawFaceUp(slot: number): boolean {
    if (!isMyTurn) return false;
    const base = isSecondDraw ? FACE_UP_SECOND_START : FACE_UP_FIRST_START;
    return legalActions.includes(base + slot);
  }

  function canDrawDeck(): boolean {
    if (!isMyTurn) return false;
    const action = isSecondDraw ? DRAW_DECK_SECOND : DRAW_DECK_FIRST;
    return legalActions.includes(action);
  }

  return (
    <div className="face-up-cards">
      <h3>Train Cards</h3>
      <div className="card-row">
        {faceUp.map((color, i) => {
          const legal = canDrawFaceUp(i);
          const hex = color ? COLOR_HEX[color] : "#374151";
          return (
            <button
              key={i}
              className={`train-card ${legal ? "legal" : ""}`}
              style={{ background: hex, color: color === "W" ? "#111" : "#fff" }}
              onClick={() => legal && onDrawFaceUp(i)}
              disabled={!legal}
              title={color ? COLOR_NAMES[color] : "Empty"}
            >
              {color ?? "—"}
            </button>
          );
        })}
      </div>
      <div className="deck-row">
        <button
          className={`deck-btn ${canDrawDeck() ? "legal" : ""}`}
          onClick={() => canDrawDeck() && onDrawDeck()}
          disabled={!canDrawDeck()}
          title="Draw from deck"
        >
          Deck ({deckSize})
        </button>
        <span className="discard-count">Discard: {discardSize}</span>
      </div>
      {isSecondDraw && <div className="phase-hint">Pick your second card</div>}
    </div>
  );
}
