"""Standard chess variant for EngineLab."""

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_legal_moves


def apply_standard_move(board: Board, move: Move) -> Board:
    """Apply move under standard rules. Returns new Board (no mutation)."""
    return apply_move(board, move)


def generate_standard_moves(board: Board) -> list[Move]:
    """Legal moves for standard chess."""
    return generate_legal_moves(board)
