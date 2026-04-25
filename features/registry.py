"""Feature registry for EngineLab.

Central registry mapping feature names to their evaluation functions.
All 10 features are registered here.
"""

from typing import Callable

from core.board import Board

from features.material import material
from features.piece_position import piece_position
from features.center_control import center_control
from features.king_safety import king_safety
from features.king_danger import enemy_king_danger
from features.mobility import mobility
from features.pawn_structure import pawn_structure
from features.bishop_pair import bishop_pair
from features.rook_activity import rook_activity
from features.capture_threats import capture_threats
from features.antichess_material import antichess_material
from features.explosion_proximity import explosion_proximity


FEATURES: dict[str, Callable[[Board, str], float]] = {
    "material": material,
    "piece_position": piece_position,
    "center_control": center_control,
    "king_safety": king_safety,
    "enemy_king_danger": enemy_king_danger,
    "mobility": mobility,
    "pawn_structure": pawn_structure,
    "bishop_pair": bishop_pair,
    "rook_activity": rook_activity,
    "capture_threats": capture_threats,
    "antichess_material": antichess_material,
    "explosion_proximity": explosion_proximity,
}

FEATURE_DESCRIPTIONS: dict[str, str] = {
    "material": "Own material minus opponent material (P=1, N=3, B=3, R=5, Q=9)",
    "piece_position": "Piece-square table positional bonus",
    "center_control": "Pieces on/attacking d4,d5,e4,e5 (center pieces 2x)",
    "king_safety": "Adjacent pawns, open files, nearby enemy pieces",
    "enemy_king_danger": "Own piece proximity to enemy king + attacked king squares",
    "mobility": "Own move count minus opponent move count",
    "pawn_structure": "Doubled (-0.5), isolated (-0.5), passed (+1.0), connected (+0.3)",
    "bishop_pair": "+0.5 if 2+ bishops",
    "rook_activity": "Open file (+0.5), semi-open (+0.25), 7th rank (+0.5)",
    "capture_threats": "Sum of capturable piece values",
    "antichess_material": "Inverted material: opponent material minus own material (antichess: fewer pieces = better)",
    "explosion_proximity": "Own non-pawns adjacent to enemy king minus enemy non-pawns adjacent to own king (atomic: explosion threat)",
}


def get_feature_names() -> list[str]:
    """Return sorted list of registered feature names."""
    return sorted(FEATURES.keys())


def get_feature_function(name: str) -> Callable[[Board, str], float]:
    """Return the feature function for the given name."""
    return FEATURES[name]


def get_feature_description(name: str) -> str:
    """Return human-readable description for the given feature."""
    return FEATURE_DESCRIPTIONS[name]
