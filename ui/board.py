from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
import chess.svg


def render_board(
    fen: str,
    last_move_uci: str | None = None,
    exploded_squares: list[str] | None = None,
    size: int = 400,
    flipped: bool = False,
) -> str:
    """Return SVG string for a chess position.

    Args:
        fen: FEN string for the position.
        last_move_uci: UCI move string e.g. "e2e4" for arrow highlight.
        exploded_squares: list of square names e.g. ["e4","d5"] to highlight orange.
        size: board size in pixels.
        flipped: True to show from black's perspective.

    Returns:
        SVG string representation of the board.
    """
    board = chess.Board(fen)

    lastmove = _parse_uci_move(last_move_uci)
    fill = _build_explosion_fill(exploded_squares)

    svg = chess.svg.board(
        board,
        lastmove=lastmove,
        fill=fill,
        size=size,
        flipped=flipped,
    )
    return svg


def starting_fen() -> str:
    """Return the starting position FEN."""
    return chess.STARTING_FEN


def _parse_uci_move(last_move_uci: str | None) -> chess.Move | None:
    """Parse a UCI move string into a chess.Move, or return None on failure."""
    if not last_move_uci:
        return None
    try:
        return chess.Move.from_uci(last_move_uci)
    except Exception:
        return None


def _build_explosion_fill(exploded_squares: list[str] | None) -> dict[int, str]:
    """Build a fill dict mapping square indices to orange highlight color."""
    fill: dict[int, str] = {}
    if not exploded_squares:
        return fill
    for sq_name in exploded_squares:
        try:
            sq = chess.parse_square(sq_name)
            fill[sq] = "#ff6b3560"
        except Exception:
            pass
    return fill
