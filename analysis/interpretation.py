"""Natural-language interpretation — stub for Area 2 implementation."""

from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow


def generate_interpretation(
    best_agent: LeaderboardRow,
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    variant: str,
) -> str:
    """Generate interpretation paragraph. Stub — to be implemented in Area 2."""
    raise NotImplementedError("Interpretation not yet implemented")
