"""Material evaluation feature."""

from core.board import Board
from core.types import piece_color

_PIECE_VALUES = {
    "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9,
    "p": 1, "n": 3, "b": 3, "r": 5, "q": 9,
}


def material(board: Board, color: str) -> float:
    """Own material minus opponent material. Kings excluded."""
    own = 0
    opp = 0
    for row in range(8):
        for col in range(8):
            piece = board.get_piece((row, col))
            if piece is None or piece.upper() == "K":
                continue
            value = _PIECE_VALUES.get(piece, 0)
            if piece_color(piece) == color:
                own += value
            else:
                opp += value
    return float(own - opp)
