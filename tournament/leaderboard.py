"""Leaderboard computation — stub for Area 2 implementation."""

from dataclasses import dataclass

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult


@dataclass
class LeaderboardRow:
    agent_name: str
    features: tuple[str, ...]
    games_played: int
    wins: int
    losses: int
    draws: int
    score_rate: float
    avg_game_length: float


def compute_leaderboard(
    results: list[GameResult],
    agents: list[FeatureSubsetAgent],
) -> list[LeaderboardRow]:
    """Compute leaderboard sorted by score_rate. Stub — Area 2."""
    raise NotImplementedError("Leaderboard not yet implemented")
