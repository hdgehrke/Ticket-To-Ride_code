import type { PrivateState, PublicState } from "../types";

interface Props {
  publicState: PublicState;
  privateState: PrivateState;
  isMyTurn: boolean;
  onAction: (actionIdx: number) => void;
}

export function ActionBar({ publicState, isMyTurn }: Props) {
  const { phase, players, current_player } = publicState;

  const currentName = players[current_player]?.name ?? "";

  const phaseLabels: Record<string, string> = {
    MAIN_TURN: "Main Turn",
    SECOND_DRAW: "Second Draw",
    TICKET_SELECTION: "Ticket Selection",
    INITIAL_TICKET_SELECTION: "Initial Ticket Selection",
    MEGA_LONG_SELECTION: "Long Route Selection",
    FINAL_ROUND: "Final Round",
    GAME_OVER: "Game Over",
  };

  return (
    <div className="action-bar">
      <div className="phase-info">
        <span className="phase-label">{phaseLabels[phase] ?? phase}</span>
        <span className="turn-info">
          {isMyTurn ? "Your turn" : `Waiting for ${currentName}…`}
        </span>
      </div>
    </div>
  );
}
