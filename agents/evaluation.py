"""Evaluation functions for EngineLab.

Uses the feature registry for all 10 features.
"""

from core.board import Board
from agents.feature_subset_agent import FeatureSubsetAgent
from features.registry import FEATURES

WIN_SCORE: int = 10_000
LOSS_SCORE: int = -10_000


def normalize_feature_value(x: float) -> float:
    """Clip to [-10, 10] and normalize to [-1, 1]."""
    return max(-10.0, min(10.0, x)) / 10.0


def evaluate(board: Board, color: str, agent: FeatureSubsetAgent) -> float:
    """Weighted sum of normalized features. WIN/LOSS for terminals."""
    if board.winner is not None:
        if board.winner == color:
            return WIN_SCORE
        elif board.winner == "draw":
            return 0.0
        else:
            return LOSS_SCORE

    total = 0.0
    for feat_name in agent.features:
        feat_fn = FEATURES.get(feat_name)
        if feat_fn is not None:
            raw = feat_fn(board, color)
            total += agent.weights[feat_name] * normalize_feature_value(raw)
    return total


def contributions(
    board: Board, color: str, agent: FeatureSubsetAgent,
) -> dict[str, float]:
    """Per-feature weighted contribution."""
    result = {}
    for feat_name in agent.features:
        feat_fn = FEATURES.get(feat_name)
        if feat_fn is not None:
            raw = feat_fn(board, color)
            result[feat_name] = agent.weights[feat_name] * normalize_feature_value(raw)
        else:
            result[feat_name] = 0.0
    return result
