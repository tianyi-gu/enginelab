"""Random agent — stub for Area 1 implementation."""

from core.board import Board
from core.move import Move


class RandomAgent:
    """Selects a move uniformly at random from legal moves."""

    name: str = "RandomAgent"

    def choose_move(self, board: Board) -> Move:
        """Choose a random legal move. Stub — to be implemented in Area 1."""
        raise NotImplementedError("RandomAgent not yet implemented")
