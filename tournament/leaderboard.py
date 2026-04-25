"""Leaderboard computation for EngineLab tournaments."""

from dataclasses import dataclass

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult


@dataclass
class LeaderboardRow:
    agent_name: str
    features: tuple[str, ...]
    games_played: int
    wins: int
    losses: int
    draws: int
    score_rate: float
    avg_game_length: float


def compute_leaderboard(
    results: list[GameResult],
    agents: list[FeatureSubsetAgent],
) -> list[LeaderboardRow]:
    """Compute a leaderboard from tournament results.

    Each agent accumulates wins (1 pt), draws (0.5 pt), and losses (0 pt).
    score_rate = (wins + 0.5 * draws) / games_played, or 0.0 if no games.
    avg_game_length is the mean of `moves` across all games that agent played.
    The returned list is sorted by score_rate descending.

    Args:
        results: Completed game results from a tournament.
        agents:  All agents that participated (defines the row set).

    Returns:
        List of LeaderboardRow sorted by score_rate descending.
    """
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
            elif (game.winner == "w" and game.white_agent == agent.name) or (
                game.winner == "b" and game.black_agent == agent.name
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
                score_rate=score_rate,
                avg_game_length=avg_game_length,
            )
        )

    rows.sort(key=lambda r: r.score_rate, reverse=True)
    return rows
