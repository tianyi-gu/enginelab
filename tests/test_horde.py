"""Tests for Horde variant."""

import random

from core.board import Board
from core.move import Move
from core.move_generation import is_in_check
from core.types import is_white
from variants.horde import (
    horde_starting_position,
    apply_horde_move,
    generate_horde_moves,
)
from variants.base import get_apply_move, get_generate_legal_moves


class TestHordeStartingPosition:
    def test_36_white_pawns(self):
        board = horde_starting_position()
        count = sum(
            1
            for r in range(8)
            for c in range(8)
            if board.grid[r][c] == "P"
        )
        assert count == 36

    def test_no_white_king(self):
        board = horde_starting_position()
        for r in range(8):
            for c in range(8):
                assert board.grid[r][c] != "K"

    def test_black_standard_pieces(self):
        board = horde_starting_position()
        assert board.grid[7] == ["r", "n", "b", "q", "k", "b", "n", "r"]
        assert board.grid[6] == ["p"] * 8

    def test_extra_pawns_on_rank5(self):
        board = horde_starting_position()
        assert board.grid[4][1] == "P"  # b5
        assert board.grid[4][2] == "P"  # c5
        assert board.grid[4][5] == "P"  # f5
        assert board.grid[4][6] == "P"  # g5


class TestHordeWinCondition:
    def test_all_white_captured_black_wins(self):
        board = Board()
        board.set_piece((0, 0), "P")  # Single white pawn
        board.set_piece((7, 4), "k")
        board.set_piece((1, 0), "r")  # Black rook captures
        board.side_to_move = "b"
        new = apply_horde_move(board, Move((1, 0), (0, 0)))
        assert new.winner == "b"

    def test_white_still_has_pieces_no_winner(self):
        board = Board()
        board.set_piece((0, 0), "P")
        board.set_piece((0, 1), "P")
        board.set_piece((7, 4), "k")
        board.set_piece((1, 0), "r")
        board.side_to_move = "b"
        new = apply_horde_move(board, Move((1, 0), (0, 0)))
        assert new.winner is None


class TestHordeMoveGeneration:
    def test_white_no_check_filtering(self):
        board = horde_starting_position()
        moves = generate_horde_moves(board)
        assert len(moves) > 0

    def test_black_has_legal_moves(self):
        board = horde_starting_position()
        # Make one white move first
        board.side_to_move = "b"
        moves = generate_horde_moves(board)
        assert len(moves) > 0

    def test_is_in_check_false_for_white_no_king(self):
        board = horde_starting_position()
        assert is_in_check(board, "w") is False


class TestHordeDispatch:
    def test_registered(self):
        assert get_apply_move("horde") is apply_horde_move
        assert get_generate_legal_moves("horde") is generate_horde_moves


class TestHordeStress:
    def test_100_random_plies_no_crash(self):
        rng = random.Random(42)
        board = horde_starting_position()
        apply_fn = get_apply_move("horde")
        gen_fn = get_generate_legal_moves("horde")

        for _ in range(100):
            legal = gen_fn(board)
            if not legal or board.is_terminal():
                break
            move = rng.choice(legal)
            board = apply_fn(board, move)
