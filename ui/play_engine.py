"""Play-against-engine logic for the EngineLab Streamlit UI.

Uses the real AlphaBetaEngine with variant-aware move application.
All moves go through the same dispatch system as the CLI and tournaments.
"""
from __future__ import annotations

import random

import chess

from core.board import Board
from core.move import Move
from core.coordinates import algebraic_to_square
from core.move_generation import is_in_check
from agents.feature_subset_agent import FeatureSubsetAgent
from search.alpha_beta import AlphaBetaEngine
from variants.base import get_apply_move, get_generate_legal_moves


def get_legal_moves_uci(fen: str, variant: str) -> list[str]:
    """Return legal moves as UCI strings for the current position."""
    board = Board.from_fen(fen)
    gen_legal_fn = get_generate_legal_moves(variant)
    return sorted(m.to_uci() for m in gen_legal_fn(board))


def apply_move_for_ui(fen: str, uci: str, variant: str) -> dict:
    """Apply a move using real variant logic. Returns new game state.

    Args:
        fen: Current board FEN.
        uci: Move in UCI format (e.g. "e2e4", "a7a8q").
        variant: Chess variant ("standard", "atomic", "antichess").

    Returns:
        dict with keys:
            fen: New board FEN after the move.
            status: "ongoing", "checkmate", "stalemate", or "terminal".
            winner: "w", "b", or None.
            move_uci: The UCI string of the applied move.
    """
    board = Board.from_fen(fen)
    apply_fn = get_apply_move(variant)
    gen_legal_fn = get_generate_legal_moves(variant)

    # Parse UCI to Move
    move = _parse_uci(uci, board.side_to_move)

    # Verify legality
    legal = gen_legal_fn(board)
    matched = _find_matching_move(move, legal)
    if matched is None:
        raise ValueError(f"Illegal move: {uci}")

    # Apply with real variant logic (explosions, forced captures, etc.)
    new_board = apply_fn(board, matched)
    new_fen = new_board.to_fen()

    # Detect terminal state
    status = "ongoing"
    winner = None

    if new_board.is_terminal():
        # Variant-specific terminal (king explosion, piece depletion)
        status = "terminal"
        winner = new_board.winner
    else:
        next_legal = gen_legal_fn(new_board)
        if not next_legal:
            if is_in_check(new_board, new_board.side_to_move):
                status = "checkmate"
                winner = "w" if new_board.side_to_move == "b" else "b"
            else:
                status = "stalemate"
                winner = None

    return {
        "fen": new_fen,
        "status": status,
        "winner": winner,
        "move_uci": matched.to_uci(),
    }


def engine_reply(
    fen: str,
    agent: FeatureSubsetAgent | None = None,
    depth: int = 2,
    variant: str = "standard",
    move_index: int = 0,
) -> str | None:
    """Return a UCI move for the given position using the real engine.

    Uses AlphaBetaEngine with variant-aware search. Falls back to
    a random legal move if the engine fails or no agent is provided.

    Returns:
        UCI string or None if no legal moves.
    """
    board = Board.from_fen(fen)
    gen_legal_fn = get_generate_legal_moves(variant)
    legal = gen_legal_fn(board)
    if not legal:
        return None

    if agent is not None:
        try:
            engine = AlphaBetaEngine(agent, depth, variant=variant)
            move = engine.choose_move(board)
            return move.to_uci()
        except Exception as exc:
            import logging
            logging.warning("Engine failed, falling back to random: %s", exc)

    # Fallback: random legal move
    rng = random.Random(42 + move_index)
    return rng.choice(legal).to_uci()


def game_status_variant(fen: str, variant: str) -> str:
    """Classify the game state using real variant logic.

    Returns:
        'checkmate' | 'stalemate' | 'terminal' | 'ongoing'
    """
    board = Board.from_fen(fen)

    if board.is_terminal():
        return "terminal"

    gen_legal_fn = get_generate_legal_moves(variant)
    legal = gen_legal_fn(board)

    if not legal:
        if is_in_check(board, board.side_to_move):
            return "checkmate"
        return "stalemate"

    return "ongoing"


# Keep for backward compatibility with game viewer
def game_status(fen: str) -> str:
    """Classify game state using python-chess (standard variant only)."""
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


def _parse_uci(uci: str, side_to_move: str) -> Move:
    """Parse a UCI string like 'e2e4' or 'a7a8q' into a Move."""
    start = algebraic_to_square(uci[0:2])
    end = algebraic_to_square(uci[2:4])
    promo = None
    if len(uci) > 4:
        promo = uci[4].upper() if side_to_move == "w" else uci[4].lower()
    return Move(start=start, end=end, promotion=promo)


def _find_matching_move(candidate: Move, legal: list[Move]) -> Move | None:
    """Find the legal move matching the candidate, or None."""
    for m in legal:
        if m.start == candidate.start and m.end == candidate.end:
            if candidate.promotion is None or m.promotion == candidate.promotion:
                return m
    return None
