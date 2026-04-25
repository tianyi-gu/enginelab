"""Tests for all evaluation features."""

import pytest

from core.board import Board
from features.registry import FEATURES, get_feature_names, get_feature_function


class TestFeatureRegistry:
    def test_ten_features_registered(self):
        assert len(FEATURES) == 12

    def test_all_feature_names(self):
        expected = {
            "material", "piece_position", "center_control", "king_safety",
            "enemy_king_danger", "mobility", "pawn_structure", "bishop_pair",
            "rook_activity", "capture_threats",
            "negative_material", "explosion_proximity",
        }
        assert set(get_feature_names()) == expected

    def test_get_feature_function(self):
        for name in get_feature_names():
            fn = get_feature_function(name)
            assert callable(fn)


class TestFeaturesReturnFloat:
    @pytest.mark.parametrize("feature_name", [
        "material", "piece_position", "center_control", "king_safety",
        "enemy_king_danger", "mobility", "pawn_structure", "bishop_pair",
        "rook_activity", "capture_threats", "negative_material", "explosion_proximity",
    ])
    def test_returns_float(self, feature_name):
        b = Board.starting_position()
        fn = get_feature_function(feature_name)
        result = fn(b, "w")
        assert isinstance(result, (int, float))

    @pytest.mark.parametrize("feature_name", [
        "material", "piece_position", "center_control", "king_safety",
        "enemy_king_danger", "mobility", "pawn_structure", "bishop_pair",
        "rook_activity", "capture_threats", "negative_material", "explosion_proximity",
    ])
    def test_does_not_mutate_board(self, feature_name):
        b = Board.starting_position()
        original_grid = [row[:] for row in b.grid]
        fn = get_feature_function(feature_name)
        fn(b, "w")
        fn(b, "b")
        assert b.grid == original_grid


class TestMaterial:
    def test_starting_position_zero(self):
        b = Board.starting_position()
        assert FEATURES["material"](b, "w") == 0.0

    def test_white_advantage(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")
        assert FEATURES["material"](b, "w") == 9.0
        assert FEATURES["material"](b, "b") == -9.0


class TestPawnStructure:
    def test_doubled_pawns(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((2, 0), "P")
        b.set_piece((4, 0), "P")  # Doubled on file a
        score = FEATURES["pawn_structure"](b, "w")
        # Should be negative due to doubled penalty
        assert score < 1.0  # Net should reflect doubled penalty

    def test_passed_pawn(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((5, 0), "P")  # Advanced pawn with no blockers
        score = FEATURES["pawn_structure"](b, "w")
        assert score > 0  # Passed pawn bonus


class TestBishopPair:
    def test_bishop_pair_bonus(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((0, 2), "B")
        b.set_piece((0, 5), "B")
        assert FEATURES["bishop_pair"](b, "w") == 0.5

    def test_single_bishop_no_bonus(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((0, 2), "B")
        assert FEATURES["bishop_pair"](b, "w") == 0.0

    def test_symmetric(self):
        b = Board.starting_position()
        assert FEATURES["bishop_pair"](b, "w") == 0.0  # Both have pair, net 0


class TestMobility:
    def test_starting_position_zero(self):
        b = Board.starting_position()
        # Both sides have equal mobility from starting position
        assert FEATURES["mobility"](b, "w") == 0.0

    def test_more_mobility_positive(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")  # Queen has many moves
        b.side_to_move = "w"
        score = FEATURES["mobility"](b, "w")
        assert score > 0


class TestCenterControl:
    def test_starting_position(self):
        b = Board.starting_position()
        # Both sides attack center equally
        score = FEATURES["center_control"](b, "w")
        assert isinstance(score, float)

    def test_piece_on_center(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "N")  # Knight on d4
        score = FEATURES["center_control"](b, "w")
        assert score > 0


class TestRookActivity:
    def test_open_file(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((0, 0), "R")  # Rook on open a-file
        score = FEATURES["rook_activity"](b, "w")
        assert score > 0

    def test_seventh_rank(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((6, 0), "R")  # Rook on 7th rank
        score = FEATURES["rook_activity"](b, "w")
        assert score > 0


class TestCaptureThreats:
    def test_no_captures_zero(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        score = FEATURES["capture_threats"](b, "w")
        assert score == 0.0

    def test_capturable_piece(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "R")
        b.set_piece((3, 7), "n")  # Knight capturable by rook
        score = FEATURES["capture_threats"](b, "w")
        assert score > 0


class TestAntichessMaterial:
    def test_starting_position_zero(self):
        b = Board.starting_position()
        assert FEATURES["negative_material"](b, "w") == 0.0

    def test_only_kings_zero(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        assert FEATURES["negative_material"](b, "w") == 0.0

    def test_white_extra_queen_negative(self):
        # White has more pieces → opp - own < 0 → bad for antichess
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")
        assert FEATURES["negative_material"](b, "w") == pytest.approx(-9.0)

    def test_black_extra_queen_positive(self):
        # Opponent has more pieces → opp - own > 0 → good for antichess
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "q")
        assert FEATURES["negative_material"](b, "w") == pytest.approx(9.0)

    def test_perspective_symmetry(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "Q")
        w_score = FEATURES["negative_material"](b, "w")
        b_score = FEATURES["negative_material"](b, "b")
        assert w_score == pytest.approx(-b_score)

    def test_inverts_standard_material(self):
        # negative_material(w) == -material(w) when kings are the only shared pieces
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "R")  # white rook  (+5 standard)
        b.set_piece((5, 5), "n")  # black knight (-3 standard)
        assert FEATURES["material"](b, "w") == pytest.approx(2.0)
        assert FEATURES["negative_material"](b, "w") == pytest.approx(-2.0)

    def test_exact_piece_values(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((1, 0), "P")  # white pawn  = 1
        b.set_piece((2, 0), "N")  # white knight = 3
        b.set_piece((5, 0), "r")  # black rook   = 5
        # opp=5, own=4 → score = 1.0
        assert FEATURES["negative_material"](b, "w") == pytest.approx(1.0)


class TestExplosionProximity:
    def test_starting_position_zero(self):
        b = Board.starting_position()
        assert FEATURES["explosion_proximity"](b, "w") == 0.0

    def test_own_piece_adjacent_to_enemy_king_positive(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")   # black king at (7,4)
        b.set_piece((6, 4), "R")   # white rook adjacent to black king
        assert FEATURES["explosion_proximity"](b, "w") == pytest.approx(1.0)

    def test_enemy_piece_adjacent_to_own_king_negative(self):
        b = Board()
        b.set_piece((0, 4), "K")   # white king at (0,4)
        b.set_piece((7, 4), "k")
        b.set_piece((1, 4), "r")   # black rook adjacent to white king
        assert FEATURES["explosion_proximity"](b, "w") == pytest.approx(-1.0)

    def test_pawns_excluded_from_count(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((6, 4), "P")   # white pawn adjacent to black king — immune, not counted
        b.set_piece((1, 4), "p")   # black pawn adjacent to white king — immune, not counted
        assert FEATURES["explosion_proximity"](b, "w") == 0.0

    def test_net_difference(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((6, 3), "R")   # white rook adj to black king
        b.set_piece((6, 5), "N")   # white knight adj to black king
        b.set_piece((1, 4), "r")   # black rook adj to white king
        # offensive=2, defensive=1 → 1.0
        assert FEATURES["explosion_proximity"](b, "w") == pytest.approx(1.0)

    def test_corner_king_bounded_squares(self):
        # King in corner has only 3 adjacent squares — no out-of-bounds error
        b = Board()
        b.set_piece((0, 0), "K")   # white king at corner (0,0)
        b.set_piece((7, 7), "k")   # black king at corner (7,7)
        b.set_piece((6, 7), "R")   # white rook adj to black king
        score = FEATURES["explosion_proximity"](b, "w")
        assert score == pytest.approx(1.0)

    def test_no_own_king_returns_zero_defensive(self):
        # If own king missing, defensive threat is 0 (guard against None)
        b = Board()
        b.set_piece((7, 4), "k")
        b.set_piece((6, 4), "R")   # white rook adj to black king
        score = FEATURES["explosion_proximity"](b, "w")
        assert score == pytest.approx(1.0)  # offensive still counts

    def test_no_enemy_king_returns_zero_offensive(self):
        # If enemy king missing, offensive count is 0
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((1, 4), "r")   # black rook adj to white king
        score = FEATURES["explosion_proximity"](b, "w")
        assert score == pytest.approx(-1.0)  # defensive still counts
