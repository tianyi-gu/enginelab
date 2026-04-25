"""Pawn structure evaluation feature."""

from core.board import Board
from core.types import piece_color, opponent_color


def pawn_structure(board: Board, color: str) -> float:
    """-0.5 doubled, -0.5 isolated, +1.0 passed, +0.3 connected.

    Computed for own pawns minus opponent pawns.
    Positive = better pawn structure for color.
    """
    own = _evaluate_pawns(board, color)
    opp = _evaluate_pawns(board, opponent_color(color))
    return own - opp


def _evaluate_pawns(board: Board, color: str) -> float:
    """Evaluate pawn structure for a single color."""
    pawn = "P" if color == "w" else "p"
    direction = 1 if color == "w" else -1

    # Collect pawn positions by file
    pawns_by_file: dict[int, list[int]] = {}
    pawn_positions: list[tuple[int, int]] = []
    for row in range(8):
        for col in range(8):
            if board.get_piece((row, col)) == pawn:
                pawn_positions.append((row, col))
                pawns_by_file.setdefault(col, []).append(row)

    score = 0.0

    # Doubled pawns: -0.5 for each extra pawn on the same file
    for col, rows in pawns_by_file.items():
        if len(rows) > 1:
            score -= 0.5 * (len(rows) - 1)

    for row, col in pawn_positions:
        # Isolated pawn: no friendly pawns on adjacent files
        has_neighbor = False
        for adj_col in [col - 1, col + 1]:
            if adj_col in pawns_by_file:
                has_neighbor = True
                break
        if not has_neighbor:
            score -= 0.5

        # Passed pawn: no enemy pawns ahead on same or adjacent files
        opp_pawn = "p" if color == "w" else "P"
        is_passed = True
        promo_rank = 7 if color == "w" else 0
        check_start = row + direction
        check_end = promo_rank + direction  # one past promotion rank
        for check_col in [col - 1, col, col + 1]:
            if not (0 <= check_col < 8):
                continue
            r = check_start
            while (direction == 1 and r <= 7) or (direction == -1 and r >= 0):
                if board.get_piece((r, check_col)) == opp_pawn:
                    is_passed = False
                    break
                r += direction
            if not is_passed:
                break
        if is_passed:
            score += 1.0

        # Connected pawn: friendly pawn on adjacent file, same or ±1 rank
        is_connected = False
        for adj_col in [col - 1, col + 1]:
            if not (0 <= adj_col < 8):
                continue
            for adj_row in [row - 1, row, row + 1]:
                if not (0 <= adj_row < 8):
                    continue
                if (adj_row, adj_col) != (row, col):
                    if board.get_piece((adj_row, adj_col)) == pawn:
                        is_connected = True
                        break
            if is_connected:
                break
        if is_connected:
            score += 0.3

    return score
