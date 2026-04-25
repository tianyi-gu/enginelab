# Development Workflow

This document describes the parallel development process for EngineLab.
It covers branching, the Foundation-first approach, testing conventions,
and integration procedures.

---

## 1. Foundation-First Development

### Rationale

EngineLab has a dependency chain:

```
Core -> Features -> Agents/Search -> Simulation/Tournament -> Analysis/CLI
```

Instead of sequential development, we split the project into a **Foundation**
(built first on `main`) and **two parallel workstreams** that can develop
simultaneously with zero coordination.

### Foundation

Before any parallel work begins, build a complete, runnable standard chess
engine on `main`. This includes:

- Full Board class (with castling rights, en passant tracking)
- Complete pseudo-legal move generation (all piece types, castling, en passant,
  all promotion types)
- Check detection and legal move generation
- Standard chess variant with variant dispatch
- Material-only evaluation and basic alpha-beta at depth 1
- A working `play_game()` function
- Stub files for all remaining interfaces

Both developers branch from this commit.

### Stub Structure

Every function/class from `docs/interfaces.md` that is NOT part of the
Foundation gets a stub. Example:

```python
# features/material.py (stub)
from core.board import Board

def material(board: Board, color: str) -> float:
    raise NotImplementedError("Stub: implement in Area 1")
```

---

## 2. Branching Strategy

### Branch Naming

```
main                  # Foundation + merged implementations
area-1-engine         # Developer 1: variants, features, search
area-2-harness        # Developer 2: tournament, analysis, CLI
```

### Branch Lifecycle

1. Foundation is built and committed to `main`.
2. Both developers branch from `main`.
3. Each developer works exclusively on their branch.
4. At integration: Area 1 merges first, then Area 2 rebases and merges.

### File Ownership

Each developer may only modify files in their area. See
`docs/agent_definitions.md` for per-area file ownership lists.

**Exception:** All developers may read/import from any module. They must not
write to modules outside their area.

---

## 3. Zero-Dependency Workstream Split

```
Workstream ENGINE (Area 1)              Workstream HARNESS (Area 2)
================================        ================================
Atomic variant rules                    Tournament runner (round-robin)
Antichess variant rules (optional)      Leaderboard computation
10-feature evaluation library           Result I/O (JSON, CSV)
Feature registry                        Analysis (marginals, synergy)
Agent generation (exhaustive/sampled)   Report generation (Markdown)
Full evaluation function                CLI (Typer)
Production alpha-beta search            Optional Streamlit UI
      |                                        |
      +------ play_game() interface -----------+
              GameResult dataclass
```

**Why this works with zero dependencies:**

- **ENGINE** produces a working `play_game(white, black, variant, depth,
  max_moves, seed) -> GameResult` function. It has no knowledge of
  tournaments, leaderboards, or analysis.

- **HARNESS** consumes `GameResult` objects. During development, it uses a
  `mock_play_game()` that returns random results:

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

  This lets HARNESS develop and test its entire pipeline (tournament
  scheduling, leaderboard computation, analysis, reporting, CLI) with
  **zero imports from ENGINE**. At integration time, swap the mock for
  the real `play_game` -- one line change.

---

## 4. Testing Conventions

### Test Structure

Each area has its own test files in `tests/`. Developers write tests for
their own area only.

### Testing with Stubs and Mocks

- **Area 1 (ENGINE):** Tests use the Foundation's working Board and move
  generation. Set up known board positions as fixtures.

- **Area 2 (HARNESS):** Use `mock_play_game()` for tournament tests. Use
  synthetic `LeaderboardRow` lists for analysis tests. At integration time,
  tests automatically activate against real implementations.

### Test Files

```
tests/test_board.py                # Foundation / Area 1
tests/test_move_generation.py      # Foundation / Area 1
tests/test_standard.py             # Foundation / Area 1
tests/test_atomic.py               # Area 1
tests/test_antichess.py            # Area 1 (optional)
tests/test_features.py             # Area 1
tests/test_agents.py               # Area 1
tests/test_alpha_beta.py           # Area 1
tests/test_tournament.py           # Area 2
tests/test_analysis.py             # Area 2
```

### Running Tests

```bash
# Run all tests
pytest

# Run Foundation tests
pytest tests/test_board.py tests/test_move_generation.py tests/test_standard.py

# Run Area 1 tests
pytest tests/test_atomic.py tests/test_features.py tests/test_agents.py tests/test_alpha_beta.py

# Run Area 2 tests
pytest tests/test_tournament.py tests/test_analysis.py

# Run with verbose output
pytest -v
```

---

## 5. Integration Procedure

### Merge Order

```
1. Area 1: ENGINE (variants, features, agents, search)
2. Area 2: HARNESS (tournament, analysis, CLI) — after rebasing onto updated main
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

After both areas are merged:

```bash
# 1. All unit tests
pytest

# 2. Quick smoke test (2 features, 3 agents, 6 games)
python main.py full-pipeline --variant standard --depth 1 --max-moves 20

# 3. Medium test (5 features, 31 agents, 930 games)
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80

# 4. Full test (10 features, ~80 sampled agents)
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

---

## 6. Communication Protocol

### Interface Change Requests

If a developer discovers that a shared interface needs to change:

1. **Do not change the signature unilaterally.**
2. Propose the change to the team with:
   - What needs to change
   - Why it needs to change
   - Which other area is affected
3. If approved, update `docs/interfaces.md` first.
4. Then implement the change in the owning area.
5. The other area updates their code to match.

---

## 7. Code Quality Standards

### Style

- Python 3.11+ syntax (type unions with `|`, `tuple[str, ...]`)
- snake_case for functions and variables
- PascalCase for classes
- No unused imports
- No wildcard imports (`from x import *`)

### Docstrings

- Required on all public functions and classes
- One-line summary, then optionally a longer description
- Use Google-style docstrings

### Error Handling

- Functions should fail loudly on invalid input (let exceptions propagate).
- Do not silently return defaults for error cases.
- Edge cases to handle explicitly:
  - Missing king -> return sentinel values in features, WIN/LOSS in evaluation
  - No legal moves -> terminate game, return appropriate GameResult
  - Empty feature list -> raise ValueError in agent generation

---

## 8. Runtime Parallelism (Multiprocessing)

Beyond development parallelism, the tournament itself is embarrassingly
parallel at the game level. Each game is a pure function:

```
Input:  (white_agent, black_agent, variant, depth, max_moves, seed)
Output: GameResult
```

No shared state, no side effects. Use `multiprocessing.Pool` to run games
across CPU cores. With 4 workers, a large tournament completes ~4x faster.
Add a `--workers` CLI flag. Default to 1 (sequential) for determinism
debugging, then scale up for production runs.

---

## 9. Academic Foundations

### Contract-First Development

The Foundation-first approach follows the **Design by Contract** principle
(Meyer, 1992), where interfaces are specified before implementations.

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
for feature selection (Kohavi & John, 1997).

> Kohavi, R. & John, G. H. (1997). "Wrappers for Feature Subset Selection."
> *Artificial Intelligence*, 97(1-2), 273-324.

### Alpha-Beta Search

The search engine implements the alpha-beta algorithm (Knuth & Moore, 1975).
The negamax formulation simplifies implementation for two-player zero-sum
games.

> Knuth, D. E. & Moore, R. W. (1975). "An Analysis of Alpha-Beta Pruning."
> *Artificial Intelligence*, 6(4), 293-326.
