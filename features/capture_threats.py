"""Capture threats evaluation feature."""

from core.board import Board
from core.move import Move
from core.move_generation import generate_moves_for_color
from core.types import piece_color, opponent_color

_PIECE_VALUES = {
    "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0,
    "p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0,
}


def capture_threats(board: Board, color: str) -> float:
    """Sum of capturable piece values. Positive = good for color."""
    own_score = _capture_value(board, color)
    opp_score = _capture_value(board, opponent_color(color))
    return own_score - opp_score


def _capture_value(board: Board, color: str) -> float:
    """Sum values of pieces that color can capture."""
    moves = generate_moves_for_color(board, color)
    total = 0.0
    seen_targets: set[tuple[int, int]] = set()
    for move in moves:
        target = board.get_piece(move.end)
        if target is not None and piece_color(target) != color:
            if move.end not in seen_targets:
                seen_targets.add(move.end)
                total += _PIECE_VALUES.get(target, 0)
    return total
