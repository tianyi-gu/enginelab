# Shared Interface Lockfile

This file is the **single source of truth** for all cross-module interfaces.
All developers must implement exactly these signatures. If a signature must
change, update this file first and notify all developers.

Last updated: 2026-04-24

---

## 1. Core Types

```python
# core/types.py

Square = tuple[int, int]
# (row, col)
# row 0 = rank 1 (white's back rank)
# row 7 = rank 8 (black's back rank)
# col 0 = file a
# col 7 = file h
```

Piece representation uses FEN convention:
- Uppercase = white: `P N B R Q K`
- Lowercase = black: `p n b r q k`
- Empty = `None`

Color is always `"w"` or `"b"`.

---

## 2. Board

```python
# core/board.py

class Board:
    grid: list[list[str | None]]   # 8x8
    side_to_move: str              # "w" or "b"
    winner: str | None             # "w", "b", or None
    move_count: int                # incremented each ply

    @staticmethod
    def starting_position() -> "Board":
        """Standard chess starting position."""

    def copy(self) -> "Board":
        """Deep copy. Modifying the copy must not affect the original."""

    def get_piece(self, square: Square) -> str | None:
        """Return piece at (row, col) or None."""

    def set_piece(self, square: Square, piece: str | None) -> None:
        """Set piece at (row, col)."""

    def find_king(self, color: str) -> Square | None:
        """Return (row, col) of the king for the given color, or None."""

    def is_terminal(self) -> bool:
        """True if winner is set."""

    def print_board(self) -> None:
        """Pretty-print with rank 8 at top, file labels."""
```

---

## 3. Move

```python
# core/move.py
from dataclasses import dataclass
from core.types import Square

@dataclass(frozen=True)
class Move:
    start: Square              # (row, col) origin
    end: Square                # (row, col) destination
    promotion: str | None = None  # e.g. "Q" or "q"

    def to_uci(self) -> str:
        """e.g. 'e2e4', 'a7a8q'"""

    def __str__(self) -> str: ...
```

---

## 4. Move Generation

```python
# core/move_generation.py
from core.board import Board
from core.move import Move

def generate_moves(board: Board) -> list[Move]:
    """Pseudo-legal moves for board.side_to_move."""

def generate_moves_for_color(board: Board, color: str) -> list[Move]:
    """Pseudo-legal moves for the given color, regardless of turn."""
```

---

## 5. Atomic Variant

```python
# variants/atomic.py
from core.board import Board
from core.move import Move

def apply_atomic_move(board: Board, move: Move) -> Board:
    """Apply move under Atomic rules. Returns new Board (no mutation).
    Handles explosion on captures. Sets winner if king destroyed."""

def generate_atomic_moves(board: Board) -> list[Move]:
    """Legal moves under Atomic rules: pseudo-legal minus
    captures that would explode the moving side's own king."""
```

---

## 6. Features

```python
# features/registry.py
from typing import Callable
from core.board import Board

FEATURES: dict[str, Callable[[Board, str], float]]
# key = feature name, value = function(board, color) -> float
# Positive = good for color.

FEATURE_DESCRIPTIONS: dict[str, str]
# key = feature name, value = human-readable description

def get_feature_names() -> list[str]: ...
def get_feature_function(name: str) -> Callable[[Board, str], float]: ...
def get_feature_description(name: str) -> str: ...
```

Each feature function:

```python
def feature_name(board: Board, color: str) -> float:
    """Positive = good for color. Must not mutate board."""
```

MVP features: `material`, `mobility`, `enemy_king_danger`,
`own_king_safety`, `capture_threats`.

---

## 7. Feature-Subset Agent

```python
# agents/feature_subset_agent.py
from dataclasses import dataclass

@dataclass(frozen=True)
class FeatureSubsetAgent:
    name: str                      # "Agent_material__mobility"
    features: tuple[str, ...]      # ("material", "mobility")
    weights: dict[str, float]      # {"material": 0.5, "mobility": 0.5}
```

---

## 8. Agent Generation

```python
# agents/generate_agents.py
from agents.feature_subset_agent import FeatureSubsetAgent

def generate_feature_subset_agents(
    feature_names: list[str],
) -> list[FeatureSubsetAgent]:
    """One agent per nonempty subset. Weights = 1/len(subset).
    Names: sorted features joined by '__', prefixed 'Agent_'."""
```

---

## 9. Evaluation

```python
# agents/evaluation.py
from core.board import Board
from agents.feature_subset_agent import FeatureSubsetAgent

WIN_SCORE: int = 10_000
LOSS_SCORE: int = -10_000

def evaluate(board: Board, color: str, agent: FeatureSubsetAgent) -> float:
    """Weighted sum of normalized features. WIN/LOSS for terminals."""

def contributions(
    board: Board, color: str, agent: FeatureSubsetAgent,
) -> dict[str, float]:
    """Per-feature weighted contribution."""
```

Normalization:

```python
def normalize_feature_value(x: float) -> float:
    return max(-10.0, min(10.0, x)) / 10.0
```

---

## 10. Alpha-Beta Engine

```python
# search/alpha_beta.py
from core.board import Board
from core.move import Move
from agents.feature_subset_agent import FeatureSubsetAgent

class AlphaBetaEngine:
    def __init__(self, agent: FeatureSubsetAgent, depth: int): ...

    def choose_move(self, board: Board) -> Move:
        """Best move by alpha-beta search. Must always return a legal move."""

    @property
    def nodes_searched(self) -> int: ...

    @property
    def search_time_seconds(self) -> float: ...
```

---

## 11. Game Result

```python
# simulation/game.py
from dataclasses import dataclass

@dataclass
class GameResult:
    white_agent: str           # agent name
    black_agent: str           # agent name
    winner: str | None         # "w", "b", or None
    moves: int                 # total plies
    termination_reason: str    # "king_exploded" | "no_legal_moves" | "move_cap"
    white_avg_nodes: float
    black_avg_nodes: float
    white_avg_time: float
    black_avg_time: float
```

---

## 12. Game Simulation

```python
# simulation/game.py
from simulation.game import GameResult

def play_game(
    white_agent,               # FeatureSubsetAgent or RandomAgent
    black_agent,
    variant: str = "atomic",
    depth: int = 2,
    max_moves: int = 80,
    seed: int | None = None,
) -> GameResult: ...
```

---

## 13. Random Agent

```python
# simulation/random_agent.py
from core.board import Board
from core.move import Move

class RandomAgent:
    name: str = "RandomAgent"

    def choose_move(self, board: Board) -> Move: ...
```

---

## 14. Round-Robin Tournament

```python
# tournament/round_robin.py
from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult

def run_round_robin(
    agents: list[FeatureSubsetAgent],
    variant: str,
    depth: int,
    max_moves: int,
    seed: int,
) -> list[GameResult]:
    """Play every ordered pair once: N*(N-1) games."""
```

---

## 15. Leaderboard

```python
# tournament/leaderboard.py
from dataclasses import dataclass
from agents.feature_subset_agent import FeatureSubsetAgent
from simulation.game import GameResult

@dataclass
class LeaderboardRow:
    agent_name: str
    features: tuple[str, ...]
    games_played: int
    wins: int
    losses: int
    draws: int
    score_rate: float          # (wins + 0.5 * draws) / games_played
    avg_game_length: float

def compute_leaderboard(
    results: list[GameResult],
    agents: list[FeatureSubsetAgent],
) -> list[LeaderboardRow]:
    """Sorted by score_rate descending."""
```

---

## 16. Result I/O

```python
# tournament/results_io.py
from simulation.game import GameResult

def save_results_json(results: list[GameResult], path: str) -> None: ...
def load_results_json(path: str) -> list[GameResult]: ...
def save_results_csv(results: list[GameResult], path: str) -> None: ...
```

---

## 17. Feature Marginals

```python
# analysis/feature_marginals.py
from dataclasses import dataclass
from tournament.leaderboard import LeaderboardRow

@dataclass
class FeatureContributionRow:
    feature: str
    avg_score_with: float
    avg_score_without: float
    marginal: float            # avg_score_with - avg_score_without
    top_k_frequency: float     # fraction of top-k agents containing feature

def compute_feature_marginals(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
    top_k: int = 10,
) -> list[FeatureContributionRow]: ...
```

---

## 18. Pairwise Synergy

```python
# analysis/synergy.py
from dataclasses import dataclass
from tournament.leaderboard import LeaderboardRow

@dataclass
class SynergyRow:
    feature_a: str
    feature_b: str
    avg_score_with_both: float
    synergy: float

def compute_pairwise_synergies(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
) -> list[SynergyRow]: ...
```

Formula:

```
synergy(a, b) = avg_with_both - avg_with_a - avg_with_b + overall_avg
```

---

## 19. Interpretation

```python
# analysis/interpretation.py
from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow

def generate_interpretation(
    best_agent: LeaderboardRow,
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    variant: str,
) -> str:
    """Natural-language interpretation paragraph."""
```

---

## 20. Markdown Report

```python
# reports/markdown_report.py
from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow

def generate_markdown_report(
    variant: str,
    feature_names: list[str],
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    interpretation: str,
    output_path: str,
    config: dict,
) -> None:
    """Write Markdown report to output_path."""
```
