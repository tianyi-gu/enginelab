"""Variant dispatch for EngineLab.

Maps variant names to their apply_move and generate_legal_moves functions.
"""

from typing import Callable

from core.board import Board
from core.move import Move
from variants.standard import apply_standard_move, generate_standard_moves
from variants.atomic import apply_atomic_move, generate_atomic_moves
from variants.antichess import apply_antichess_move, generate_antichess_moves
from variants.king_of_the_hill import apply_koth_move, generate_koth_moves
from variants.three_check import apply_three_check_move, generate_three_check_moves
from variants.chess960 import apply_chess960_move, generate_chess960_moves
from variants.horde import apply_horde_move, generate_horde_moves


VARIANT_DISPATCH: dict[str, dict[str, Callable]] = {
    "standard": {
        "apply_move": apply_standard_move,
        "generate_legal_moves": generate_standard_moves,
    },
    "atomic": {
        "apply_move": apply_atomic_move,
        "generate_legal_moves": generate_atomic_moves,
    },
    "antichess": {
        "apply_move": apply_antichess_move,
        "generate_legal_moves": generate_antichess_moves,
    },
    "kingofthehill": {
        "apply_move": apply_koth_move,
        "generate_legal_moves": generate_koth_moves,
    },
    "threecheck": {
        "apply_move": apply_three_check_move,
        "generate_legal_moves": generate_three_check_moves,
    },
    "chess960": {
        "apply_move": apply_chess960_move,
        "generate_legal_moves": generate_chess960_moves,
    },
    "horde": {
        "apply_move": apply_horde_move,
        "generate_legal_moves": generate_horde_moves,
    },
}


def get_apply_move(variant: str) -> Callable[[Board, Move], Board]:
    """Return the apply_move function for the given variant."""
    return VARIANT_DISPATCH[variant]["apply_move"]


def get_generate_legal_moves(variant: str) -> Callable[[Board], list[Move]]:
    """Return the generate_legal_moves function for the given variant."""
    return VARIANT_DISPATCH[variant]["generate_legal_moves"]


def get_supported_variants() -> list[str]:
    """Return list of supported variant names."""
    return list(VARIANT_DISPATCH.keys())
