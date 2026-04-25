"""Bishop pair evaluation feature."""

from core.board import Board
from core.types import piece_color, opponent_color


def bishop_pair(board: Board, color: str) -> float:
    """+0.5 if own side has 2+ bishops, else 0. Minus opponent's bonus.

    Positive = good for color.
    """
    own = _count_bishops(board, color)
    opp = _count_bishops(board, opponent_color(color))
    own_bonus = 0.5 if own >= 2 else 0.0
    opp_bonus = 0.5 if opp >= 2 else 0.0
    return own_bonus - opp_bonus


def _count_bishops(board: Board, color: str) -> int:
    """Count bishops for a given color."""
    bishop = "B" if color == "w" else "b"
    count = 0
    for row in range(8):
        for col in range(8):
            if board.get_piece((row, col)) == bishop:
                count += 1
    return count
