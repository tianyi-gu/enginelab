"""Round-robin tournament — stub for Area 2 implementation."""

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult


def run_round_robin(
    agents: list[FeatureSubsetAgent],
    variant: str,
    depth: int,
    max_moves: int,
    seed: int,
) -> list[GameResult]:
    """Play every ordered pair once. Stub — to be implemented in Area 2."""
    raise NotImplementedError("Round-robin tournament not yet implemented")
