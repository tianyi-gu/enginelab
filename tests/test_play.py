"""Tests for the play-against-engine pipeline (move application + explosion detection)."""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
import pytest

from ui.play_engine import (
    get_legal_moves_uci,
    apply_move_for_ui,
    _parse_uci,
)


# ---------------------------------------------------------------------------
# Legal-move generation
# ---------------------------------------------------------------------------

class TestLegalMoves:
    def test_starting_position_standard_has_20_moves(self):
        legal = get_legal_moves_uci(chess.STARTING_FEN, "standard")
        assert len(legal) == 20
        # Common opening moves should all be present
        for m in ("e2e4", "e2e3", "d2d4", "g1f3", "b1c3"):
            assert m in legal

    def test_starting_position_atomic_has_20_moves(self):
        legal = get_legal_moves_uci(chess.STARTING_FEN, "atomic")
        assert len(legal) == 20
        assert "e2e4" in legal

    def test_starting_position_antichess_has_20_moves(self):
        legal = get_legal_moves_uci(chess.STARTING_FEN, "antichess")
        # Antichess starting position: all 20 standard pawn/knight moves are legal
        # (no captures available at move 1, so no forcing).
        assert len(legal) == 20
        assert "e2e4" in legal


# ---------------------------------------------------------------------------
# Player move application
# ---------------------------------------------------------------------------

class TestPlayerMoveApplication:
    def test_e2e4_standard(self):
        result = apply_move_for_ui(chess.STARTING_FEN, "e2e4", "standard")
        assert result["status"] == "ongoing"
        assert result["move_uci"] == "e2e4"
        # White pawn now on e4, e2 empty
        new_board = chess.Board(result["fen"])
        assert new_board.piece_at(chess.E4) is not None
        assert new_board.piece_at(chess.E2) is None

    def test_e2e4_atomic(self):
        result = apply_move_for_ui(chess.STARTING_FEN, "e2e4", "atomic")
        assert result["status"] == "ongoing"
        new_board = chess.Board(result["fen"])
        assert new_board.piece_at(chess.E4) is not None

    def test_illegal_move_raises(self):
        with pytest.raises(ValueError):
            apply_move_for_ui(chess.STARTING_FEN, "e2e5", "standard")  # pawn can't jump 3

    def test_promotion_e7e8q(self):
        # Position with white pawn on e7 about to promote
        fen = "8/4P3/8/8/8/8/8/4K2k w - - 0 1"
        result = apply_move_for_ui(fen, "e7e8q", "standard")
        new_board = chess.Board(result["fen"])
        promoted = new_board.piece_at(chess.E8)
        assert promoted is not None
        assert promoted.symbol().upper() == "Q"


# ---------------------------------------------------------------------------
# Atomic explosion detection
# ---------------------------------------------------------------------------

class TestAtomicExplosions:
    def test_simple_capture_creates_explosion_in_atomic(self):
        """White rook captures black queen — both should be gone in atomic."""
        # Setup: white rook on a1, black queen on a8, kings out of way
        fen = "q3k3/8/8/8/8/8/8/R3K3 w - - 0 1"
        result = apply_move_for_ui(fen, "a1a8", "atomic")
        new_board = chess.Board(result["fen"])
        # In atomic, both pieces explode — neither rook nor queen remains on a8/a1.
        assert new_board.piece_at(chess.A1) is None
        assert new_board.piece_at(chess.A8) is None

    def test_standard_capture_keeps_capturing_piece(self):
        """White rook captures black queen — rook remains in standard chess."""
        fen = "q3k3/8/8/8/8/8/8/R3K3 w - - 0 1"
        result = apply_move_for_ui(fen, "a1a8", "standard")
        new_board = chess.Board(result["fen"])
        # In standard, rook is now on a8.
        assert new_board.piece_at(chess.A8) is not None
        assert new_board.piece_at(chess.A8).symbol() == "R"

    def test_explosion_detection_via_dest_empty(self):
        """The explosion-detection helper flags atomic captures correctly."""
        from ui.app import _detect_explosions
        before = "q3k3/8/8/8/8/8/8/R3K3 w - - 0 1"
        after = apply_move_for_ui(before, "a1a8", "atomic")["fen"]
        exploded = _detect_explosions(before, after, "a1a8")
        assert exploded is not None
        # At minimum the source (a1) and dest (a8) squares are exploded
        assert "a1" in exploded
        assert "a8" in exploded

    def test_explosion_detection_returns_none_for_non_capture(self):
        from ui.app import _detect_explosions
        before = chess.STARTING_FEN
        after = apply_move_for_ui(before, "e2e4", "atomic")["fen"]
        exploded = _detect_explosions(before, after, "e2e4")
        assert exploded is None  # No piece on e4 was captured

    def test_explosion_detection_returns_none_for_standard_capture(self):
        """Standard chess captures should NOT trigger explosion detection."""
        from ui.app import _detect_explosions
        before = "q3k3/8/8/8/8/8/8/R3K3 w - - 0 1"
        after = apply_move_for_ui(before, "a1a8", "standard")["fen"]
        # In standard, the rook is on a8 after capture, so dest is occupied
        exploded = _detect_explosions(before, after, "a1a8")
        assert exploded is None

    def test_pawns_immune_to_explosion(self):
        """In atomic, pawns adjacent to an explosion survive."""
        # White rook on a1, black queen on a2, white pawn on b2.
        # Capture a1xa2 explodes — but b2 pawn survives.
        fen = "4k3/8/8/8/8/8/qP6/R3K3 w - - 0 1"
        result = apply_move_for_ui(fen, "a1a2", "atomic")
        new_board = chess.Board(result["fen"])
        assert new_board.piece_at(chess.A2) is None  # queen gone
        assert new_board.piece_at(chess.A1) is None  # rook gone
        assert new_board.piece_at(chess.B2) is not None  # pawn survives


# ---------------------------------------------------------------------------
# UCI parser
# ---------------------------------------------------------------------------

class TestUciParser:
    def test_simple_move(self):
        m = _parse_uci("e2e4", "w")
        # start = (row 1, col 4), end = (row 3, col 4) in project coords
        assert m.start == (1, 4)
        assert m.end == (3, 4)
        assert m.promotion is None

    def test_promotion_white(self):
        m = _parse_uci("e7e8q", "w")
        assert m.promotion == "Q"

    def test_promotion_black(self):
        m = _parse_uci("e2e1q", "b")
        assert m.promotion == "q"
