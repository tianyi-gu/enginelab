"""Markdown report generation for EngineLab."""

from pathlib import Path

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
    """Write a Markdown strategy report to output_path.

    Sections: title, config summary, top-10 leaderboard, feature contributions,
    top-10 synergies, interpretation, limitations.
    Creates parent directories as needed.
    """
    sections: list[str] = []
    sections.append(_build_title(variant))
    sections.append(_build_config_table(variant, feature_names, config))
    sections.append(_build_leaderboard_table(leaderboard))
    sections.append(_build_marginals_table(marginals))
    sections.append(_build_synergies_table(synergies))
    sections.append(_build_interpretation(interpretation))
    sections.append(_build_limitations())

    content = "\n\n".join(sections) + "\n"

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_title(variant: str) -> str:
    return f"# EngineLab Strategy Report — {variant.title()}"


def _build_config_table(variant: str, feature_names: list[str], config: dict) -> str:
    features_str = ", ".join(feature_names) if feature_names else "—"
    rows = [
        ("variant", variant),
        ("features", features_str),
        ("depth", str(config.get("depth", "—"))),
        ("max_moves", str(config.get("max_moves", "—"))),
        ("seed", str(config.get("seed", "—"))),
        ("agents", str(config.get("agents", "—"))),
        ("games", str(config.get("games", "—"))),
    ]
    lines = ["## Configuration", "", "| Parameter | Value |", "| --- | --- |"]
    for key, val in rows:
        lines.append(f"| {key} | {val} |")
    return "\n".join(lines)


def _shorten_name(name: str, max_len: int = 28) -> str:
    return name if len(name) <= max_len else name[: max_len - 1] + "…"


def _build_leaderboard_table(leaderboard: list[LeaderboardRow]) -> str:
    header = ["## Top-10 Leaderboard", "", "| Rank | Agent | Features | Score Rate | W | D | L |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    if not leaderboard:
        return "\n".join(header) + "\n| — | No data available | — | — | — | — | — |"

    top10 = sorted(leaderboard, key=lambda r: r.score_rate, reverse=True)[:10]
    lines = list(header)
    for rank, row in enumerate(top10, start=1):
        name = _shorten_name(row.agent_name)
        feats = ", ".join(row.features) if row.features else "—"
        lines.append(
            f"| {rank} | {name} | {feats} | {row.score_rate:.4f} "
            f"| {row.wins} | {row.draws} | {row.losses} |"
        )
    return "\n".join(lines)


def _build_marginals_table(marginals: list[FeatureContributionRow]) -> str:
    header = [
        "## Feature Contributions",
        "",
        "| Feature | Marginal | Avg With | Avg Without | Top-10 Freq |",
        "| --- | --- | --- | --- | --- |",
    ]
    if not marginals:
        return "\n".join(header) + "\n| — | No data available | — | — | — |"

    lines = list(header)
    for row in marginals:
        lines.append(
            f"| {row.feature} | {row.marginal:+.4f} | {row.avg_score_with:.4f} "
            f"| {row.avg_score_without:.4f} | {row.top_k_frequency:.2%} |"
        )
    return "\n".join(lines)


def _build_synergies_table(synergies: list[SynergyRow]) -> str:
    header = [
        "## Top-10 Synergies",
        "",
        "| Feature A | Feature B | Synergy |",
        "| --- | --- | --- |",
    ]
    if not synergies:
        return "\n".join(header) + "\n| — | No data available | — |"

    top10 = synergies[:10]
    lines = list(header)
    for row in top10:
        lines.append(f"| {row.feature_a} | {row.feature_b} | {row.synergy:+.4f} |")
    return "\n".join(lines)


def _build_interpretation(interpretation: str) -> str:
    return f"## Interpretation\n\n{interpretation}"


def _build_limitations() -> str:
    return (
        "## Limitations\n\n"
        "- Results depend on search depth and move cap; shallow search may not reflect "
        "true engine strength.\n"
        "- Marginal and synergy estimates are observational: agents with more features "
        "may benefit from correlated advantages not captured by pairwise analysis.\n"
        "- A fixed random seed ensures reproducibility but may not generalise across "
        "different opening sequences.\n"
        "- The leaderboard reflects performance within the evaluated agent pool only; "
        "out-of-sample generalisation is not guaranteed."
    )
