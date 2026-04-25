"""Foundation tests for standard chess — apply_move, variant dispatch, game play."""

import pytest
from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_legal_moves
from variants.standard import apply_standard_move, generate_standard_moves
from variants.base import get_apply_move, get_generate_legal_moves, get_supported_variants
from agents.feature_subset_agent import FeatureSubsetAgent
from agents.evaluation import evaluate, normalize_feature_value, WIN_SCORE, LOSS_SCORE
from search.alpha_beta import AlphaBetaEngine
from simulation.game import play_game, GameResult


class TestApplyMove:
    def test_basic_pawn_push(self):
        b = Board.starting_position()
        m = Move((1, 4), (3, 4))  # e2e4
        new = apply_move(b, m)
        assert new.get_piece((3, 4)) == "P"
        assert new.get_piece((1, 4)) is None
        assert new.side_to_move == "b"
        assert new.move_count == 1

    def test_original_unchanged(self):
        b = Board.starting_position()
        m = Move((1, 4), (3, 4))
        new = apply_move(b, m)
        assert b.get_piece((1, 4)) == "P"
        assert b.side_to_move == "w"
        assert b.move_count == 0

    def test_en_passant_square_set(self):
        b = Board.starting_position()
        m = Move((1, 4), (3, 4))  # e2e4 double push
        new = apply_move(b, m)
        assert new.en_passant_square == (2, 4)

    def test_en_passant_square_cleared(self):
        b = Board.starting_position()
        b.en_passant_square = (2, 4)
        m = Move((0, 1), (2, 2))  # Knight move
        new = apply_move(b, m)
        assert new.en_passant_square is None

    def test_en_passant_capture(self):
        b = Board()
        b.set_piece((4, 4), "P")
        b.set_piece((4, 5), "p")
        b.en_passant_square = (5, 5)
        b.side_to_move = "w"
        m = Move((4, 4), (5, 5))
        new = apply_move(b, m)
        assert new.get_piece((5, 5)) == "P"
        assert new.get_piece((4, 5)) is None  # Captured pawn removed
        assert new.get_piece((4, 4)) is None

    def test_promotion(self):
        b = Board()
        b.set_piece((6, 0), "P")
        b.side_to_move = "w"
        m = Move((6, 0), (7, 0), promotion="Q")
        new = apply_move(b, m)
        assert new.get_piece((7, 0)) == "Q"

    def test_kingside_castling(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.castling_rights = {"K": True, "Q": False, "k": False, "q": False}
        b.side_to_move = "w"
        m = Move((0, 4), (0, 6))
        new = apply_move(b, m)
        assert new.get_piece((0, 6)) == "K"
        assert new.get_piece((0, 5)) == "R"
        assert new.get_piece((0, 4)) is None
        assert new.get_piece((0, 7)) is None

    def test_queenside_castling(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 0), "R")
        b.castling_rights = {"K": False, "Q": True, "k": False, "q": False}
        b.side_to_move = "w"
        m = Move((0, 4), (0, 2))
        new = apply_move(b, m)
        assert new.get_piece((0, 2)) == "K"
        assert new.get_piece((0, 3)) == "R"
        assert new.get_piece((0, 4)) is None
        assert new.get_piece((0, 0)) is None

    def test_castling_rights_lost_on_king_move(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.set_piece((0, 0), "R")
        b.castling_rights = {"K": True, "Q": True, "k": False, "q": False}
        b.side_to_move = "w"
        m = Move((0, 4), (0, 5))  # King steps right
        new = apply_move(b, m)
        assert new.castling_rights["K"] is False
        assert new.castling_rights["Q"] is False

    def test_castling_rights_lost_on_rook_move(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.castling_rights = {"K": True, "Q": False, "k": False, "q": False}
        b.side_to_move = "w"
        m = Move((0, 7), (0, 6))  # Rook moves
        new = apply_move(b, m)
        assert new.castling_rights["K"] is False

    def test_castling_rights_lost_on_rook_capture(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.set_piece((7, 7), "r")
        b.castling_rights = {"K": True, "Q": False, "k": True, "q": False}
        b.side_to_move = "w"
        # If something captures on h8, black loses kingside rights
        b.set_piece((6, 7), "Q")
        m = Move((6, 7), (7, 7))
        new = apply_move(b, m)
        assert new.castling_rights["k"] is False


class TestVariantDispatch:
    def test_standard_in_supported(self):
        assert "standard" in get_supported_variants()

    def test_get_apply_move(self):
        fn = get_apply_move("standard")
        assert fn is apply_standard_move

    def test_get_generate_legal(self):
        fn = get_generate_legal_moves("standard")
        assert fn is generate_standard_moves

    def test_standard_moves_match(self):
        b = Board.starting_position()
        assert generate_standard_moves(b) == generate_legal_moves(b)


class TestEvaluation:
    def test_normalize(self):
        assert normalize_feature_value(0.0) == 0.0
        assert normalize_feature_value(10.0) == 1.0
        assert normalize_feature_value(-10.0) == -1.0
        assert normalize_feature_value(20.0) == 1.0  # Clipped
        assert normalize_feature_value(-20.0) == -1.0

    def test_starting_material_equal(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        score = evaluate(b, "w", agent)
        assert score == 0.0  # Equal material

    def test_material_advantage(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")  # White has a queen
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        score = evaluate(b, "w", agent)
        assert score > 0

    def test_win_score(self):
        b = Board()
        b.winner = "w"
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        assert evaluate(b, "w", agent) == WIN_SCORE
        assert evaluate(b, "b", agent) == LOSS_SCORE

    def test_draw_score(self):
        b = Board()
        b.winner = "draw"
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        assert evaluate(b, "w", agent) == 0.0


class TestAlphaBeta:
    def test_choose_move_returns_legal(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        move = engine.choose_move(b)
        legal = generate_legal_moves(b)
        assert move in legal

    def test_captures_when_possible(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")
        b.set_piece((3, 5), "r")  # Hanging black rook
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        move = engine.choose_move(b)
        # Should capture the rook
        assert move.end == (3, 5)

    def test_nodes_searched_positive(self):
        b = Board.starting_position()
        agent = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        engine = AlphaBetaEngine(agent, depth=1)
        engine.choose_move(b)
        assert engine.nodes_searched > 0
        assert engine.search_time_seconds >= 0


class TestPlayGame:
    def test_foundation_acceptance(self):
        """The Foundation acceptance test from the PRD."""
        a = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        result = play_game(a, a, variant="standard", depth=1, max_moves=40, seed=42)
        assert isinstance(result, GameResult)
        assert result.moves > 0
        assert result.termination_reason in ("checkmate", "stalemate", "move_cap")
        assert result.white_agent == "Agent_material"
        assert result.black_agent == "Agent_material"

    def test_deterministic(self):
        """Same seed should produce identical results."""
        a = FeatureSubsetAgent("Agent_material", ("material",), {"material": 1.0})
        r1 = play_game(a, a, variant="standard", depth=1, max_moves=20, seed=42)
        r2 = play_game(a, a, variant="standard", depth=1, max_moves=20, seed=42)
        assert r1.moves == r2.moves
        assert r1.winner == r2.winner
        assert r1.termination_reason == r2.termination_reason
