import random
import sys
import os
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.game import GameResult
from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow
from agents.feature_subset_agent import FeatureSubsetAgent
from ui.constants import ALL_FEATURES


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_mock_session_state(seed: int = 42) -> dict:
    """Return a dict of session state values matching the full schema.

    All randomness is seeded for reproducibility. The returned keys match
    the results subset of SESSION_DEFAULTS (not config or runtime keys).

    Args:
        seed: RNG seed for reproducibility.

    Returns:
        Dict with keys: agents, results, leaderboard, marginals, synergies,
        interpretation, report_md, config_snapshot, duration_seconds.
    """
    rng = random.Random(seed)

    agents = _generate_agents(rng)
    results = _generate_results(agents, rng)
    leaderboard = _compute_leaderboard(results, agents)
    marginals = _generate_marginals(leaderboard)
    synergies = _generate_synergies(leaderboard)
    interpretation = _generate_interpretation(leaderboard, marginals)
    report_md = _generate_report_md(leaderboard, marginals)
    config_snapshot = _make_config_snapshot()

    return {
        "agents": agents,
        "results": results,
        "leaderboard": leaderboard,
        "marginals": marginals,
        "synergies": synergies,
        "interpretation": interpretation,
        "report_md": report_md,
        "config_snapshot": config_snapshot,
        "duration_seconds": 142.3,
    }


# ---------------------------------------------------------------------------
# Agent generation
# ---------------------------------------------------------------------------

def _generate_agents(rng: random.Random) -> list[FeatureSubsetAgent]:
    """Generate 15-20 FeatureSubsetAgents with varied feature subsets."""
    agents: list[FeatureSubsetAgent] = []

    # Hand-picked subsets that are interesting for atomic chess
    interesting_subsets: list[tuple[str, ...]] = [
        ("enemy_king_danger", "capture_threats", "king_safety"),
        ("enemy_king_danger", "capture_threats"),
        ("king_safety", "capture_threats", "mobility"),
        ("material", "piece_position", "center_control"),
        ("enemy_king_danger", "king_safety"),
        ("mobility", "capture_threats"),
        ("material", "mobility"),
        ("pawn_structure", "bishop_pair", "rook_activity"),
        ("enemy_king_danger", "capture_threats", "mobility", "king_safety"),
        ("material",),
        ("center_control", "mobility", "piece_position"),
        ("king_safety", "pawn_structure"),
        ("capture_threats", "rook_activity", "bishop_pair"),
        ("enemy_king_danger", "mobility", "center_control"),
        ("material", "king_safety", "enemy_king_danger"),
        ("piece_position", "mobility"),
        ("capture_threats",),
        ("bishop_pair", "mobility", "king_safety"),
    ]

    for subset in interesting_subsets:
        agents.append(_make_agent(subset, rng))

    return agents


def _make_agent(features: tuple[str, ...], rng: random.Random) -> FeatureSubsetAgent:
    """Create a FeatureSubsetAgent with uniform-random weights that sum to 1."""
    raw = [rng.uniform(0.5, 1.5) for _ in features]
    total = sum(raw)
    weights = {f: w / total for f, w in zip(features, raw)}
    name = "Agent_" + "__".join(features)
    return FeatureSubsetAgent(name=name, features=tuple(features), weights=weights)


# ---------------------------------------------------------------------------
# Result generation
# ---------------------------------------------------------------------------

def _generate_results(
    agents: list[FeatureSubsetAgent],
    rng: random.Random,
) -> list[GameResult]:
    """Generate ~200 GameResults between the provided agents."""
    results: list[GameResult] = []

    # Generate round-robin pairs
    pairs = list(combinations(agents, 2))
    rng.shuffle(pairs)

    # Play each pair once (both color directions for some)
    for white_agent, black_agent in pairs:
        results.append(_make_result(white_agent, black_agent, rng))
        # Play the reverse color game occasionally
        if rng.random() < 0.6:
            results.append(_make_result(black_agent, white_agent, rng))

    return results


def _make_result(
    white: FeatureSubsetAgent,
    black: FeatureSubsetAgent,
    rng: random.Random,
) -> GameResult:
    """Simulate a single game result with outcome influenced by features."""
    white_strength = _agent_strength(white)
    black_strength = _agent_strength(black)

    total = white_strength + black_strength
    p_white = white_strength / total if total > 0 else 0.5
    p_draw = 0.08
    p_black = 1.0 - p_white - p_draw

    # Clamp probabilities
    p_black = max(p_black, 0.0)
    p_white = max(p_white, 0.0)
    roll = rng.random()

    if roll < p_white:
        winner: str | None = "w"
        termination = "checkmate"
    elif roll < p_white + p_draw:
        winner = None
        termination = rng.choice(["stalemate", "move_cap"])
    else:
        winner = "b"
        termination = "checkmate"

    moves = rng.randint(15, 80)

    return GameResult(
        white_agent=white.name,
        black_agent=black.name,
        winner=winner,
        moves=moves,
        termination_reason=termination,
        white_avg_nodes=float(rng.randint(80, 400)),
        black_avg_nodes=float(rng.randint(80, 400)),
        white_avg_time=round(rng.uniform(0.01, 0.12), 4),
        black_avg_time=round(rng.uniform(0.01, 0.12), 4),
    )


def _agent_strength(agent: FeatureSubsetAgent) -> float:
    """Estimate agent strength for atomic chess based on feature composition."""
    # Atomic-biased strength values
    feature_values: dict[str, float] = {
        "enemy_king_danger": 1.5,
        "capture_threats": 1.3,
        "king_safety": 1.2,
        "mobility": 1.1,
        "center_control": 0.9,
        "piece_position": 0.85,
        "pawn_structure": 0.8,
        "bishop_pair": 0.75,
        "rook_activity": 0.7,
        "material": 0.5,  # liability in atomic
    }
    return sum(feature_values.get(f, 0.8) for f in agent.features)


# ---------------------------------------------------------------------------
# Leaderboard computation
# ---------------------------------------------------------------------------

def _compute_leaderboard(
    results: list[GameResult],
    agents: list[FeatureSubsetAgent],
) -> list[LeaderboardRow]:
    """Compute leaderboard by accumulating W/D/L from results."""
    rows: list[LeaderboardRow] = []

    for agent in agents:
        agent_games = [
            r for r in results
            if r.white_agent == agent.name or r.black_agent == agent.name
        ]
        wins = losses = draws = 0
        move_totals: list[int] = []

        for game in agent_games:
            move_totals.append(game.moves)
            if game.winner is None:
                draws += 1
            elif (
                (game.winner == "w" and game.white_agent == agent.name)
                or (game.winner == "b" and game.black_agent == agent.name)
            ):
                wins += 1
            else:
                losses += 1

        games_played = len(agent_games)
        score_rate = (wins + 0.5 * draws) / games_played if games_played else 0.0
        avg_game_length = sum(move_totals) / len(move_totals) if move_totals else 0.0

        rows.append(
            LeaderboardRow(
                agent_name=agent.name,
                features=agent.features,
                games_played=games_played,
                wins=wins,
                losses=losses,
                draws=draws,
                score_rate=round(score_rate, 4),
                avg_game_length=round(avg_game_length, 1),
            )
        )

    rows.sort(key=lambda r: r.score_rate, reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Marginals generation
# ---------------------------------------------------------------------------

def _generate_marginals(
    leaderboard: list[LeaderboardRow],
) -> list[FeatureContributionRow]:
    """Generate FeatureContributionRows derived from leaderboard data."""
    rows: list[FeatureContributionRow] = []

    # Target marginals based on atomic chess domain knowledge
    target_marginals: dict[str, float] = {
        "enemy_king_danger": 0.15,
        "capture_threats": 0.11,
        "king_safety": 0.08,
        "mobility": 0.04,
        "center_control": 0.02,
        "piece_position": 0.01,
        "pawn_structure": 0.00,
        "bishop_pair": -0.01,
        "rook_activity": -0.01,
        "material": -0.02,
    }

    baseline = 0.50

    for feature in ALL_FEATURES:
        with_rows = [r for r in leaderboard if feature in r.features]
        without_rows = [r for r in leaderboard if feature not in r.features]

        marginal = target_marginals.get(feature, 0.0)
        avg_with = baseline + marginal * 1.5
        avg_without = baseline - marginal * 0.5

        # Override with real data if available
        if with_rows:
            avg_with = sum(r.score_rate for r in with_rows) / len(with_rows)
        if without_rows:
            avg_without = sum(r.score_rate for r in without_rows) / len(without_rows)
        if with_rows and without_rows:
            marginal = avg_with - avg_without

        top_k_rows = sorted(leaderboard, key=lambda r: r.score_rate, reverse=True)[:10]
        top_k_count = sum(1 for r in top_k_rows if feature in r.features)
        top_k_freq = top_k_count / len(top_k_rows) if top_k_rows else 0.0

        rows.append(
            FeatureContributionRow(
                feature=feature,
                avg_score_with=round(avg_with, 4),
                avg_score_without=round(avg_without, 4),
                marginal=round(marginal, 4),
                top_k_frequency=round(top_k_freq, 3),
            )
        )

    return sorted(rows, key=lambda r: r.marginal, reverse=True)


# ---------------------------------------------------------------------------
# Synergy generation
# ---------------------------------------------------------------------------

def _generate_synergies(
    leaderboard: list[LeaderboardRow],
) -> list[SynergyRow]:
    """Generate SynergyRows for all feature pairs."""
    if not leaderboard:
        return []

    overall_avg = sum(r.score_rate for r in leaderboard) / len(leaderboard)

    feature_mean: dict[str, float] = {}
    for feature in ALL_FEATURES:
        rows_with = [r for r in leaderboard if feature in r.features]
        feature_mean[feature] = (
            sum(r.score_rate for r in rows_with) / len(rows_with)
            if rows_with else overall_avg
        )

    synergy_rows: list[SynergyRow] = []
    for feat_a, feat_b in combinations(ALL_FEATURES, 2):
        both_rows = [
            r for r in leaderboard
            if feat_a in r.features and feat_b in r.features
        ]

        if not both_rows:
            synergy_rows.append(
                SynergyRow(
                    feature_a=feat_a,
                    feature_b=feat_b,
                    avg_score_with_both=0.0,
                    synergy=0.0,
                )
            )
            continue

        avg_with_both = sum(r.score_rate for r in both_rows) / len(both_rows)
        synergy = (
            avg_with_both
            - feature_mean[feat_a]
            - feature_mean[feat_b]
            + overall_avg
        )

        synergy_rows.append(
            SynergyRow(
                feature_a=feat_a,
                feature_b=feat_b,
                avg_score_with_both=round(avg_with_both, 4),
                synergy=round(synergy, 4),
            )
        )

    return sorted(synergy_rows, key=lambda r: r.synergy, reverse=True)


# ---------------------------------------------------------------------------
# Text generation
# ---------------------------------------------------------------------------

def _generate_interpretation(
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
) -> str:
    """Generate a short interpretation paragraph for the mock results."""
    if not leaderboard or not marginals:
        return "No data available."

    best = leaderboard[0]
    top_feature = marginals[0].feature if marginals else "enemy_king_danger"
    top_marginal = marginals[0].marginal if marginals else 0.15

    return (
        f"In Atomic Chess, the tournament revealed that {top_feature.replace('_', ' ')} "
        f"is the strongest single feature, contributing +{top_marginal:.2f} to win rate. "
        f"The best agent — {best.agent_name} — achieved a score rate of "
        f"{best.score_rate:.3f} across {best.games_played} games with "
        f"{best.wins} wins, {best.draws} draws, and {best.losses} losses. "
        "Material evaluation, while dominant in standard chess, proved nearly "
        "irrelevant and slightly counterproductive in the Atomic variant, where "
        "explosion chains trump positional considerations. The synergy analysis "
        "shows that enemy_king_danger and capture_threats are highly complementary, "
        "rewarding agents that combine both pressure metrics."
    )


def _generate_report_md(
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
) -> str:
    """Generate a short Markdown strategy report for the mock results."""
    if not leaderboard or not marginals:
        return "# Report\n\nNo data available."

    best = leaderboard[0]
    top_features = marginals[:3]

    lines = [
        "# Atomic Chess Strategy Report",
        "",
        "## Executive Summary",
        "",
        f"Tournament completed with {len(leaderboard)} agents across "
        f"{sum(r.games_played for r in leaderboard) // 2} unique games.",
        "",
        f"**Best Agent:** `{best.agent_name}`  ",
        f"**Score Rate:** {best.score_rate:.4f}  ",
        f"**Record:** {best.wins}W / {best.draws}D / {best.losses}L",
        "",
        "## Top Features by Marginal Contribution",
        "",
        "| Feature | Avg With | Avg Without | Marginal | Top-10 Freq |",
        "|---------|----------|-------------|----------|-------------|",
    ]

    for row in top_features:
        lines.append(
            f"| {row.feature} | {row.avg_score_with:.4f} | "
            f"{row.avg_score_without:.4f} | {row.marginal:+.4f} | "
            f"{row.top_k_frequency:.0%} |"
        )

    lines += [
        "",
        "## Key Findings",
        "",
        "- **Enemy King Danger** is the dominant feature in Atomic Chess. "
        "Agents that track threats near the enemy king win significantly more games.",
        "- **Capture Threats** synergizes strongly with King Danger, as explosion "
        "chains amplify the value of tracking capture sequences.",
        "- **Material** has a small negative marginal contribution, confirming "
        "that standard chess intuitions do not transfer to Atomic.",
        "",
        "## Recommendation",
        "",
        "For Atomic Chess, prioritize: `enemy_king_danger + capture_threats + king_safety`. "
        "Avoid over-weighting material or pawn structure.",
    ]

    return "\n".join(lines)


def _make_config_snapshot() -> dict:
    """Return a config dict matching the tournament config schema."""
    return {
        "variant": "atomic",
        "selected_features": list(ALL_FEATURES),
        "depth": 2,
        "max_moves": 80,
        "workers": 1,
        "seed": 42,
    }
