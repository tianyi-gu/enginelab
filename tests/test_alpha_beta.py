"""Tests for alpha-beta search engine."""

import pytest

from core.board import Board
from core.move import Move
from core.move_generation import generate_legal_moves
from agents.feature_subset_agent import FeatureSubsetAgent
from search.alpha_beta import AlphaBetaEngine


class TestAlphaBetaDepth1:
    def test_returns_legal_move_depth1(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        move = engine.choose_move(b)
        assert move in generate_legal_moves(b)

    def test_captures_hanging_piece(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")
        b.set_piece((3, 7), "r")  # Hanging rook
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        move = engine.choose_move(b)
        assert move.end == (3, 7)

    def test_nodes_searched_positive(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        engine.choose_move(b)
        assert engine.nodes_searched > 0
        assert engine.search_time_seconds >= 0


class TestAlphaBetaDepth2:
    def test_returns_legal_move_depth2(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=2)
        move = engine.choose_move(b)
        assert move in generate_legal_moves(b)

    def test_depth2_searches_more_nodes(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})

        e1 = AlphaBetaEngine(agent, depth=1)
        e1.choose_move(b)

        e2 = AlphaBetaEngine(agent, depth=2)
        e2.choose_move(b)

        assert e2.nodes_searched > e1.nodes_searched


class TestAlphaBetaVariantAware:
    def test_standard_variant(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1, variant="standard")
        move = engine.choose_move(b)
        assert move in generate_legal_moves(b)

    def test_atomic_variant(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1, variant="atomic")
        move = engine.choose_move(b)
        from variants.atomic import generate_atomic_moves
        assert move in generate_atomic_moves(b)


class TestMoveOrdering:
    def test_captures_ordered_by_victim_value(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")  # Queen can capture both
        b.set_piece((3, 7), "r")  # Rook (value 5)
        b.set_piece((3, 0), "n")  # Knight (value 3)
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        move = engine.choose_move(b)
        # Should prefer capturing the rook (higher value)
        assert move.end == (3, 7)


class TestMultiFeatureSearch:
    def test_search_with_multiple_features(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent(
            "Agent_material__mobility",
            ("material", "mobility"),
            {"material": 0.5, "mobility": 0.5},
        )
        engine = AlphaBetaEngine(agent, depth=1)
        move = engine.choose_move(b)
        assert move in generate_legal_moves(b)
