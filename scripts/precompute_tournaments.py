"""Pre-compute tournament data for all variants at depth=2.

Usage:
    python scripts/precompute_tournaments.py [--workers N] [--agents N]

Defaults: workers=cpu_count, agents=20 (→ 380 games/variant, ~3 min total).
For higher coverage use --agents 30 (870 games, ~8 min on 8 cores).
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.generate_agents import generate_feature_subset_agents
from analysis.feature_marginals import compute_feature_marginals
from tournament.round_robin import run_round_robin

VARIANT_FEATURES: dict[str, tuple[list[str], int]] = {
    "standard": (
        ["material", "mobility", "king_safety", "enemy_king_danger",
         "capture_threats", "center_control", "piece_position", "pawn_structure"],
        80,  # max_moves
    ),
    "atomic": (
        ["mobility", "capture_threats", "center_control", "enemy_king_danger",
         "explosion_proximity", "piece_position", "bishop_pair", "material"],
        80,
    ),
    "antichess": (
        ["antichess_material", "center_control", "mobility", "enemy_king_danger",
         "pawn_structure", "material", "piece_position", "king_safety"],
        60,
    ),
}

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "outputs", "data")


def _run_variant(variant: str, features: list[str], max_moves: int,
                 max_agents: int, depth: int, workers: int) -> dict:
    agents = generate_feature_subset_agents(features, max_agents=max_agents)
    n_games = len(agents) * (len(agents) - 1)
    print(f"  [{variant}] {len(agents)} agents, {n_games} games, depth={depth}, workers={workers}")

    t0 = time.time()
    results = run_round_robin(
        agents, variant, depth=depth, max_moves=max_moves, seed=42, workers=workers,
    )
    elapsed = time.time() - t0
    print(f"  [{variant}] Done in {elapsed:.1f}s ({len(results)} games)")

    out = [
        {
            "white_agent": r.white_agent,
            "black_agent": r.black_agent,
            "winner": r.winner,
            "moves": r.moves,
            "termination_reason": r.termination_reason,
            "white_avg_nodes": r.white_avg_nodes,
            "black_avg_nodes": r.black_avg_nodes,
            "white_avg_time": r.white_avg_time,
            "black_avg_time": r.black_avg_time,
            "move_list": getattr(r, "move_list", []),
        }
        for r in results
    ]
    path = os.path.join(OUT_DIR, f"tournament_results_{variant}.json")
    with open(path, "w") as f:
        json.dump(out, f)

    marginals = compute_feature_marginals(results, features)
    sorted_m = sorted(marginals.items(), key=lambda x: -x[1])
    print(f"  [{variant}] Marginals: " +
          ", ".join(f"{k}={v:+.3f}" for k, v in sorted_m[:4]))
    return {"variant": variant, "games": len(results), "elapsed": elapsed, "marginals": marginals}


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-compute tournament data")
    parser.add_argument("--workers", type=int, default=multiprocessing.cpu_count(),
                        help="Parallel game workers (default: cpu_count)")
    parser.add_argument("--agents", type=int, default=20,
                        help="Max agents per variant (default: 20 → 380 games)")
    parser.add_argument("--depth", type=int, default=2,
                        help="Search depth (default: 2)")
    parser.add_argument("--variants", nargs="+", default=list(VARIANT_FEATURES.keys()),
                        help="Variants to run (default: all)")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Precomputing {args.variants} | depth={args.depth} | "
          f"agents={args.agents} | workers={args.workers}")
    print()

    # Run variants sequentially (each already uses all workers internally)
    total_t0 = time.time()
    for variant in args.variants:
        features, max_moves = VARIANT_FEATURES[variant]
        _run_variant(variant, features, max_moves, args.agents, args.depth, args.workers)
        print()

    print(f"All done in {time.time() - total_t0:.1f}s")
    print(f"Files written to: {OUT_DIR}")


if __name__ == "__main__":
    # Required for ProcessPoolExecutor on macOS (spawn start method)
    multiprocessing.freeze_support()
    main()
