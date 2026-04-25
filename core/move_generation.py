"""Pseudo-legal and legal move generation for EngineLab.

Move generation iterates pieces in deterministic order: row 0-7, col 0-7.
For each piece, destinations are produced in a consistent order.
"""

from core.board import Board
from core.move import Move
from core.types import Square, piece_color, piece_type, opponent_color

# Direction vectors for sliding pieces
_BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
_ROOK_DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
_QUEEN_DIRS = _BISHOP_DIRS + _ROOK_DIRS
_KING_DIRS = _QUEEN_DIRS  # same 8 directions, but single step
_KNIGHT_JUMPS = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2),
]


def _in_bounds(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def _generate_pawn_moves(board: Board, row: int, col: int, color: str) -> list[Move]:
    """Generate pseudo-legal pawn moves from (row, col)."""
    moves: list[Move] = []
    direction = 1 if color == "w" else -1
    start_rank = 1 if color == "w" else 6
    promo_rank = 7 if color == "w" else 0
    promo_pieces = ["Q", "R", "B", "N"] if color == "w" else ["q", "r", "b", "n"]

    # Single push
    nr = row + direction
    if _in_bounds(nr, col) and board.get_piece((nr, col)) is None:
        if nr == promo_rank:
            for p in promo_pieces:
                moves.append(Move((row, col), (nr, col), promotion=p))
        else:
            moves.append(Move((row, col), (nr, col)))

        # Double push (only if single push square is empty)
        if row == start_rank:
            nr2 = row + 2 * direction
            if board.get_piece((nr2, col)) is None:
                moves.append(Move((row, col), (nr2, col)))

    # Diagonal captures (left then right for determinism)
    for dc in [-1, 1]:
        nc = col + dc
        nr = row + direction
        if not _in_bounds(nr, nc):
            continue
        target = board.get_piece((nr, nc))
        if target is not None and piece_color(target) != color:
            if nr == promo_rank:
                for p in promo_pieces:
                    moves.append(Move((row, col), (nr, nc), promotion=p))
            else:
                moves.append(Move((row, col), (nr, nc)))

    # En passant
    if board.en_passant_square is not None:
        ep_row, ep_col = board.en_passant_square
        if ep_row == row + direction and abs(ep_col - col) == 1:
            moves.append(Move((row, col), (ep_row, ep_col)))

    return moves


def _generate_knight_moves(board: Board, row: int, col: int, color: str) -> list[Move]:
    """Generate pseudo-legal knight moves from (row, col)."""
    moves: list[Move] = []
    for dr, dc in _KNIGHT_JUMPS:
        nr, nc = row + dr, col + dc
        if not _in_bounds(nr, nc):
            continue
        target = board.get_piece((nr, nc))
        if target is None or piece_color(target) != color:
            moves.append(Move((row, col), (nr, nc)))
    return moves


def _generate_sliding_moves(
    board: Board, row: int, col: int, color: str, directions: list[tuple[int, int]]
) -> list[Move]:
    """Generate pseudo-legal sliding moves (bishop, rook, queen)."""
    moves: list[Move] = []
    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        while _in_bounds(nr, nc):
            target = board.get_piece((nr, nc))
            if target is None:
                moves.append(Move((row, col), (nr, nc)))
            elif piece_color(target) != color:
                moves.append(Move((row, col), (nr, nc)))
                break  # capture ends the slide
            else:
                break  # own piece blocks
            nr += dr
            nc += dc
    return moves


def _generate_king_moves(board: Board, row: int, col: int, color: str) -> list[Move]:
    """Generate pseudo-legal king moves including castling."""
    moves: list[Move] = []

    # Normal king moves (8 directions)
    for dr, dc in _KING_DIRS:
        nr, nc = row + dr, col + dc
        if not _in_bounds(nr, nc):
            continue
        target = board.get_piece((nr, nc))
        if target is None or piece_color(target) != color:
            moves.append(Move((row, col), (nr, nc)))

    # Castling
    # King must be on its starting square
    if color == "w" and (row, col) == (0, 4):
        moves.extend(_generate_castling_moves(board, 0, color))
    elif color == "b" and (row, col) == (7, 4):
        moves.extend(_generate_castling_moves(board, 7, color))

    return moves


def _generate_castling_moves(board: Board, rank: int, color: str) -> list[Move]:
    """Generate castling moves for the given color.

    All 5 castling conditions are checked here so castling moves in the
    pseudo-legal list are already valid with respect to castling rules.
    """
    moves: list[Move] = []
    opp = opponent_color(color)

    # Check king is not in check (condition 3)
    if _is_square_attacked_raw(board, (rank, 4), opp):
        return moves

    # Kingside
    ks_right = "K" if color == "w" else "k"
    if board.castling_rights[ks_right]:
        # No pieces between king and rook (condition 2)
        if (board.get_piece((rank, 5)) is None and
                board.get_piece((rank, 6)) is None):
            # King doesn't pass through attacked square (condition 4)
            if not _is_square_attacked_raw(board, (rank, 5), opp):
                # King doesn't end on attacked square (condition 5)
                if not _is_square_attacked_raw(board, (rank, 6), opp):
                    moves.append(Move((rank, 4), (rank, 6)))

    # Queenside
    qs_right = "Q" if color == "w" else "q"
    if board.castling_rights[qs_right]:
        # No pieces between king and rook (condition 2)
        if (board.get_piece((rank, 3)) is None and
                board.get_piece((rank, 2)) is None and
                board.get_piece((rank, 1)) is None):
            # King doesn't pass through attacked square (condition 4)
            if not _is_square_attacked_raw(board, (rank, 3), opp):
                # King doesn't end on attacked square (condition 5)
                if not _is_square_attacked_raw(board, (rank, 2), opp):
                    moves.append(Move((rank, 4), (rank, 2)))

    return moves


def _is_square_attacked_raw(board: Board, square: Square, by_color: str) -> bool:
    """Check if a square is attacked by any piece of by_color.

    Uses reverse-lookup: for each attacker type, check if a piece of that
    type exists at a position that could attack the square.
    """
    sr, sc = square

    # Pawn attacks
    if by_color == "w":
        # White pawns attack upward diagonally
        # A white pawn at (sr-1, sc±1) attacks (sr, sc)
        for dc in [-1, 1]:
            pr, pc = sr - 1, sc + dc
            if _in_bounds(pr, pc):
                p = board.get_piece((pr, pc))
                if p == "P":
                    return True
    else:
        # Black pawns attack downward diagonally
        # A black pawn at (sr+1, sc±1) attacks (sr, sc)
        for dc in [-1, 1]:
            pr, pc = sr + 1, sc + dc
            if _in_bounds(pr, pc):
                p = board.get_piece((pr, pc))
                if p == "p":
                    return True

    # Knight attacks
    knight = "N" if by_color == "w" else "n"
    for dr, dc in _KNIGHT_JUMPS:
        nr, nc = sr + dr, sc + dc
        if _in_bounds(nr, nc) and board.get_piece((nr, nc)) == knight:
            return True

    # King attacks (adjacent squares)
    king = "K" if by_color == "w" else "k"
    for dr, dc in _KING_DIRS:
        nr, nc = sr + dr, sc + dc
        if _in_bounds(nr, nc) and board.get_piece((nr, nc)) == king:
            return True

    # Bishop/Queen attacks (diagonals)
    bishop = "B" if by_color == "w" else "b"
    queen = "Q" if by_color == "w" else "q"
    for dr, dc in _BISHOP_DIRS:
        nr, nc = sr + dr, sc + dc
        while _in_bounds(nr, nc):
            p = board.get_piece((nr, nc))
            if p is not None:
                if p == bishop or p == queen:
                    return True
                break  # blocked by another piece
            nr += dr
            nc += dc

    # Rook/Queen attacks (orthogonals)
    rook = "R" if by_color == "w" else "r"
    for dr, dc in _ROOK_DIRS:
        nr, nc = sr + dr, sc + dc
        while _in_bounds(nr, nc):
            p = board.get_piece((nr, nc))
            if p is not None:
                if p == rook or p == queen:
                    return True
                break  # blocked by another piece
            nr += dr
            nc += dc

    return False


def is_square_attacked(board: Board, square: Square, by_color: str) -> bool:
    """True if any piece of by_color attacks the given square."""
    return _is_square_attacked_raw(board, square, by_color)


def is_in_check(board: Board, color: str) -> bool:
    """True if color's king is under attack by the opponent."""
    king_sq = board.find_king(color)
    if king_sq is None:
        return False
    return _is_square_attacked_raw(board, king_sq, opponent_color(color))


def _generate_pseudo_legal_for_color(board: Board, color: str) -> list[Move]:
    """Generate all pseudo-legal moves for the given color.

    Iterates pieces in deterministic order: row 0-7, col 0-7.
    """
    moves: list[Move] = []

    for row in range(8):
        for col in range(8):
            piece = board.get_piece((row, col))
            if piece is None or piece_color(piece) != color:
                continue

            pt = piece_type(piece)
            if pt == "P":
                moves.extend(_generate_pawn_moves(board, row, col, color))
            elif pt == "N":
                moves.extend(_generate_knight_moves(board, row, col, color))
            elif pt == "B":
                moves.extend(
                    _generate_sliding_moves(board, row, col, color, _BISHOP_DIRS)
                )
            elif pt == "R":
                moves.extend(
                    _generate_sliding_moves(board, row, col, color, _ROOK_DIRS)
                )
            elif pt == "Q":
                moves.extend(
                    _generate_sliding_moves(board, row, col, color, _QUEEN_DIRS)
                )
            elif pt == "K":
                moves.extend(_generate_king_moves(board, row, col, color))

    return moves


def generate_moves(board: Board) -> list[Move]:
    """Generate pseudo-legal moves for board.side_to_move.

    Includes castling and en passant. Does NOT filter for check legality.
    """
    return _generate_pseudo_legal_for_color(board, board.side_to_move)


def generate_moves_for_color(board: Board, color: str) -> list[Move]:
    """Generate pseudo-legal moves for the given color, regardless of turn."""
    return _generate_pseudo_legal_for_color(board, color)


def generate_legal_moves(board: Board) -> list[Move]:
    """Pseudo-legal moves filtered to remove those that leave the
    moving side's king in check.

    Two-step approach: generate pseudo-legal, apply each on a copy,
    check if own king is attacked.
    """
    from core.apply_move import apply_move

    color = board.side_to_move
    pseudo_legal = generate_moves(board)
    legal: list[Move] = []

    for move in pseudo_legal:
        new_board = apply_move(board, move)
        if not is_in_check(new_board, color):
            legal.append(move)

    return legal
