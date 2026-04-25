"""Round-robin tournament for EngineLab.

Plays every ordered pair (A as white, B as black) once.
N agents produce N*(N-1) games.
"""

from __future__ import annotations

import concurrent.futures
import os

from tqdm import tqdm

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult, play_game


def _play_one(args: tuple) -> tuple[int, GameResult]:
    """Top-level wrapper so ProcessPoolExecutor can pickle it."""
    idx, white, black, variant, depth, max_moves, game_seed = args
    result = play_game(white, black, variant=variant, depth=depth,
                       max_moves=max_moves, seed=game_seed)
    return idx, result


def run_round_robin(
    agents: list[FeatureSubsetAgent],
    variant: str,
    depth: int,
    max_moves: int,
    seed: int,
    on_game_complete=None,
    workers: int = 1,
) -> list[GameResult]:
    """Play every ordered pair once: N*(N-1) games.

    Per-game seed = tournament_seed + game_index for reproducibility.

    Args:
        on_game_complete: Optional callback(games_done, total, result).
            Only called in single-worker mode (serial execution).
        workers: Number of parallel worker processes (default 1 = serial).
            Pass workers=os.cpu_count() for full parallelism.
    """
    game_args: list[tuple] = []
    game_index = 0
    for i, white in enumerate(agents):
        for j, black in enumerate(agents):
            if i == j:
                continue
            game_args.append(
                (game_index, white, black, variant, depth, max_moves, seed + game_index)
            )
            game_index += 1

    total = len(game_args)

    if workers == 1:
        results: list[GameResult] = []
        for args in tqdm(game_args, desc="Tournament"):
            _, result = _play_one(args)
            results.append(result)
            if on_game_complete is not None:
                on_game_complete(len(results), total, result)
        return results

    # Parallel execution — preserves game order via index
    ordered: list[GameResult | None] = [None] * total
    done = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_play_one, args): args[0] for args in game_args}
        pbar = tqdm(total=total, desc="Tournament")
        for fut in concurrent.futures.as_completed(futures):
            idx, result = fut.result()
            ordered[idx] = result
            done += 1
            pbar.update(1)
        pbar.close()

    return ordered  # type: ignore[return-value]
