"""Three-Check variant for EngineLab.

Standard chess rules plus an extra win condition: deliver three checks
to the opponent and you win.  The check counter is tracked on
``board.check_count`` (a dict ``{"w": int, "b": int}``).
"""

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_legal_moves, is_in_check
from core.types import opponent_color


def apply_three_check_move(board: Board, move: Move) -> Board:
    """Apply move under Three-Check rules. Returns new Board."""
    mover = board.side_to_move
    new_board = apply_move(board, move)

    # After the move, check if the opponent is now in check
    opp = opponent_color(mover)
    if is_in_check(new_board, opp):
        new_board.check_count[mover] = new_board.check_count.get(mover, 0) + 1
        if new_board.check_count[mover] >= 3:
            new_board.winner = mover
    return new_board


def generate_three_check_moves(board: Board) -> list[Move]:
    """Legal moves for Three-Check (same as standard)."""
    return generate_legal_moves(board)
