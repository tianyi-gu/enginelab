"""Natural-language interpretation generation for EngineLab."""

from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow


def generate_interpretation(
    best_agent: LeaderboardRow,
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    variant: str,
) -> str:
    """Generate a natural-language interpretation paragraph."""
    lines: list[str] = []

    # Best agent summary
    feat_list = ", ".join(best_agent.features)
    lines.append(
        f"In {variant} chess, the best-performing agent was "
        f"{best_agent.agent_name} (features: {feat_list}) with a "
        f"score rate of {best_agent.score_rate:.3f} over "
        f"{best_agent.games_played} games."
    )

    # Top contributing features
    positive = [m for m in marginals if m.marginal > 0]
    if positive:
        top_feats = positive[:3]
        feat_strs = [
            f"{m.feature} (+{m.marginal:.3f})" for m in top_feats
        ]
        lines.append(
            f"The most valuable features were {', '.join(feat_strs)}."
        )

    negative = [m for m in marginals if m.marginal < 0]
    if negative:
        worst = negative[-1]
        lines.append(
            f"The least valuable feature was {worst.feature} "
            f"({worst.marginal:.3f})."
        )

    # Top synergies
    pos_synergies = [s for s in synergies if s.synergy > 0]
    if pos_synergies:
        top_syn = pos_synergies[0]
        lines.append(
            f"The strongest synergy was between {top_syn.feature_a} and "
            f"{top_syn.feature_b} (synergy={top_syn.synergy:.3f}), meaning "
            f"these features are more valuable together than their "
            f"individual contributions suggest."
        )

    neg_synergies = [s for s in synergies if s.synergy < 0]
    if neg_synergies:
        worst_syn = neg_synergies[-1]
        lines.append(
            f"The most redundant pair was {worst_syn.feature_a} and "
            f"{worst_syn.feature_b} (synergy={worst_syn.synergy:.3f})."
        )

    return " ".join(lines)
