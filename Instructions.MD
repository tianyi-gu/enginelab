# EngineLab -- Feature-Subset Alpha-Beta Engine Lab for Chess Variants

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Core Mechanism](#2-core-mechanism)
3. [Technical Conventions & Standards](#3-technical-conventions--standards)
4. [Chess Variant System](#4-chess-variant-system)
5. [Technology Stack](#5-technology-stack)
6. [Repository Structure](#6-repository-structure)
7. [Shared Interface Specification](#7-shared-interface-specification)
8. [Development Area Specifications](#8-development-area-specifications)
9. [Parallel Development Workflow](#9-parallel-development-workflow)
10. [Integration & Merge Plan](#10-integration--merge-plan)
11. [Performance Budget](#11-performance-budget)
12. [Determinism Requirements](#12-determinism-requirements)
13. [MVP Acceptance Criteria](#13-mvp-acceptance-criteria)
14. [Hackathon Execution Strategy](#14-hackathon-execution-strategy)
15. [Known Limitations & Future Work](#15-known-limitations--future-work)
16. [References](#16-references)

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

- ~80-100 AI engines (stratified sample of feature subsets from 10 features)
- Thousands of tournament games (full round-robin, both colors)
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

## 4. Chess Variant System

EngineLab compares how strategic features perform across different chess
variants. Start with standard chess as the baseline, then add variants where
different strategies should dominate. The most compelling demo shows the
same five features producing **completely different marginal rankings** under
different rule sets.

### 4.1 Variant Progression (Build Order)

| Phase | Variant         | Key Mechanic                        | Expected Dominant Features     |
|-------|-----------------|-------------------------------------|--------------------------------|
| 1     | Standard Chess  | Normal captures, win by king capture| material, mobility             |
| 2     | Atomic Chess    | Explosion on capture                | king_danger, capture_threats   |
| 3*    | Antichess       | Must capture, lose pieces to win    | material (NEGATIVE), mobility  |

*Phase 3 is optional but produces the most dramatic analysis contrast.

**Build Phase 1 first.** Get the entire pipeline working end-to-end with
standard chess before adding any variants. This gives a validated baseline
and a working system to extend incrementally.

### 4.2 Variant Abstraction

Each variant provides two functions that the rest of the system calls:

```python
def apply_move(board: Board, move: Move) -> Board:
    """Apply a move under this variant's rules. Returns a new Board."""

def generate_legal_moves(board: Board) -> list[Move]:
    """Generate legal moves under this variant's rules."""
```

Everything else (features, agents, tournament, analysis) is variant-agnostic.
It calls `apply_move` and `generate_legal_moves` through a dispatch lookup:

```python
VARIANT_DISPATCH = {
    "standard": {
        "apply_move": apply_standard_move,
        "generate_legal_moves": generate_standard_moves,
    },
    "atomic": {
        "apply_move": apply_atomic_move,
        "generate_legal_moves": generate_atomic_moves,
    },
    "antichess": {
        "apply_move": apply_antichess_move,
        "generate_legal_moves": generate_antichess_moves,
    },
}
```

This keeps the variant system simple (no class hierarchy) while supporting
clean dispatch everywhere via `variant: str` parameters.

### 4.3 Complete Movement Rules

The foundation implements **all standard chess rules**. This is not a
simplified subset -- the engine must handle every legal chess position
correctly. Getting this right is the foundation that everything else
depends on.

#### Piece Movement

- **Pawn:** Single push, double push from starting rank, diagonal capture,
  en passant capture, promotion to queen/rook/bishop/knight.
- **Knight:** 8 possible L-shaped jumps.
- **Bishop:** Slide diagonally until blocked or capture.
- **Rook:** Slide orthogonally until blocked or capture.
- **Queen:** Combine bishop + rook movement.
- **King:** Single step in all 8 directions, plus castling.

#### Castling

Both kingside (O-O) and queenside (O-O-O) castling must be implemented.

Requirements for a legal castle:
1. King and the target rook have not previously moved.
2. No pieces between king and rook.
3. King is not currently in check.
4. King does not pass through a square attacked by an opponent piece.
5. King does not end on a square attacked by an opponent piece.

Board state must track castling rights:

```python
castling_rights: dict[str, bool]
# {"K": True, "Q": True, "k": True, "q": True}
# K/Q = white kingside/queenside, k/q = black kingside/queenside
```

Castling rights are lost when:
- The king moves (lose both sides for that color).
- A rook moves or is captured (lose that specific side).

#### En Passant

When a pawn advances two squares from its starting rank, the opponent may
capture it "in passing" on the very next move as if it had moved only one
square.

Board state must track the en passant target square:

```python
en_passant_square: Square | None
# Set to the square the capturing pawn would land on.
# Reset to None after each move unless a new double pawn push occurs.
```

#### Promotion

When a pawn reaches the last rank, it must promote. All four options must
be supported: queen, rook, bishop, knight. The `Move.promotion` field
specifies the target piece type (e.g., `"Q"`, `"R"`, `"B"`, `"N"` for
white; `"q"`, `"r"`, `"b"`, `"n"` for black).

#### Check and Legal Move Filtering

Move generation uses a two-step process:

1. Generate pseudo-legal moves (all moves ignoring check).
2. Filter: for each pseudo-legal move, apply it to a copy of the board.
   If the moving side's king is in check after the move, discard it.

This requires a helper:

```python
def is_square_attacked(board: Board, square: Square, by_color: str) -> bool:
    """Return True if any piece of by_color attacks the given square."""

def is_in_check(board: Board, color: str) -> bool:
    """Return True if color's king is attacked."""
```

#### Terminal Conditions (Standard Chess)

- **Checkmate:** Side to move is in check and has no legal moves. Opponent
  wins.
- **Stalemate:** Side to move is NOT in check but has no legal moves. Draw.
- **Move cap:** `board.move_count >= max_moves`. Draw.

**Not implemented** (acceptable simplification):
- Threefold repetition
- Fifty-move rule
- Insufficient material

### 4.4 Standard Chess Variant (Phase 1 -- Build First)

Standard chess is the foundation. It uses the complete movement rules above.

**Move application (`variants/standard.py`):**
- Move piece from start to end square.
- If destination has an enemy piece, remove it (standard capture).
- Handle en passant captures (remove the captured pawn from its actual square).
- Handle castling (move king + rook together, update castling rights).
- Handle pawn promotion.
- Update castling rights if king or rook moved or rook captured.
- Set `en_passant_square` if pawn double-pushed, else clear it.
- Toggle `side_to_move`, increment `move_count`.
- Check for checkmate/stalemate after the move.

**Legal move generation:**
- Pseudo-legal moves + check filtering (Section 4.3).
- Includes castling and en passant when legal.

**Terminal conditions:**
- Checkmate -- opponent wins.
- Stalemate -- draw.
- Move cap -- draw.

### 4.5 Atomic Chess Variant (Phase 2)

Atomic Chess extends standard chess with explosion mechanics on captures.

**Explosion mechanics:**

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

**Self-preservation rule (CRITICAL):**

A player may NOT make a capture that would destroy their own king in the
resulting explosion. If the capturing player's king is within Chebyshev
distance 1 of the capture square, the capture is illegal and must be
filtered out. This is the one legality filter that Atomic Chess MUST
implement.

**Terminal conditions:**
- King explosion (`find_king(color)` returns `None`) -- opponent wins.
- No legal moves (after filtering self-explosive captures) -- side to
  move loses.
- Move cap -- draw.

### 4.6 Antichess Variant (Phase 3 -- Optional)

Antichess (also called Losing Chess or Giveaway) inverts the objective:
the goal is to **lose all your pieces**. This is analytically valuable
because features like `material` should have **negative** marginal value
(less material = closer to winning), creating a dramatic contrast with
standard chess results.

**Move application:**
- Same as standard chess. No special capture mechanics.
- King has no special status -- it can be captured like any other piece.

**Legal move generation (forced capture rule):**

```python
def generate_antichess_moves(board: Board) -> list[Move]:
    all_moves = generate_moves(board)
    captures = [m for m in all_moves if board.get_piece(m.end) is not None]
    return captures if captures else all_moves
```

If any capture is available, the player MUST capture. This is the defining
rule of Antichess and is trivial to implement.

**Terminal conditions:**
- No pieces remaining -- that player **WINS** (they lost all pieces).
- No legal moves -- that player **WINS** (they are blocked).
- Move cap -- draw.

### 4.7 Variant-Specific Feature Behavior

Most features work identically across all variants:
`material`, `mobility`, `enemy_king_danger`, `king_safety`, etc.

The `capture_threats` feature is variant-aware:

| Variant   | capture_threats Computation                                     |
|-----------|-----------------------------------------------------------------|
| Standard  | Sum of capturable piece values                                  |
| Atomic    | Capturable values + 3x adjacent explosions + 100x king explosion|
| Antichess | Value of own pieces that opponent can capture (inverted logic)   |

The feature signature remains `(board, color) -> float` but the function
internally checks the variant. See Section 8 (Area 1) for implementation
details.

### 4.8 Check Legality Enforcement

All variants enforce check legality unless otherwise noted:

- **Standard Chess:** A move is legal only if it does not leave the moving
  side's king in check. Use the two-step approach: generate pseudo-legal
  moves, then filter out any that leave the king in check (see Section 4.3).
- **Atomic Chess:** The self-preservation rule (Section 4.5) applies in
  addition to standard check filtering. A move that would explode the
  moving side's own king is always illegal.
- **Antichess:** The king has no special status. Check is not enforced.
  All pseudo-legal moves are legal. If captures exist, only capture moves
  are legal (forced capture rule).

Helper functions required (see Section 7.4):

```python
def is_square_attacked(board: Board, square: Square, by_color: str) -> bool:
    """True if any piece of by_color attacks the given square."""

def is_in_check(board: Board, color: str) -> bool:
    """True if color's king is under attack."""

def generate_legal_moves(board: Board) -> list[Move]:
    """Pseudo-legal moves filtered by check legality."""
```

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
|-- main.py                          # CLI entry point (Area 2)
|
|-- core/                            # Foundation
|   |-- __init__.py
|   |-- types.py                     # Square type alias, color helpers
|   |-- board.py                     # Board class
|   |-- move.py                      # Move class
|   |-- coordinates.py               # Square/algebraic conversion helpers
|   |-- move_generation.py           # Pseudo-legal + legal move generation
|   `-- apply_move.py                # Standard move application
|
|-- variants/                        # Foundation + Area 1
|   |-- __init__.py
|   |-- base.py                      # Variant dispatch + shared helpers
|   |-- standard.py                  # Standard Chess (Foundation)
|   |-- atomic.py                    # Atomic Chess (Area 1)
|   `-- antichess.py                 # Antichess (Area 1, optional)
|
|-- features/                        # Area 1
|   |-- __init__.py
|   |-- registry.py                  # Feature registry and access functions
|   |-- material.py                  # Material balance
|   |-- piece_position.py            # Piece-square table bonus
|   |-- center_control.py            # Center square control
|   |-- king_safety.py               # Own king safety (defense)
|   |-- king_danger.py               # Pressure on opponent king
|   |-- mobility.py                  # Move count difference
|   |-- pawn_structure.py            # Pawn quality analysis
|   |-- bishop_pair.py               # Bishop pair bonus
|   |-- rook_activity.py             # Rook open file / 7th rank
|   `-- capture_threats.py           # Tactical capture/explosion threats
|
|-- agents/                          # Area 1
|   |-- __init__.py
|   |-- feature_subset_agent.py      # FeatureSubsetAgent dataclass
|   |-- generate_agents.py           # Exhaustive/sampled agent generation
|   `-- evaluation.py                # Position evaluation from features
|
|-- search/                          # Area 1
|   |-- __init__.py
|   `-- alpha_beta.py                # Alpha-beta search engine
|
|-- simulation/                      # Area 2
|   |-- __init__.py
|   |-- game.py                      # Single game simulation
|   `-- random_agent.py              # Random move baseline agent
|
|-- tournament/                      # Area 2
|   |-- __init__.py
|   |-- round_robin.py               # Round-robin tournament runner
|   |-- leaderboard.py               # Leaderboard computation
|   `-- results_io.py                # JSON/CSV save and load
|
|-- analysis/                        # Area 2
|   |-- __init__.py
|   |-- feature_marginals.py         # Marginal feature contribution
|   |-- synergy.py                   # Pairwise synergy analysis
|   `-- interpretation.py            # Natural-language interpretation
|
|-- reports/                         # Area 2
|   |-- __init__.py
|   `-- markdown_report.py           # Markdown report generator
|
|-- ui/                              # Area 2 (optional)
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
    |-- test_board.py                # Foundation
    |-- test_move_generation.py      # Foundation
    |-- test_standard.py             # Foundation
    |-- test_atomic.py               # Area 1
    |-- test_antichess.py            # Area 1 (optional)
    |-- test_features.py             # Area 1
    |-- test_agents.py               # Area 1
    |-- test_alpha_beta.py           # Area 1
    |-- test_tournament.py           # Area 2
    `-- test_analysis.py             # Area 2
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
    grid: list[list[str | None]]       # 8x8, FEN piece chars or None
    side_to_move: str                  # "w" or "b"
    winner: str | None                 # "w", "b", or None (draw uses "draw")
    move_count: int                    # incremented after each ply
    castling_rights: dict[str, bool]   # {"K": True, "Q": True, "k": True, "q": True}
    en_passant_square: Square | None   # target square for en passant, or None

    @staticmethod
    def starting_position() -> "Board": ...
        # All castling rights True, en_passant_square None.

    def copy(self) -> "Board": ...
        # Must deep-copy grid, castling_rights dict, and all fields.

    def get_piece(self, square: Square) -> str | None: ...

    def set_piece(self, square: Square, piece: str | None) -> None: ...

    def find_king(self, color: str) -> Square | None: ...

    def is_terminal(self) -> bool: ...
        # True if winner is set.

    def print_board(self) -> None: ...
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

```python
# Check detection and legal move generation

def is_square_attacked(board: Board, square: Square, by_color: str) -> bool:
    """True if any piece of by_color attacks the given square."""

def is_in_check(board: Board, color: str) -> bool:
    """True if color's king is under attack by the opponent."""

def generate_legal_moves(board: Board) -> list[Move]:
    """Pseudo-legal moves filtered to remove those that leave the
    moving side's king in check."""
```

Notes:
- `generate_moves` and `generate_moves_for_color` produce pseudo-legal moves
  (including castling and en passant). They do NOT filter for check legality.
- `generate_legal_moves` applies each pseudo-legal move, checks if the
  moving side's king is attacked, and filters accordingly.
- For Atomic Chess, the variant layer adds additional filtering (captures
  that would explode the moving side's own king -- see Section 4.5).
- **Move ordering must be deterministic** (see Section 12). Iterate pieces
  by row 0-7, col 0-7. For each piece, produce destination squares in a
  consistent order. This is required for alpha-beta reproducibility.

### 7.5 Variant Dispatch

```python
# variants/base.py

VARIANT_DISPATCH: dict[str, dict[str, Callable]]
# Maps variant name -> {"apply_move": fn, "generate_legal_moves": fn}

def get_apply_move(variant: str) -> Callable[[Board, Move], Board]: ...
def get_generate_legal_moves(variant: str) -> Callable[[Board], list[Move]]: ...
def get_supported_variants() -> list[str]: ...
```

### 7.6 Standard Chess Variant

```python
# variants/standard.py

def apply_standard_move(board: Board, move: Move) -> Board:
    """Apply a move under standard chess rules. Returns a new Board (does not
    mutate the input). Handles captures and pawn promotion. Sets board.winner
    if a king is captured."""
    ...

def generate_standard_moves(board: Board) -> list[Move]:
    """Generate legal moves under standard chess rules. For the MVP this is
    identical to generate_moves() (no check filtering)."""
    ...
```

### 7.7 Atomic Chess Variant

```python
# variants/atomic.py

def apply_atomic_move(board: Board, move: Move) -> Board:
    """Apply a move under Atomic Chess rules. Returns a new Board (does not
    mutate the input). Handles explosion on captures. Sets board.winner if
    a king is destroyed."""
    ...

def generate_atomic_moves(board: Board) -> list[Move]:
    """Generate legal moves under Atomic Chess rules. This calls
    generate_moves() and filters out captures that would explode the
    moving side's own king."""
    ...
```

### 7.8 Antichess Variant (Optional)

```python
# variants/antichess.py

def apply_antichess_move(board: Board, move: Move) -> Board:
    """Apply a move under Antichess rules. Same as standard move application.
    Sets board.winner if a player has no pieces left (that player wins)."""
    ...

def generate_antichess_moves(board: Board) -> list[Move]:
    """Generate legal moves under Antichess rules. If any captures exist,
    return only captures (forced capture rule). Otherwise return all moves."""
    ...
```

### 7.9 Features

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

### 7.10 Feature-Subset Agent

```python
# agents/feature_subset_agent.py
from dataclasses import dataclass

@dataclass(frozen=True)
class FeatureSubsetAgent:
    name: str                      # e.g. "Agent_material__mobility"
    features: tuple[str, ...]      # e.g. ("material", "mobility")
    weights: dict[str, float]      # e.g. {"material": 0.5, "mobility": 0.5}
```

### 7.11 Agent Generation

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

### 7.12 Evaluation

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

### 7.13 Alpha-Beta Engine

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

### 7.14 Game Result

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

### 7.15 Game Simulation

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

### 7.16 Round-Robin Tournament

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

### 7.17 Leaderboard

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

### 7.18 Result I/O

```python
# tournament/results_io.py

def save_results_json(results: list[GameResult], path: str) -> None: ...
def load_results_json(path: str) -> list[GameResult]: ...
def save_results_csv(results: list[GameResult], path: str) -> None: ...
```

### 7.19 Analysis

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

### 7.20 Reporting

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

EngineLab is split into a **shared foundation** (built first, committed to
`main`) and **two parallel development areas** that can be developed
simultaneously by two developers using AI coding agents.

### Foundation: Working Chess Engine (Built First)

**Goal:** Deliver a minimal but complete, runnable chess system on `main`
before any parallel work begins. Both developers branch from this.

**What it includes:**

1. Complete `Board` class with all fields (including `castling_rights`,
   `en_passant_square`).
2. Complete `Move` dataclass.
3. Full pseudo-legal move generation for all piece types (including castling,
   en passant, promotion to all pieces).
4. Check detection helpers: `is_square_attacked`, `is_in_check`.
5. Legal move generation (pseudo-legal filtered by check legality).
6. Standard chess variant (`variants/standard.py`): apply move, generate
   legal moves, winner detection on checkmate/stalemate.
7. Variant dispatch (`variants/base.py`) with `"standard"` registered.
8. A material-only evaluation function and trivial alpha-beta at depth 1.
9. A minimal `play_game()` function that can run standard chess games.
10. Stub files for all remaining interfaces (raise `NotImplementedError`).

**Files:**

```
core/types.py, core/board.py, core/move.py, core/coordinates.py
core/move_generation.py, core/apply_move.py, core/__init__.py
variants/base.py, variants/standard.py, variants/__init__.py
agents/feature_subset_agent.py, agents/evaluation.py, agents/__init__.py
search/alpha_beta.py, search/__init__.py
simulation/game.py, simulation/__init__.py
+ all __init__.py files and stubs for remaining modules
```

**Foundation acceptance test:**

```bash
# This must work before branching:
python -c "
from simulation.game import play_game
from agents.feature_subset_agent import FeatureSubsetAgent
a = FeatureSubsetAgent('Agent_material', ('material',), {'material': 1.0})
result = play_game(a, a, variant='standard', depth=1, max_moves=40, seed=42)
print(f'Game completed: {result.moves} moves, winner={result.winner}')
"
```

**Checkpoints:**

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 0A  | Board starting position correct, `copy()` is deep                |
| 0B  | Starting position generates exactly 20 white pseudo-legal moves  |
| 0C  | Castling generates correctly (kingside and queenside)            |
| 0D  | En passant capture works                                         |
| 0E  | Promotion to all 4 piece types works                             |
| 0F  | Legal move filter removes moves that leave king in check         |
| 0G  | Standard game completes (material-only eval, depth 1)            |
| 0H  | Variant dispatch resolves `"standard"` correctly                 |

---

### Area 1: Variants, Features & Search (Developer 1)

**Owner:** Developer 1

**Branch:** `area-1-engine`

**Goal:** Build the complete chess engine: all variant rules, the full
10-feature evaluation library, feature-subset agent generation, and
production alpha-beta search. This is the ENGINE workstream.

**Files owned:**

```
core/move_generation.py        # extend for variant-specific filtering
core/apply_move.py             # extend for variant-specific application
variants/atomic.py
variants/antichess.py
variants/standard.py           # extend if needed
variants/base.py               # register new variants
features/registry.py
features/material.py
features/piece_position.py
features/center_control.py
features/king_safety.py
features/king_danger.py
features/mobility.py
features/pawn_structure.py
features/bishop_pair.py
features/rook_activity.py
features/capture_threats.py
features/__init__.py
agents/feature_subset_agent.py # extend if needed
agents/generate_agents.py
agents/evaluation.py           # full weighted evaluation
agents/__init__.py
search/alpha_beta.py           # production depth search
search/__init__.py
tests/test_board.py
tests/test_move_generation.py
tests/test_standard.py
tests/test_atomic.py
tests/test_antichess.py
tests/test_features.py
tests/test_agents.py
tests/test_alpha_beta.py
```

**Must not edit:** `simulation/`, `tournament/`, `analysis/`, `reports/`,
`ui/`, `main.py`

#### Detailed Responsibilities

##### Phase 1: Atomic Chess Variant

**Atomic variant (`variants/atomic.py`):**

- `apply_atomic_move(board, move)`: Copy board, apply move, handle explosion
  if capture (remove capturing piece, captured piece, and all adjacent
  non-pawn pieces; pawns are immune to explosion), set winner if king
  destroyed, toggle `side_to_move`, increment `move_count`.
- `generate_atomic_moves(board)`: Call `generate_moves(board)`, filter out
  captures where the moving side's king is adjacent (Chebyshev distance <= 1)
  to the capture square (self-preservation rule).
- Register `"atomic"` in `VARIANT_DISPATCH`.

##### Phase 2: Full Feature Library

Implement all 10 features. Each feature has signature
`feature(board: Board, color: str) -> float` where positive = good for
`color`. No feature may mutate the board.

**Material features:**

1. **`material`**: Raw material difference using standard piece values
   (P=1, N=3, B=3, R=5, Q=9, K=0).

**Positional features:**

2. **`piece_position`**: Piece-square table bonus. Sum table values for own
   pieces minus opponent pieces. Use standard tables from chess programming
   literature (pawns prefer center/advanced ranks, knights prefer center,
   bishops prefer long diagonals, rooks prefer open files/7th rank, king
   prefers corners in middlegame).

3. **`center_control`**: Count own pieces/pawns on or attacking center
   squares (d4, d5, e4, e5) minus opponent's. Pieces on center squares
   count double.

**Safety features:**

4. **`king_safety`**: Own king defensive position. +1 per adjacent own pawn
   (shield), -1 per open/semi-open file adjacent to king, -0.5 per enemy
   piece within Chebyshev distance 3.

5. **`enemy_king_danger`**: Pressure on opponent's king. Per own piece:
   `+= 1.0 / max(chebyshev_distance, 1)`. Per adjacent enemy king square
   attacked: `+= 1.0`.

**Dynamic features:**

6. **`mobility`**: Legal move count difference (own - opponent).

7. **`pawn_structure`**: -0.5 per doubled pawn, -0.5 per isolated pawn,
   +1.0 per passed pawn, +0.3 per connected pawn.

8. **`bishop_pair`**: +0.5 if side has 2+ bishops, else 0.

9. **`rook_activity`**: +0.5 per rook on open file, +0.25 per rook on
   semi-open file, +0.5 per rook on 7th rank.

10. **`capture_threats`**: Value of available captures. Variant-aware
    (standard: sum of capturable piece values; atomic: + 3x adjacent
    explosions + 100x king explosion).

**Registry (`features/registry.py`):** Map all 10 feature names to functions
and descriptions via `FEATURES`, `FEATURE_DESCRIPTIONS`, `get_feature_names()`,
`get_feature_function()`, `get_feature_description()`.

##### Phase 3: Agent Generation & Evaluation

**Agent generation (`agents/generate_agents.py`):**

Dual-mode generation:

- **Exhaustive (n <= 6):** One agent per nonempty subset. `2^n - 1` agents.
- **Stratified sampling (n > 6):** All singles, all pairs, full set,
  plus random subsets of sizes 3 to n-1 up to `max_agents` (default 100).

Both modes use uniform weights: `weight = 1.0 / len(subset)`.
Agent names: features sorted alphabetically, joined with `__`, prefixed
with `Agent_`.

```python
def generate_feature_subset_agents(
    feature_names: list[str],
    max_agents: int = 100,
    seed: int = 42,
) -> list[FeatureSubsetAgent]:
    """Exhaustive if 2^n - 1 <= max_agents, else stratified sample."""
```

**Evaluation (`agents/evaluation.py`):**

- `evaluate(board, color, agent)`: Weighted sum of normalized features.
  Terminal positions return `WIN_SCORE` (+10000) or `LOSS_SCORE` (-10000).
- Normalization: `clip(x, -10, 10) / 10`.
- `contributions(board, color, agent)`: Per-feature weighted contribution.

##### Phase 4: Production Alpha-Beta Search

**Alpha-beta (`search/alpha_beta.py`):**

- Negamax with alpha-beta pruning.
- Move ordering: captures first (sorted by victim value descending).
- `choose_move(board) -> Move`: Must always return a legal move.
- Track `nodes_searched` and `search_time_seconds`.
- Variant-aware: use `get_apply_move(variant)` and
  `get_generate_legal_moves(variant)`.

##### Phase 5: Antichess (Optional)

- `apply_antichess_move`: Same as standard. Winner = player with no pieces.
- `generate_antichess_moves`: If captures exist, return only captures.
- Register `"antichess"` in `VARIANT_DISPATCH`.

#### Checkpoints

**Atomic Chess:**

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 1A  | Atomic explosion removes correct pieces, pawns survive           |
| 1B  | Self-preservation: captures that would explode own king filtered |
| 1C  | 100 random atomic plies without crash                            |

**Features:**

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 1D  | `material` at starting position returns 0.0 for both colors      |
| 1E  | All 10 feature functions return floats                            |
| 1F  | No feature mutates the board (verify with before/after copy)     |
| 1G  | `pawn_structure` detects doubled and passed pawns correctly      |

**Agents & Search:**

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 1H  | 5 features generate exactly 31 agents, all names unique          |
| 1I  | Weights sum to 1.0 for every agent (within float epsilon)        |
| 1J  | `evaluate` returns a numeric float for non-terminal boards       |
| 1K  | Alpha-beta returns a legal move at depth 1 and depth 2           |

**Antichess (optional):**

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 1L  | Forced capture rule works (only captures returned when available)|
| 1M  | Win condition: player with no pieces left wins                   |

---

### Area 2: Tournament, Analysis & CLI (Developer 2)

**Owner:** Developer 2

**Branch:** `area-2-harness`

**Goal:** Build the tournament infrastructure, statistical analysis,
reporting, and CLI. This is the HARNESS workstream. During development,
use `mock_play_game()` with random outcomes so that all tournament,
analysis, and reporting code can be built and tested with **zero imports
from the ENGINE** (Area 1). At integration time, swap the mock for the
real `play_game` -- a one-line change.

**Files owned:**

```
simulation/game.py             # play_game + mock_play_game
simulation/random_agent.py
simulation/__init__.py
tournament/round_robin.py
tournament/leaderboard.py
tournament/results_io.py
tournament/__init__.py
analysis/feature_marginals.py
analysis/synergy.py
analysis/interpretation.py
analysis/__init__.py
reports/markdown_report.py
reports/__init__.py
main.py
ui/app.py                     # optional Streamlit UI
tests/test_tournament.py
tests/test_analysis.py
```

**Must not edit:** `core/`, `variants/`, `features/`, `agents/`, `search/`

**May import from:** all modules (at integration time).

#### Detailed Responsibilities

##### Game Simulation (`simulation/game.py`)

**`play_game(white, black, variant, depth, max_moves, seed) -> GameResult`:**

- Initialize board from `Board.starting_position()`.
- Alternate turns: white moves first.
- For `FeatureSubsetAgent`: create `AlphaBetaEngine(agent, depth)` and call
  `engine.choose_move(board)`.
- For `RandomAgent`: call `agent.choose_move(board, variant)`.
- Apply moves with `get_apply_move(variant)(board, move)`.
- Terminate on: winner set, no legal moves, or move cap.
- Track per-side average nodes searched and time per move.
- Use `random.Random(seed)` for local seeded RNG (never `random.seed()`).

**`mock_play_game(white, black, **kwargs) -> GameResult`:**

For development before ENGINE integration:

```python
def mock_play_game(white, black, **kwargs) -> GameResult:
    rng = random.Random(kwargs.get("seed", 42))
    return GameResult(
        white_agent=white.name, black_agent=black.name,
        winner=rng.choice(["w", "b", None]),
        moves=rng.randint(10, 80),
        termination_reason="move_cap",
        white_avg_nodes=0, black_avg_nodes=0,
        white_avg_time=0, black_avg_time=0,
    )
```

**Random agent (`simulation/random_agent.py`):**

```python
class RandomAgent:
    name: str = "RandomAgent"
    def choose_move(self, board: Board, variant: str = "standard") -> Move:
        moves = get_generate_legal_moves(variant)(board)
        return random.choice(moves)
```

##### Round-Robin Tournament (`tournament/round_robin.py`)

- Every ordered pair `(A, B)` where `A != B`: A as white, B as black.
- N agents -> `N * (N - 1)` games.
- Progress bar with `tqdm`.
- Per-game seed: `tournament_seed + game_index`.
- **Optional multiprocessing:** Games are embarrassingly parallel:
  ```python
  from multiprocessing import Pool
  with Pool(workers) as pool:
      results = list(tqdm(pool.imap(run_single_game, game_args), total=n))
  ```
  Add `--workers` CLI flag. Default to 1 for determinism debugging.

##### Result I/O (`tournament/results_io.py`)

- `save_results_json`, `load_results_json`, `save_results_csv`.

##### Leaderboard (`tournament/leaderboard.py`)

- win = 1.0, draw = 0.5, loss = 0.0.
- `score_rate = (wins + 0.5 * draws) / games_played`.
- Sort descending by `score_rate`.

##### Feature Marginals (`analysis/feature_marginals.py`)

For each feature `f`:

```
avg_score_with    = mean score_rate of agents containing f
avg_score_without = mean score_rate of agents excluding f
marginal          = avg_score_with - avg_score_without
top_k_frequency   = (# of top-k agents containing f) / k
```

##### Pairwise Synergy (`analysis/synergy.py`)

```
synergy(a, b) = avg_with_both - avg_with_a - avg_with_b + overall_avg
```

This is the standard ANOVA two-way interaction term (see References,
Section 16).

##### Interpretation (`analysis/interpretation.py`)

Natural-language paragraph summarizing which features contribute most,
which pairs are synergistic, and what this implies about the variant.

##### Markdown Report (`reports/markdown_report.py`)

Sections: title, summary, variant, features, config, top-10 leaderboard,
best subset, marginals, synergies, interpretation, limitations.

##### CLI (`main.py`)

Use Typer. Required commands:

```bash
python main.py random-game --variant atomic
python main.py match --white material --black enemy_king_danger,capture_threats --depth 2
python main.py tournament --variant atomic --depth 2 --max-moves 80
python main.py analyze --input outputs/data/tournament_results_atomic.json
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

##### Optional Streamlit UI (`ui/app.py`)

Variant selector, feature checkboxes, depth/max-moves sliders, run button,
leaderboard table, feature contribution bar chart, synergy heatmap.

#### Checkpoints

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 2A  | Random vs random game completes (with mock or real play_game)    |
| 2B  | FeatureSubsetAgent vs FeatureSubsetAgent game completes          |
| 2C  | 3 agents produce 6 ordered games                                 |
| 2D  | Leaderboard contains all agents with correct game counts         |
| 2E  | Results save to JSON and load back identically                   |
| 2F  | Feature marginals correct on synthetic leaderboard data          |
| 2G  | Synergy analysis correct on synthetic leaderboard data           |
| 2H  | Markdown report generates without error                          |
| 2I  | `python main.py --help` shows all commands                       |
| 2J  | `full-pipeline` calls all components end-to-end                  |
| 2K  | `pytest tests/test_tournament.py tests/test_analysis.py` passes  |

---

## 9. Parallel Development Workflow

### 9.1 Branch Strategy

```
main                  # Foundation (working standard chess engine) + stubs
area-1-engine         # Developer 1: variants, features, search
area-2-harness        # Developer 2: tournament, analysis, reporting, CLI
```

Both branches are created from `main` after the Foundation is committed.

### 9.2 Foundation-First Development

Before branching, build the Foundation on `main` (see Section 8). This
gives both developers a working chess engine to build on. All remaining
interfaces are committed as stubs that raise `NotImplementedError`.

**Area 2 (HARNESS) uses `mock_play_game()`** during development so it has
zero dependency on Area 1's progress. This means both developers can work
in full parallel from the moment they branch.

### 9.3 Merge Order

```
Foundation (main)
    |
    +--- Area 1 (ENGINE) ---> merge to main first
    |
    +--- Area 2 (HARNESS) --> rebase onto main after Area 1, then merge
```

Area 1 merges first because Area 2's `play_game()` needs the real engine
at integration time. However, Area 2's analysis, reporting, and CLI code
is fully tested against mock data before integration.

### 9.4 Conflict Minimization Rules

1. **Own your files.** Do not edit files in the other area's file list.
2. **Do not change shared interface signatures.** If a signature must change,
   update `docs/interfaces.md` first and notify the other developer.
3. **Tests live with ownership.** Each developer writes tests for their area.
4. **No global state.** Pass all configuration explicitly: variant, depth,
   max_moves, seed, feature_names, output_dir.
5. **Keep output formats stable.** `GameResult` and `LeaderboardRow` fields
   should not change after initial agreement.

---

## 10. Integration & Merge Plan

### Phase 1: Foundation

Build and commit the Foundation on `main` (Section 8). Verify with the
Foundation acceptance test. Both developers branch from this commit.

### Phase 2: Parallel Development

- **Developer 1** (Area 1) builds variants, features, agents, and search
  on `area-1-engine`.
- **Developer 2** (Area 2) builds tournament, analysis, reporting, and CLI
  on `area-2-harness`, using `mock_play_game()` for all testing.

Both work simultaneously with zero coordination.

### Phase 3: Integration

1. Merge Area 1 to `main`. Run all Area 1 tests.
2. Rebase Area 2 onto `main`. Swap `mock_play_game` for real `play_game`.
3. Merge Area 2 to `main`. Run all tests.

### Phase 4: End-to-End Validation

```bash
# Standard chess
python main.py full-pipeline --variant standard --depth 2 --max-moves 80

# Atomic chess
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

Verify all outputs are generated and cross-variant comparison shows
different feature rankings.

---

## 11. Performance Budget

### Estimated Runtime (depth 2, max 80 moves)

With stratified sampling for 10 features (see Section 8, Area 1, Phase 3):

| Metric            | Value (exhaustive, 5 feat) | Value (sampled, 10 feat) |
|-------------------|---------------------------|--------------------------|
| Agents            | 31                        | ~80-100                  |
| Games             | 930                       | ~6,300-9,900             |
| Avg plies/game    | ~40-60                    | ~40-60                   |
| Nodes per move    | ~100-400                  | ~100-400                 |
| Time per game     | ~0.5-2 sec                | ~0.5-2 sec               |
| **Total runtime** | **~8-30 min**             | **~1-3 hours**           |
| With 4 workers    | ~2-8 min                  | ~15-45 min               |

### Recommended Staged Approach

| Stage      | Features | Mode       | Agents | Games  | Est. Runtime |
|------------|----------|------------|--------|--------|--------------|
| Debug      | 2        | exhaustive | 3      | 6      | < 10 sec     |
| Small      | 3        | exhaustive | 7      | 42     | ~30 sec      |
| Medium     | 5        | exhaustive | 31     | 930    | ~10-30 min   |
| **Full**   | **10**   | **sampled**| **~80**| **~6K**| **~1-3 hr**  |

Start at the Debug stage. Graduate to Full only after the pipeline is stable.
Use `--workers 4` to parallelize tournament games for production runs.

### Scaling Note

Exhaustive subset enumeration is exponential. Stratified sampling makes
larger feature sets tractable:

| Features | Exhaustive Agents | Sampled Agents (max_agents=100) |
|----------|-------------------|---------------------------------|
| 5        | 31                | 31 (exhaustive, under limit)    |
| 6        | 63                | 63 (exhaustive, under limit)    |
| 7        | 127               | ~80 (sampled)                   |
| 10       | 1,023             | ~80-100 (sampled)               |

The `max_agents` parameter controls the sampling budget. The stratified
approach guarantees coverage of all single-feature and pairwise effects
while sampling larger subsets uniformly.

---

## 12. Determinism Requirements

EngineLab must be fully deterministic: given the same inputs, it must produce
the same outputs every time. This is a hard requirement, not a nice-to-have.

### Why Determinism Matters

- **Reproducibility:** Results must be independently verifiable. If a reviewer
  runs the same pipeline, they must get identical results.
- **Debugging:** Non-deterministic bugs are the hardest to diagnose. During a
  hackathon, there is no time for flaky behavior.
- **Credibility:** A system that produces different "strategic insights" on
  each run undermines trust in the analysis.

### Determinism Contract

Given identical values for `variant`, `feature_names`, `depth`, `max_moves`,
and `seed`, the system MUST produce identical:

1. Agent list (same names, features, weights, same ordering)
2. Game results (same moves played, same outcomes)
3. Leaderboard (same rankings, same scores)
4. Analysis (same marginals, same synergies)
5. Report (same content)

### Implementation Requirements

**Move generation order must be deterministic.** This is the most subtle
requirement. Alpha-beta search with pruning produces different results if
moves are explored in different orders. Move generation must iterate pieces
in a fixed order (row 0-7, col 0-7) and for each piece produce destination
moves in a fixed order (e.g., row 0-7, col 0-7). The exact ordering does
not matter as long as it is consistent across runs.

**Random agent uses seeded RNG.** The `play_game` function receives a `seed`
parameter. Use `random.Random(seed)` to create a local RNG instance (do NOT
call `random.seed()` on the global RNG, as that creates hidden coupling
between games). Pass this local RNG to the `RandomAgent`.

**Tournament seed propagation.** The round-robin `seed` parameter produces
per-game seeds via `game_seed = tournament_seed + game_index`. Game ordering
must also be deterministic (iterate white agents in list order, then black
agents in list order).

**No floating-point non-determinism.** Avoid operations whose results depend
on execution order (e.g., summing a set of floats). Always iterate in
deterministic order (sorted lists, not sets or dict iteration on pre-3.7
Python). Python 3.7+ guarantees dict insertion order, so this is safe for
dicts created in deterministic order.

**Agent name generation is deterministic.** Features in the name are sorted
alphabetically. The power-set generation must also produce subsets in a
deterministic order (e.g., `itertools.combinations` is deterministic given
a deterministic input list).

---

## 13. MVP Acceptance Criteria

The project is complete when the following commands both succeed:

```bash
# Phase 1: Standard chess (must work first)
python main.py full-pipeline --variant standard --depth 2 --max-moves 80

# Phase 2: Atomic chess
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

Each pipeline run produces **all** of the following:

1. **Feature-subset agents** (stratified sample from 10 features, or exhaustive for fewer)
2. **Tournament game results** (full round-robin, all ordered pairs)
3. **Ranked leaderboard** sorted by score_rate
4. **Best feature subset** identified
5. **Feature marginal contribution table** (one row per feature)
6. **Pairwise synergy table** (one row per feature pair)
7. **Natural-language interpretation** paragraph
8. **Markdown report** saved to `outputs/reports/{variant}_strategy_report.md`
9. **All tests pass:** `pytest` exits with code 0
10. **Cross-variant comparison:** Running both variants shows different
    feature rankings (material dominant in standard, king_danger dominant
    in atomic). This contrast IS the core deliverable.

### Expected Terminal Output Structure

```
EngineLab: Interpretable Strategy Discovery for Chess Variants
==============================================================

Variant: Atomic Chess
Features: material, piece_position, center_control, king_safety, enemy_king_danger,
          mobility, pawn_structure, bishop_pair, rook_activity, capture_threats

Generating feature-subset agents...
  Created 87 agents (stratified sample from 1023 possible subsets).

Running tournament (7482 games, depth=2, max_moves=80, workers=4)...
  [########################################] 100% (7482/7482)
  Tournament complete in X minutes.

Leaderboard (top 10):
  1. Agent_capture_threats__enemy_king_danger__king_safety  0.68
  2. ...

Feature Contributions:
  enemy_king_danger:  +0.17
  capture_threats:    +0.11
  king_safety:        +0.07
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

## 14. Hackathon Execution Strategy

### Hour-by-Hour Plan (for a ~12-hour hackathon, 2 developers)

| Hours  | Developer 1 (ENGINE)                  | Developer 2 (HARNESS)                |
|--------|---------------------------------------|--------------------------------------|
| 0-1    | Build Foundation on `main` together   | Build Foundation on `main` together  |
| 1-1.5  | Branch `area-1-engine`                | Branch `area-2-harness`              |
| 1.5-3  | Atomic variant + first features       | Tournament + leaderboard (mock data) |
| 3-4    | Complete feature library (10 feat)    | Analysis + synergy + marginals       |
| 4-5    | Agent generation + evaluation         | Report generation + CLI              |
| 5-6    | Production alpha-beta search          | Polish CLI, add multiprocessing      |
| 6-7    | Run per-area tests, fix failures      | Run per-area tests, fix failures     |
| 7-8    | Merge Area 1 to main                  | Rebase, swap mock, merge Area 2      |
| 8-9    | Integration debugging, full pipeline  | Integration debugging, full pipeline |
| 9-10   | Optional: Antichess variant           | Optional: Streamlit UI               |
| 10-11  | Prepare presentation, rehearse demo   | Prepare presentation, rehearse demo  |
| 11-12  | Final testing, buffer for fixes       | Final testing, buffer for fixes      |

### Priority Stack (if time is limited)

1. **Must have:** Working `full-pipeline` command producing report
2. **Should have:** Clean leaderboard + marginals output in terminal
3. **Nice to have:** Synergy analysis, charts, interpretation paragraph
4. **Stretch:** Streamlit UI

### Demo Tips

- Run with 3 features (7 agents, 42 games) for a live demo -- finishes in
  under a minute.
- Have pre-computed 10-feature results ready to show.
- Lead with the factor-analysis analogy when presenting to Point 72 judges.
- Show the Markdown report as the polished deliverable.

---

## 15. Known Limitations & Future Work

### MVP Limitations

1. **Equal weights only:** The system discovers which features matter but not
   optimal weighting. A future extension could apply weight optimization.
2. **Single game per ordered pair:** More games per matchup would increase
   statistical power and reduce variance.
3. **Depth 2 search:** Very shallow. Depth 3-4 would produce higher-quality
   play but at significantly increased runtime.
4. **Python performance:** Pure Python limits search speed. For deeper search,
   a compiled engine (Rust, C++) would be needed.
5. **No draw detection:** The system does not detect threefold repetition or
   the 50-move rule. Games terminate only on king capture/explosion, no
   legal moves, or move cap.

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

## 16. References

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
