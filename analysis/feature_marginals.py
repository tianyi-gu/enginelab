"""Feature marginal contribution analysis for EngineLab.

For each feature f:
  avg_score_with    = mean score_rate of agents containing f
  avg_score_without = mean score_rate of agents excluding f
  marginal          = avg_score_with - avg_score_without
  top_k_frequency   = fraction of top-k agents containing f
"""

from dataclasses import dataclass

from tournament.leaderboard import LeaderboardRow


@dataclass
class FeatureContributionRow:
    """Marginal contribution of a single feature."""

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
    """Compute marginal contribution for each feature.

    Returns list sorted by marginal descending.
    """
    top_agents = leaderboard[:top_k]

    rows: list[FeatureContributionRow] = []
    for feat in feature_names:
        with_feat = [r for r in leaderboard if feat in r.features]
        without_feat = [r for r in leaderboard if feat not in r.features]

        avg_with = _mean_score_rate(with_feat)
        avg_without = _mean_score_rate(without_feat)

        top_count = sum(1 for r in top_agents if feat in r.features)
        top_freq = top_count / len(top_agents) if top_agents else 0.0

        rows.append(FeatureContributionRow(
            feature=feat,
            avg_score_with=avg_with,
            avg_score_without=avg_without,
            marginal=avg_with - avg_without,
            top_k_frequency=top_freq,
        ))

    rows.sort(key=lambda r: r.marginal, reverse=True)
    return rows


def _mean_score_rate(rows: list[LeaderboardRow]) -> float:
    """Mean score_rate of a list of leaderboard rows, 0.0 if empty."""
    if not rows:
        return 0.0
    return sum(r.score_rate for r in rows) / len(rows)
