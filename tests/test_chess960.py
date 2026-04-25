"""Tests for Chess960 variant."""

import random

from core.board import Board
from core.move import Move
from variants.chess960 import (
    chess960_starting_position,
    apply_chess960_move,
    generate_chess960_moves,
)
from variants.base import get_apply_move, get_generate_legal_moves


class TestChess960StartingPosition:
    def test_valid_position_king_between_rooks(self):
        board = chess960_starting_position(42)
        rank = board.grid[0]
        king_col = rank.index("K")
        rook_cols = [i for i, p in enumerate(rank) if p == "R"]
        assert len(rook_cols) == 2
        assert rook_cols[0] < king_col < rook_cols[1]

    def test_bishops_on_opposite_colors(self):
        board = chess960_starting_position(42)
        rank = board.grid[0]
        bishop_cols = [i for i, p in enumerate(rank) if p == "B"]
        assert len(bishop_cols) == 2
        assert bishop_cols[0] % 2 != bishop_cols[1] % 2

    def test_all_pieces_present(self):
        board = chess960_starting_position(42)
        rank = sorted(board.grid[0])
        assert rank == ["B", "B", "K", "N", "N", "Q", "R", "R"]

    def test_black_mirrors_white(self):
        board = chess960_starting_position(42)
        for col in range(8):
            assert board.grid[7][col] == board.grid[0][col].lower()

    def test_deterministic_same_seed(self):
        b1 = chess960_starting_position(123)
        b2 = chess960_starting_position(123)
        assert b1.grid[0] == b2.grid[0]

    def test_different_seeds_different_positions(self):
        positions = set()
        for seed in range(20):
            board = chess960_starting_position(seed)
            positions.add(tuple(board.grid[0]))
        assert len(positions) > 1

    def test_castling_disabled(self):
        board = chess960_starting_position(42)
        assert all(not v for v in board.castling_rights.values())

    def test_pawns_on_rank_2_and_7(self):
        board = chess960_starting_position(42)
        assert board.grid[1] == ["P"] * 8
        assert board.grid[6] == ["p"] * 8


class TestChess960MoveGeneration:
    def test_has_legal_moves(self):
        board = chess960_starting_position(42)
        moves = generate_chess960_moves(board)
        assert len(moves) > 0

    def test_no_castling_moves(self):
        board = chess960_starting_position(42)
        moves = generate_chess960_moves(board)
        for m in moves:
            piece = board.get_piece(m.start)
            if piece and piece.upper() == "K":
                assert abs(m.end[1] - m.start[1]) <= 1


class TestChess960Dispatch:
    def test_registered(self):
        assert get_apply_move("chess960") is apply_chess960_move
        assert get_generate_legal_moves("chess960") is generate_chess960_moves


class TestChess960Stress:
    def test_100_random_plies_no_crash(self):
        rng = random.Random(42)
        board = chess960_starting_position(42)
        apply_fn = get_apply_move("chess960")
        gen_fn = get_generate_legal_moves("chess960")

        for _ in range(100):
            legal = gen_fn(board)
            if not legal or board.is_terminal():
                break
            move = rng.choice(legal)
            board = apply_fn(board, move)
