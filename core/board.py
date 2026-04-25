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
        self.check_count: dict[str, int] = {"w": 0, "b": 0}

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
        new_board.check_count = dict(self.check_count)
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

    def to_fen(self) -> str:
        """Convert board state to a FEN string."""
        rows = []
        for rank in range(7, -1, -1):
            empty = 0
            row_str = ""
            for col in range(8):
                piece = self.grid[rank][col]
                if piece is None:
                    empty += 1
                else:
                    if empty > 0:
                        row_str += str(empty)
                        empty = 0
                    row_str += piece
            if empty > 0:
                row_str += str(empty)
            rows.append(row_str)

        castling = ""
        for c in ["K", "Q", "k", "q"]:
            if self.castling_rights.get(c, False):
                castling += c
        if not castling:
            castling = "-"

        ep = "-"
        if self.en_passant_square is not None:
            ep = square_to_algebraic(
                self.en_passant_square[0], self.en_passant_square[1],
            )

        halfmove = 0
        fullmove = self.move_count // 2 + 1
        return (
            f"{'/'.join(rows)} {self.side_to_move} "
            f"{castling} {ep} {halfmove} {fullmove}"
        )

    @staticmethod
    def from_fen(fen: str) -> "Board":
        """Create a Board from a FEN string."""
        from core.coordinates import algebraic_to_square

        parts = fen.split()
        board = Board()

        # Piece placement
        rows = parts[0].split("/")
        for rank_idx, row_str in enumerate(rows):
            rank = 7 - rank_idx
            col = 0
            for ch in row_str:
                if ch.isdigit():
                    col += int(ch)
                else:
                    board.grid[rank][col] = ch
                    col += 1

        # Side to move
        board.side_to_move = parts[1] if len(parts) > 1 else "w"

        # Castling rights
        castling_str = parts[2] if len(parts) > 2 else "-"
        board.castling_rights = {
            "K": "K" in castling_str,
            "Q": "Q" in castling_str,
            "k": "k" in castling_str,
            "q": "q" in castling_str,
        }

        # En passant
        ep_str = parts[3] if len(parts) > 3 else "-"
        if ep_str != "-":
            board.en_passant_square = algebraic_to_square(ep_str)
        else:
            board.en_passant_square = None

        # Move count (use fullmove number)
        if len(parts) > 5:
            fullmove = int(parts[5])
            halfmove_offset = 0 if board.side_to_move == "w" else 1
            board.move_count = (fullmove - 1) * 2 + halfmove_offset
        else:
            board.move_count = 0

        return board

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
