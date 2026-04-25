"""Move application for standard chess in EngineLab.

Applies a move to a board, returning a new board. Handles:
- Basic piece movement
- Captures
- Castling (king + rook movement)
- En passant (capture behind the pawn)
- Promotion
- Castling rights updates (on king/rook move or rook capture)
- En passant square updates (on double pawn push)
- Side-to-move toggle and move count increment

Does NOT set winner or detect checkmate/stalemate — that is handled
at the game-loop level.
"""

from core.board import Board
from core.move import Move
from core.types import piece_type, piece_color


def apply_move(board: Board, move: Move) -> Board:
    """Apply move and return a new Board. Does not mutate the original."""
    new = board.copy()
    piece = new.get_piece(move.start)

    # Move the piece
    new.set_piece(move.start, None)
    new.set_piece(move.end, piece)

    # --- Castling: move the rook ---
    if piece is not None and piece_type(piece) == "K":
        dr = move.end[1] - move.start[1]
        if abs(dr) == 2:
            rank = move.start[0]
            if dr > 0:
                # Kingside
                rook = "R" if piece_color(piece) == "w" else "r"
                new.set_piece((rank, 7), None)
                new.set_piece((rank, 5), rook)
            else:
                # Queenside
                rook = "R" if piece_color(piece) == "w" else "r"
                new.set_piece((rank, 0), None)
                new.set_piece((rank, 3), rook)

    # --- En passant capture ---
    if piece is not None and piece_type(piece) == "P":
        if board.en_passant_square is not None and move.end == board.en_passant_square:
            # Remove the captured pawn (it's on the same rank as the moving pawn)
            captured_pawn_row = move.start[0]
            captured_pawn_col = move.end[1]
            new.set_piece((captured_pawn_row, captured_pawn_col), None)

    # --- Promotion ---
    if move.promotion is not None:
        new.set_piece(move.end, move.promotion)

    # --- Update castling rights ---
    # If king moves, lose both castling rights for that color
    if piece is not None and piece_type(piece) == "K":
        if piece_color(piece) == "w":
            new.castling_rights["K"] = False
            new.castling_rights["Q"] = False
        else:
            new.castling_rights["k"] = False
            new.castling_rights["q"] = False

    # If rook moves from its starting square, lose that castling right
    if piece is not None and piece_type(piece) == "R":
        if move.start == (0, 7):
            new.castling_rights["K"] = False
        elif move.start == (0, 0):
            new.castling_rights["Q"] = False
        elif move.start == (7, 7):
            new.castling_rights["k"] = False
        elif move.start == (7, 0):
            new.castling_rights["q"] = False

    # If a rook is captured on its starting square, lose that castling right
    if move.end == (0, 7):
        new.castling_rights["K"] = False
    elif move.end == (0, 0):
        new.castling_rights["Q"] = False
    elif move.end == (7, 7):
        new.castling_rights["k"] = False
    elif move.end == (7, 0):
        new.castling_rights["q"] = False

    # --- Update en passant square ---
    if piece is not None and piece_type(piece) == "P" and abs(move.end[0] - move.start[0]) == 2:
        # Double pawn push — en passant target is the square the pawn skipped
        ep_row = (move.start[0] + move.end[0]) // 2
        new.en_passant_square = (ep_row, move.start[1])
    else:
        new.en_passant_square = None

    # --- Toggle side to move and increment move count ---
    new.side_to_move = "b" if board.side_to_move == "w" else "w"
    new.move_count = board.move_count + 1

    return new
