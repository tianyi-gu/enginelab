"""Explosion proximity evaluation feature for atomic chess."""

from core.board import Board
from core.types import piece_color


def explosion_proximity(board: Board, color: str) -> float:
    """Own non-pawns adjacent to enemy king minus enemy non-pawns adjacent to own king.

    Positive = you threaten more explosions near their king than they do near yours.
    Pawns are excluded because they are immune to explosions in atomic chess.
    """
    opp = "b" if color == "w" else "w"

    own_king_sq = board.find_king(color)
    enemy_king_sq = board.find_king(opp)

    # Count own non-pawns within Chebyshev distance 1 of enemy king (offensive threat)
    offensive = 0
    if enemy_king_sq is not None:
        ekr, ekc = enemy_king_sq
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = ekr + dr, ekc + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    piece = board.get_piece((nr, nc))
                    if piece is not None and piece_color(piece) == color and piece.upper() != "P":
                        offensive += 1

    # Count enemy non-pawns within Chebyshev distance 1 of own king (defensive exposure)
    defensive = 0
    if own_king_sq is not None:
        okr, okc = own_king_sq
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = okr + dr, okc + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    piece = board.get_piece((nr, nc))
                    if piece is not None and piece_color(piece) == opp and piece.upper() != "P":
                        defensive += 1

    return float(offensive - defensive)
