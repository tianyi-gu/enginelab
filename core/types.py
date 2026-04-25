"""Core type definitions for EngineLab."""

Square = tuple[int, int]
# (row, col)
# row 0 = rank 1 (white's back rank)
# row 7 = rank 8 (black's back rank)
# col 0 = file a
# col 7 = file h


def is_white(piece: str) -> bool:
    """True if piece is white (uppercase FEN char)."""
    return piece.isupper()


def is_black(piece: str) -> bool:
    """True if piece is black (lowercase FEN char)."""
    return piece.islower()


def piece_color(piece: str) -> str:
    """Return 'w' for white pieces, 'b' for black pieces."""
    return "w" if piece.isupper() else "b"


def piece_type(piece: str) -> str:
    """Return uppercase piece type (e.g., 'p' -> 'P')."""
    return piece.upper()


def opponent_color(color: str) -> str:
    """Return the opponent's color."""
    return "b" if color == "w" else "w"
