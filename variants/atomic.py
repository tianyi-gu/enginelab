"""Atomic chess variant for EngineLab.

Atomic chess rules:
- On capture, an explosion occurs: the capturing piece, captured piece,
  and all non-pawn pieces adjacent to the capture square are destroyed.
- Pawns are immune to explosions (they survive adjacent explosions).
- If a king is destroyed by an explosion, that side loses.
- A player cannot make a capture that would explode their own king
  (self-preservation rule).
"""

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_moves, is_in_check
from core.types import piece_color, piece_type, opponent_color


_ADJACENT_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


def apply_atomic_move(board: Board, move: Move) -> Board:
    """Apply move under Atomic rules. Returns new Board (no mutation).

    If the move is a capture, an explosion occurs at the destination:
    - Capturing piece is destroyed
    - Captured piece is destroyed
    - All adjacent non-pawn pieces are destroyed
    - If a king is destroyed, that side's winner is set
    """
    captured = board.get_piece(move.end)

    if captured is not None:
        # Capture -> explosion
        return _apply_explosion(board, move)
    else:
        # Non-capture -> standard move application
        return apply_move(board, move)


def _apply_explosion(board: Board, move: Move) -> Board:
    """Apply a capture with atomic explosion."""
    new = board.copy()

    # Destroy the captured piece and capturing piece at the destination
    new.set_piece(move.end, None)
    new.set_piece(move.start, None)

    # Destroy all adjacent non-pawn pieces
    er, ec = move.end
    for dr, dc in _ADJACENT_OFFSETS:
        nr, nc = er + dr, ec + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            adj_piece = new.get_piece((nr, nc))
            if adj_piece is not None and piece_type(adj_piece) != "P":
                new.set_piece((nr, nc), None)

    # Check if either king was destroyed
    white_king = new.find_king("w")
    black_king = new.find_king("b")

    if white_king is None and black_king is None:
        # Both kings destroyed — the side that made the move loses
        new.winner = opponent_color(board.side_to_move)
    elif white_king is None:
        new.winner = "b"
    elif black_king is None:
        new.winner = "w"

    # Update castling rights based on what was destroyed
    _update_castling_after_explosion(new)

    # Clear en passant, toggle side, increment move count
    new.en_passant_square = None
    new.side_to_move = opponent_color(board.side_to_move)
    new.move_count = board.move_count + 1

    return new


def _update_castling_after_explosion(board: Board) -> None:
    """Revoke castling rights if kings or rooks are gone."""
    if board.find_king("w") is None or board.get_piece((0, 4)) is None:
        board.castling_rights["K"] = False
        board.castling_rights["Q"] = False
    else:
        if board.get_piece((0, 7)) is None:
            board.castling_rights["K"] = False
        if board.get_piece((0, 0)) is None:
            board.castling_rights["Q"] = False

    if board.find_king("b") is None or board.get_piece((7, 4)) is None:
        board.castling_rights["k"] = False
        board.castling_rights["q"] = False
    else:
        if board.get_piece((7, 7)) is None:
            board.castling_rights["k"] = False
        if board.get_piece((7, 0)) is None:
            board.castling_rights["q"] = False


def generate_atomic_moves(board: Board) -> list[Move]:
    """Legal moves under Atomic rules.

    Pseudo-legal moves filtered by:
    1. Self-preservation: captures that would explode own king are removed.
    2. Standard check legality for non-capture moves.
    """
    color = board.side_to_move
    pseudo_legal = generate_moves(board)
    legal: list[Move] = []

    for move in pseudo_legal:
        captured = board.get_piece(move.end)

        if captured is not None:
            # Capture move — check self-preservation
            if _would_explode_own_king(board, move, color):
                continue
            legal.append(move)
        else:
            # Non-capture — standard check legality
            new_board = apply_move(board, move)
            if not is_in_check(new_board, color):
                legal.append(move)

    return legal


def _would_explode_own_king(board: Board, move: Move, color: str) -> bool:
    """Check if a capture would destroy the moving side's own king."""
    king_sq = board.find_king(color)
    if king_sq is None:
        return False

    # The king is destroyed if it's adjacent to or on the explosion square
    er, ec = move.end
    kr, kc = king_sq

    # King is the capturing piece
    if move.start == king_sq:
        return True  # King always destroyed in atomic capture (it's on the explosion square)

    # Wait — in atomic chess, kings CAN capture if they won't be destroyed.
    # Actually, the king is at move.start, and the explosion is at move.end.
    # The king is always adjacent to move.end (since it moved there).
    # So king captures always destroy the king. Hence king captures are always illegal.

    # King is adjacent to explosion square
    if abs(kr - er) <= 1 and abs(kc - ec) <= 1:
        return True

    return False
