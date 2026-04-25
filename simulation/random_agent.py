"""Random agent for EngineLab baseline comparisons."""

import random

from core.board import Board
from core.move import Move
from variants.base import get_generate_legal_moves


class RandomAgent:
    """Selects a move uniformly at random from legal moves."""

    name: str = "RandomAgent"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def choose_move(self, board: Board, variant: str = "standard") -> Move:
        """Choose a random legal move for the given variant."""
        moves = get_generate_legal_moves(variant)(board)
        if not moves:
            raise ValueError("No legal moves available")
        return self._rng.choice(moves)
