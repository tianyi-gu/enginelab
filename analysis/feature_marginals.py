"""Feature marginal analysis for EngineLab."""

from dataclasses import dataclass
from statistics import mean

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
    """Compute per-feature marginal contribution from the leaderboard.

    For each feature f:
      - avg_score_with    = mean score_rate of rows whose features contain f
      - avg_score_without = mean score_rate of rows that do NOT contain f
      - marginal          = avg_score_with - avg_score_without
      - top_k_frequency   = fraction of top-k rows (by score_rate) that contain f

    Returns a list sorted by marginal descending.
    Empty leaderboard or feature_names returns [].
    """
    if not leaderboard or not feature_names:
        return []

    top_k_rows = sorted(leaderboard, key=lambda r: r.score_rate, reverse=True)[:top_k]

    rows: list[FeatureContributionRow] = []
    for feature in feature_names:
        with_rows = [r for r in leaderboard if feature in r.features]
        without_rows = [r for r in leaderboard if feature not in r.features]

        avg_with = mean(r.score_rate for r in with_rows) if with_rows else 0.0
        avg_without = mean(r.score_rate for r in without_rows) if without_rows else 0.0
        marginal = avg_with - avg_without

        top_k_count = sum(1 for r in top_k_rows if feature in r.features)
        top_k_freq = top_k_count / len(top_k_rows) if top_k_rows else 0.0

        rows.append(
            FeatureContributionRow(
                feature=feature,
                avg_score_with=avg_with,
                avg_score_without=avg_without,
                marginal=marginal,
                top_k_frequency=top_k_freq,
            )
        )

    return sorted(rows, key=lambda r: r.marginal, reverse=True)
