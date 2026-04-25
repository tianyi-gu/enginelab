"""Center control evaluation feature."""

from core.board import Board
from core.move_generation import is_square_attacked
from core.types import piece_color, opponent_color

_CENTER_SQUARES = [(3, 3), (3, 4), (4, 3), (4, 4)]  # d4, e4, d5, e5


def center_control(board: Board, color: str) -> float:
    """Pieces on/attacking center squares. Center pieces count 2x.

    Positive = good for color.
    """
    opp = opponent_color(color)
    score = 0.0

    for sq in _CENTER_SQUARES:
        piece = board.get_piece(sq)

        # Piece on center square (2x bonus)
        if piece is not None:
            if piece_color(piece) == color:
                score += 2.0
            else:
                score -= 2.0

        # Attacking the center square
        if is_square_attacked(board, sq, color):
            score += 1.0
        if is_square_attacked(board, sq, opp):
            score -= 1.0

    return score
