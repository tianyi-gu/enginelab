"""Feature marginal analysis — stub for Area 2 implementation."""

from dataclasses import dataclass

from tournament.leaderboard import LeaderboardRow


@dataclass
class FeatureContributionRow:
    feature: str
    avg_score_with: float
    avg_score_without: float
    marginal: float
    top_k_frequency: float


def compute_feature_marginals(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
    top_k: int = 10,
) -> list[FeatureContributionRow]:
    """Compute feature marginals. Stub — to be implemented in Area 2."""
    raise NotImplementedError("Feature marginals not yet implemented")
