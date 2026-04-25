# Development Workflow

This document describes the parallel development process for EngineLab.
It covers branching, stub-based decoupling, testing conventions, and
integration procedures.

---

## 1. Parallel Development via Stubs

### Rationale

EngineLab has a linear dependency chain:

```
Core -> Features -> Agents/Search -> Simulation/Tournament -> Analysis/CLI
```

Naive sequential development would waste 80% of the team's capacity. Instead,
we use **stub-based decoupling**: all shared interfaces are implemented as
`NotImplementedError` stubs on `main` before any area branches. Each developer
imports from stubs and replaces them with real implementations independently.

This is an application of the **Dependency Inversion Principle** (Martin, 2000)
and mirrors the **Contract-First Development** pattern common in distributed
systems engineering (Fowler, 2002).

### Stub Structure

Every function/class in `docs/interfaces.md` gets a stub. Example:

```python
# core/move_generation.py (stub)
from core.board import Board
from core.move import Move

def generate_moves(board: Board) -> list[Move]:
    raise NotImplementedError("Stub: implement in Area 1")

def generate_moves_for_color(board: Board, color: str) -> list[Move]:
    raise NotImplementedError("Stub: implement in Area 1")
```

Stubs must:
- Have correct function signatures (name, parameters, return type annotation)
- Import correctly (so downstream code can `from core.move_generation import generate_moves`)
- Raise `NotImplementedError` with a message identifying the owning area

### Stub Commit

The stub commit is the **first commit after repo setup** and should contain:
- All `__init__.py` files
- All stub modules for Sections 2-20 of `docs/interfaces.md`
- A minimal `requirements.txt`
- An empty `outputs/` directory with `.gitkeep` files

---

## 2. Branching Strategy

### Branch Naming

```
main                          # stubs + merged implementations
area-1-core-variant           # Developer 1
area-2-features               # Developer 2
area-3-agents-search          # Developer 3
area-4-simulation-tournament  # Developer 4
area-5-analysis-cli           # Developer 5
```

### Branch Lifecycle

1. All branches are created from `main` after the stub commit.
2. Each developer works exclusively on their branch.
3. When an area is complete and tests pass, it is merged to `main` in
   dependency order (see Section 4).
4. After Area 1 merges, Areas 2-5 should rebase onto the updated `main` to
   pick up real implementations. Repeat as each area merges.

### File Ownership

Each developer may only modify files in their area. See
`docs/agent_definitions.md` for per-area file ownership lists.

**Exception:** All developers may read/import from any module. They must not
write to modules outside their area.

---

## 3. Testing Conventions

### Test Structure

Each area has its own test file(s) in `tests/`. Developers write tests for
their own area only.

### Testing with Stubs

Areas that depend on unimplemented upstream areas should use one of:

1. **Fixture-based mocking:** Create pytest fixtures that return known board
   states, feature values, or game results. This lets you test your logic
   without real upstream implementations.

2. **Synthetic data:** For analysis (Area 5), create fake `LeaderboardRow`
   lists with known statistical properties to validate marginal/synergy
   calculations.

3. **Skip on NotImplementedError:** Use `pytest.importorskip` or
   `pytest.mark.skipif` for tests that require real upstream implementations.
   These tests will automatically activate once the dependency merges.

Example fixture for Area 3 (testing evaluation without real features):

```python
@pytest.fixture
def mock_board():
    board = Board.starting_position()
    # Set up a known position...
    return board
```

### Test Naming

```
tests/test_board.py                # Area 1
tests/test_move_generation.py      # Area 1
tests/test_atomic.py               # Area 1
tests/test_features.py             # Area 2
tests/test_agents.py               # Area 3
tests/test_alpha_beta.py           # Area 3
tests/test_tournament.py           # Area 4
tests/test_analysis.py             # Area 5
```

### Running Tests

```bash
# Run all tests
pytest

# Run a specific area
pytest tests/test_board.py tests/test_move_generation.py tests/test_atomic.py

# Run with verbose output
pytest -v

# Run with stdout visible (useful for debugging)
pytest -s
```

---

## 4. Integration Procedure

### Merge Order

```
1. Area 1: Core + Atomic      (no dependencies)
2. Area 2: Features            (depends on Area 1)
3. Area 3: Agents + Search     (depends on Areas 1 + 2)
4. Area 4: Simulation + Tourney (depends on Areas 1 + 3)
5. Area 5: Analysis + CLI      (depends on Areas 1-4)
```

### Per-Merge Checklist

Before merging Area N:

- [ ] All Area N tests pass on the area branch
- [ ] Rebase area branch onto latest `main`
- [ ] Resolve any conflicts (should be minimal due to file ownership)
- [ ] Run all previously-merged tests to check for regressions
- [ ] Merge to `main`
- [ ] Tag: `git tag area-N-merged`

### Post-Integration Test Sequence

After all 5 areas are merged:

```bash
# 1. All unit tests
pytest

# 2. Quick smoke test (2 features, 3 agents, 6 games)
python main.py full-pipeline --variant atomic --depth 1 --max-moves 20

# 3. Medium test (4 features, 15 agents, 210 games)
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80

# 4. Full test (5 features, 31 agents, 930 games)
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

---

## 5. Communication Protocol

### Interface Change Requests

If a developer discovers that a shared interface needs to change:

1. **Do not change the signature unilaterally.**
2. Propose the change to the team with:
   - What needs to change
   - Why it needs to change
   - Which other areas are affected
3. If approved, update `docs/interfaces.md` first.
4. Then implement the change in the owning area.
5. Other areas update their code to match.

### Status Updates

Each developer should track their progress against the checkpoints listed in
`Instructions.MD` Section 8.

---

## 6. Code Quality Standards

### Style

- Python 3.11+ syntax (type unions with `|`, `tuple[str, ...]`)
- snake_case for functions and variables
- PascalCase for classes
- No unused imports
- No wildcard imports (`from x import *`)

### Docstrings

- Required on all public functions and classes
- One-line summary, then optionally a longer description
- Use Google-style docstrings:
  ```python
  def evaluate(board: Board, color: str, agent: FeatureSubsetAgent) -> float:
      """Evaluate a position from color's perspective.

      Args:
          board: Current board state.
          color: "w" or "b".
          agent: The feature-subset agent to use.

      Returns:
          Evaluation score. Positive = good for color.
      """
  ```

### Error Handling

- Functions should fail loudly on invalid input (let exceptions propagate).
- Do not silently return defaults for error cases.
- Edge cases to handle explicitly:
  - Missing king -> return sentinel values in features, WIN/LOSS in evaluation
  - No legal moves -> terminate game, return appropriate GameResult
  - Empty feature list -> raise ValueError in agent generation

---

## 7. Academic Foundations

The development methodology in EngineLab draws on established practices:

### Contract-First Development

The stub-based approach follows the **Design by Contract** principle
(Meyer, 1992), where interfaces are specified before implementations.
This enables parallel development while preserving correctness at
integration boundaries.

> Meyer, B. (1992). "Applying Design by Contract."
> *IEEE Computer*, 25(10), 40-51.

### Factorial Experimental Design

The exhaustive feature-subset tournament is a **full factorial experiment**
(Montgomery, 2017) with binary factors (feature present/absent). The synergy
formula is the standard two-way interaction term from ANOVA.

> Montgomery, D. C. (2017). *Design and Analysis of Experiments* (9th ed.).
> Wiley.

### Feature Subset Selection

The exhaustive evaluation of all feature subsets follows the **wrapper method**
for feature selection (Kohavi & John, 1997), where a learning algorithm
(here, alpha-beta search + tournament) evaluates each subset's performance.

> Kohavi, R. & John, G. H. (1997). "Wrappers for Feature Subset Selection."
> *Artificial Intelligence*, 97(1-2), 273-324.

### Alpha-Beta Search

The search engine implements the alpha-beta algorithm, whose efficiency was
formally analyzed by Knuth and Moore (1975). The negamax formulation
simplifies implementation for two-player zero-sum games.

> Knuth, D. E. & Moore, R. W. (1975). "An Analysis of Alpha-Beta Pruning."
> *Artificial Intelligence*, 6(4), 293-326.
