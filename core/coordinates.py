"""Square-to-algebraic conversion helpers for EngineLab."""

from core.types import Square


def square_to_algebraic(row: int, col: int) -> str:
    """Convert (row, col) to algebraic notation, e.g. (0, 0) -> 'a1'."""
    return chr(ord("a") + col) + str(row + 1)


def algebraic_to_square(alg: str) -> Square:
    """Convert algebraic notation to (row, col), e.g. 'a1' -> (0, 0)."""
    col = ord(alg[0]) - ord("a")
    row = int(alg[1]) - 1
    return (row, col)
