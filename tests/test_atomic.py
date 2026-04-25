"""Tests for Atomic chess variant."""

import pytest

from core.board import Board
from core.move import Move
from core.move_generation import generate_moves
from variants.atomic import apply_atomic_move, generate_atomic_moves
from variants.base import get_apply_move, get_generate_legal_moves


class TestAtomicExplosion:
    def test_capture_removes_both_pieces(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "N")
        b.set_piece((4, 4), "p")
        b.side_to_move = "w"
        new = apply_atomic_move(b, Move((3, 3), (4, 4)))  # Capture not adjacent to own king
        # Wait, need to check if king is adjacent. (0,4) is far from (4,4), so ok.
        # Actually _would_explode_own_king checks adjacency to move.end (4,4).
        # King at (0,4) is NOT adjacent to (4,4), so this is legal.
        assert new.get_piece((3, 3)) is None  # Capturing piece gone
        assert new.get_piece((4, 4)) is None  # Captured piece gone

    def test_explosion_destroys_adjacent_non_pawns(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.set_piece((7, 7), "k")
        b.set_piece((3, 3), "R")  # White rook captures
        b.set_piece((4, 4), "n")  # Black knight (target)
        b.set_piece((4, 3), "b")  # Adjacent black bishop — destroyed
        b.set_piece((4, 5), "r")  # Adjacent black rook — destroyed
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        new = apply_atomic_move(b, Move((3, 3), (4, 4)))
        assert new.get_piece((4, 3)) is None  # Bishop destroyed
        assert new.get_piece((4, 5)) is None  # Rook destroyed

    def test_pawns_survive_explosion(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.set_piece((7, 7), "k")
        b.set_piece((3, 3), "R")
        b.set_piece((4, 4), "n")
        b.set_piece((4, 3), "p")  # Adjacent pawn — survives
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        new = apply_atomic_move(b, Move((3, 3), (4, 4)))
        assert new.get_piece((4, 3)) == "p"  # Pawn survived

    def test_king_explosion_sets_winner(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.set_piece((4, 4), "R")
        b.set_piece((5, 5), "n")
        b.set_piece((5, 4), "k")  # Black king adjacent to capture
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        new = apply_atomic_move(b, Move((4, 4), (5, 5)))
        assert new.winner == "w"  # Black king destroyed


class TestAtomicSelfPreservation:
    def test_capture_exploding_own_king_filtered(self):
        b = Board()
        b.set_piece((3, 3), "K")  # King adjacent to capture square
        b.set_piece((7, 7), "k")
        b.set_piece((3, 4), "R")  # Rook next to king
        b.set_piece((4, 5), "n")  # Target — capture at (4,5) is far from king, ok
        # But let's put target adjacent to king
        b.set_piece((4, 4), "n")  # Target at (4,4) — adjacent to king at (3,3)
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        legal = generate_atomic_moves(b)
        # Capture of (4,4) by rook at (3,4) would explode adjacent to king at (3,3)
        capture_moves = [m for m in legal if m.end == (4, 4)]
        assert len(capture_moves) == 0

    def test_king_cannot_capture_in_atomic(self):
        b = Board()
        b.set_piece((3, 3), "K")
        b.set_piece((7, 7), "k")
        b.set_piece((3, 4), "n")  # Black knight next to white king
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        legal = generate_atomic_moves(b)
        king_captures = [m for m in legal if m.start == (3, 3) and
                         b.get_piece(m.end) is not None]
        assert len(king_captures) == 0

    def test_safe_capture_allowed(self):
        b = Board()
        b.set_piece((0, 0), "K")
        b.set_piece((7, 7), "k")
        b.set_piece((4, 4), "R")
        b.set_piece((6, 4), "n")  # Far from white king
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        legal = generate_atomic_moves(b)
        capture_moves = [m for m in legal if m.end == (6, 4)]
        assert len(capture_moves) == 1


class TestAtomicGameplay:
    def test_non_capture_uses_standard_rules(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((1, 0), "P")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        new = apply_atomic_move(b, Move((1, 0), (2, 0)))
        assert new.get_piece((2, 0)) == "P"
        assert new.get_piece((1, 0)) is None

    def test_100_random_plies_no_crash(self):
        """Play 100 random plies of atomic chess without crashing."""
        import random
        rng = random.Random(42)
        b = Board.starting_position()
        apply_fn = get_apply_move("atomic")
        gen_fn = get_generate_legal_moves("atomic")

        for _ in range(100):
            legal = gen_fn(b)
            if not legal or b.is_terminal():
                break
            move = rng.choice(legal)
            b = apply_fn(b, move)

    def test_variant_dispatch_registered(self):
        assert get_apply_move("atomic") is apply_atomic_move
        assert get_generate_legal_moves("atomic") is generate_atomic_moves
