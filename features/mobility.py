"""Mobility evaluation feature."""

from core.board import Board
from core.move_generation import generate_moves_for_color
from core.types import opponent_color


def mobility(board: Board, color: str) -> float:
    """Own pseudo-legal move count minus opponent pseudo-legal move count.

    Positive = more mobile for color.
    """
    own_moves = len(generate_moves_for_color(board, color))
    opp_moves = len(generate_moves_for_color(board, opponent_color(color)))
    return float(own_moves - opp_moves)
