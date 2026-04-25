"""Rook activity evaluation feature."""

from core.board import Board
from core.types import piece_color, piece_type, opponent_color


def rook_activity(board: Board, color: str) -> float:
    """+0.5 open file, +0.25 semi-open, +0.5 on 7th rank.

    Computed for own rooks minus opponent rooks.
    Positive = good for color.
    """
    own = _evaluate_rooks(board, color)
    opp = _evaluate_rooks(board, opponent_color(color))
    return own - opp


def _evaluate_rooks(board: Board, color: str) -> float:
    """Evaluate rook activity for a single color."""
    rook = "R" if color == "w" else "r"
    own_pawn = "P" if color == "w" else "p"
    opp_pawn = "p" if color == "w" else "P"
    seventh_rank = 6 if color == "w" else 1

    score = 0.0
    for row in range(8):
        for col in range(8):
            if board.get_piece((row, col)) != rook:
                continue

            # Check file status
            has_own_pawn = False
            has_opp_pawn = False
            for r in range(8):
                p = board.get_piece((r, col))
                if p == own_pawn:
                    has_own_pawn = True
                elif p == opp_pawn:
                    has_opp_pawn = True

            if not has_own_pawn and not has_opp_pawn:
                score += 0.5  # Open file
            elif not has_own_pawn:
                score += 0.25  # Semi-open file

            # 7th rank bonus
            if row == seventh_rank:
                score += 0.5

    return score
