"""Tests for King of the Hill variant."""

import random

from core.board import Board
from core.move import Move
from variants.king_of_the_hill import apply_koth_move, generate_koth_moves, _CENTER
from variants.base import get_apply_move, get_generate_legal_moves


class TestKothWinCondition:
    def test_king_on_e4_wins(self):
        board = Board()
        board.set_piece((0, 4), "K")
        board.set_piece((7, 4), "k")
        board.side_to_move = "w"
        # Move king from e1 to e4 (simulate via direct placement)
        board.set_piece((0, 4), None)
        board.set_piece((2, 4), "K")
        board.side_to_move = "w"
        # Now move king from e3 to e4 (center)
        new = apply_koth_move(board, Move((2, 4), (3, 4)))
        assert new.winner == "w"

    def test_king_on_d5_wins(self):
        board = Board()
        board.set_piece((3, 3), "K")
        board.set_piece((7, 4), "k")
        board.side_to_move = "w"
        new = apply_koth_move(board, Move((3, 3), (4, 3)))
        assert new.winner == "w"

    def test_black_king_on_center_wins(self):
        board = Board()
        board.set_piece((0, 4), "K")
        board.set_piece((4, 4), "k")  # e5 adjacent
        board.side_to_move = "b"
        new = apply_koth_move(board, Move((4, 4), (3, 4)))  # to e4
        assert new.winner == "b"

    def test_king_not_on_center_no_winner(self):
        board = Board()
        board.set_piece((0, 4), "K")
        board.set_piece((7, 4), "k")
        board.side_to_move = "w"
        new = apply_koth_move(board, Move((0, 4), (1, 4)))
        assert new.winner is None

    def test_center_squares_are_correct(self):
        assert _CENTER == {(3, 3), (3, 4), (4, 3), (4, 4)}


class TestKothMoveGeneration:
    def test_generates_standard_legal_moves(self):
        board = Board.starting_position()
        moves = generate_koth_moves(board)
        assert len(moves) == 20  # Standard opening: 20 legal moves


class TestKothDispatch:
    def test_registered(self):
        assert get_apply_move("kingofthehill") is apply_koth_move
        assert get_generate_legal_moves("kingofthehill") is generate_koth_moves


class TestKothStress:
    def test_100_random_plies_no_crash(self):
        rng = random.Random(42)
        board = Board.starting_position()
        apply_fn = get_apply_move("kingofthehill")
        gen_fn = get_generate_legal_moves("kingofthehill")

        for _ in range(100):
            legal = gen_fn(board)
            if not legal or board.is_terminal():
                break
            move = rng.choice(legal)
            board = apply_fn(board, move)
