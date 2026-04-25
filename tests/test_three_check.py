"""Tests for Three-Check variant."""

import random

from core.board import Board
from core.move import Move
from core.move_generation import is_in_check
from variants.three_check import apply_three_check_move, generate_three_check_moves
from variants.base import get_apply_move, get_generate_legal_moves


class TestThreeCheckCount:
    def test_non_check_move_no_increment(self):
        board = Board()
        board.set_piece((0, 0), "K")
        board.set_piece((7, 4), "k")
        board.set_piece((0, 7), "R")  # White rook on h1
        board.side_to_move = "w"
        # Move rook from h1 to h2 — no check on black king at e8
        new = apply_three_check_move(board, Move((0, 7), (1, 7)))
        assert new.check_count["w"] == 0

    def test_delivering_check_increments(self):
        board = Board()
        board.set_piece((0, 0), "K")
        board.set_piece((7, 4), "k")
        board.set_piece((0, 4), "R")
        board.side_to_move = "w"
        # Rook from e1 to e7 checks king on e8
        new = apply_three_check_move(board, Move((0, 4), (6, 4)))
        assert new.check_count["w"] == 1

    def test_three_checks_wins(self):
        board = Board()
        board.set_piece((0, 0), "K")
        board.set_piece((7, 4), "k")
        board.set_piece((0, 4), "R")
        board.check_count = {"w": 2, "b": 0}
        board.side_to_move = "w"
        # Deliver 3rd check
        new = apply_three_check_move(board, Move((0, 4), (6, 4)))  # Rook to e7
        assert new.check_count["w"] == 3
        assert new.winner == "w"

    def test_non_check_does_not_increment(self):
        board = Board()
        board.set_piece((0, 0), "K")
        board.set_piece((7, 4), "k")
        board.side_to_move = "w"
        new = apply_three_check_move(board, Move((0, 0), (1, 0)))  # King moves, no check (no rook)
        assert new.check_count["w"] == 0

    def test_check_count_preserved_by_copy(self):
        board = Board()
        board.check_count = {"w": 2, "b": 1}
        copy = board.copy()
        assert copy.check_count == {"w": 2, "b": 1}
        copy.check_count["w"] = 3
        assert board.check_count["w"] == 2  # Original unchanged


class TestThreeCheckMoveGeneration:
    def test_generates_standard_legal_moves(self):
        board = Board.starting_position()
        moves = generate_three_check_moves(board)
        assert len(moves) == 20


class TestThreeCheckDispatch:
    def test_registered(self):
        assert get_apply_move("threecheck") is apply_three_check_move
        assert get_generate_legal_moves("threecheck") is generate_three_check_moves


class TestThreeCheckStress:
    def test_100_random_plies_no_crash(self):
        rng = random.Random(42)
        board = Board.starting_position()
        apply_fn = get_apply_move("threecheck")
        gen_fn = get_generate_legal_moves("threecheck")

        for _ in range(100):
            legal = gen_fn(board)
            if not legal or board.is_terminal():
                break
            move = rng.choice(legal)
            board = apply_fn(board, move)
