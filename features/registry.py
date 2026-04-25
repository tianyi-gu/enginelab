"""Feature registry — stub for Area 1 implementation.

Foundation provides material-only evaluation directly in agents/evaluation.py.
The full feature registry with all 10 features is implemented in Area 1.
"""

from typing import Callable

from core.board import Board

FEATURES: dict[str, Callable[[Board, str], float]] = {}
FEATURE_DESCRIPTIONS: dict[str, str] = {}


def get_feature_names() -> list[str]:
    """Return sorted list of registered feature names."""
    return sorted(FEATURES.keys())


def get_feature_function(name: str) -> Callable[[Board, str], float]:
    """Return the feature function for the given name."""
    return FEATURES[name]


def get_feature_description(name: str) -> str:
    """Return human-readable description for the given feature."""
    return FEATURE_DESCRIPTIONS[name]
