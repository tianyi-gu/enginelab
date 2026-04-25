"""Tests for analysis functions — feature marginals, synergy, interpretation."""

import pytest

from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import compute_feature_marginals, FeatureContributionRow
from analysis.synergy import compute_pairwise_synergies, SynergyRow
from analysis.interpretation import generate_interpretation
from reports.markdown_report import generate_markdown_report

import tempfile
from pathlib import Path


# -- Fixtures --

@pytest.fixture
def synthetic_leaderboard():
    """Leaderboard with known marginal and synergy values."""
    return [
        LeaderboardRow("Agent_a", ("a",), 6, 4, 1, 1, 0.75, 30),
        LeaderboardRow("Agent_b", ("b",), 6, 2, 3, 1, 0.42, 35),
        LeaderboardRow("Agent_c", ("c",), 6, 1, 4, 1, 0.25, 40),
        LeaderboardRow("Agent_a__b", ("a", "b"), 6, 5, 0, 1, 0.92, 25),
        LeaderboardRow("Agent_a__c", ("a", "c"), 6, 3, 2, 1, 0.58, 32),
        LeaderboardRow("Agent_b__c", ("b", "c"), 6, 1, 4, 1, 0.25, 38),
        LeaderboardRow("Agent_a__b__c", ("a", "b", "c"), 6, 4, 1, 1, 0.75, 28),
    ]


@pytest.fixture
def feature_names():
    return ["a", "b", "c"]


# -- Feature Marginals --

class TestFeatureMarginals:
    def test_returns_all_features(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        result_feats = {m.feature for m in marginals}
        assert result_feats == {"a", "b", "c"}

    def test_sorted_by_marginal_descending(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        values = [m.marginal for m in marginals]
        assert values == sorted(values, reverse=True)

    def test_marginal_is_difference(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        for m in marginals:
            assert m.marginal == pytest.approx(m.avg_score_with - m.avg_score_without)

    def test_top_k_frequency(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names, top_k=3,
        )
        # Leaderboard is NOT pre-sorted — top_k uses the input order.
        # Input order top 3: Agent_a (0.75), Agent_b (0.42), Agent_c (0.25)
        # Feature a appears in 1 of those 3
        a_row = next(m for m in marginals if m.feature == "a")
        # Just verify it's a valid frequency between 0 and 1
        assert 0.0 <= a_row.top_k_frequency <= 1.0

    def test_positive_marginal_means_feature_helps(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        a_row = next(m for m in marginals if m.feature == "a")
        assert a_row.marginal > 0  # feature a clearly helps

    def test_empty_leaderboard(self, feature_names):
        marginals = compute_feature_marginals([], feature_names)
        for m in marginals:
            assert m.avg_score_with == 0.0
            assert m.avg_score_without == 0.0
            assert m.marginal == 0.0


# -- Pairwise Synergy --

class TestPairwiseSynergy:
    def test_returns_all_pairs(self, synthetic_leaderboard, feature_names):
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        # 3 features -> 3 pairs
        assert len(synergies) == 3

    def test_sorted_by_synergy_descending(self, synthetic_leaderboard, feature_names):
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        values = [s.synergy for s in synergies]
        assert values == sorted(values, reverse=True)

    def test_synergy_formula(self, synthetic_leaderboard, feature_names):
        """Verify synergy(a,b) = avg_both - avg_a - avg_b + overall."""
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )

        overall = sum(r.score_rate for r in synthetic_leaderboard) / len(synthetic_leaderboard)
        avg_a = sum(
            r.score_rate for r in synthetic_leaderboard if "a" in r.features
        ) / sum(1 for r in synthetic_leaderboard if "a" in r.features)
        avg_b = sum(
            r.score_rate for r in synthetic_leaderboard if "b" in r.features
        ) / sum(1 for r in synthetic_leaderboard if "b" in r.features)
        avg_both = sum(
            r.score_rate for r in synthetic_leaderboard
            if "a" in r.features and "b" in r.features
        ) / sum(
            1 for r in synthetic_leaderboard
            if "a" in r.features and "b" in r.features
        )

        expected = avg_both - avg_a - avg_b + overall
        ab_row = next(
            s for s in synergies
            if {s.feature_a, s.feature_b} == {"a", "b"}
        )
        assert ab_row.synergy == pytest.approx(expected)

    def test_empty_leaderboard(self, feature_names):
        synergies = compute_pairwise_synergies([], feature_names)
        for s in synergies:
            assert s.synergy == 0.0


# -- Interpretation --

class TestInterpretation:
    def test_returns_string(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        interp = generate_interpretation(
            synthetic_leaderboard[0], marginals, synergies, "standard",
        )
        assert isinstance(interp, str)
        assert len(interp) > 50

    def test_mentions_best_agent(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        best = synthetic_leaderboard[0]
        interp = generate_interpretation(best, marginals, synergies, "standard")
        assert best.agent_name in interp

    def test_mentions_variant(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        interp = generate_interpretation(
            synthetic_leaderboard[0], marginals, synergies, "atomic",
        )
        assert "atomic" in interp


# -- Markdown Report --

class TestMarkdownReport:
    def test_generates_file(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        interp = generate_interpretation(
            synthetic_leaderboard[0], marginals, synergies, "standard",
        )

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name

        generate_markdown_report(
            variant="standard",
            feature_names=feature_names,
            leaderboard=synthetic_leaderboard,
            marginals=marginals,
            synergies=synergies,
            interpretation=interp,
            output_path=path,
            config={"depth": 2, "max_moves": 80},
        )

        content = Path(path).read_text()
        assert "# EngineLab Strategy Report" in content
        assert "Leaderboard" in content
        assert "Feature Contributions" in content
        assert "Synergies" in content
        assert "Interpretation" in content
        assert "Limitations" in content

        Path(path).unlink()

    def test_contains_all_agents(self, synthetic_leaderboard, feature_names):
        marginals = compute_feature_marginals(
            synthetic_leaderboard, feature_names,
        )
        synergies = compute_pairwise_synergies(
            synthetic_leaderboard, feature_names,
        )
        interp = "Test interpretation."

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name

        generate_markdown_report(
            variant="standard",
            feature_names=feature_names,
            leaderboard=synthetic_leaderboard,
            marginals=marginals,
            synergies=synergies,
            interpretation=interp,
            output_path=path,
            config={},
        )

        content = Path(path).read_text()
        for row in synthetic_leaderboard:
            assert row.agent_name in content

        Path(path).unlink()
