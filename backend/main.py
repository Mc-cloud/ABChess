import os
import threading
from typing import Optional

import chess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.alphabeta_agent import AlphaBeta_agent

# --- configuration -------------------------------------------------------

# Lock this down to your actual github.io origin once you're live -
# leaving it wide open lets any site on the internet spend your free-tier
# CPU minutes.
ALLOWED_ORIGINS = [
    "https://mc-cloud.github.io",
]

DEFAULT_MOVE_SECONDS = 3.0
MAX_MOVE_SECONDS = 4.0   # hard ceiling - a client can ask for less, never more
MIN_MOVE_SECONDS = 0.5

BOOK_PATH = os.path.join(os.path.dirname(__file__), "book.bin")

# --- engine ----------------------------------------------------------------

# get_move()'s internal formula is time_limit = time_left / 30 + increment / 2,
# then clamped. Passing increment=0 and time_left = seconds * 30 is just a way
# to hand it a plain "think for N seconds" budget through that same formula,
# without touching alphabeta_agent.py.
def seconds_to_time_left(seconds: float) -> float:
    return seconds * 30.0


agent = AlphaBeta_agent(depth=99, time_limit=DEFAULT_MOVE_SECONDS, book_path=BOOK_PATH)

# uvicorn runs sync route handlers in a thread pool, so two requests can
# call agent.get_move() concurrently and stomp on its shared mutable state
# (transposition table, killer moves, node counters). One lock serializes
# that - the free-tier CPU can't usefully run two searches at once anyway.
engine_lock = threading.Lock()

# --- API ---------------------------------------------------------------

app = FastAPI(title="AlphaBeta chess API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class MoveRequest(BaseModel):
    fen: str
    move_seconds: Optional[float] = None


class MoveResponse(BaseModel):
    move: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/move", response_model=MoveResponse)
def get_move(payload: MoveRequest):
    try:
        board = chess.Board(payload.fen)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid FEN")

    if board.is_game_over():
        raise HTTPException(status_code=400, detail="game is already over")

    requested = payload.move_seconds or DEFAULT_MOVE_SECONDS
    target_seconds = max(MIN_MOVE_SECONDS, min(requested, MAX_MOVE_SECONDS))

    with engine_lock:
        try:
            move = agent.get_move(board, time_left=seconds_to_time_left(target_seconds))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"engine error: {exc}")

    if move is None:
        raise HTTPException(status_code=500, detail="engine failed to find a move")

    return MoveResponse(move=move.uci())