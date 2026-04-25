# EngineLab -- Feature-Subset Alpha-Beta Engine Lab for Chess Variants

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Core Mechanism](#2-core-mechanism)
3. [Technical Conventions & Standards](#3-technical-conventions--standards)
4. [Atomic Chess Rules](#4-atomic-chess-rules)
5. [Technology Stack](#5-technology-stack)
6. [Repository Structure](#6-repository-structure)
7. [Shared Interface Specification](#7-shared-interface-specification)
8. [Development Area Specifications](#8-development-area-specifications)
9. [Parallel Development Workflow](#9-parallel-development-workflow)
10. [Integration & Merge Plan](#10-integration--merge-plan)
11. [Performance Budget](#11-performance-budget)
12. [MVP Acceptance Criteria](#12-mvp-acceptance-criteria)
13. [Hackathon Execution Strategy](#13-hackathon-execution-strategy)
14. [Known Limitations & Future Work](#14-known-limitations--future-work)
15. [References](#15-references)

---

## 1. Executive Summary

**Project name:** EngineLab

**One-line pitch:** EngineLab is an interpretable strategy-discovery system for
chess variants. Given a variant and a set of strategic features, it creates one
alpha-beta engine for every nonempty feature subset, runs tournaments, and
discovers which strategic concepts actually win.

### Why This Matters

The approach draws directly on principles from quantitative factor analysis.
The mapping is exact:

| Quant Finance          | EngineLab                        |
|------------------------|----------------------------------|
| Factor                 | Evaluation feature               |
| Factor portfolio       | Feature-subset agent             |
| Return                 | Tournament win rate              |
| Alpha                  | Marginal feature contribution    |
| Factor interaction     | Pairwise feature synergy         |
| Factor model selection | Best-performing feature subset   |

By exhaustively testing every feature combination, EngineLab discovers not just
*which* features matter, but *which combinations are synergistic or redundant* --
without any gradient-based optimization or neural network black box. The
discovery is transparent, reproducible, and fully interpretable.

### What It Produces

- 31 AI engines (one per nonempty subset of 5 features)
- 930 tournament games (full round-robin, both colors)
- Ranked leaderboard with win rates
- Feature marginal contribution analysis
- Pairwise feature synergy matrix
- Natural-language interpretation
- Human-readable strategy report (Markdown + optional charts)

---

## 2. Core Mechanism

```
Input: Variant rules (e.g., Atomic Chess)
        |
        v
Define strategic evaluation features (material, mobility, ...)
        |
        v
Generate power set of features (2^n - 1 nonempty subsets)
        |
        v
Each subset becomes an agent with equal-weight evaluation function
        |
        v
Each agent powers an alpha-beta search engine
        |
        v
All engines play a full round-robin tournament
        |
        v
Analyze: leaderboard, marginal feature value, pairwise synergy
        |
        v
Generate human-readable strategy report
```

**There is no meta-optimizer.** The discovery comes from exhaustive
feature-subset testing. This is intentional: equal weights isolate the
contribution of feature *presence* rather than confounding it with weight
tuning. The system answers "which strategic concepts matter?" not "what are the
optimal weights?"

---

## 3. Technical Conventions & Standards

These conventions are mandatory across all development areas. Every developer
and Claude Code agent must follow them exactly.

### 3.1 Piece Representation (FEN Convention)

Pieces are single characters. Case encodes color:

| Piece  | White | Black |
|--------|-------|-------|
| Pawn   | `P`   | `p`   |
| Knight | `N`   | `n`   |
| Bishop | `B`   | `b`   |
| Rook   | `R`   | `r`   |
| Queen  | `Q`   | `q`   |
| King   | `K`   | `k`   |

Empty squares are `None`.

Helper logic (not a separate function -- each module can inline this):

```python
def is_white(piece: str) -> bool: return piece.isupper()
def is_black(piece: str) -> bool: return piece.islower()
def piece_color(piece: str) -> str: return "w" if piece.isupper() else "b"
def piece_type(piece: str) -> str: return piece.upper()
```

### 3.2 Color Convention

Colors are **always** the single-character strings `"w"` or `"b"`:

- `Board.side_to_move`: `"w"` or `"b"`
- `Board.winner`: `"w"`, `"b"`, or `None`
- Feature function `color` parameter: `"w"` or `"b"`
- `GameResult.winner`: `"w"`, `"b"`, or `None`

The opponent color is derived as:

```python
opponent = "b" if color == "w" else "w"
```

For display purposes only (CLI output, reports), use `"White"` / `"Black"`.

### 3.3 Board Coordinate System

The board is an 8x8 grid indexed as `grid[row][col]`:

- **Row 0** = Rank 1 (white's back rank)
- **Row 7** = Rank 8 (black's back rank)
- **Col 0** = File a
- **Col 7** = File h

Starting position layout:

```
grid[7] = ['r','n','b','q','k','b','n','r']   # Rank 8 (black)
grid[6] = ['p','p','p','p','p','p','p','p']   # Rank 7
grid[5] = [None] * 8                           # Rank 6
grid[4] = [None] * 8                           # Rank 5
grid[3] = [None] * 8                           # Rank 4
grid[2] = [None] * 8                           # Rank 3
grid[1] = ['P','P','P','P','P','P','P','P']   # Rank 2
grid[0] = ['R','N','B','Q','K','B','N','R']   # Rank 1 (white)
```

Square-to-algebraic conversion:

```python
def square_to_algebraic(row: int, col: int) -> str:
    return chr(ord('a') + col) + str(row + 1)
# (0, 0) -> "a1", (7, 4) -> "e8"
```

### 3.4 Naming Conventions

- **Agent names:** `Agent_{feature1}__{feature2}__...` with double-underscore
  separators (single underscores appear within feature names like
  `enemy_king_danger`). Features are sorted alphabetically in the name.
  Example: `Agent_capture_threats__enemy_king_danger__material`

- **File naming:** snake_case for all Python files.

- **Class naming:** PascalCase for classes, snake_case for functions.

- **Type alias convention:**
  ```python
  Square = tuple[int, int]  # (row, col)
  ```

### 3.5 Deep Copy Rule

`Board.copy()` must produce a fully independent deep copy. Modifying the copy
must never affect the original. Since `grid` is a nested list, this requires:

```python
import copy
new_grid = copy.deepcopy(self.grid)
```

Or equivalently: `[row[:] for row in self.grid]` (since elements are strings
or None, a shallow copy of each row suffices).

---

## 4. Atomic Chess Rules

Atomic Chess follows standard chess movement rules with critical modifications
on captures. Implementing these correctly is essential for meaningful games.

### 4.1 Standard Movement

All pieces move identically to standard chess. The MVP scope includes:

**Included:**
- Pawn single push, double push from starting rank, diagonal capture
- Knight L-shaped movement
- Bishop diagonal sliding
- Rook orthogonal sliding
- Queen diagonal + orthogonal sliding
- King single-step in all 8 directions
- Pawn promotion to queen when reaching the last rank

**Excluded from MVP (not needed):**
- Castling
- En passant
- Underpromotion (promote to rook/bishop/knight)
- Threefold repetition
- Fifty-move rule

### 4.2 Explosion Mechanics

When a piece captures another piece at square S, an **explosion** occurs:

1. The **captured piece** at S is removed.
2. The **capturing piece** at S is removed.
3. Every piece on the **8 squares adjacent** to S (king-move distance = 1,
   i.e., Chebyshev distance = 1) is also removed, **UNLESS it is a pawn**.
   Pawns are immune to explosion -- they survive unless directly captured.
4. If any **king** is removed by the explosion, that player loses immediately.

Visual example -- capture at e4:

```
Explosion radius:     d5  e5  f5
                      d4 [e4] f4
                      d3  e3  f3
```

All non-pawn pieces on d3, d4, d5, e3, e5, f3, f4, f5 are destroyed.

### 4.3 Self-Preservation Rule (CRITICAL)

**A player may NOT make a capture that would destroy their own king in the
resulting explosion.**

This is a hard legality constraint. If the capturing player's king is within
Chebyshev distance 1 of the capture square, the capture is illegal and must
be filtered out.

**Implementation approach:** After generating pseudo-legal moves, for each
capture move, check whether the moving side's king is adjacent to the capture
square. If so, remove that move from the legal move list.

This is the one legality filter the MVP MUST implement. Without it, engines
can make moves that immediately kill their own king, producing nonsensical
games and corrupting all analysis.

### 4.4 Terminal State Detection

A position is terminal when any of:

1. **King explosion:** `board.find_king(color)` returns `None` for some color.
   That color loses. Set `board.winner` to the opponent.
2. **No legal moves:** The side to move has zero legal moves (after filtering
   illegal self-explosion captures). The side to move loses (simplified rule
   for MVP -- standard atomic chess treats this as stalemate/draw in some
   rulesets, but loss simplifies implementation and produces more decisive
   games for analysis).
3. **Move cap:** `board.move_count >= max_moves`. Result is a draw
   (`winner = None`).

### 4.5 Check Handling (MVP Simplification)

The MVP does **not** enforce the obligation to escape check. A player whose
king is in check may play any legal move, including one that ignores the check.
This simplification may produce some unrealistic positions but does not break
the system because:

- The self-preservation rule (4.3) prevents the worst illegal states.
- If a king remains in check, the opponent can capture/explode it next move.
- The evaluation features (king_danger, king_safety) will still correctly
  assess dangerous positions, so engines with those features will naturally
  avoid leaving their king in danger.

---

## 5. Technology Stack

### Language

Python 3.11+ (required for `tuple[str, ...]` syntax, `X | Y` union types)

### Libraries

| Library      | Purpose                                    | Required |
|--------------|--------------------------------------------|----------|
| `pytest`     | Unit and integration testing               | Yes      |
| `pandas`     | Tournament result tables, CSV export       | Yes      |
| `numpy`      | Numeric calculations for analysis          | Yes      |
| `tqdm`       | Tournament progress bars                   | Yes      |
| `typer`      | CLI framework                              | Yes      |
| `rich`       | Pretty terminal output, tables             | Yes      |
| `pydantic`   | Structured result models, validation       | Yes      |
| `matplotlib` | Charts for reports                         | Yes      |
| `streamlit`  | Optional demo dashboard UI                 | Optional |

### Package Management

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### No Database

All data is stored as local files:
- **JSON** for raw game results and configuration
- **CSV** for leaderboards and analysis tables
- **Markdown** for final reports
- **PNG** for optional charts

---

## 6. Repository Structure

```
engine-lab/
|
|-- README.md
|-- requirements.txt
|-- main.py                          # CLI entry point (Area 5)
|
|-- core/                            # Area 1
|   |-- __init__.py
|   |-- types.py                     # Square type alias, color helpers
|   |-- board.py                     # Board class
|   |-- move.py                      # Move class
|   |-- coordinates.py               # Square/algebraic conversion helpers
|   |-- move_generation.py           # Pseudo-legal move generation
|   `-- apply_move.py                # Standard move application (non-atomic)
|
|-- variants/                        # Area 1
|   |-- __init__.py
|   |-- base.py                      # Base variant interface
|   `-- atomic.py                    # Atomic Chess rules
|
|-- features/                        # Area 2
|   |-- __init__.py
|   |-- registry.py                  # Feature registry and access functions
|   |-- material.py                  # Material balance feature
|   |-- mobility.py                  # Move count difference feature
|   |-- king_danger.py               # Pressure on opponent king
|   |-- king_safety.py               # Own king safety (defense)
|   `-- capture_threats.py           # Tactical capture/explosion threats
|
|-- agents/                          # Area 3
|   |-- __init__.py
|   |-- feature_subset_agent.py      # FeatureSubsetAgent dataclass
|   |-- generate_agents.py           # Power-set agent generation
|   `-- evaluation.py                # Position evaluation from features
|
|-- search/                          # Area 3
|   |-- __init__.py
|   `-- alpha_beta.py                # Alpha-beta search engine
|
|-- simulation/                      # Area 4
|   |-- __init__.py
|   |-- game.py                      # Single game simulation
|   `-- random_agent.py              # Random move baseline agent
|
|-- tournament/                      # Area 4
|   |-- __init__.py
|   |-- round_robin.py               # Round-robin tournament runner
|   |-- leaderboard.py               # Leaderboard computation
|   `-- results_io.py                # JSON/CSV save and load
|
|-- analysis/                        # Area 5
|   |-- __init__.py
|   |-- feature_marginals.py         # Marginal feature contribution
|   |-- synergy.py                   # Pairwise synergy analysis
|   `-- interpretation.py            # Natural-language interpretation
|
|-- reports/                         # Area 5
|   |-- __init__.py
|   `-- markdown_report.py           # Markdown report generator
|
|-- ui/                              # Area 5 (optional)
|   `-- app.py                       # Streamlit dashboard
|
|-- outputs/                         # Generated artifacts (gitignored)
|   |-- reports/
|   |-- charts/
|   `-- data/
|
|-- docs/                            # Project documentation
|   |-- interfaces.md                # Shared interface lockfile
|   |-- development_workflow.md      # Parallel development process
|   `-- agent_definitions.md         # Per-developer agent prompts
|
`-- tests/                           # All test files
    |-- __init__.py
    |-- test_board.py                # Area 1
    |-- test_move_generation.py      # Area 1
    |-- test_atomic.py               # Area 1
    |-- test_features.py             # Area 2
    |-- test_agents.py               # Area 3
    |-- test_alpha_beta.py           # Area 3
    |-- test_tournament.py           # Area 4
    `-- test_analysis.py             # Area 5
```

---

## 7. Shared Interface Specification

This section defines the exact function signatures and class definitions that
all areas must respect. **Do not change these signatures without updating this
document and notifying all developers.**

The formal, extractable version lives in `docs/interfaces.md`.

### 7.1 Core Types

```python
# core/types.py
Square = tuple[int, int]  # (row, col), row 0 = rank 1, col 0 = file a
```

### 7.2 Board

```python
# core/board.py
class Board:
    grid: list[list[str | None]]   # 8x8, FEN piece chars or None
    side_to_move: str              # "w" or "b"
    winner: str | None             # "w", "b", or None
    move_count: int                # incremented after each ply

    @staticmethod
    def starting_position() -> "Board": ...

    def copy(self) -> "Board": ...
        # Must return a fully independent deep copy.

    def get_piece(self, square: Square) -> str | None: ...

    def set_piece(self, square: Square, piece: str | None) -> None: ...

    def find_king(self, color: str) -> Square | None: ...
        # Returns (row, col) of the king, or None if no king found.

    def is_terminal(self) -> bool: ...
        # True if winner is set or no legal moves exist.

    def print_board(self) -> None: ...
        # Display with rank 8 at top, rank 1 at bottom, file labels.
```

### 7.3 Move

```python
# core/move.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Move:
    start: Square          # (row, col) of origin
    end: Square            # (row, col) of destination
    promotion: str | None = None  # Piece type to promote to, e.g. "Q"/"q"

    def to_uci(self) -> str: ...
        # e.g., "e2e4", "a7a8q"

    def __str__(self) -> str: ...
```

### 7.4 Move Generation

```python
# core/move_generation.py

def generate_moves(board: Board) -> list[Move]:
    """Generate pseudo-legal moves for the side to move."""
    ...

def generate_moves_for_color(board: Board, color: str) -> list[Move]:
    """Generate pseudo-legal moves for the specified color,
    regardless of whose turn it is."""
    ...
```

Note: These produce pseudo-legal moves. For Atomic Chess, the variant layer
must filter out captures that would explode the moving side's own king (see
Section 4.3).

### 7.5 Atomic Variant

```python
# variants/atomic.py

def apply_atomic_move(board: Board, move: Move) -> Board:
    """Apply a move under Atomic Chess rules. Returns a new Board (does not
    mutate the input). Handles explosion on captures. Sets board.winner if
    a king is destroyed. Filters or rejects self-destructive captures."""
    ...

def generate_atomic_moves(board: Board) -> list[Move]:
    """Generate legal moves under Atomic Chess rules. This calls
    generate_moves() and filters out captures that would explode the
    moving side's own king."""
    ...
```

### 7.6 Features

```python
# features/registry.py

FEATURES: dict[str, Callable[[Board, str], float]]
# Maps feature name -> function(board, color) -> float
# Positive means good for `color`.

FEATURE_DESCRIPTIONS: dict[str, str]
# Maps feature name -> human-readable description.

def get_feature_names() -> list[str]: ...
def get_feature_function(name: str) -> Callable[[Board, str], float]: ...
def get_feature_description(name: str) -> str: ...
```

Each feature function signature:

```python
def feature_name(board: Board, color: str) -> float:
    """Return a score where positive = good for `color`."""
    ...
```

### 7.7 Feature-Subset Agent

```python
# agents/feature_subset_agent.py
from dataclasses import dataclass

@dataclass(frozen=True)
class FeatureSubsetAgent:
    name: str                      # e.g. "Agent_material__mobility"
    features: tuple[str, ...]      # e.g. ("material", "mobility")
    weights: dict[str, float]      # e.g. {"material": 0.5, "mobility": 0.5}
```

### 7.8 Agent Generation

```python
# agents/generate_agents.py

def generate_feature_subset_agents(
    feature_names: list[str],
) -> list[FeatureSubsetAgent]:
    """Generate one agent for every nonempty subset of feature_names.
    Weights are normalized: weight = 1.0 / len(subset).
    Agent names are sorted alphabetically by feature name."""
    ...
```

### 7.9 Evaluation

```python
# agents/evaluation.py

WIN_SCORE = 10_000
LOSS_SCORE = -10_000

def evaluate(board: Board, color: str, agent: FeatureSubsetAgent) -> float:
    """Evaluate a position from `color`'s perspective using the agent's
    feature subset and weights. Returns WIN_SCORE / LOSS_SCORE for terminal
    positions."""
    ...

def contributions(
    board: Board, color: str, agent: FeatureSubsetAgent,
) -> dict[str, float]:
    """Return per-feature weighted contribution to the evaluation."""
    ...
```

Feature values should be clipped and normalized before weighting:

```python
def normalize_feature_value(x: float) -> float:
    clipped = max(-10.0, min(10.0, x))
    return clipped / 10.0
```

### 7.10 Alpha-Beta Engine

```python
# search/alpha_beta.py

class AlphaBetaEngine:
    def __init__(self, agent: FeatureSubsetAgent, depth: int): ...

    def choose_move(self, board: Board) -> Move:
        """Return the best move found by alpha-beta search."""
        ...

    @property
    def nodes_searched(self) -> int: ...

    @property
    def search_time_seconds(self) -> float: ...
```

Implementation requirements:
- Minimax with alpha-beta pruning (negamax formulation recommended)
- Depth-limited with leaf-node evaluation
- Terminal position scoring (WIN_SCORE / LOSS_SCORE)
- Move ordering: captures first (improves pruning)
- Must always return a legal move if one exists

### 7.11 Game Result

```python
# simulation/game.py
from dataclasses import dataclass

@dataclass
class GameResult:
    white_agent: str           # Agent name
    black_agent: str           # Agent name
    winner: str | None         # "w", "b", or None (draw)
    moves: int                 # Total plies played
    termination_reason: str    # "king_exploded", "no_legal_moves", "move_cap"
    white_avg_nodes: float     # Average nodes searched per white move
    black_avg_nodes: float     # Average nodes searched per black move
    white_avg_time: float      # Average seconds per white move
    black_avg_time: float      # Average seconds per black move
```

### 7.12 Game Simulation

```python
# simulation/game.py

def play_game(
    white_agent,               # FeatureSubsetAgent, RandomAgent, or similar
    black_agent,
    variant: str = "atomic",
    depth: int = 2,
    max_moves: int = 80,
    seed: int | None = None,
) -> GameResult: ...
```

### 7.13 Round-Robin Tournament

```python
# tournament/round_robin.py

def run_round_robin(
    agents: list[FeatureSubsetAgent],
    variant: str,
    depth: int,
    max_moves: int,
    seed: int,
) -> list[GameResult]:
    """Play every ordered pair (A as white vs B as black) once.
    For N agents, this produces N * (N - 1) games."""
    ...
```

### 7.14 Leaderboard

```python
# tournament/leaderboard.py
from dataclasses import dataclass

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
    """Compute leaderboard sorted by score_rate descending."""
    ...
```

### 7.15 Result I/O

```python
# tournament/results_io.py

def save_results_json(results: list[GameResult], path: str) -> None: ...
def load_results_json(path: str) -> list[GameResult]: ...
def save_results_csv(results: list[GameResult], path: str) -> None: ...
```

### 7.16 Analysis

```python
# analysis/feature_marginals.py
from dataclasses import dataclass

@dataclass
class FeatureContributionRow:
    feature: str
    avg_score_with: float       # Avg score_rate of agents that include feature
    avg_score_without: float    # Avg score_rate of agents that exclude feature
    marginal: float             # avg_score_with - avg_score_without
    top_k_frequency: float      # Fraction of top-k agents containing feature

def compute_feature_marginals(
    leaderboard: list[LeaderboardRow],
    feature_names: list[str],
    top_k: int = 10,
) -> list[FeatureContributionRow]: ...
```

```python
# analysis/synergy.py
from dataclasses import dataclass

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

Synergy formula (interaction term):

```
synergy(a, b) = avg_with_both - avg_with_a_only - avg_with_b_only + overall_avg
```

This is the standard two-way interaction term from factorial ANOVA (see
References). Positive synergy means the features are more valuable together
than their individual contributions would predict.

### 7.17 Reporting

```python
# analysis/interpretation.py

def generate_interpretation(
    best_agent: LeaderboardRow,
    marginals: list[FeatureContributionRow],
    synergies: list[SynergyRow],
    variant: str,
) -> str:
    """Generate a natural-language interpretation paragraph."""
    ...
```

```python
# reports/markdown_report.py

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
    """Write a complete Markdown report to output_path."""
    ...
```

---

## 8. Development Area Specifications

### Area 1: Core Chess State + Atomic Variant Rules

**Owner:** Developer 1

**Goal:** Build the board representation, move representation, pseudo-legal
move generation, and Atomic Chess rule application.

**Files owned:**

```
core/types.py
core/board.py
core/move.py
core/coordinates.py
core/move_generation.py
core/apply_move.py
core/__init__.py
variants/base.py
variants/atomic.py
variants/__init__.py
tests/test_board.py
tests/test_move_generation.py
tests/test_atomic.py
```

**Must not edit:** `features/`, `agents/`, `search/`, `tournament/`,
`analysis/`, `reports/`, `ui/`

#### Detailed Responsibilities

**Board (`core/board.py`):**

- `__init__`: Initialize with 8x8 grid, `side_to_move="w"`, `winner=None`,
  `move_count=0`.
- `starting_position()`: Return a board with standard chess starting position
  using the coordinate system defined in Section 3.3.
- `copy()`: Deep copy (see Section 3.5).
- `get_piece(square)`, `set_piece(square, piece)`: Grid access.
- `find_king(color)`: Scan grid for `"K"` (if color `"w"`) or `"k"` (if
  color `"b"`). Return `(row, col)` or `None`.
- `is_terminal()`: Return `True` if `winner is not None`.
- `print_board()`: Print with rank 8 at top, file labels at bottom.

**Move (`core/move.py`):**

- Frozen dataclass with `start`, `end`, `promotion`.
- `to_uci()`: Format as UCI string, e.g., `"e2e4"`, `"a7a8q"`.

**Move generation (`core/move_generation.py`):**

- Generate pseudo-legal moves for all piece types.
- **Pawn:** Single push (one square forward), double push from starting rank
  (row 1 for white, row 6 for black), diagonal capture. Promotion to queen
  when reaching last rank (row 7 for white, row 0 for black).
- **Knight:** 8 possible L-shaped jumps.
- **Bishop:** Slide diagonally until blocked or capture.
- **Rook:** Slide orthogonally until blocked or capture.
- **Queen:** Combine bishop + rook movement.
- **King:** Single step in all 8 directions.
- Bounds checking: all destination squares must be in [0,7] x [0,7].
- Cannot capture own pieces.
- `generate_moves(board)`: Generate for `board.side_to_move`.
- `generate_moves_for_color(board, color)`: Generate for specified color
  regardless of turn.

**Atomic variant (`variants/atomic.py`):**

- `apply_atomic_move(board, move)`: Copy board, apply move, handle explosion
  if capture, set winner if king destroyed, toggle `side_to_move`, increment
  `move_count`, return new board.
- `generate_atomic_moves(board)`: Call `generate_moves(board)`, filter out
  captures where the moving side's king is adjacent (Chebyshev distance <= 1)
  to the capture square.

#### Checkpoints

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 1A  | `pytest tests/test_board.py` passes                              |
| 1B  | Starting position generates exactly 20 white pseudo-legal moves  |
| 1C  | Atomic explosion tests pass (pieces removed, pawns survive)      |
| 1D  | Self-preservation: captures that would explode own king filtered |
| 1E  | 100 random plies can be applied without crash                    |

---

### Area 2: Feature Library + Feature Registry

**Owner:** Developer 2

**Goal:** Implement all interpretable evaluation features and expose them
through a central registry.

**Files owned:**

```
features/registry.py
features/material.py
features/mobility.py
features/king_danger.py
features/king_safety.py
features/capture_threats.py
features/__init__.py
tests/test_features.py
```

**Must not edit:** `core/`, `variants/`, `agents/`, `search/`, `tournament/`,
`analysis/`, `reports/`, `ui/`

**May import from:** `core`, `variants`

#### Feature Specifications

**1. `material(board, color) -> float`**

Difference in material value:

```
own_material - opponent_material
```

Piece values:

```python
PIECE_VALUES = {"P": 1.0, "N": 3.0, "B": 3.0, "R": 5.0, "Q": 9.0, "K": 0.0}
```

Use `piece_type(piece).upper()` to look up values regardless of color.

**2. `mobility(board, color) -> float`**

Difference in pseudo-legal move count:

```
len(generate_moves_for_color(board, color)) - len(generate_moves_for_color(board, opponent))
```

**3. `enemy_king_danger(board, color) -> float`**

Measures pressure near the opponent's king. For each own piece:

```
score += 1.0 / max(chebyshev_distance(piece_square, enemy_king_square), 1)
```

Additionally, for each square adjacent to the enemy king that is attacked by
an own piece:

```
score += 1.0
```

Chebyshev distance: `max(abs(r1 - r2), abs(c1 - c2))`

If the enemy king is not on the board (already exploded), return a large
positive value (e.g., 10.0).

**4. `own_king_safety(board, color) -> float`**

Penalty for opponent pressure near own king. Computed as the negative of
the danger to own king:

```
own_king_safety(board, color) = -enemy_king_danger(board, opponent)
```

where the danger calculation reuses the same logic but from the opponent's
perspective. If own king is not on the board, return a large negative value
(e.g., -10.0).

**5. `capture_threats(board, color) -> float`**

For each legal capture available to `color`:

```
score += captured_piece_value
score += 3.0 * (number of adjacent enemy non-pawn pieces that would explode)
score += 100.0 if enemy king would be destroyed by the explosion
```

This feature is Atomic-specific and evaluates immediate tactical threats.

#### Registry (`features/registry.py`)

```python
FEATURES: dict[str, Callable[[Board, str], float]] = {
    "material": material,
    "mobility": mobility,
    "enemy_king_danger": enemy_king_danger,
    "own_king_safety": own_king_safety,
    "capture_threats": capture_threats,
}

FEATURE_DESCRIPTIONS: dict[str, str] = {
    "material": "Ordinary piece-value advantage.",
    "mobility": "Difference in pseudo-legal move availability.",
    "enemy_king_danger": "Pressure near the opponent king.",
    "own_king_safety": "Penalty for opponent explosion pressure near own king.",
    "capture_threats": "Immediate tactical capture and explosion opportunities.",
}

def get_feature_names() -> list[str]: ...
def get_feature_function(name: str) -> Callable[[Board, str], float]: ...
def get_feature_description(name: str) -> str: ...
```

#### Invariants

- Every feature returns a `float`.
- Positive values are good for `color`.
- No feature mutates the board.
- `material(starting_position, "w")` returns `0.0`.
- All features handle missing kings gracefully.

#### Checkpoints

| ID  | Criterion                                                    |
|-----|--------------------------------------------------------------|
| 2A  | `material` at starting position returns 0.0 for both colors |
| 2B  | All 5 feature functions return floats                        |
| 2C  | No feature mutates the board (verify with before/after copy) |
| 2D  | `pytest tests/test_features.py` passes                       |

---

### Area 3: Agents + Evaluation + Alpha-Beta Search

**Owner:** Developer 3

**Goal:** Generate feature-subset agents, evaluate positions using weighted
feature combinations, and implement alpha-beta search.

**Files owned:**

```
agents/feature_subset_agent.py
agents/generate_agents.py
agents/evaluation.py
agents/__init__.py
search/alpha_beta.py
search/__init__.py
tests/test_agents.py
tests/test_alpha_beta.py
```

**Must not edit:** `core/`, `variants/`, `features/`, `simulation/`,
`tournament/`, `analysis/`, `reports/`, `ui/`

**May import from:** `core`, `variants`, `features`

#### Detailed Responsibilities

**Agent generation (`agents/generate_agents.py`):**

- Generate one `FeatureSubsetAgent` for every nonempty subset of the given
  feature names.
- For `n` features, this produces `2^n - 1` agents.
- Weights are uniform within each agent: `weight = 1.0 / len(subset)`.
- Agent names: features sorted alphabetically, joined with `__`, prefixed
  with `Agent_`.
- Example for subset `{"mobility", "material"}`:
  ```python
  FeatureSubsetAgent(
      name="Agent_material__mobility",
      features=("material", "mobility"),
      weights={"material": 0.5, "mobility": 0.5},
  )
  ```

**Evaluation (`agents/evaluation.py`):**

- `evaluate(board, color, agent)`: Sum weighted, normalized feature values.
  Return `WIN_SCORE` (+10000) or `LOSS_SCORE` (-10000) for terminal positions.
- Feature normalization:
  ```python
  def normalize_feature_value(x: float) -> float:
      return max(-10.0, min(10.0, x)) / 10.0
  ```
  This clips features to [-10, +10] and scales to [-1, +1], preventing any
  single feature from dominating. After normalization, the weighted sum
  produces values in [-1, +1] for non-terminal positions.
- `contributions(board, color, agent)`: Return the per-feature weighted
  contribution (for debugging and analysis).

**Alpha-beta search (`search/alpha_beta.py`):**

- Negamax with alpha-beta pruning is the recommended implementation:
  ```
  negamax(board, depth, alpha, beta, color):
      if depth == 0 or board.is_terminal():
          return evaluate(board, color, agent)
      moves = generate_atomic_moves(board)
      if not moves:
          return LOSS_SCORE  # no legal moves = loss
      order moves (captures first)
      for move in moves:
          child = apply_atomic_move(board, move)
          score = -negamax(child, depth-1, -beta, -alpha, opponent)
          alpha = max(alpha, score)
          if alpha >= beta:
              break  # beta cutoff
      return alpha
  ```
- `choose_move`: Run the search at the configured depth and return the move
  with the best score.
- Track `nodes_searched` (number of positions evaluated) and
  `search_time_seconds` for performance monitoring.
- **Must always return a legal move if one exists.** If the search somehow
  fails to find a move, fall back to the first legal move.

#### Checkpoints

| ID  | Criterion                                                  |
|-----|------------------------------------------------------------|
| 3A  | 5 features generate exactly 31 agents                     |
| 3B  | All 31 agent names are unique                              |
| 3C  | Weights sum to 1.0 for every agent (within float epsilon)  |
| 3D  | `evaluate` returns a numeric float for non-terminal boards |
| 3E  | Alpha-beta returns a legal move at depth 1 and depth 2     |
| 3F  | `pytest tests/test_agents.py tests/test_alpha_beta.py`     |

---

### Area 4: Game Simulation + Tournament Harness

**Owner:** Developer 4

**Goal:** Build game simulation, random baseline agent, round-robin tournament,
result storage, and leaderboard computation.

**Files owned:**

```
simulation/game.py
simulation/random_agent.py
simulation/__init__.py
tournament/round_robin.py
tournament/leaderboard.py
tournament/results_io.py
tournament/__init__.py
tests/test_tournament.py
```

**Must not edit:** `core/`, `variants/`, `features/`, `agents/`, `search/`,
`analysis/`, `reports/`, `ui/`

**May import from:** `core`, `variants`, `agents`, `search`

#### Detailed Responsibilities

**Random agent (`simulation/random_agent.py`):**

```python
class RandomAgent:
    name: str = "RandomAgent"

    def choose_move(self, board: Board) -> Move:
        moves = generate_atomic_moves(board)
        return random.choice(moves)
```

**Game simulation (`simulation/game.py`):**

- Initialize board from `Board.starting_position()`.
- Alternate turns: white moves first.
- For `FeatureSubsetAgent`: create `AlphaBetaEngine(agent, depth)` and call
  `engine.choose_move(board)`.
- For `RandomAgent`: call `agent.choose_move(board)`.
- Apply moves with `apply_atomic_move(board, move)`.
- Terminate on: king explosion, no legal moves, or move cap.
- Track per-side average nodes searched and average time per move.
- Use the `seed` parameter to seed `random` for reproducibility.

**Round-robin (`tournament/round_robin.py`):**

- For every ordered pair `(A, B)` where `A != B`, play one game with `A` as
  white and `B` as black.
- For N agents: `N * (N - 1)` total games.
- Display progress with `tqdm`.
- **Seed propagation:** Generate per-game seeds deterministically from the
  tournament seed, e.g., `game_seed = tournament_seed + game_index`.

**Result I/O (`tournament/results_io.py`):**

- `save_results_json`: Serialize `list[GameResult]` to JSON.
- `load_results_json`: Deserialize from JSON.
- `save_results_csv`: Write flat CSV for external analysis.

**Leaderboard (`tournament/leaderboard.py`):**

- Scoring: win = 1.0, draw = 0.5, loss = 0.0.
- `score_rate = (wins + 0.5 * draws) / games_played`
- Sort descending by `score_rate`.
- Include agent's feature tuple for cross-referencing with analysis.

#### Checkpoints

| ID  | Criterion                                                  |
|-----|------------------------------------------------------------|
| 4A  | Random vs random game completes without crash              |
| 4B  | FeatureSubsetAgent vs FeatureSubsetAgent game completes    |
| 4C  | 3 agents produce 6 ordered games (3 * 2 = 6)              |
| 4D  | Leaderboard contains all agents with correct game counts   |
| 4E  | Results save to JSON and load back identically             |
| 4F  | `pytest tests/test_tournament.py` passes                   |

---

### Area 5: Analysis + Reporting + CLI + Optional UI

**Owner:** Developer 5

**Goal:** Analyze tournament results for feature importance, generate reports,
expose CLI commands, and optionally build a Streamlit dashboard.

**Files owned:**

```
analysis/feature_marginals.py
analysis/synergy.py
analysis/interpretation.py
analysis/__init__.py
reports/markdown_report.py
reports/__init__.py
main.py
ui/app.py
tests/test_analysis.py
```

**Must not edit:** `core/`, `variants/`, `features/`, `agents/`, `search/`,
`simulation/`, `tournament/`

**May import from:** all modules.

#### Detailed Responsibilities

**Feature marginals (`analysis/feature_marginals.py`):**

For each feature `f`:

```
avg_score_with    = mean score_rate of all agents that include f
avg_score_without = mean score_rate of all agents that exclude f
marginal          = avg_score_with - avg_score_without
top_k_frequency   = (# of top-k agents containing f) / k
```

**Pairwise synergy (`analysis/synergy.py`):**

For each pair `(a, b)`:

```
avg_with_both     = mean score_rate of agents containing both a and b
avg_with_a_only   = mean score_rate of agents containing a (with or without b)
avg_with_b_only   = mean score_rate of agents containing b (with or without a)
overall_avg       = mean score_rate of all agents

synergy(a, b)     = avg_with_both - avg_with_a_only - avg_with_b_only + overall_avg
```

This is the standard two-way interaction term from factorial experimental
design (see References, Section 15).

**Interpretation (`analysis/interpretation.py`):**

Generate a natural-language paragraph summarizing:
- Which features contribute most to winning.
- Which feature pairs are synergistic.
- What this implies about the variant's strategic character.

**Markdown report (`reports/markdown_report.py`):**

Report sections:
1. Title and date
2. Executive summary
3. Variant description
4. Feature library (names + descriptions)
5. Tournament configuration (depth, max_moves, agent count, game count)
6. Top-10 leaderboard table
7. Best discovered feature subset
8. Feature contribution analysis table
9. Top pairwise synergies table
10. Interpretation paragraph
11. Limitations section

**CLI (`main.py`):**

Use Typer. Required commands:

```bash
# Play a random game and print the result
python main.py random-game --variant atomic

# Play a match between two specific feature sets
python main.py match --white material --black enemy_king_danger,capture_threats --depth 2

# Run full round-robin tournament
python main.py tournament --variant atomic --depth 2 --max-moves 80

# Analyze existing tournament results
python main.py analyze --input outputs/data/tournament_results_atomic.json

# Run the complete pipeline end-to-end
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

**Optional Streamlit UI (`ui/app.py`):**

Sections:
- Variant selector
- Feature selector checkboxes
- Depth and max-moves sliders
- Run tournament button
- Leaderboard table
- Feature contribution bar chart
- Synergy heatmap
- Report preview

#### Checkpoints

| ID  | Criterion                                                    |
|-----|--------------------------------------------------------------|
| 5A  | Feature marginals correct on synthetic leaderboard data      |
| 5B  | Synergy analysis correct on synthetic leaderboard data       |
| 5C  | Markdown report generates without error                      |
| 5D  | `python main.py --help` shows all commands                   |
| 5E  | `full-pipeline` calls all components end-to-end              |
| 5F  | `pytest tests/test_analysis.py` passes                       |

---

## 9. Parallel Development Workflow

### 9.1 Branch Strategy

Each developer works on a dedicated branch:

```
area-1-core-variant
area-2-features
area-3-agents-search
area-4-simulation-tournament
area-5-analysis-cli
```

All branches are created from `main` after the initial stub commit.

### 9.2 Stub-First Development

Before any area-specific work begins, create a single commit on `main` with
**stub files** for all shared interfaces. Every function and class listed in
Section 7 should exist as a stub that raises `NotImplementedError`:

```python
def generate_moves(board: Board) -> list[Move]:
    raise NotImplementedError
```

This allows all 5 areas to develop and test in parallel by importing from
stubs. Each area replaces stubs with real implementations as they develop.

### 9.3 Merge Order

The recommended merge order reflects the dependency graph:

```
Area 1 (core)  -->  Area 2 (features)  -->  Area 3 (agents/search)
                                                      |
                                                      v
                                            Area 4 (simulation/tournament)
                                                      |
                                                      v
                                            Area 5 (analysis/CLI)
```

However, with stubs, all areas can develop simultaneously. At integration
time, merge in dependency order and run cross-area integration tests.

### 9.4 Conflict Minimization Rules

1. **Own your folder.** Do not edit files in another area's folder.
2. **Do not change shared function signatures.** If a signature must change,
   update `docs/interfaces.md` first and notify all developers.
3. **Tests live with ownership.** Each developer writes tests for their area.
4. **Use imports, not duplication.** Area 5 must not reimplement tournament
   logic; it imports from tournament/.
5. **No global state.** Pass all configuration explicitly: variant, depth,
   max_moves, seed, feature_names, output_dir.
6. **Keep output formats stable.** `GameResult` and `LeaderboardRow` fields
   should not change after initial agreement.

---

## 10. Integration & Merge Plan

### Phase 1: Stub Foundation

Create stubs on `main`. All developers branch from this.

### Phase 2: Parallel Development

All 5 areas develop independently on their branches. Each area's tests use
stubs or mocks for dependencies.

### Phase 3: Integration (merge order)

1. Merge Area 1. Run `test_board.py`, `test_move_generation.py`, `test_atomic.py`.
2. Merge Area 2. Run all Area 1 tests + `test_features.py`.
3. Merge Area 3. Run all prior tests + `test_agents.py`, `test_alpha_beta.py`.
4. Merge Area 4. Run all prior tests + `test_tournament.py`.
5. Merge Area 5. Run all tests + `python main.py full-pipeline`.

### Phase 4: End-to-End Validation

Run the full pipeline:

```bash
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

Verify all outputs are generated.

---

## 11. Performance Budget

### Estimated Runtime (5 features, depth 2, max 80 moves)

| Metric            | Value              |
|-------------------|--------------------|
| Agents            | 31                 |
| Games             | 930                |
| Avg plies/game    | ~40-60 (atomic is decisive) |
| Nodes per move    | ~100-400 (depth 2 with alpha-beta pruning) |
| Time per game     | ~0.5-2 seconds     |
| **Total runtime** | **~8-30 minutes**  |

### Recommended Staged Approach

For initial development and debugging:

| Stage   | Features | Agents | Games | Est. Runtime |
|---------|----------|--------|-------|--------------|
| Debug   | 2        | 3      | 6     | < 10 sec     |
| Small   | 3        | 7      | 42    | ~30 sec      |
| Medium  | 4        | 15     | 210   | ~3-5 min     |
| **Full**| **5**    | **31** | **930** | **~10-30 min** |

Start at the Debug stage. Graduate to Full only after the pipeline is stable.

### Scaling Note

Adding features is exponential. Each additional feature doubles the number of
agents and roughly quadruples game count:

| Features | Agents | Games   |
|----------|--------|---------|
| 5        | 31     | 930     |
| 6        | 63     | 3,906   |
| 7        | 127    | 16,002  |
| 8        | 255    | 65,026  |

Do not exceed 5 features for the hackathon MVP. If more features are desired
post-MVP, sampling strategies would be needed.

---

## 12. MVP Acceptance Criteria

The project is complete when the following command:

```bash
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

produces **all** of the following:

1. **31 generated feature-subset agents** (one per nonempty subset of 5 features)
2. **930 tournament game results** (31 * 30 ordered pairs)
3. **Ranked leaderboard** sorted by score_rate
4. **Best feature subset** identified
5. **Feature marginal contribution table** (5 rows)
6. **Pairwise synergy table** (10 pairs)
7. **Natural-language interpretation** paragraph
8. **Markdown report** saved to `outputs/reports/atomic_strategy_report.md`
9. **All tests pass:** `pytest` exits with code 0

### Expected Terminal Output Structure

```
EngineLab: Interpretable Strategy Discovery for Chess Variants
==============================================================

Variant: Atomic Chess
Features: material, mobility, enemy_king_danger, own_king_safety, capture_threats

Generating feature-subset agents...
  Created 31 agents.

Running tournament (930 games, depth=2, max_moves=80)...
  [########################################] 100% (930/930)
  Tournament complete in X minutes.

Leaderboard (top 10):
  1. Agent_capture_threats__enemy_king_danger__own_king_safety  0.68
  2. ...

Feature Contributions:
  enemy_king_danger:  +0.17
  capture_threats:    +0.11
  own_king_safety:    +0.07
  mobility:           +0.01
  material:           -0.03

Top Synergies:
  enemy_king_danger + capture_threats:  +0.08
  ...

Interpretation:
  The tournament suggests that Atomic Chess rewards direct explosion
  pressure near the enemy king more than ordinary material advantage.
  ...

Report saved: outputs/reports/atomic_strategy_report.md
```

---

## 13. Hackathon Execution Strategy

### Hour-by-Hour Plan (for a ~12-hour hackathon)

| Hours  | Activity                                                     |
|--------|--------------------------------------------------------------|
| 0-0.5  | Set up repo, create stubs, branch per area                   |
| 0.5-3  | Parallel development: each area implements core logic        |
| 3-4    | Checkpoint: run per-area tests, fix failures                 |
| 4-5    | Begin integration: merge Areas 1-2, resolve issues           |
| 5-6    | Continue integration: merge Areas 3-4                        |
| 6-7    | Merge Area 5, run end-to-end pipeline                        |
| 7-8    | Debug integration issues, run full tournament                |
| 8-9    | Polish output: improve report, add charts                    |
| 9-10   | Optional: build Streamlit UI                                 |
| 10-11  | Prepare presentation, rehearse demo                          |
| 11-12  | Final testing, buffer time for fixes                         |

### Priority Stack (if time is limited)

1. **Must have:** Working `full-pipeline` command producing report
2. **Should have:** Clean leaderboard + marginals output in terminal
3. **Nice to have:** Synergy analysis, charts, interpretation paragraph
4. **Stretch:** Streamlit UI

### Demo Tips

- Run with 3 features (7 agents, 42 games) for a live demo -- finishes in
  under a minute.
- Have pre-computed 5-feature results ready to show.
- Lead with the factor-analysis analogy when presenting to Point 72 judges.
- Show the Markdown report as the polished deliverable.

---

## 14. Known Limitations & Future Work

### MVP Limitations

1. **No check enforcement:** Engines can ignore check. This may produce some
   unrealistic positions but does not break the analysis pipeline.
2. **No castling or en passant:** Simplified move generation omits these
   standard chess rules.
3. **Equal weights only:** The system discovers which features matter but not
   optimal weighting. A future extension could apply weight optimization.
4. **Single game per ordered pair:** With 930 games across 31 agents, there
   are 2 games per unordered pair (one per color). More games would increase
   statistical power.
5. **Depth 2 search:** Very shallow. Depth 3-4 would produce higher-quality
   play but at significantly increased runtime.
6. **Python performance:** Pure Python limits search speed. For deeper search,
   a compiled engine (Rust, C++) would be needed.
7. **Atomic-only:** The system currently supports only Atomic Chess. The
   variant abstraction (`variants/base.py`) is designed for extension.

### Future Extensions

- Support for additional variants (Crazyhouse, King of the Hill, Horde)
- Weight optimization via Bayesian methods or gradient-free search
- Statistical significance testing (e.g., binomial confidence intervals on
  win rates, Elo rating computation)
- Deeper search with iterative deepening
- Opening book avoidance (randomized first N moves)
- Parallel game execution (multiprocessing)
- Web-based interactive UI

---

## 15. References

1. **Shannon, C. E.** (1950). "Programming a Computer for Playing Chess."
   *Philosophical Magazine*, 41(314). -- Foundation for evaluation-function
   design in game-playing programs.

2. **Knuth, D. E. & Moore, R. W.** (1975). "An Analysis of Alpha-Beta
   Pruning." *Artificial Intelligence*, 6(4), 293-326. -- Theoretical
   analysis of alpha-beta search efficiency.

3. **Kohavi, R. & John, G. H.** (1997). "Wrappers for Feature Subset
   Selection." *Artificial Intelligence*, 97(1-2), 273-324. -- Exhaustive
   feature subset evaluation methodology.

4. **Montgomery, D. C.** (2017). *Design and Analysis of Experiments* (9th
   ed.). Wiley. -- Factorial experimental design, interaction terms, and
   ANOVA; basis for the synergy formula.

5. **Shapley, L. S.** (1953). "A Value for n-Person Games." In *Contributions
   to the Theory of Games II*, Annals of Mathematics Studies, 28, 307-317.
   -- Shapley values as a principled approach to feature attribution.

6. **Fama, E. F. & French, K. R.** (1993). "Common Risk Factors in the
   Returns on Stocks and Bonds." *Journal of Financial Economics*, 33(1),
   3-56. -- Factor model methodology that EngineLab's approach parallels.

7. **Lichess.org.** "Atomic Chess Rules."
   https://lichess.org/variant/atomic -- Definitive reference for Atomic
   Chess rules and edge cases.
