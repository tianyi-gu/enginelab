"""Antichess variant for EngineLab.

Rules:
- If captures exist, the moving side MUST capture (forced capture).
- Standard move application (no explosions).
- A player who loses all their pieces WINS.
- King has no special status: can be captured like any other piece.
- No castling, no check concept.
"""

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_moves
from core.types import piece_color


def apply_antichess_move(board: Board, move: Move) -> Board:
    """Apply move under Antichess rules. Returns new Board (no mutation).

    Same as standard move application. After the move, checks if
    the moving side has no pieces left — if so, that player wins.
    """
    new_board = apply_move(board, move)

    # Check if either side has no pieces left — that side wins
    for color in ("w", "b"):
        has_pieces = False
        for r in range(8):
            for c in range(8):
                p = new_board.get_piece((r, c))
                if p is not None and piece_color(p) == color:
                    has_pieces = True
                    break
            if has_pieces:
                break
        if not has_pieces:
            new_board.winner = color  # Losing all pieces = winning in antichess
            break

    return new_board


def generate_antichess_moves(board: Board) -> list[Move]:
    """Legal moves under Antichess: if captures exist, return only captures.

    No check legality filtering — king has no special status in antichess.
    Uses pseudo-legal moves (not filtered for check) since check doesn't
    exist in antichess.
    """
    all_moves = generate_moves(board)

    captures = []
    for move in all_moves:
        target = board.get_piece(move.end)
        if target is not None:
            captures.append(move)

    if captures:
        return captures
    return all_moves
