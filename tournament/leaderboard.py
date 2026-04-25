"""Leaderboard computation for EngineLab.

Scoring: win=1.0, draw=0.5, loss=0.0.
score_rate = (wins + 0.5 * draws) / games_played.
"""

from dataclasses import dataclass

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult


@dataclass
class LeaderboardRow:
    """A single row in the tournament leaderboard."""

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
    """Compute leaderboard sorted by score_rate descending."""
    agent_map = {a.name: a for a in agents}

    stats: dict[str, dict] = {}
    for agent in agents:
        stats[agent.name] = {
            "wins": 0, "losses": 0, "draws": 0,
            "games": 0, "total_moves": 0,
        }

    for result in results:
        for name, role in [(result.white_agent, "w"), (result.black_agent, "b")]:
            if name not in stats:
                continue
            stats[name]["games"] += 1
            stats[name]["total_moves"] += result.moves
            if result.winner is None:
                stats[name]["draws"] += 1
            elif result.winner == role:
                stats[name]["wins"] += 1
            else:
                stats[name]["losses"] += 1

    rows: list[LeaderboardRow] = []
    for name, s in stats.items():
        games = s["games"]
        if games == 0:
            score_rate = 0.0
            avg_length = 0.0
        else:
            score_rate = (s["wins"] + 0.5 * s["draws"]) / games
            avg_length = s["total_moves"] / games

        agent = agent_map[name]
        rows.append(LeaderboardRow(
            agent_name=name,
            features=agent.features,
            games_played=games,
            wins=s["wins"],
            losses=s["losses"],
            draws=s["draws"],
            score_rate=score_rate,
            avg_game_length=avg_length,
        ))

    rows.sort(key=lambda r: r.score_rate, reverse=True)
    return rows
