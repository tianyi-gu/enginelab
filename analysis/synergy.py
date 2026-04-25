"""Pairwise synergy analysis — stub for Area 2 implementation."""

from dataclasses import dataclass

from tournament.leaderboard import LeaderboardRow


@dataclass
class SynergyRow:
    feature_a: str
    feature_b: str
    avg_score_with_both: float
    synergy: float


def compute_pairwise_synergies(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
) -> list[SynergyRow]:
    """Compute pairwise synergies. Stub — to be implemented in Area 2."""
    raise NotImplementedError("Pairwise synergies not yet implemented")
