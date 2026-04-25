"""Enemy king danger evaluation feature."""

from core.board import Board
from core.move_generation import is_square_attacked
from core.types import piece_color, piece_type, opponent_color


def enemy_king_danger(board: Board, color: str) -> float:
    """How much danger the enemy king is in.

    Per own piece: += 1 / max(chebyshev_distance_to_enemy_king, 1)
    Per adjacent enemy king square attacked by color: += 1

    Positive = good for color (enemy king in danger).
    """
    opp = opponent_color(color)
    enemy_king_sq = board.find_king(opp)
    if enemy_king_sq is None:
        return 0.0

    ekr, ekc = enemy_king_sq
    score = 0.0

    # Per own piece: proximity to enemy king
    for row in range(8):
        for col in range(8):
            piece = board.get_piece((row, col))
            if piece is None or piece_color(piece) != color:
                continue
            if piece_type(piece) == "K":
                continue
            dist = max(abs(row - ekr), abs(col - ekc))
            score += 1.0 / max(dist, 1)

    # Per adjacent enemy king square attacked
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            nr, nc = ekr + dr, ekc + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if is_square_attacked(board, (nr, nc), color):
                    score += 1.0

    return score
