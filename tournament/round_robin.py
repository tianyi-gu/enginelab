"""Round-robin tournament for EngineLab.

Plays every ordered pair (A as white, B as black) once.
N agents produce N*(N-1) games.
"""

from tqdm import tqdm

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult, play_game


def run_round_robin(
    agents: list[FeatureSubsetAgent],
    variant: str,
    depth: int,
    max_moves: int,
    seed: int,
    on_game_complete=None,
) -> list[GameResult]:
    """Play every ordered pair once: N*(N-1) games.

    Per-game seed = tournament_seed + game_index for reproducibility.

    Args:
        on_game_complete: Optional callback(games_done, total, result)
            called after each game completes. For UI progress updates.
    """
    games: list[tuple[FeatureSubsetAgent, FeatureSubsetAgent, int]] = []
    game_index = 0
    for i, white in enumerate(agents):
        for j, black in enumerate(agents):
            if i == j:
                continue
            games.append((white, black, seed + game_index))
            game_index += 1

    total = len(games)
    results: list[GameResult] = []
    for white, black, game_seed in tqdm(games, desc="Tournament"):
        result = play_game(
            white, black,
            variant=variant,
            depth=depth,
            max_moves=max_moves,
            seed=game_seed,
        )
        results.append(result)
        if on_game_complete is not None:
            on_game_complete(len(results), total, result)

    return results
