"""Game simulation for EngineLab.

Plays a game between two agents using the specified variant rules.
Provides both real play_game() and mock_play_game() for development.
"""

import random
from dataclasses import dataclass

from core.board import Board
from core.move_generation import is_in_check
from agents.feature_subset_agent import FeatureSubsetAgent
from search.alpha_beta import AlphaBetaEngine
from simulation.random_agent import RandomAgent
from variants.base import get_apply_move, get_generate_legal_moves


@dataclass
class GameResult:
    """Result of a completed game."""

    white_agent: str
    black_agent: str
    winner: str | None        # "w", "b", or None (draw)
    moves: int                # total plies
    termination_reason: str   # "checkmate" | "stalemate" | "move_cap"
    white_avg_nodes: float
    black_avg_nodes: float
    white_avg_time: float
    black_avg_time: float


def mock_play_game(
    white_agent: FeatureSubsetAgent | RandomAgent,
    black_agent: FeatureSubsetAgent | RandomAgent,
    **kwargs,
) -> GameResult:
    """Mock game for development — returns random GameResult.

    Uses seeded RNG for determinism. No ENGINE imports required.
    """
    rng = random.Random(kwargs.get("seed", 42))
    return GameResult(
        white_agent=white_agent.name,
        black_agent=black_agent.name,
        winner=rng.choice(["w", "b", None]),
        moves=rng.randint(10, 80),
        termination_reason="move_cap",
        white_avg_nodes=0.0,
        black_avg_nodes=0.0,
        white_avg_time=0.0,
        black_avg_time=0.0,
    )


def play_game(
    white_agent: FeatureSubsetAgent | RandomAgent,
    black_agent: FeatureSubsetAgent | RandomAgent,
    variant: str = "standard",
    depth: int = 1,
    max_moves: int = 80,
    seed: int | None = None,
) -> GameResult:
    """Play a complete game between two agents.

    Supports FeatureSubsetAgent (uses AlphaBetaEngine) and RandomAgent.
    Returns a GameResult with outcome and statistics.
    """
    board = Board.starting_position()
    apply_fn = get_apply_move(variant)
    gen_legal_fn = get_generate_legal_moves(variant)

    # Build engines for each side
    white_engine = _make_engine(white_agent, depth, seed)
    black_engine = _make_engine(black_agent, depth, seed)

    white_nodes: list[int] = []
    black_nodes: list[int] = []
    white_times: list[float] = []
    black_times: list[float] = []

    for ply in range(max_moves):
        legal = gen_legal_fn(board)

        if not legal:
            color = board.side_to_move
            if is_in_check(board, color):
                winner = "b" if color == "w" else "w"
                return GameResult(
                    white_agent=white_agent.name,
                    black_agent=black_agent.name,
                    winner=winner,
                    moves=ply,
                    termination_reason="checkmate",
                    white_avg_nodes=_avg(white_nodes),
                    black_avg_nodes=_avg(black_nodes),
                    white_avg_time=_avg(white_times),
                    black_avg_time=_avg(black_times),
                )
            else:
                return GameResult(
                    white_agent=white_agent.name,
                    black_agent=black_agent.name,
                    winner=None,
                    moves=ply,
                    termination_reason="stalemate",
                    white_avg_nodes=_avg(white_nodes),
                    black_avg_nodes=_avg(black_nodes),
                    white_avg_time=_avg(white_times),
                    black_avg_time=_avg(black_times),
                )

        if board.side_to_move == "w":
            move, nodes, time_s = _choose_move(white_engine, board, variant)
            white_nodes.append(nodes)
            white_times.append(time_s)
        else:
            move, nodes, time_s = _choose_move(black_engine, board, variant)
            black_nodes.append(nodes)
            black_times.append(time_s)

        board = apply_fn(board, move)

    return GameResult(
        white_agent=white_agent.name,
        black_agent=black_agent.name,
        winner=None,
        moves=max_moves,
        termination_reason="move_cap",
        white_avg_nodes=_avg(white_nodes),
        black_avg_nodes=_avg(black_nodes),
        white_avg_time=_avg(white_times),
        black_avg_time=_avg(black_times),
    )


def _make_engine(
    agent: FeatureSubsetAgent | RandomAgent, depth: int, seed: int | None
) -> AlphaBetaEngine | RandomAgent:
    """Create the appropriate engine for an agent."""
    if isinstance(agent, RandomAgent):
        return agent
    return AlphaBetaEngine(agent, depth)


def _choose_move(
    engine: AlphaBetaEngine | RandomAgent,
    board: Board,
    variant: str,
) -> tuple:
    """Choose a move and return (move, nodes_searched, time_seconds)."""
    if isinstance(engine, RandomAgent):
        move = engine.choose_move(board, variant)
        return move, 0, 0.0
    move = engine.choose_move(board)
    return move, engine.nodes_searched, engine.search_time_seconds


def _avg(values: list[int | float]) -> float:
    """Average of a list, 0.0 if empty."""
    if not values:
        return 0.0
    return sum(values) / len(values)
