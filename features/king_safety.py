"""King safety evaluation feature."""

from core.board import Board
from core.types import piece_color, piece_type, opponent_color


def king_safety(board: Board, color: str) -> float:
    """+1 per adjacent own pawn, -1 per open file near king,
    -0.5 per enemy piece within Chebyshev distance 3.

    Positive = safer king for color.
    """
    king_sq = board.find_king(color)
    if king_sq is None:
        return 0.0

    kr, kc = king_sq
    opp = opponent_color(color)
    score = 0.0

    # +1 per adjacent own pawn
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = kr + dr, kc + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = board.get_piece((nr, nc))
                if piece is not None and piece_color(piece) == color and piece_type(piece) == "P":
                    score += 1.0

    # -1 per open file near king (files within 1 of king)
    for fc in range(max(0, kc - 1), min(8, kc + 2)):
        has_own_pawn = False
        for row in range(8):
            piece = board.get_piece((row, fc))
            if piece is not None and piece_color(piece) == color and piece_type(piece) == "P":
                has_own_pawn = True
                break
        if not has_own_pawn:
            score -= 1.0

    # -0.5 per enemy piece within Chebyshev distance 3
    for row in range(max(0, kr - 3), min(8, kr + 4)):
        for col in range(max(0, kc - 3), min(8, kc + 4)):
            piece = board.get_piece((row, col))
            if piece is not None and piece_color(piece) == opp:
                score -= 0.5

    return score
