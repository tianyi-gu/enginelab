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
    """Write a complete Markdown strategy report to output_path."""
    lines: list[str] = []

    # Title
    lines.append(f"# EngineLab Strategy Report: {variant.title()} Chess")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    best = leaderboard[0] if leaderboard else None
    if best:
        lines.append(
            f"Best agent: **{best.agent_name}** "
            f"(score rate: {best.score_rate:.3f})"
        )
    total_games = sum(r.games_played for r in leaderboard) // 2
    lines.append(f"Total games played: {total_games}")
    lines.append(f"Number of agents: {len(leaderboard)}")
    lines.append("")

    # Variant
    lines.append("## Variant")
    lines.append("")
    lines.append(f"**{variant.title()}** chess rules were used for all games.")
    lines.append("")

    # Features
    lines.append("## Features")
    lines.append("")
    for feat in feature_names:
        lines.append(f"- {feat}")
    lines.append("")

    # Configuration
    lines.append("## Configuration")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    for key, value in config.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    # Top-10 Leaderboard
    lines.append("## Leaderboard (Top 10)")
    lines.append("")
    lines.append("| Rank | Agent | Features | Score Rate | W | L | D | Games |")
    lines.append("|------|-------|----------|------------|---|---|---|-------|")
    for i, row in enumerate(leaderboard[:10], 1):
        feats = ", ".join(row.features)
        lines.append(
            f"| {i} | {row.agent_name} | {feats} | "
            f"{row.score_rate:.3f} | {row.wins} | {row.losses} | "
            f"{row.draws} | {row.games_played} |"
        )
    lines.append("")

    # Best Subset
    if best:
        lines.append("## Best Feature Subset")
        lines.append("")
        lines.append(f"**{best.agent_name}**")
        lines.append("")
        lines.append(f"- Features: {', '.join(best.features)}")
        lines.append(f"- Score rate: {best.score_rate:.3f}")
        lines.append(
            f"- Record: {best.wins}W / {best.losses}L / {best.draws}D"
        )
        lines.append(f"- Avg game length: {best.avg_game_length:.1f} plies")
        lines.append("")

    # Feature Marginals
    lines.append("## Feature Contributions")
    lines.append("")
    lines.append(
        "| Feature | Avg With | Avg Without | Marginal | Top-K Freq |"
    )
    lines.append("|---------|----------|-------------|----------|------------|")
    for m in marginals:
        lines.append(
            f"| {m.feature} | {m.avg_score_with:.3f} | "
            f"{m.avg_score_without:.3f} | {m.marginal:+.3f} | "
            f"{m.top_k_frequency:.2f} |"
        )
    lines.append("")

    # Pairwise Synergies
    lines.append("## Top Synergies")
    lines.append("")
    lines.append("| Feature A | Feature B | Avg Both | Synergy |")
    lines.append("|-----------|-----------|----------|---------|")
    for s in synergies[:10]:
        lines.append(
            f"| {s.feature_a} | {s.feature_b} | "
            f"{s.avg_score_with_both:.3f} | {s.synergy:+.3f} |"
        )
    lines.append("")

    # Interpretation
    lines.append("## Interpretation")
    lines.append("")
    lines.append(interpretation)
    lines.append("")

    # Limitations
    lines.append("## Limitations")
    lines.append("")
    lines.append("- Equal weights only; does not optimize weight values.")
    lines.append("- Results depend on search depth and move cap.")
    lines.append("- Feature interactions beyond pairs are not analyzed.")
    lines.append(
        "- Stratified sampling may miss some feature subsets "
        "when >6 features are used."
    )
    lines.append("")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
