"""Board representation for EngineLab."""

from core.types import Square
from core.coordinates import square_to_algebraic


class Board:
    """8x8 chess board with full state tracking."""

    def __init__(self) -> None:
        self.grid: list[list[str | None]] = [[None] * 8 for _ in range(8)]
        self.side_to_move: str = "w"
        self.winner: str | None = None
        self.move_count: int = 0
        self.castling_rights: dict[str, bool] = {
            "K": True, "Q": True, "k": True, "q": True,
        }
        self.en_passant_square: Square | None = None

    @staticmethod
    def starting_position() -> "Board":
        """Return a board with the standard chess starting position."""
        board = Board()
        # Rank 1 (row 0) - white pieces
        board.grid[0] = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        # Rank 2 (row 1) - white pawns
        board.grid[1] = ["P", "P", "P", "P", "P", "P", "P", "P"]
        # Ranks 3-6 (rows 2-5) - empty
        for r in range(2, 6):
            board.grid[r] = [None] * 8
        # Rank 7 (row 6) - black pawns
        board.grid[6] = ["p", "p", "p", "p", "p", "p", "p", "p"]
        # Rank 8 (row 7) - black pieces
        board.grid[7] = ["r", "n", "b", "q", "k", "b", "n", "r"]
        return board

    def copy(self) -> "Board":
        """Deep copy. Modifying the copy must not affect the original."""
        new_board = Board()
        new_board.grid = [row[:] for row in self.grid]
        new_board.side_to_move = self.side_to_move
        new_board.winner = self.winner
        new_board.move_count = self.move_count
        new_board.castling_rights = dict(self.castling_rights)
        new_board.en_passant_square = self.en_passant_square
        return new_board

    def get_piece(self, square: Square) -> str | None:
        """Return piece at (row, col) or None."""
        return self.grid[square[0]][square[1]]

    def set_piece(self, square: Square, piece: str | None) -> None:
        """Set piece at (row, col)."""
        self.grid[square[0]][square[1]] = piece

    def find_king(self, color: str) -> Square | None:
        """Return (row, col) of the king for the given color, or None."""
        target = "K" if color == "w" else "k"
        for row in range(8):
            for col in range(8):
                if self.grid[row][col] == target:
                    return (row, col)
        return None

    def is_terminal(self) -> bool:
        """True if winner is set (includes 'draw')."""
        return self.winner is not None

    def print_board(self) -> None:
        """Pretty-print with rank 8 at top, file labels at bottom."""
        piece_display = {None: "."}
        for rank in range(7, -1, -1):
            rank_str = str(rank + 1) + " "
            for col in range(8):
                piece = self.grid[rank][col]
                rank_str += " " + piece_display.get(piece, piece)
            print(rank_str)
        print("   a b c d e f g h")
