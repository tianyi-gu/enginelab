"""Natural-language interpretation for EngineLab analysis results."""

from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow

_VARIANT_FRAMES: dict[str, str] = {
    "atomic": (
        "Atomic Chess rewards explosion pressure, where captures trigger chain reactions "
        "that can rapidly swing material balance."
    ),
    "standard": (
        "Standard Chess rewards material and positional advantages, "
        "with long-term strategic control driving outcomes."
    ),
    "antichess": (
        "Antichess inverts the usual logic, where losing material is the objective "
        "and forcing captures becomes the dominant strategy."
    ),
}

_DEFAULT_FRAME = "This variant rewards careful feature selection and adaptive evaluation."


def generate_interpretation(
    best_agent: LeaderboardRow,
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    variant: str,
) -> str:
    """Generate a 2-3 sentence NL interpretation of the analysis results.

    Covers: variant framing, top marginal feature, top synergy pair,
    and the best agent's feature set. Returns "No data available." when
    marginals and synergies are both empty.
    """
    if not marginals and not synergies:
        return "No data available."

    frame = _VARIANT_FRAMES.get(variant.lower(), _DEFAULT_FRAME)

    # Top positive marginal feature
    top_marginal_str = "no dominant feature"
    if marginals:
        top = marginals[0]
        if top.marginal > 0:
            top_marginal_str = (
                f'"{top.feature}" showed the largest marginal benefit '
                f"(+{top.marginal:.3f} score-rate lift)"
            )
        else:
            top_marginal_str = (
                f'"{top.feature}" had the least negative marginal impact '
                f"({top.marginal:.3f})"
            )

    # Top synergy pair
    top_synergy_str = "no notable feature synergy was detected"
    if synergies:
        top_syn = synergies[0]
        if top_syn.synergy != 0.0:
            top_synergy_str = (
                f'the pair ("{top_syn.feature_a}", "{top_syn.feature_b}") '
                f"produced the strongest synergy ({top_syn.synergy:+.3f})"
            )

    # Best agent
    feature_list = ", ".join(best_agent.features) if best_agent.features else "no features"
    best_agent_str = (
        f'The best-performing agent "{best_agent.agent_name}" '
        f"used features [{feature_list}] "
        f"and achieved a score rate of {best_agent.score_rate:.3f}."
    )

    paragraph = (
        f"{frame} "
        f"Across the tournament, {top_marginal_str}, "
        f"while {top_synergy_str}. "
        f"{best_agent_str}"
    )
    return paragraph
