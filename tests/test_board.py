"""Foundation tests for Board class."""

import pytest
from core.board import Board
from core.types import piece_color


class TestBoardStartingPosition:
    def test_white_pieces_rank1(self):
        b = Board.starting_position()
        assert b.grid[0] == ["R", "N", "B", "Q", "K", "B", "N", "R"]

    def test_white_pawns_rank2(self):
        b = Board.starting_position()
        assert b.grid[1] == ["P"] * 8

    def test_empty_middle(self):
        b = Board.starting_position()
        for row in range(2, 6):
            assert b.grid[row] == [None] * 8

    def test_black_pawns_rank7(self):
        b = Board.starting_position()
        assert b.grid[6] == ["p"] * 8

    def test_black_pieces_rank8(self):
        b = Board.starting_position()
        assert b.grid[7] == ["r", "n", "b", "q", "k", "b", "n", "r"]

    def test_side_to_move(self):
        b = Board.starting_position()
        assert b.side_to_move == "w"

    def test_castling_rights_all_true(self):
        b = Board.starting_position()
        assert b.castling_rights == {"K": True, "Q": True, "k": True, "q": True}

    def test_en_passant_none(self):
        b = Board.starting_position()
        assert b.en_passant_square is None

    def test_not_terminal(self):
        b = Board.starting_position()
        assert not b.is_terminal()


class TestBoardCopy:
    def test_copy_is_independent(self):
        b = Board.starting_position()
        c = b.copy()
        c.set_piece((0, 0), None)
        assert b.get_piece((0, 0)) == "R"
        assert c.get_piece((0, 0)) is None

    def test_copy_castling_independent(self):
        b = Board.starting_position()
        c = b.copy()
        c.castling_rights["K"] = False
        assert b.castling_rights["K"] is True

    def test_copy_preserves_state(self):
        b = Board.starting_position()
        b.side_to_move = "b"
        b.move_count = 5
        b.en_passant_square = (2, 3)
        c = b.copy()
        assert c.side_to_move == "b"
        assert c.move_count == 5
        assert c.en_passant_square == (2, 3)


class TestBoardMethods:
    def test_get_set_piece(self):
        b = Board()
        assert b.get_piece((3, 3)) is None
        b.set_piece((3, 3), "Q")
        assert b.get_piece((3, 3)) == "Q"

    def test_find_king_white(self):
        b = Board.starting_position()
        assert b.find_king("w") == (0, 4)

    def test_find_king_black(self):
        b = Board.starting_position()
        assert b.find_king("b") == (7, 4)

    def test_find_king_missing(self):
        b = Board()
        assert b.find_king("w") is None

    def test_is_terminal(self):
        b = Board()
        assert not b.is_terminal()
        b.winner = "w"
        assert b.is_terminal()
        b.winner = "draw"
        assert b.is_terminal()
