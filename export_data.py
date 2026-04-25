"""Export comprehensive tournament data for visualization.

Loads tournament results and exports:
- Per-game CSV with all stats
- Leaderboard CSV
- Feature marginals CSV
- Pairwise synergy CSV + heatmap matrix CSV
- Head-to-head matchup matrix CSV (win rates)
- Agent metadata CSV (features, weights, feature count)
- Game length distribution data
- Termination reason breakdown
- Per-feature-count performance data
- Summary JSON with all computed metrics
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

from tournament.results_io import load_results_json, save_results_csv
from tournament.leaderboard import compute_leaderboard
from analysis.feature_marginals import compute_feature_marginals
from analysis.synergy import compute_pairwise_synergies
from analysis.interpretation import generate_interpretation
from agents.feature_subset_agent import FeatureSubsetAgent


def _agents_from_results(results):
    """Reconstruct agents from result names."""
    names = set()
    for r in results:
        names.add(r.white_agent)
        names.add(r.black_agent)
    agents = []
    for name in sorted(names):
        if name.startswith("Agent_"):
            feat_str = name[len("Agent_"):]
            feats = tuple(sorted(feat_str.split("__")))
            weights = {f: 1.0 / len(feats) for f in feats}
            agents.append(FeatureSubsetAgent(name, feats, weights))
    return agents


def export_all(variant: str, out_dir: str = "outputs/data"):
    """Export all data for a variant's tournament results."""
    input_path = f"{out_dir}/tournament_results_{variant}.json"
    results = load_results_json(input_path)
    agents = _agents_from_results(results)
    lb = compute_leaderboard(results, agents)
    feature_names = sorted({f for a in agents for f in a.features})
    marginals = compute_feature_marginals(lb, feature_names, top_k=10)
    synergies = compute_pairwise_synergies(lb, feature_names)

    viz_dir = Path(out_dir) / f"{variant}_viz"
    viz_dir.mkdir(parents=True, exist_ok=True)

    # 1. Per-game CSV (already have JSON, add CSV + game index + computed fields)
    _export_games_csv(results, viz_dir / "games.csv")

    # 2. Leaderboard CSV
    _export_leaderboard_csv(lb, viz_dir / "leaderboard.csv")

    # 3. Agent metadata CSV
    _export_agents_csv(agents, lb, viz_dir / "agents.csv")

    # 4. Feature marginals CSV
    _export_marginals_csv(marginals, viz_dir / "feature_marginals.csv")

    # 5. Synergy CSV
    _export_synergies_csv(synergies, viz_dir / "synergies.csv")

    # 6. Synergy heatmap matrix CSV
    _export_synergy_matrix(synergies, feature_names, viz_dir / "synergy_matrix.csv")

    # 7. Head-to-head matchup matrix CSV
    _export_matchup_matrix(results, agents, viz_dir / "matchup_matrix.csv")

    # 8. Head-to-head detailed (every pair with W/L/D counts)
    _export_head_to_head(results, viz_dir / "head_to_head.csv")

    # 9. Termination reason breakdown
    _export_termination_breakdown(results, viz_dir / "termination_reasons.csv")

    # 10. Game length distribution
    _export_game_lengths(results, viz_dir / "game_lengths.csv")

    # 11. Performance by feature count
    _export_by_feature_count(lb, viz_dir / "performance_by_feature_count.csv")

    # 12. Per-feature win rate when present vs absent
    _export_feature_presence_impact(lb, feature_names, viz_dir / "feature_presence_impact.csv")

    # 13. Summary JSON
    best = lb[0] if lb else None
    interp = generate_interpretation(best, marginals, synergies, variant) if best else ""
    _export_summary_json(variant, results, agents, lb, marginals, synergies, interp,
                         viz_dir / "summary.json")

    print(f"Exported {len(list(viz_dir.glob('*')))} files to {viz_dir}/")
    for f in sorted(viz_dir.glob("*")):
        size = f.stat().st_size
        print(f"  {f.name:40s} {size:>8,d} bytes")


def _export_games_csv(results, path):
    fields = [
        "game_index", "white_agent", "black_agent", "winner",
        "white_won", "black_won", "draw",
        "moves", "termination_reason",
        "white_avg_nodes", "black_avg_nodes",
        "white_avg_time", "black_avg_time",
        "total_avg_nodes", "total_avg_time",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(results):
            w.writerow({
                "game_index": i,
                "white_agent": r.white_agent,
                "black_agent": r.black_agent,
                "winner": r.winner or "draw",
                "white_won": 1 if r.winner == "w" else 0,
                "black_won": 1 if r.winner == "b" else 0,
                "draw": 1 if r.winner is None else 0,
                "moves": r.moves,
                "termination_reason": r.termination_reason,
                "white_avg_nodes": round(r.white_avg_nodes, 2),
                "black_avg_nodes": round(r.black_avg_nodes, 2),
                "white_avg_time": round(r.white_avg_time, 6),
                "black_avg_time": round(r.black_avg_time, 6),
                "total_avg_nodes": round((r.white_avg_nodes + r.black_avg_nodes) / 2, 2),
                "total_avg_time": round((r.white_avg_time + r.black_avg_time) / 2, 6),
            })


def _export_leaderboard_csv(lb, path):
    fields = [
        "rank", "agent_name", "features", "feature_count",
        "games_played", "wins", "losses", "draws",
        "score_rate", "win_rate", "draw_rate", "loss_rate",
        "avg_game_length",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, row in enumerate(lb, 1):
            gp = row.games_played or 1
            w.writerow({
                "rank": i,
                "agent_name": row.agent_name,
                "features": "|".join(row.features),
                "feature_count": len(row.features),
                "games_played": row.games_played,
                "wins": row.wins,
                "losses": row.losses,
                "draws": row.draws,
                "score_rate": round(row.score_rate, 4),
                "win_rate": round(row.wins / gp, 4),
                "draw_rate": round(row.draws / gp, 4),
                "loss_rate": round(row.losses / gp, 4),
                "avg_game_length": round(row.avg_game_length, 2),
            })


def _export_agents_csv(agents, lb, path):
    lb_lookup = {row.agent_name: row for row in lb}
    fields = ["agent_name", "features", "feature_count", "weights", "score_rate"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for a in agents:
            row = lb_lookup.get(a.name)
            w.writerow({
                "agent_name": a.name,
                "features": "|".join(a.features),
                "feature_count": len(a.features),
                "weights": "|".join(f"{k}={v:.4f}" for k, v in sorted(a.weights.items())),
                "score_rate": round(row.score_rate, 4) if row else "",
            })


def _export_marginals_csv(marginals, path):
    fields = ["feature", "avg_score_with", "avg_score_without", "marginal", "top_k_frequency"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for m in marginals:
            w.writerow({
                "feature": m.feature,
                "avg_score_with": round(m.avg_score_with, 4),
                "avg_score_without": round(m.avg_score_without, 4),
                "marginal": round(m.marginal, 4),
                "top_k_frequency": round(m.top_k_frequency, 4),
            })


def _export_synergies_csv(synergies, path):
    fields = ["feature_a", "feature_b", "avg_score_with_both", "synergy"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in synergies:
            w.writerow({
                "feature_a": s.feature_a,
                "feature_b": s.feature_b,
                "avg_score_with_both": round(s.avg_score_with_both, 4),
                "synergy": round(s.synergy, 4),
            })


def _export_synergy_matrix(synergies, feature_names, path):
    matrix = {a: {b: 0.0 for b in feature_names} for a in feature_names}
    for s in synergies:
        matrix[s.feature_a][s.feature_b] = round(s.synergy, 4)
        matrix[s.feature_b][s.feature_a] = round(s.synergy, 4)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([""] + feature_names)
        for feat in feature_names:
            w.writerow([feat] + [matrix[feat][b] for b in feature_names])


def _export_matchup_matrix(results, agents, path):
    """Win rate of row agent vs column agent."""
    names = sorted(a.name for a in agents)
    wins = defaultdict(lambda: defaultdict(int))
    games = defaultdict(lambda: defaultdict(int))
    for r in results:
        if r.winner == "w":
            wins[r.white_agent][r.black_agent] += 1
        elif r.winner == "b":
            wins[r.black_agent][r.white_agent] += 1
        games[r.white_agent][r.black_agent] += 1
        games[r.black_agent][r.white_agent] += 1

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([""] + names)
        for a in names:
            row = []
            for b in names:
                if a == b:
                    row.append("")
                else:
                    g = games[a][b]
                    row.append(round(wins[a][b] / g, 3) if g > 0 else "")
            w.writerow([a] + row)


def _export_head_to_head(results, path):
    """Detailed head-to-head records."""
    pairs = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "games": 0})
    for r in results:
        key_w = (r.white_agent, r.black_agent)
        pairs[key_w]["games"] += 1
        if r.winner == "w":
            pairs[key_w]["wins"] += 1
        elif r.winner == "b":
            pairs[key_w]["losses"] += 1
        else:
            pairs[key_w]["draws"] += 1

    fields = ["agent_a", "agent_b", "a_as_white_wins", "a_as_white_losses",
              "a_as_white_draws", "games_as_white"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for (a, b), stats in sorted(pairs.items()):
            w.writerow({
                "agent_a": a,
                "agent_b": b,
                "a_as_white_wins": stats["wins"],
                "a_as_white_losses": stats["losses"],
                "a_as_white_draws": stats["draws"],
                "games_as_white": stats["games"],
            })


def _export_termination_breakdown(results, path):
    counts = defaultdict(int)
    for r in results:
        counts[r.termination_reason] += 1
    fields = ["reason", "count", "percentage"]
    total = len(results)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for reason, count in sorted(counts.items(), key=lambda x: -x[1]):
            w.writerow({
                "reason": reason,
                "count": count,
                "percentage": round(100 * count / total, 2),
            })


def _export_game_lengths(results, path):
    """Per-game length + histogram buckets."""
    lengths = [r.moves for r in results]
    # Raw data
    fields = ["game_index", "moves", "termination_reason", "winner"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(results):
            w.writerow({
                "game_index": i,
                "moves": r.moves,
                "termination_reason": r.termination_reason,
                "winner": r.winner or "draw",
            })


def _export_by_feature_count(lb, path):
    """Average performance grouped by how many features an agent uses."""
    by_count = defaultdict(list)
    for row in lb:
        by_count[len(row.features)].append(row.score_rate)
    fields = ["feature_count", "num_agents", "avg_score_rate", "min_score_rate",
              "max_score_rate", "std_score_rate"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for count in sorted(by_count):
            rates = by_count[count]
            avg = sum(rates) / len(rates)
            std = (sum((x - avg) ** 2 for x in rates) / len(rates)) ** 0.5
            w.writerow({
                "feature_count": count,
                "num_agents": len(rates),
                "avg_score_rate": round(avg, 4),
                "min_score_rate": round(min(rates), 4),
                "max_score_rate": round(max(rates), 4),
                "std_score_rate": round(std, 4),
            })


def _export_feature_presence_impact(lb, feature_names, path):
    """For each feature: win rate when present vs absent, with counts."""
    fields = ["feature", "agents_with", "avg_rate_with", "agents_without",
              "avg_rate_without", "lift"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for feat in feature_names:
            with_rates = [r.score_rate for r in lb if feat in r.features]
            without_rates = [r.score_rate for r in lb if feat not in r.features]
            avg_w = sum(with_rates) / len(with_rates) if with_rates else 0
            avg_wo = sum(without_rates) / len(without_rates) if without_rates else 0
            w.writerow({
                "feature": feat,
                "agents_with": len(with_rates),
                "avg_rate_with": round(avg_w, 4),
                "agents_without": len(without_rates),
                "avg_rate_without": round(avg_wo, 4),
                "lift": round(avg_w - avg_wo, 4),
            })


def _export_summary_json(variant, results, agents, lb, marginals, synergies, interp, path):
    """Single JSON with all top-level stats."""
    total_games = len(results)
    decisive = sum(1 for r in results if r.winner is not None)
    draws = total_games - decisive

    term_counts = defaultdict(int)
    for r in results:
        term_counts[r.termination_reason] += 1

    lengths = [r.moves for r in results]

    summary = {
        "variant": variant,
        "total_agents": len(agents),
        "total_games": total_games,
        "decisive_games": decisive,
        "draws": draws,
        "draw_rate": round(draws / total_games, 4) if total_games else 0,
        "avg_game_length": round(sum(lengths) / len(lengths), 2) if lengths else 0,
        "min_game_length": min(lengths) if lengths else 0,
        "max_game_length": max(lengths) if lengths else 0,
        "termination_breakdown": dict(term_counts),
        "best_agent": {
            "name": lb[0].agent_name,
            "features": list(lb[0].features),
            "score_rate": lb[0].score_rate,
            "wins": lb[0].wins,
            "losses": lb[0].losses,
            "draws": lb[0].draws,
        } if lb else None,
        "worst_agent": {
            "name": lb[-1].agent_name,
            "features": list(lb[-1].features),
            "score_rate": lb[-1].score_rate,
        } if lb else None,
        "feature_rankings": [
            {"feature": m.feature, "marginal": round(m.marginal, 4)}
            for m in marginals
        ],
        "top_synergies": [
            {
                "pair": f"{s.feature_a} + {s.feature_b}",
                "synergy": round(s.synergy, 4),
            }
            for s in synergies[:5]
        ],
        "interpretation": interp,
    }

    with open(path, "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    import sys
    variant = sys.argv[1] if len(sys.argv) > 1 else "atomic"
    export_all(variant)
