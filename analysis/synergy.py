"""Pairwise feature synergy analysis for EngineLab.

synergy(a, b) = avg_with_both - avg_with_a - avg_with_b + overall_avg

This is the standard ANOVA two-way interaction term. Positive synergy
means the features are more valuable together than their individual
contributions would predict.
"""

from dataclasses import dataclass

from tournament.leaderboard import LeaderboardRow


@dataclass
class SynergyRow:
    """Pairwise synergy between two features."""

    feature_a: str
    feature_b: str
    avg_score_with_both: float
    synergy: float


def compute_pairwise_synergies(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
) -> list[SynergyRow]:
    """Compute pairwise synergies for all feature pairs.

    Returns list sorted by synergy descending.
    """
    overall_avg = _mean_score_rate(leaderboard)

    # Precompute per-feature averages
    feat_avg: dict[str, float] = {}
    for feat in feature_names:
        with_feat = [r for r in leaderboard if feat in r.features]
        feat_avg[feat] = _mean_score_rate(with_feat)

    rows: list[SynergyRow] = []
    for i, fa in enumerate(feature_names):
        for fb in feature_names[i + 1:]:
            with_both = [
                r for r in leaderboard
                if fa in r.features and fb in r.features
            ]
            avg_both = _mean_score_rate(with_both)
            synergy = avg_both - feat_avg[fa] - feat_avg[fb] + overall_avg

            rows.append(SynergyRow(
                feature_a=fa,
                feature_b=fb,
                avg_score_with_both=avg_both,
                synergy=synergy,
            ))

    rows.sort(key=lambda r: r.synergy, reverse=True)
    return rows


def _mean_score_rate(rows: list[LeaderboardRow]) -> float:
    """Mean score_rate of a list of leaderboard rows, 0.0 if empty."""
    if not rows:
        return 0.0
    return sum(r.score_rate for r in rows) / len(rows)
