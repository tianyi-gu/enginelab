"""Markdown report generation — stub for Area 2 implementation."""

from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow


def generate_markdown_report(
    variant: str,
    feature_names: list[str],
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    interpretation: str,
    output_path: str,
    config: dict,
) -> None:
    """Write Markdown report. Stub — to be implemented in Area 2."""
    raise NotImplementedError("Markdown report not yet implemented")
