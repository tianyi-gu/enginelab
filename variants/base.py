"""Variant dispatch for EngineLab.

Maps variant names to their apply_move and generate_legal_moves functions.
"""

from typing import Callable

from core.board import Board
from core.move import Move
from variants.standard import apply_standard_move, generate_standard_moves


VARIANT_DISPATCH: dict[str, dict[str, Callable]] = {
    "standard": {
        "apply_move": apply_standard_move,
        "generate_legal_moves": generate_standard_moves,
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
