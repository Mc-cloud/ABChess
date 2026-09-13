(function () {
  // TODO: replace with your deployed backend URL, e.g. https://your-app.onrender.com/move
  const BACKEND_URL = "https://abchess.onrender.com/move";

  const game = new Chess();
  let board = null;
  let playerColor = "w";
  let botThinking = false;

  const consoleEl = document.getElementById("console");
  const moveListEl = document.getElementById("moveList");
  const statusEl = document.getElementById("status");

  function log(line) {
    const p = document.createElement("div");
    p.className = "console-line";
    p.textContent = line;
    consoleEl.appendChild(p);
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  function clearConsole() {
    consoleEl.innerHTML = "";
  }

  function updateMoveList() {
    moveListEl.innerHTML = "";
    const history = game.history();
    for (let i = 0; i < history.length; i += 2) {
      const li = document.createElement("li");
      const white = history[i] || "";
      const black = history[i + 1] || "";
      li.textContent = black ? `${white}   ${black}` : white;
      moveListEl.appendChild(li);
    }
  }

  function updateStatus() {
    let text;
    if (game.in_checkmate()) {
      text = (game.turn() === "w" ? "White" : "Black") + " is checkmated.";
    } else if (game.in_draw()) {
      text = "Draw.";
    } else if (game.in_check()) {
      text = (game.turn() === "w" ? "White" : "Black") + " is in check.";
    } else {
      text = (game.turn() === "w" ? "White" : "Black") + " to move.";
    }
    statusEl.textContent = text;
  }

  function onDragStart(source, piece) {
    if (game.game_over() || botThinking) return false;
    if (game.turn() !== playerColor) return false;
    if (
      (playerColor === "w" && piece.startsWith("b")) ||
      (playerColor === "b" && piece.startsWith("w"))
    ) {
      return false;
    }
  }

  function onDrop(source, target) {
    const move = game.move({ from: source, to: target, promotion: "q" });
    if (move === null) return "snapback";

    updateMoveList();
    updateStatus();
    log(`you play ${move.san}`);

    if (game.game_over()) {
      announceGameOver();
      return;
    }
    requestBotMove();
  }

  function onSnapEnd() {
    board.position(game.fen());
  }

  function requestBotMove() {
    botThinking = true;
    log("bot is thinking\u2026");

    fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fen: game.fen() }),
    })
      .then((res) => {
        if (!res.ok) throw new Error(`server responded ${res.status}`);
        return res.json();
      })
      .then((data) => {
        const uci = data.move;
        if (!uci) throw new Error("no move returned");

        const from = uci.slice(0, 2);
        const to = uci.slice(2, 4);
        const promotion = uci.length > 4 ? uci.slice(4, 5) : "q";

        const move = game.move({ from, to, promotion });
        if (move === null) {
          throw new Error(`engine returned an illegal move: ${uci}`);
        }

        board.position(game.fen());
        updateMoveList();
        updateStatus();

        const evalNote =
          typeof data.eval === "number" ? `  (eval ${(data.eval / 100).toFixed(2)})` : "";
        log(`bot plays ${move.san}${evalNote}`);

        if (game.game_over()) announceGameOver();
      })
      .catch((err) => {
        log(`error: ${err.message}`);
        log("the backend may still be waking up \u2014 try again in a moment.");
      })
      .finally(() => {
        botThinking = false;
      });
  }

  function announceGameOver() {
    if (game.in_checkmate()) log("checkmate.");
    else if (game.in_stalemate()) log("stalemate.");
    else if (game.in_draw()) log("draw.");
  }

  function newGame() {
    game.reset();
    clearConsole();
    updateMoveList();
    updateStatus();
    board.start();
    log("new game started.");
    if (playerColor === "b") requestBotMove();
  }

  document.getElementById("newGameBtn").addEventListener("click", newGame);
  document.getElementById("flipBtn").addEventListener("click", () => board.flip());
  document.getElementById("sideSelect").addEventListener("change", (e) => {
    playerColor = e.target.value === "white" ? "w" : "b";
    newGame();
    board.orientation(e.target.value);
  });

  window.addEventListener("resize", () => board.resize());

  board = Chessboard("board", {
    draggable: true,
    position: "start",
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    pieceTheme:
      "https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/img/chesspieces/wikipedia/{piece}.png",
  });

  updateStatus();
  log("board ready \u2014 move a piece to begin.");
})();