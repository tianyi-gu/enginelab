"""Tests for tournament infrastructure — round-robin, leaderboard, results I/O."""

import json
import tempfile
from pathlib import Path

import pytest

from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult, mock_play_game, play_game
from simulation.random_agent import RandomAgent
from tournament.round_robin import run_round_robin
from tournament.leaderboard import compute_leaderboard, LeaderboardRow
from tournament.results_io import save_results_json, load_results_json, save_results_csv


# -- Fixtures --

def _make_agent(name: str, *features: str) -> FeatureSubsetAgent:
    feats = tuple(sorted(features))
    weights = {f: 1.0 / len(feats) for f in feats}
    return FeatureSubsetAgent(f"Agent_{'__'.join(feats)}", feats, weights)


@pytest.fixture
def three_agents():
    return [
        _make_agent("a1", "material"),
        _make_agent("a2", "mobility"),
        _make_agent("a3", "material", "mobility"),
    ]


@pytest.fixture
def sample_results():
    """Hand-crafted results for deterministic testing."""
    return [
        GameResult("A", "B", "w", 30, "checkmate", 10, 12, 0.1, 0.1),
        GameResult("B", "A", "b", 25, "checkmate", 8, 15, 0.1, 0.1),
        GameResult("A", "C", None, 80, "move_cap", 10, 10, 0.1, 0.1),
        GameResult("C", "A", "w", 40, "checkmate", 10, 10, 0.1, 0.1),
        GameResult("B", "C", "w", 35, "checkmate", 10, 10, 0.1, 0.1),
        GameResult("C", "B", None, 80, "move_cap", 10, 10, 0.1, 0.1),
    ]


# -- MockPlayGame --

class TestMockPlayGame:
    def test_returns_game_result(self):
        a = _make_agent("x", "material")
        result = mock_play_game(a, a, seed=42)
        assert isinstance(result, GameResult)

    def test_deterministic(self):
        a = _make_agent("x", "material")
        r1 = mock_play_game(a, a, seed=42)
        r2 = mock_play_game(a, a, seed=42)
        assert r1.winner == r2.winner
        assert r1.moves == r2.moves

    def test_different_seeds_differ(self):
        a = _make_agent("x", "material")
        results = [mock_play_game(a, a, seed=i) for i in range(20)]
        winners = {r.winner for r in results}
        assert len(winners) > 1  # Should get variety


# -- RandomAgent --

class TestRandomAgent:
    def test_random_vs_random_completes(self):
        ra = RandomAgent(seed=1)
        rb = RandomAgent(seed=2)
        result = play_game(ra, rb, variant="standard", max_moves=20, seed=42)
        assert isinstance(result, GameResult)
        assert result.moves > 0

    def test_deterministic(self):
        ra1 = RandomAgent(seed=1)
        rb1 = RandomAgent(seed=2)
        r1 = play_game(ra1, rb1, variant="standard", max_moves=20, seed=42)

        ra2 = RandomAgent(seed=1)
        rb2 = RandomAgent(seed=2)
        r2 = play_game(ra2, rb2, variant="standard", max_moves=20, seed=42)

        assert r1.moves == r2.moves
        assert r1.winner == r2.winner


# -- FeatureSubsetAgent Game --

class TestAgentGame:
    def test_agent_vs_agent_completes(self):
        a = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        result = play_game(a, a, variant="standard", depth=1, max_moves=20, seed=42)
        assert isinstance(result, GameResult)
        assert result.moves > 0
        assert result.white_agent == "Agent_material"


# -- RoundRobin --

class TestRoundRobin:
    def test_three_agents_six_games(self, three_agents):
        results = run_round_robin(
            three_agents, variant="standard", depth=1, max_moves=10, seed=42,
        )
        assert len(results) == 6

    def test_all_pairs_played(self, three_agents):
        results = run_round_robin(
            three_agents, variant="standard", depth=1, max_moves=10, seed=42,
        )
        pairs = {(r.white_agent, r.black_agent) for r in results}
        for i, a in enumerate(three_agents):
            for j, b in enumerate(three_agents):
                if i != j:
                    assert (a.name, b.name) in pairs

    def test_deterministic(self, three_agents):
        r1 = run_round_robin(three_agents, "standard", 1, 10, seed=42)
        r2 = run_round_robin(three_agents, "standard", 1, 10, seed=42)
        for a, b in zip(r1, r2):
            assert a.winner == b.winner
            assert a.moves == b.moves


# -- Leaderboard --

class TestLeaderboard:
    def test_all_agents_present(self, sample_results):
        agents = [
            FeatureSubsetAgent("A", ("a",), {"a": 1.0}),
            FeatureSubsetAgent("B", ("b",), {"b": 1.0}),
            FeatureSubsetAgent("C", ("c",), {"c": 1.0}),
        ]
        lb = compute_leaderboard(sample_results, agents)
        names = {r.agent_name for r in lb}
        assert names == {"A", "B", "C"}

    def test_game_counts_correct(self, sample_results):
        agents = [
            FeatureSubsetAgent("A", ("a",), {"a": 1.0}),
            FeatureSubsetAgent("B", ("b",), {"b": 1.0}),
            FeatureSubsetAgent("C", ("c",), {"c": 1.0}),
        ]
        lb = compute_leaderboard(sample_results, agents)
        for row in lb:
            assert row.games_played == 4
            assert row.wins + row.losses + row.draws == 4

    def test_sorted_by_score_rate(self, sample_results):
        agents = [
            FeatureSubsetAgent("A", ("a",), {"a": 1.0}),
            FeatureSubsetAgent("B", ("b",), {"b": 1.0}),
            FeatureSubsetAgent("C", ("c",), {"c": 1.0}),
        ]
        lb = compute_leaderboard(sample_results, agents)
        rates = [r.score_rate for r in lb]
        assert rates == sorted(rates, reverse=True)

    def test_score_rate_formula(self):
        results = [
            GameResult("X", "Y", "w", 30, "checkmate", 0, 0, 0, 0),
            GameResult("Y", "X", None, 80, "move_cap", 0, 0, 0, 0),
        ]
        agents = [
            FeatureSubsetAgent("X", ("x",), {"x": 1.0}),
            FeatureSubsetAgent("Y", ("y",), {"y": 1.0}),
        ]
        lb = compute_leaderboard(results, agents)
        x_row = next(r for r in lb if r.agent_name == "X")
        # X: 1 win + 0.5*1 draw = 1.5 / 2 = 0.75
        assert x_row.score_rate == pytest.approx(0.75)
        y_row = next(r for r in lb if r.agent_name == "Y")
        # Y: 0 wins + 0.5*1 draw = 0.5 / 2 = 0.25
        assert y_row.score_rate == pytest.approx(0.25)


# -- Results I/O --

class TestResultsIO:
    def test_json_round_trip(self, sample_results):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        save_results_json(sample_results, path)
        loaded = load_results_json(path)

        assert len(loaded) == len(sample_results)
        for orig, load in zip(sample_results, loaded):
            assert orig.white_agent == load.white_agent
            assert orig.black_agent == load.black_agent
            assert orig.winner == load.winner
            assert orig.moves == load.moves
            assert orig.termination_reason == load.termination_reason

        Path(path).unlink()

    def test_csv_export(self, sample_results):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        save_results_csv(sample_results, path)
        content = Path(path).read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 7  # header + 6 results

        Path(path).unlink()

    def test_creates_parent_dirs(self, sample_results):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/nested/dir/results.json"
            save_results_json(sample_results, path)
            assert Path(path).exists()
