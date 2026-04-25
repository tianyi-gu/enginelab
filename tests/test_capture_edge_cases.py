"""Capture edge cases across UI play and variant move generation."""

from __future__ import annotations

from core.board import Board
from core.move import Move
from core.move_generation import generate_legal_moves
from ui.app import _detect_explosions
from ui.play_engine import apply_move_for_ui
from variants.antichess import generate_antichess_moves
from variants.atomic import generate_atomic_moves


def _no_castling() -> dict[str, bool]:
    return {"K": False, "Q": False, "k": False, "q": False}


def test_standard_legal_moves_do_not_capture_the_king() -> None:
    board = Board()
    board.set_piece((0, 4), "K")
    board.set_piece((6, 4), "R")
    board.set_piece((7, 4), "k")
    board.side_to_move = "w"
    board.castling_rights = _no_castling()

    legal = generate_legal_moves(board)

    assert Move((6, 4), (7, 4)) not in legal


def test_atomic_legal_moves_do_not_capture_the_king() -> None:
    board = Board()
    board.set_piece((0, 4), "K")
    board.set_piece((6, 4), "R")
    board.set_piece((7, 4), "k")
    board.side_to_move = "w"
    board.castling_rights = _no_castling()

    legal = generate_atomic_moves(board)

    assert Move((6, 4), (7, 4)) not in legal


def test_atomic_capture_cannot_leave_own_king_in_check() -> None:
    board = Board()
    board.set_piece((0, 4), "K")
    board.set_piece((7, 7), "k")
    board.set_piece((1, 4), "R")
    board.set_piece((3, 4), "n")
    board.set_piece((7, 4), "r")
    board.side_to_move = "w"
    board.castling_rights = _no_castling()

    legal = generate_atomic_moves(board)

    assert Move((1, 4), (3, 4)) not in legal


def test_antichess_en_passant_counts_as_forced_capture() -> None:
    board = Board()
    board.set_piece((0, 0), "K")
    board.set_piece((7, 7), "k")
    board.set_piece((4, 4), "P")
    board.set_piece((4, 5), "p")
    board.en_passant_square = (5, 5)
    board.side_to_move = "w"
    board.castling_rights = _no_castling()

    legal = generate_antichess_moves(board)

    assert legal == [Move((4, 4), (5, 5))]


def test_atomic_two_piece_capture_is_reported_as_explosion() -> None:
    fen = "4k3/8/8/4p3/3P4/8/8/4K3 w - - 0 1"
    result = apply_move_for_ui(fen, "d4e5", "atomic")

    exploded = _detect_explosions(fen, result["fen"], "d4e5")

    assert exploded == ["d4", "e5"]
