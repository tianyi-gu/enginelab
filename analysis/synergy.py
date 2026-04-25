"""Pairwise synergy analysis for EngineLab."""

from dataclasses import dataclass
from itertools import combinations
from statistics import mean

from tournament.leaderboard import LeaderboardRow


@dataclass
class SynergyRow:
    feature_a: str
    feature_b: str
    avg_score_with_both: float
    synergy: float


def compute_pairwise_synergies(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
) -> list[SynergyRow]:
    """Compute ANOVA two-way interaction synergy for every feature pair.

    synergy(a, b) = avg_with_both - avg_with_a_only - avg_with_b_only + overall_avg

    Where "avg_with_x_only" means mean score_rate of all rows containing x,
    regardless of whether they also contain the other feature.

    Returns a list sorted by synergy descending.
    Pairs where no rows contain both features get synergy = 0.0.
    Empty inputs return [].
    """
    if not leaderboard or len(feature_names) < 2:
        return []

    overall_avg = mean(r.score_rate for r in leaderboard)

    # Pre-compute per-feature means to avoid repeated scans
    feature_mean: dict[str, float] = {}
    for feature in feature_names:
        rows_with = [r for r in leaderboard if feature in r.features]
        feature_mean[feature] = mean(r.score_rate for r in rows_with) if rows_with else 0.0

    rows: list[SynergyRow] = []
    for feat_a, feat_b in combinations(feature_names, 2):
        both_rows = [r for r in leaderboard if feat_a in r.features and feat_b in r.features]

        if not both_rows:
            rows.append(
                SynergyRow(
                    feature_a=feat_a,
                    feature_b=feat_b,
                    avg_score_with_both=0.0,
                    synergy=0.0,
                )
            )
            continue

        avg_with_both = mean(r.score_rate for r in both_rows)
        synergy = avg_with_both - feature_mean[feat_a] - feature_mean[feat_b] + overall_avg

        rows.append(
            SynergyRow(
                feature_a=feat_a,
                feature_b=feat_b,
                avg_score_with_both=avg_with_both,
                synergy=synergy,
            )
        )

    return sorted(rows, key=lambda r: r.synergy, reverse=True)
