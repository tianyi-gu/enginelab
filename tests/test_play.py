import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
import pytest

from ui.play_engine import engine_reply, apply_san_move, game_status

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STARTING_FEN = chess.STARTING_FEN

def fools_mate_fen() -> str:
    """Return the FEN after fool's mate: 1. f3 e5 2. g4 Qh4#"""
    board = chess.Board()
    for san in ["f3", "e5", "g4", "Qh4"]:
        board.push_san(san)
    return board.fen()


# ---------------------------------------------------------------------------
# 1. engine_reply returns a legal move on the starting position
# ---------------------------------------------------------------------------

def test_engine_reply_returns_legal_move():
    reply = engine_reply(STARTING_FEN)
    assert reply is not None, "engine_reply should return a UCI string, not None"
    board = chess.Board(STARTING_FEN)
    legal_ucis = {move.uci() for move in board.legal_moves}
    assert reply in legal_ucis, f"engine_reply returned '{reply}' which is not a legal move"


# ---------------------------------------------------------------------------
# 2. engine_reply is deterministic for the same fen + move_index
# ---------------------------------------------------------------------------

def test_engine_reply_is_deterministic():
    reply_a = engine_reply(STARTING_FEN, move_index=0)
    reply_b = engine_reply(STARTING_FEN, move_index=0)
    assert reply_a == reply_b, "engine_reply must be deterministic for the same inputs"


# ---------------------------------------------------------------------------
# 3. engine_reply varies across different move_index values
# ---------------------------------------------------------------------------

def test_engine_reply_varies_by_move_index():
    replies = {engine_reply(STARTING_FEN, move_index=i) for i in range(10)}
    # At least 2 distinct moves should appear across 10 different indices
    assert len(replies) > 1, (
        "engine_reply should produce different moves for different move_index values"
    )


# ---------------------------------------------------------------------------
# 4. engine_reply returns None after game over (fool's mate)
# ---------------------------------------------------------------------------

def test_engine_reply_after_game_over():
    fen = fools_mate_fen()
    result = engine_reply(fen)
    assert result is None, f"engine_reply should return None after checkmate, got '{result}'"


# ---------------------------------------------------------------------------
# 5. apply_san_move with "e4" on starting position
# ---------------------------------------------------------------------------

def test_apply_san_e4():
    new_fen, uci = apply_san_move(STARTING_FEN, "e4")
    assert uci == "e2e4", f"Expected UCI 'e2e4', got '{uci}'"
    board = chess.Board(new_fen)
    piece = board.piece_at(chess.E4)
    assert piece is not None and piece.piece_type == chess.PAWN, (
        "After e4 the pawn should be on e4"
    )


# ---------------------------------------------------------------------------
# 6. apply_san_move raises ValueError for an illegal move
# ---------------------------------------------------------------------------

def test_apply_san_illegal_raises():
    with pytest.raises(ValueError):
        apply_san_move(STARTING_FEN, "Qxe7")


# ---------------------------------------------------------------------------
# 7. apply_san_move for castling O-O returns uci "e1g1"
# ---------------------------------------------------------------------------

def test_apply_san_castling():
    board = chess.Board()
    board.remove_piece_at(chess.F1)
    board.remove_piece_at(chess.G1)
    fen = board.fen()
    new_fen, uci = apply_san_move(fen, "O-O")
    assert uci == "e1g1", f"Expected UCI 'e1g1' for O-O, got '{uci}'"


# ---------------------------------------------------------------------------
# 8. game_status on starting position returns "ongoing"
# ---------------------------------------------------------------------------

def test_game_status_ongoing():
    assert game_status(STARTING_FEN) == "ongoing"


# ---------------------------------------------------------------------------
# 9. game_status after fool's mate returns "checkmate"
# ---------------------------------------------------------------------------

def test_game_status_checkmate():
    fen = fools_mate_fen()
    assert game_status(fen) == "checkmate"


# ---------------------------------------------------------------------------
# 10. game_status on a known stalemate position returns "stalemate"
# ---------------------------------------------------------------------------

def test_game_status_stalemate():
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.A8, chess.Piece(chess.KING, chess.BLACK))
    board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.C6, chess.Piece(chess.KING, chess.WHITE))
    board.turn = chess.BLACK
    assert game_status(board.fen()) == "stalemate"


# ---------------------------------------------------------------------------
# 11. Full game loop: e4, engine, Nf3, engine, Bc4 — game stays "ongoing"
# ---------------------------------------------------------------------------

def test_full_game_loop():
    fen = STARTING_FEN

    # White plays e4
    fen, uci = apply_san_move(fen, "e4")
    assert uci == "e2e4"
    assert game_status(fen) == "ongoing"

    # Engine replies (black move)
    engine_uci = engine_reply(fen, move_index=0)
    assert engine_uci is not None
    board = chess.Board(fen)
    move = chess.Move.from_uci(engine_uci)
    assert move in board.legal_moves
    board.push(move)
    fen = board.fen()
    assert game_status(fen) == "ongoing"

    # White plays Nf3
    fen, uci = apply_san_move(fen, "Nf3")
    assert uci == "g1f3"
    assert game_status(fen) == "ongoing"

    # Engine replies (black move)
    engine_uci = engine_reply(fen, move_index=1)
    assert engine_uci is not None
    board = chess.Board(fen)
    move = chess.Move.from_uci(engine_uci)
    assert move in board.legal_moves
    board.push(move)
    fen = board.fen()
    assert game_status(fen) == "ongoing"

    # White plays Bc4
    fen, uci = apply_san_move(fen, "Bc4")
    assert uci == "f1c4"
    assert game_status(fen) == "ongoing"
