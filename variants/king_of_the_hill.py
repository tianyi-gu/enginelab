"""King of the Hill variant for EngineLab.

Standard chess rules plus an extra win condition: if a player's king
reaches one of the four center squares (d4, d5, e4, e5), that player wins.
"""

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_legal_moves, is_in_check
from core.types import opponent_color

# Center squares: d4=(3,3), e4=(3,4), d5=(4,3), e5=(4,4)
_CENTER = {(3, 3), (3, 4), (4, 3), (4, 4)}


def apply_koth_move(board: Board, move: Move) -> Board:
    """Apply move under King of the Hill rules. Returns new Board."""
    # Who is moving (before apply flips side_to_move)
    mover = board.side_to_move
    new_board = apply_move(board, move)

    # Check if mover's king is now on a center square
    king_sq = new_board.find_king(mover)
    if king_sq is not None and king_sq in _CENTER:
        new_board.winner = mover
    return new_board


def generate_koth_moves(board: Board) -> list[Move]:
    """Legal moves for King of the Hill (same as standard)."""
    return generate_legal_moves(board)
