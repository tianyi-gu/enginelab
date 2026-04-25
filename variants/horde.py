"""Horde variant for EngineLab.

White starts with 36 pawns (filling ranks 1-4 with extras on rank 5)
and no king.  Black has the standard starting pieces.

White wins by checkmating Black's king.
Black wins by capturing all of White's pieces.
"""

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import (
    generate_legal_moves,
    generate_moves,
    is_in_check,
)
from core.types import is_white, opponent_color


def horde_starting_position() -> Board:
    """Create the Horde starting position.

    White: pawns on ranks 1-4 (rows 0-3) = 32 pawns,
           plus pawns on b5, c5, f5, g5 (row 4) = 4 extra = 36 total.
    Black: standard back rank + pawns.
    No white king.
    """
    board = Board()
    # White pawns on rows 0-3 (ranks 1-4)
    for r in range(4):
        board.grid[r] = ["P"] * 8
    # Extra pawns on row 4 (rank 5): b5, c5, f5, g5
    board.grid[4] = [None] * 8
    board.grid[4][1] = "P"  # b5
    board.grid[4][2] = "P"  # c5
    board.grid[4][5] = "P"  # f5
    board.grid[4][6] = "P"  # g5
    # Rows 5 empty
    board.grid[5] = [None] * 8
    # Black pawns on row 6 (rank 7)
    board.grid[6] = ["p"] * 8
    # Black pieces on row 7 (rank 8)
    board.grid[7] = ["r", "n", "b", "q", "k", "b", "n", "r"]
    # White has no king — disable all white castling
    board.castling_rights = {"K": False, "Q": False, "k": True, "q": True}
    return board


def _white_has_pieces(board: Board) -> bool:
    """Return True if white has any pieces left on the board."""
    for row in range(8):
        for col in range(8):
            piece = board.grid[row][col]
            if piece is not None and is_white(piece):
                return True
    return False


def apply_horde_move(board: Board, move: Move) -> Board:
    """Apply move under Horde rules. Returns new Board."""
    new_board = apply_move(board, move)

    # Check if white has been wiped out
    if not _white_has_pieces(new_board):
        new_board.winner = "b"

    return new_board


def generate_horde_moves(board: Board) -> list[Move]:
    """Legal moves for Horde.

    White has no king, so no check-filtering is needed for white.
    Black uses standard legal move generation (check-filtered).
    """
    if board.side_to_move == "w":
        # No king means no check filtering — all pseudo-legal moves are legal
        return generate_moves(board)
    else:
        return generate_legal_moves(board)
