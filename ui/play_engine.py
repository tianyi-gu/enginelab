"""Play-against-engine logic for the EngineLab Streamlit UI.

Uses the real AlphaBetaEngine with the specified agent's feature subset.
Falls back to random legal moves if the engine fails.
"""
from __future__ import annotations

import random

import chess

from core.board import Board
from agents.feature_subset_agent import FeatureSubsetAgent
from search.alpha_beta import AlphaBetaEngine


def engine_reply(
    fen: str,
    agent: FeatureSubsetAgent | None = None,
    depth: int = 2,
    variant: str = "standard",
    move_index: int = 0,
) -> str | None:
    """Return a UCI move for the given position using the real engine.

    Args:
        fen: Current board FEN.
        agent: The FeatureSubsetAgent to use. Falls back to random if None.
        depth: Search depth for alpha-beta.
        variant: Chess variant.
        move_index: Fallback seed offset if engine is not available.

    Returns:
        UCI string or None if the game is already over.
    """
    board_chess = chess.Board(fen)
    if board_chess.is_game_over():
        return None
    legal = list(board_chess.legal_moves)
    if not legal:
        return None

    if agent is not None:
        try:
            board = Board.from_fen(fen)
            engine = AlphaBetaEngine(agent, depth, variant=variant)
            move = engine.choose_move(board)
            return move.to_uci()
        except Exception:
            pass

    # Fallback: random legal move
    rng = random.Random(42 + move_index)
    return rng.choice(legal).uci()


def apply_san_move(fen: str, san: str) -> tuple[str, str]:
    """Parse and apply a SAN move string to the given position.

    Args:
        fen: Current board FEN.
        san: Move in Standard Algebraic Notation (e.g. "e4", "Nf3", "O-O").

    Returns:
        (new_fen, uci_string) after the move is applied.

    Raises:
        ValueError: If the move is illegal or cannot be parsed.
    """
    board = chess.Board(fen)
    try:
        move = board.parse_san(san)
    except Exception as exc:
        raise ValueError(f"Cannot parse move '{san}': {exc}") from exc
    if move not in board.legal_moves:
        raise ValueError(f"Illegal move: {san}")
    uci = move.uci()
    board.push(move)
    return board.fen(), uci


def game_status(fen: str) -> str:
    """Classify the game state for a given FEN.

    Returns:
        'checkmate' | 'stalemate' | 'draw' | 'ongoing'
    """
    board = chess.Board(fen)
    if board.is_checkmate():
        return "checkmate"
    if board.is_stalemate():
        return "stalemate"
    if (
        board.is_insufficient_material()
        or board.is_seventyfive_moves()
        or board.is_fivefold_repetition()
    ):
        return "draw"
    return "ongoing"
