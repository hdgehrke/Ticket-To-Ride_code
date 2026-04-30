import { useState } from "react";
import { useGameWS } from "../api/ws";
import { MapSVG } from "./MapSVG";
import { FaceUpCards } from "./FaceUpCards";
import { PlayerHand } from "./PlayerHand";
import { TicketPanel } from "./TicketPanel";
import { Scoreboard } from "./Scoreboard";
import { ActionBar } from "./ActionBar";
import { GameOver } from "./GameOver";
import { TunnelModal } from "./TunnelModal";
import type { Ticket } from "../types";

interface Props {
  sessionId: string;
  playerIdx: number;
  onLeave: () => void;
}

export function GameBoard({ sessionId, playerIdx, onLeave }: Props) {
  const { publicState, privateState, gameOver, error, connected, sendAction } = useGameWS(sessionId, playerIdx);
  const [hoveredTicket, setHoveredTicket] = useState<Ticket | null>(null);

  if (!connected && !publicState) {
    return (
      <div className="connecting">
        <p>Connecting to game…</p>
        <button onClick={onLeave} className="btn-small">Back to Lobby</button>
      </div>
    );
  }

  if (gameOver) {
    return <GameOver scores={gameOver.scores} players={gameOver.players} breakdown={gameOver.breakdown} onNewGame={onLeave} />;
  }

  if (!publicState || !privateState) {
    return <div className="connecting"><p>Loading game state…</p></div>;
  }

  const isMyTurn = publicState.current_player === playerIdx;
  const phase = publicState.phase;

  function handleFaceUp(slot: number) {
    const isSecond = phase === "SECOND_DRAW";
    sendAction(isSecond ? 7 + slot : slot);
  }

  function handleDrawDeck() {
    sendAction(phase === "SECOND_DRAW" ? 12 : 5);
  }

  const isTunnelResolution = publicState.phase === "TUNNEL_RESOLUTION";

  return (
    <div className="game-board">
      {error && (
        <div className="error-toast">{error}</div>
      )}

      {isTunnelResolution && publicState.tunnel_cards && (
        <TunnelModal
          revealedCards={publicState.tunnel_cards}
          extraCost={publicState.tunnel_extra_cost ?? 0}
          payAction={publicState.tunnel_pay_action!}
          declineAction={publicState.tunnel_decline_action!}
          isMyTurn={isMyTurn}
          onAction={sendAction}
        />
      )}

      <div className="board-layout">
        {/* Left: Map */}
        <div className="map-panel">
          <MapSVG
            publicState={publicState}
            privateState={privateState}
            isMyTurn={isMyTurn}
            playerIdx={playerIdx}
            hoveredTicket={hoveredTicket}
            onAction={sendAction}
          />
        </div>

        {/* Right: Sidebar */}
        <div className="sidebar">
          <ActionBar
            publicState={publicState}
            privateState={privateState}
            isMyTurn={isMyTurn}
            onAction={sendAction}
          />
          <Scoreboard
            players={publicState.players}
            currentPlayer={publicState.current_player}
            myPlayerIdx={playerIdx}
          />
          <FaceUpCards
            faceUp={publicState.face_up}
            deckSize={publicState.deck_size}
            discardSize={publicState.discard_size}
            legalActions={privateState.legal_actions}
            isMyTurn={isMyTurn}
            phase={phase}
            onDrawFaceUp={handleFaceUp}
            onDrawDeck={handleDrawDeck}
          />
          <PlayerHand hand={privateState.hand} />
          <TicketPanel
            tickets={privateState.tickets}
            pendingTickets={privateState.pending_tickets}
            legalActions={privateState.legal_actions}
            isMyTurn={isMyTurn}
            phase={phase}
            onKeepTickets={sendAction}
            onDrawTickets={() => sendAction(6)}
            onTicketHover={setHoveredTicket}
          />
          <button onClick={onLeave} className="btn-small leave-btn">Leave Game</button>
        </div>
      </div>
    </div>
  );
}
