"""Tests for agent generation and evaluation."""

import pytest

from core.board import Board
from agents.feature_subset_agent import FeatureSubsetAgent
from agents.generate_agents import generate_feature_subset_agents
from agents.evaluation import evaluate, contributions, WIN_SCORE, LOSS_SCORE


class TestAgentGeneration:
    def test_five_features_exhaustive(self):
        """5 features -> 2^5 - 1 = 31 agents (exhaustive)."""
        feats = ["a", "b", "c", "d", "e"]
        agents = generate_feature_subset_agents(feats, max_agents=100)
        assert len(agents) == 31

    def test_all_names_unique(self):
        feats = ["a", "b", "c", "d", "e"]
        agents = generate_feature_subset_agents(feats)
        names = [a.name for a in agents]
        assert len(names) == len(set(names))

    def test_weights_sum_to_one(self):
        feats = ["a", "b", "c", "d", "e"]
        agents = generate_feature_subset_agents(feats)
        for agent in agents:
            assert sum(agent.weights.values()) == pytest.approx(1.0)

    def test_features_sorted_in_name(self):
        feats = ["z", "a", "m"]
        agents = generate_feature_subset_agents(feats)
        for agent in agents:
            parts = agent.name.replace("Agent_", "").split("__")
            assert parts == sorted(parts)

    def test_stratified_when_too_many(self):
        """10 features -> 1023 subsets, max_agents=100 -> stratified."""
        feats = [f"f{i}" for i in range(10)]
        agents = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        assert len(agents) <= 80
        assert len(agents) > 0

    def test_stratified_includes_all_singles(self):
        feats = [f"f{i}" for i in range(10)]
        agents = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        single_feats = {a.features[0] for a in agents if len(a.features) == 1}
        assert single_feats == set(feats)

    def test_stratified_includes_all_pairs(self):
        feats = [f"f{i}" for i in range(10)]
        agents = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        pair_count = sum(1 for a in agents if len(a.features) == 2)
        # C(10,2) = 45 pairs
        assert pair_count == 45

    def test_stratified_includes_full_set(self):
        feats = [f"f{i}" for i in range(10)]
        agents = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        full = [a for a in agents if len(a.features) == 10]
        assert len(full) == 1

    def test_deterministic(self):
        feats = [f"f{i}" for i in range(10)]
        a1 = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        a2 = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        assert [a.name for a in a1] == [a.name for a in a2]

    def test_real_features(self):
        """Generate agents from real feature registry."""
        from features.registry import get_feature_names
        feats = get_feature_names()
        agents = generate_feature_subset_agents(feats, max_agents=80, seed=42)
        assert len(agents) > 0
        for agent in agents:
            assert all(f in feats for f in agent.features)


class TestEvaluation:
    def test_evaluate_non_terminal(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        score = evaluate(b, "w", agent)
        assert isinstance(score, float)

    def test_evaluate_with_multiple_features(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent(
            "Agent_material__mobility",
            ("material", "mobility"),
            {"material": 0.5, "mobility": 0.5},
        )
        score = evaluate(b, "w", agent)
        assert isinstance(score, float)
        assert score == 0.0  # Symmetric position

    def test_evaluate_terminal_win(self):
        b = Board()
        b.winner = "w"
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        assert evaluate(b, "w", agent) == WIN_SCORE

    def test_evaluate_terminal_loss(self):
        b = Board()
        b.winner = "w"
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        assert evaluate(b, "b", agent) == LOSS_SCORE

    def test_contributions_returns_dict(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent(
            "Agent_material__mobility",
            ("material", "mobility"),
            {"material": 0.5, "mobility": 0.5},
        )
        result = contributions(b, "w", agent)
        assert isinstance(result, dict)
        assert "material" in result
        assert "mobility" in result
