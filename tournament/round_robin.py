"""Round-robin tournament runner for EngineLab."""

import random
import sys
from collections.abc import Callable
from itertools import permutations
from multiprocessing import Pool
from typing import Any

from tqdm import tqdm

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult, play_game


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def mock_play_game(
    white: FeatureSubsetAgent,
    black: FeatureSubsetAgent,
    **kwargs: Any,
) -> GameResult:
    """Return a randomly-generated GameResult (used when the variant is not implemented).

    Args:
        white:  White-side agent.
        black:  Black-side agent.
        **kwargs: Accepts `seed`, `variant`, `depth`, `max_moves` (all ignored
                  except `seed`).

    Returns:
        A GameResult with a random winner and move count.
    """
    rng = random.Random(kwargs.get("seed", 42))
    return GameResult(
        white_agent=white.name,
        black_agent=black.name,
        winner=rng.choice(["w", "b", None]),
        moves=rng.randint(10, 80),
        termination_reason="move_cap",
        white_avg_nodes=0.0,
        black_avg_nodes=0.0,
        white_avg_time=0.0,
        black_avg_time=0.0,
    )


# ---------------------------------------------------------------------------
# Internal helpers for multiprocessing (must be top-level for pickling)
# ---------------------------------------------------------------------------

def _play_one(args: tuple[FeatureSubsetAgent, FeatureSubsetAgent, str, int, int, int]) -> GameResult:
    """Play a single game; fall back to mock on NotImplementedError.

    Args:
        args: (white, black, variant, depth, max_moves, game_seed)

    Returns:
        Completed GameResult.
    """
    white, black, variant, depth, max_moves, game_seed = args
    try:
        return play_game(white, black, variant=variant, depth=depth, max_moves=max_moves, seed=game_seed)
    except NotImplementedError:
        return mock_play_game(white, black, variant=variant, depth=depth, max_moves=max_moves, seed=game_seed)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_round_robin(
    agents: list[FeatureSubsetAgent],
    variant: str,
    depth: int,
    max_moves: int,
    seed: int,
    workers: int = 1,
    on_game_complete: Callable[[int, int], None] | None = None,
) -> list[GameResult]:
    """Run a full round-robin tournament (every ordered pair plays once).

    Total games = N * (N - 1) where N = len(agents).
    Per-game seed = seed + game_index.

    Args:
        agents:            Participating agents.
        variant:           Chess variant name passed to play_game.
        depth:             Search depth passed to play_game.
        max_moves:         Move cap passed to play_game.
        seed:              Base seed; per-game seed is seed + game_index.
        workers:           Number of parallel worker processes (1 = serial).
        on_game_complete:  Optional callback invoked as (games_done, total_games)
                           after each game finishes.

    Returns:
        List of GameResult for every game that completed without error.
    """
    pairs = list(permutations(agents, 2))          # ordered pairs A!=B
    total_games = len(pairs)
    job_args = [
        (white, black, variant, depth, max_moves, seed + idx)
        for idx, (white, black) in enumerate(pairs)
    ]

    results: list[GameResult] = []
    skipped = 0
    games_done = 0

    progress = tqdm(
        total=total_games,
        desc="Round-robin",
        disable=not sys.stdout.isatty(),
    )

    def _handle_result(result: GameResult | Exception, job_idx: int) -> None:
        nonlocal skipped, games_done
        games_done += 1
        if isinstance(result, Exception):
            print(
                f"[round_robin] Game {job_idx} skipped due to error: {result}",
                file=sys.stderr,
            )
            skipped += 1
        else:
            results.append(result)
        progress.update(1)
        if on_game_complete is not None:
            on_game_complete(games_done, total_games)

    if workers > 1:
        with Pool(processes=workers) as pool:
            imap_iter = pool.imap(_play_one, job_args)
            for idx in range(total_games):
                try:
                    result = next(imap_iter)
                    _handle_result(result, idx)
                except Exception as exc:  # noqa: BLE001
                    _handle_result(exc, idx)
    else:
        for idx, args in enumerate(job_args):
            try:
                result = _play_one(args)
                _handle_result(result, idx)
            except Exception as exc:  # noqa: BLE001
                _handle_result(exc, idx)

    progress.close()

    if skipped:
        print(
            f"[round_robin] Tournament complete: {len(results)} games recorded, "
            f"{skipped} skipped.",
            file=sys.stderr,
        )

    return results
