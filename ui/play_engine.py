"""Pure-Python play-against-engine logic — no Streamlit dependency, fully testable."""
from __future__ import annotations

import random

import chess


def engine_reply(fen: str, move_index: int = 0) -> str | None:
    """Return a seeded-random legal UCI move for the given position.

    Args:
        fen: Current board FEN.
        move_index: Number of moves played so far (used as seed offset for variety).

    Returns:
        UCI string or None if the game is already over.
    """
    board = chess.Board(fen)
    if board.is_game_over():
        return None
    legal = list(board.legal_moves)
    if not legal:
        return None
    rng = random.Random(42 + move_index)
    return rng.choice(legal).uci()


def apply_san_move(fen: str, san: str) -> tuple[str, str]:
    """Parse and apply a SAN move string to the given position.

    Args:
        fen: Current board FEN.
        san: Move in Standard Algebraic Notation (e.g. "e4", "Nf3", "O-O").

    Returns:
        (new_fen, uci_string) after the move is applied.

    Raises:
        ValueError: If the move is illegal or cannot be parsed.
    """
    board = chess.Board(fen)
    try:
        move = board.parse_san(san)
    except Exception as exc:
        raise ValueError(f"Cannot parse move '{san}': {exc}") from exc
    if move not in board.legal_moves:
        raise ValueError(f"Illegal move: {san}")
    uci = move.uci()
    board.push(move)
    return board.fen(), uci


def game_status(fen: str) -> str:
    """Classify the game state for a given FEN.

    Returns:
        'checkmate' | 'stalemate' | 'draw' | 'ongoing'
    """
    board = chess.Board(fen)
    if board.is_checkmate():
        return "checkmate"
    if board.is_stalemate():
        return "stalemate"
    if (
        board.is_insufficient_material()
        or board.is_seventyfive_moves()
        or board.is_fivefold_repetition()
    ):
        return "draw"
    return "ongoing"
