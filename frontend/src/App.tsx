import { useState } from "react";
import { Lobby } from "./components/Lobby";
import { GameBoard } from "./components/GameBoard";
import "./App.css";

interface GameView {
  sessionId: string;
  playerIdx: number;
}

function App() {
  const [game, setGame] = useState<GameView | null>(null);

  function joinGame(sessionId: string, playerIdx: number) {
    setGame({ sessionId, playerIdx });
  }

  function leaveGame() {
    setGame(null);
  }

  if (game) {
    return (
      <GameBoard
        sessionId={game.sessionId}
        playerIdx={game.playerIdx}
        onLeave={leaveGame}
      />
    );
  }

  return <Lobby onJoin={joinGame} />;
}

export default App;
