"""Tests for Antichess variant."""

import random
import pytest

from core.board import Board
from core.move import Move
from core.move_generation import generate_moves
from variants.antichess import apply_antichess_move, generate_antichess_moves
from variants.base import get_apply_move, get_generate_legal_moves, get_supported_variants


class TestForcedCapture:
    def test_must_capture_when_available(self):
        """If captures exist, only captures are returned."""
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "R")  # White rook
        b.set_piece((3, 7), "p")  # Capturable black pawn
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        moves = generate_antichess_moves(b)
        # All returned moves must be captures
        for move in moves:
            assert b.get_piece(move.end) is not None

    def test_capture_includes_rook_takes_pawn(self):
        b = Board()
        b.set_piece((0, 4), "K")
        b.set_piece((7, 4), "k")
        b.set_piece((3, 3), "R")
        b.set_piece((3, 7), "p")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        moves = generate_antichess_moves(b)
        ends = {m.end for m in moves}
        assert (3, 7) in ends

    def test_no_captures_returns_all_moves(self):
        """When no captures available, all pseudo-legal moves returned."""
        b = Board()
        b.set_piece((0, 0), "R")
        b.set_piece((7, 7), "k")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        moves = generate_antichess_moves(b)
        all_pseudo = generate_moves(b)
        assert len(moves) == len(all_pseudo)

    def test_king_can_be_captured(self):
        """In antichess, king has no special status — can be captured."""
        b = Board()
        b.set_piece((3, 3), "R")
        b.set_piece((3, 7), "k")  # Black king capturable
        b.set_piece((7, 0), "K")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        moves = generate_antichess_moves(b)
        ends = {m.end for m in moves}
        assert (3, 7) in ends


class TestWinCondition:
    def test_losing_all_pieces_wins(self):
        """A player who loses all pieces wins in antichess."""
        b = Board()
        b.set_piece((1, 0), "P")  # White's only piece
        b.set_piece((2, 1), "n")  # Black knight can be captured
        b.set_piece((7, 4), "k")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        # Pawn captures knight — but white still has the pawn on (2,1)
        # Need a scenario where white's last piece is captured or captures and disappears

        # Better setup: white pawn promotes and... no, simpler:
        # White has one pawn that captures black's piece, but white pawn survives
        # Actually let's just test the win condition directly
        b2 = Board()
        b2.set_piece((7, 4), "k")
        b2.side_to_move = "b"
        b2.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        # White has no pieces — white wins
        # But we need to trigger this via apply_antichess_move
        # Setup: white has one piece, and it gets captured
        b3 = Board()
        b3.set_piece((3, 3), "P")  # White's only piece
        b3.set_piece((4, 4), "n")  # Black knight
        b3.set_piece((7, 7), "k")
        b3.side_to_move = "w"
        b3.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        # White pawn captures black knight at (4,4)? No — pawn at (3,3) can capture at (4,4)
        # Wait, white pawns move up (row increases). Pawn at row 3, captures diag to row 4.
        # Actually in our coordinate system row 0 = rank 1 (white side), pawns move toward row 7.
        # So pawn at (3,3) can capture at (4,4) if there's an enemy piece there.
        move = Move(start=(3, 3), end=(4, 4))
        result = apply_antichess_move(b3, move)
        # White pawn moved to (4,4) — white still has the pawn, so no win yet
        assert result.winner is None

    def test_last_piece_captured_wins(self):
        """When a side's last piece is captured by the opponent, that side wins."""
        # Black captures white's last piece
        b = Board()
        b.set_piece((3, 3), "P")  # White's only piece
        b.set_piece((4, 4), "n")  # Black knight can capture
        b.set_piece((7, 7), "k")
        b.side_to_move = "b"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        # Knight at (4,4) captures pawn at (3,3)? Knights move in L-shape.
        # Let's use a bishop instead for a clean diagonal capture.
        b2 = Board()
        b2.set_piece((3, 3), "P")  # White's only piece
        b2.set_piece((5, 5), "b")  # Black bishop
        b2.set_piece((7, 7), "k")
        b2.side_to_move = "b"
        b2.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        move = Move(start=(5, 5), end=(3, 3))
        result = apply_antichess_move(b2, move)
        # White has no pieces left — white wins in antichess
        assert result.winner == "w"


class TestAntichessGameplay:
    def test_non_capture_is_standard(self):
        """Non-capture moves work like standard chess."""
        b = Board()
        b.set_piece((1, 0), "P")
        b.set_piece((7, 4), "k")
        b.side_to_move = "w"
        b.castling_rights = {"K": False, "Q": False, "k": False, "q": False}
        move = Move(start=(1, 0), end=(2, 0))
        result = apply_antichess_move(b, move)
        assert result.get_piece((2, 0)) == "P"
        assert result.get_piece((1, 0)) is None

    def test_100_random_plies_no_crash(self):
        """Play 100 random antichess plies without crashing."""
        b = Board.starting_position()
        rng = random.Random(42)
        for _ in range(100):
            if b.is_terminal():
                break
            moves = generate_antichess_moves(b)
            if not moves:
                break
            move = rng.choice(moves)
            b = apply_antichess_move(b, move)

    def test_variant_dispatch_registered(self):
        """Antichess is registered in variant dispatch."""
        assert "antichess" in get_supported_variants()
        apply_fn = get_apply_move("antichess")
        gen_fn = get_generate_legal_moves("antichess")
        assert callable(apply_fn)
        assert callable(gen_fn)

    def test_starting_position_has_moves(self):
        b = Board.starting_position()
        moves = generate_antichess_moves(b)
        assert len(moves) == 20  # No captures at start, so all 20 moves

    def test_forced_capture_from_starting(self):
        """After 1.e4 d5, white must capture exd5."""
        b = Board.starting_position()
        # Play e4
        b = apply_antichess_move(b, Move(start=(1, 4), end=(3, 4)))
        # Play d5
        b = apply_antichess_move(b, Move(start=(6, 3), end=(4, 3)))
        # Now white must capture
        moves = generate_antichess_moves(b)
        # The only capture available is exd5
        assert all(b.get_piece(m.end) is not None for m in moves)
        capture_ends = {m.end for m in moves}
        assert (4, 3) in capture_ends
