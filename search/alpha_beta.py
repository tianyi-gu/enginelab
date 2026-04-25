"""Alpha-beta negamax search engine for EngineLab.

Production alpha-beta with:
- Variant-aware move generation and application
- Move ordering: captures first, sorted by victim value descending
- Configurable depth
- Node count and timing instrumentation
"""

import time

from core.board import Board
from core.move import Move
from core.types import opponent_color
from agents.feature_subset_agent import FeatureSubsetAgent
from agents.evaluation import evaluate, WIN_SCORE, LOSS_SCORE
from variants.base import get_apply_move, get_generate_legal_moves

_PIECE_VALUES = {
    "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100,
    "p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100,
}


class AlphaBetaEngine:
    """Alpha-beta search engine using negamax formulation."""

    def __init__(
        self,
        agent: FeatureSubsetAgent,
        depth: int,
        variant: str = "standard",
    ) -> None:
        self.agent = agent
        self.depth = depth
        self.variant = variant
        self._apply_fn = get_apply_move(variant)
        self._gen_legal_fn = get_generate_legal_moves(variant)
        self._nodes_searched = 0
        self._search_time = 0.0

    @property
    def nodes_searched(self) -> int:
        return self._nodes_searched

    @property
    def search_time_seconds(self) -> float:
        return self._search_time

    def choose_move(self, board: Board) -> Move:
        """Select the best move by alpha-beta search."""
        start_time = time.monotonic()
        self._nodes_searched = 0

        legal = self._gen_legal_fn(board)
        if not legal:
            raise ValueError("No legal moves available")

        legal = self._order_moves(board, legal)

        best_move = legal[0]
        best_score = float("-inf")
        color = board.side_to_move

        for move in legal:
            new_board = self._apply_fn(board, move)
            score = -self._negamax(
                new_board, self.depth - 1,
                float("-inf"), float("inf"),
                opponent_color(color),
            )
            if score > best_score:
                best_score = score
                best_move = move

        self._search_time = time.monotonic() - start_time
        return best_move

    def _negamax(
        self, board: Board, depth: int,
        alpha: float, beta: float, color: str,
    ) -> float:
        """Negamax with alpha-beta pruning."""
        self._nodes_searched += 1

        if board.is_terminal():
            return evaluate(board, color, self.agent)

        if depth == 0:
            return evaluate(board, color, self.agent)

        legal = self._gen_legal_fn(board)
        if not legal:
            from core.move_generation import is_in_check
            if is_in_check(board, color):
                return LOSS_SCORE
            return 0.0

        legal = self._order_moves(board, legal)

        best = float("-inf")
        for move in legal:
            new_board = self._apply_fn(board, move)
            score = -self._negamax(
                new_board, depth - 1, -beta, -alpha,
                opponent_color(color),
            )
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        return best

    @staticmethod
    def _order_moves(board: Board, moves: list[Move]) -> list[Move]:
        """Order moves: captures first (by victim value descending), then quiet."""
        captures: list[tuple[int, Move]] = []
        non_captures: list[Move] = []
        for move in moves:
            target = board.get_piece(move.end)
            if target is not None:
                value = _PIECE_VALUES.get(target, 0)
                captures.append((value, move))
            else:
                non_captures.append(move)
        captures.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in captures] + non_captures
