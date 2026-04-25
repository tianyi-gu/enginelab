"""Foundation tests for move generation."""

import pytest
from core.board import Board
from core.move import Move
from core.move_generation import (
    generate_moves,
    generate_legal_moves,
    is_square_attacked,
    is_in_check,
)


class TestStartingPositionMoves:
    def test_white_has_20_moves(self):
        b = Board.starting_position()
        moves = generate_moves(b)
        # 16 pawn moves (8 single + 8 double) + 4 knight moves
        assert len(moves) == 20

    def test_all_moves_are_valid(self):
        b = Board.starting_position()
        moves = generate_moves(b)
        for m in moves:
            assert 0 <= m.start[0] < 8 and 0 <= m.start[1] < 8
            assert 0 <= m.end[0] < 8 and 0 <= m.end[1] < 8


class TestPawnMoves:
    def test_single_push(self):
        b = Board()
        b.set_piece((1, 4), "P")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert Move((1, 4), (2, 4)) in moves

    def test_double_push_from_start(self):
        b = Board()
        b.set_piece((1, 4), "P")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert Move((1, 4), (3, 4)) in moves

    def test_no_double_push_if_blocked(self):
        b = Board()
        b.set_piece((1, 4), "P")
        b.set_piece((2, 4), "p")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert Move((1, 4), (3, 4)) not in moves

    def test_diagonal_capture(self):
        b = Board()
        b.set_piece((1, 4), "P")
        b.set_piece((2, 5), "p")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert Move((1, 4), (2, 5)) in moves

    def test_no_capture_own_piece(self):
        b = Board()
        b.set_piece((1, 4), "P")
        b.set_piece((2, 5), "P")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert Move((1, 4), (2, 5)) not in moves

    def test_promotion(self):
        b = Board()
        b.set_piece((6, 0), "P")
        b.side_to_move = "w"
        moves = generate_moves(b)
        promos = [m for m in moves if m.promotion is not None]
        assert len(promos) == 4
        promo_pieces = {m.promotion for m in promos}
        assert promo_pieces == {"Q", "R", "B", "N"}

    def test_black_pawn_moves(self):
        b = Board()
        b.set_piece((6, 4), "p")
        b.side_to_move = "b"
        moves = generate_moves(b)
        assert Move((6, 4), (5, 4)) in moves
        assert Move((6, 4), (4, 4)) in moves


class TestEnPassant:
    def test_en_passant_capture(self):
        b = Board()
        b.set_piece((4, 4), "P")
        b.set_piece((4, 5), "p")
        b.en_passant_square = (5, 5)
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert Move((4, 4), (5, 5)) in moves


class TestKnightMoves:
    def test_knight_center(self):
        b = Board()
        b.set_piece((3, 3), "N")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert len(moves) == 8

    def test_knight_corner(self):
        b = Board()
        b.set_piece((0, 0), "N")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert len(moves) == 2


class TestSlidingMoves:
    def test_rook_empty_board(self):
        b = Board()
        b.set_piece((3, 3), "R")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert len(moves) == 14

    def test_bishop_empty_board(self):
        b = Board()
        b.set_piece((3, 3), "B")
        b.side_to_move = "w"
        moves = generate_moves(b)
        # From d4: 4 directions, various lengths
        # NE: 4, NW: 3, SE: 3, SW: 3 = 13
        assert len(moves) == 13

    def test_queen_empty_board(self):
        b = Board()
        b.set_piece((3, 3), "Q")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert len(moves) == 27  # 14 orthogonal + 13 diagonal


class TestKingMoves:
    def test_king_center(self):
        b = Board()
        b.set_piece((3, 3), "K")
        b.side_to_move = "w"
        moves = generate_moves(b)
        assert len(moves) == 8

    def test_king_corner(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        moves = generate_moves(b)
        assert len(moves) == 3


class TestCastling:
    def test_kingside_castling_white(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.side_to_move = "w"
        b.castling_rights = {"K": True, "Q": False, "k": False, "q": False}
        moves = generate_moves(b)
        assert Move((0, 4), (0, 6)) in moves

    def test_queenside_castling_white(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 0), "R")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": True, "k": False, "q": False}
        moves = generate_moves(b)
        assert Move((0, 4), (0, 2)) in moves

    def test_no_castling_through_piece(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.set_piece((0, 5), "B")
        b.side_to_move = "w"
        b.castling_rights = {"K": True, "Q": False, "k": False, "q": False}
        moves = generate_moves(b)
        assert Move((0, 4), (0, 6)) not in moves

    def test_no_castling_through_check(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.set_piece((7, 5), "r")  # Attacks f1
        b.side_to_move = "w"
        b.castling_rights = {"K": True, "Q": False, "k": False, "q": False}
        moves = generate_moves(b)
        assert Move((0, 4), (0, 6)) not in moves

    def test_no_castling_while_in_check(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((0, 7), "R")
        b.set_piece((7, 4), "r")  # Attacks e1
        b.side_to_move = "w"
        b.castling_rights = {"K": True, "Q": False, "k": False, "q": False}
        moves = generate_moves(b)
        assert Move((0, 4), (0, 6)) not in moves

    def test_black_castling(self):
        b = Board()
        b.set_piece((7, 4), "k")
        b.set_piece((7, 7), "r")
        b.side_to_move = "b"
        b.castling_rights = {"K": False, "Q": False, "k": True, "q": False}
        moves = generate_moves(b)
        assert Move((7, 4), (7, 6)) in moves


class TestCheckDetection:
    def test_not_in_check_starting(self):
        b = Board.starting_position()
        assert not is_in_check(b, "w")
        assert not is_in_check(b, "b")

    def test_rook_gives_check(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "r")
        assert is_in_check(b, "w")

    def test_knight_gives_check(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((2, 5), "n")
        assert is_in_check(b, "w")

    def test_pawn_gives_check(self):
        b = Board()
        b.set_piece((3, 3), "K")
        b.set_piece((4, 4), "p")  # Black pawn attacks downward diagonally
        assert is_in_check(b, "w")

    def test_square_attacked_by_bishop(self):
        b = Board()
        b.set_piece((0, 0), "b")
        assert is_square_attacked(b, (3, 3), "b")

    def test_square_not_attacked_through_piece(self):
        b = Board()
        b.set_piece((0, 0), "b")
        b.set_piece((1, 1), "P")
        assert not is_square_attacked(b, (3, 3), "b")


class TestLegalMoves:
    def test_starting_position_legal(self):
        b = Board.starting_position()
        legal = generate_legal_moves(b)
        assert len(legal) == 20

    def test_must_block_check(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.set_piece((7, 0), "r")  # Rook checking along file
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        legal = generate_legal_moves(b)
        # King must move out of file a, or no other piece to block
        for m in legal:
            assert m.start == (0, 0)  # Only king can move

    def test_pinned_piece_cannot_move(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.set_piece((0, 1), "R")  # White rook
        b.set_piece((0, 7), "r")  # Black rook pinning white rook
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        legal = generate_legal_moves(b)
        # Rook is pinned along rank 1 — can only move along rank 1
        rook_moves = [m for m in legal if m.start == (0, 1)]
        for m in rook_moves:
            assert m.end[0] == 0  # Must stay on rank 1
