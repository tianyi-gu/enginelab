"""Chess960 (Fischer Random) variant for EngineLab.

Uses a randomized back-rank starting position (one of 960 possible
arrangements) with standard chess rules.  Bishops must be on opposite
colors and the king must be between the two rooks.

Castling is disabled in this implementation to avoid the complexity of
960-style castling rules while still allowing meaningful feature-subset
discovery through randomized opening positions.
"""

import random as _random_mod

from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_legal_moves


def chess960_starting_position(seed: int = 0) -> Board:
    """Generate a valid Chess960 starting position.

    Constraints:
    - Bishops on opposite-colored squares
    - King between the two rooks
    - Same arrangement mirrored for black

    Uses ``random.Random(seed)`` for determinism.
    """
    rng = _random_mod.Random(seed)

    # Generate a valid back rank using the standard 960 algorithm
    back_rank: list[str | None] = [None] * 8

    # 1. Place bishops on opposite colors
    light_squares = [1, 3, 5, 7]  # columns with light squares on rank 1
    dark_squares = [0, 2, 4, 6]   # columns with dark squares on rank 1
    b1 = rng.choice(light_squares)
    b2 = rng.choice(dark_squares)
    back_rank[b1] = "B"
    back_rank[b2] = "B"

    # 2. Place queen on a random empty square
    empty = [i for i in range(8) if back_rank[i] is None]
    q_pos = rng.choice(empty)
    back_rank[q_pos] = "Q"

    # 3. Place knights on two random empty squares
    empty = [i for i in range(8) if back_rank[i] is None]
    n1 = rng.choice(empty)
    back_rank[n1] = "N"
    empty = [i for i in range(8) if back_rank[i] is None]
    n2 = rng.choice(empty)
    back_rank[n2] = "N"

    # 4. Place rook, king, rook on the remaining 3 empty squares (in order)
    #    This guarantees king is between the two rooks.
    empty = sorted(i for i in range(8) if back_rank[i] is None)
    assert len(empty) == 3
    back_rank[empty[0]] = "R"
    back_rank[empty[1]] = "K"
    back_rank[empty[2]] = "R"

    # Build the board
    board = Board()
    # White back rank
    board.grid[0] = list(back_rank)
    # White pawns
    board.grid[1] = ["P"] * 8
    # Empty middle
    for r in range(2, 6):
        board.grid[r] = [None] * 8
    # Black pawns
    board.grid[6] = ["p"] * 8
    # Black back rank (mirror of white)
    board.grid[7] = [p.lower() if p else None for p in back_rank]

    # Disable castling (960 castling rules not implemented)
    board.castling_rights = {"K": False, "Q": False, "k": False, "q": False}

    return board


def apply_chess960_move(board: Board, move: Move) -> Board:
    """Apply move under Chess960 rules. Returns new Board.

    Same as standard chess (castling is disabled).
    """
    return apply_move(board, move)


def generate_chess960_moves(board: Board) -> list[Move]:
    """Legal moves for Chess960 (same as standard, no castling)."""
    return generate_legal_moves(board)
