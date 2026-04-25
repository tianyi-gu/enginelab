"""Move representation for EngineLab."""

from dataclasses import dataclass

from core.types import Square


@dataclass(frozen=True)
class Move:
    """A chess move from start square to end square, with optional promotion."""

    start: Square  # (row, col) origin
    end: Square  # (row, col) destination
    promotion: str | None = None  # e.g. "Q" or "q" for promotion target

    def to_uci(self) -> str:
        """Convert to UCI string, e.g. 'e2e4', 'a7a8q'."""
        start_file = chr(ord("a") + self.start[1])
        start_rank = str(self.start[0] + 1)
        end_file = chr(ord("a") + self.end[1])
        end_rank = str(self.end[0] + 1)
        uci = f"{start_file}{start_rank}{end_file}{end_rank}"
        if self.promotion is not None:
            uci += self.promotion.lower()
        return uci

    def __str__(self) -> str:
        return self.to_uci()
