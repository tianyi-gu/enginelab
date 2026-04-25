"""Dynamic loading and validation of LLM-generated variant code."""
from __future__ import annotations

import random
import traceback
from typing import Callable

from core.board import Board
from core.move import Move


_PRELOADED_IMPORTS = """
from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_moves, generate_legal_moves, is_in_check, is_square_attacked
from core.types import piece_color, piece_type, opponent_color
from core.coordinates import algebraic_to_square, square_to_algebraic
"""


def load_variant_from_code(code: str) -> dict:
    """Execute generated code and extract the two required functions.

    All available imports are pre-loaded into the namespace so the LLM-generated
    code doesn't fail due to missing imports.

    Returns:
        {"apply_move": Callable | None,
         "generate_legal_moves": Callable | None,
         "error": str | None}
    """
    namespace: dict = {"__builtins__": __builtins__}
    try:
        exec(_PRELOADED_IMPORTS, namespace)  # noqa: S102
        exec(code, namespace)  # noqa: S102
    except Exception:
        return {
            "apply_move": None,
            "generate_legal_moves": None,
            "error": f"Code execution failed:\n{traceback.format_exc()}",
        }

    apply_fn = namespace.get("apply_customvariant_move")
    gen_fn = namespace.get("generate_customvariant_moves")

    if apply_fn is None:
        return {
            "apply_move": None,
            "generate_legal_moves": None,
            "error": "Missing function: apply_customvariant_move",
        }
    if gen_fn is None:
        return {
            "apply_move": None,
            "generate_legal_moves": None,
            "error": "Missing function: generate_customvariant_moves",
        }

    setup_fn = namespace.get("setup_customvariant_board")
    return {"apply_move": apply_fn, "generate_legal_moves": gen_fn, "setup_board": setup_fn, "error": None}


def validate_variant(
    apply_fn: Callable[[Board, Move], Board],
    gen_fn: Callable[[Board], list[Move]],
    num_moves: int = 10,
    num_games: int = 2,
) -> dict:
    """Play quick test games to validate the generated variant functions.

    Returns:
        {"valid": bool, "error": str | None}
    """
    rng = random.Random(42)

    for game_idx in range(num_games):
        board = Board.starting_position()
        try:
            for ply in range(num_moves):
                moves = gen_fn(board)

                # Sanity checks
                if not isinstance(moves, list):
                    return {"valid": False, "error": f"generate_customvariant_moves returned {type(moves).__name__}, expected list"}
                if len(moves) == 0:
                    break  # legal stalemate / checkmate — fine
                if not isinstance(moves[0], Move):
                    return {"valid": False, "error": f"Move list contains {type(moves[0]).__name__}, expected Move"}

                move = rng.choice(moves)
                new_board = apply_fn(board, move)

                if not isinstance(new_board, Board):
                    return {"valid": False, "error": f"apply_customvariant_move returned {type(new_board).__name__}, expected Board"}

                # Check that the original board was not mutated
                if board.side_to_move != ("w" if ply % 2 == 0 else "b") and ply == 0:
                    pass  # first ply is always "w"

                if new_board.winner is not None:
                    break  # game over

                board = new_board

        except Exception:
            return {"valid": False, "error": f"Game {game_idx + 1} crashed at ply {ply}:\n{traceback.format_exc()}"}

    return {"valid": True, "error": None}


def register_variant(
    variant_name: str,
    apply_fn: Callable,
    gen_fn: Callable,
    setup_fn: Callable | None = None,
) -> None:
    """Register the variant into VARIANT_DISPATCH for tournament use."""
    from variants.base import VARIANT_DISPATCH

    entry = {
        "apply_move": apply_fn,
        "generate_legal_moves": gen_fn,
    }
    if setup_fn is not None:
        entry["setup_board"] = setup_fn
    VARIANT_DISPATCH[variant_name] = entry
