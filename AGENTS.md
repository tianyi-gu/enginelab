# AGENTS.md

Defines *how* you operate on this project. The *what* comes from the task prompt. When they conflict, ask first.

---

## Spec & control environment

Before any implementation:

- If `SPEC.md` exists, read it fully. It supersedes everything here on *what* to build.
- If no spec exists, stop and prompt the human to define requirements first.
- Treat spec changes like shared interface changes: require explicit human approval.
- The spec is the single source of truth for behavior, interfaces, and acceptance criteria.

---

## Repo organization

```
project-root/
├── AGENTS.md          # Agent rules (this file)
├── NOTES.md           # Living log of decisions and problems
├── README.md          # Project overview
├── SPEC.md            # Requirements & acceptance criteria (create before coding)
├── .gitignore
├── src/               # All source code
│   └── <module>/
├── tests/             # Mirrors src/ structure exactly
├── docs/              # Interfaces, diagrams, ADRs
│   └── interfaces.md
└── scripts/           # One-off scripts; not part of the importable module
```

Rules:
- No source files at the repo root.
- `tests/` mirrors `src/` — `src/foo/bar.py` → `tests/foo/test_bar.py`.
- `scripts/` is for throwaway or run-once code; don't import from it.
- Data files, model weights, and large binaries go in `.gitignore`, not the repo.

---

## Operating principles

- **Plan before coding.** Output 3–6 bullets: files to touch, what to write, what to test. No code in the plan.
- **Tests first.** Write a failing test, confirm it fails for the right reason, then implement.
- **Smallest change that works.** No premature abstractions, no refactoring adjacent code.
- **Fail loudly.** Raise specific exceptions. Never swallow errors or return defaults to hide failure.
- **Pure by default.** Don't mutate inputs unless the function name says so (`apply_`*, `update_*`).
- **No global mutable state.** Pass config through arguments.
- **Deterministic by default.** Seed all RNGs. Use fixed model params. Same spec should produce the same engine.

---

## Context & token discipline

- Read files minimally — prefer targeted line-range reads over whole-file reads.
- When subtasks are independent, batch them in parallel rather than sequentially.
- Don't hold raw file contents in context longer than needed; summarize and discard.
- Cache expensive results (API calls, heavy computation) rather than recomputing.
- Prefer incremental output over large monolithic generations — easier to catch errors early.

---

## Parallelization & worktrees

- Cap concurrent agents at **2–3 per task area**. Beyond that, coordination overhead outweighs the gain.
- Each agent gets a self-contained task with no shared mutable files. Coordinate through commits, not in-flight edits.
- For competing implementations (exploring approaches), use git worktrees:
  ```
  git worktree add ../project-v2 -b attempt/v2
  ```
  Each agent works in isolation. Compare by running the shared test suite against each branch. A human picks the winner; losing branches are deleted.
- Don't over-engineer handoffs — simple file outputs and commit messages are enough coordination.

---

## Human checkpoints

Proactively pause and check in at:

1. **After planning, before any code** — confirm the plan matches intent.
2. **After first passing implementation** — before adversarial review and commit.
3. **Before merging a worktree branch** — human picks the winner.

These are scheduled stops, separate from the "stuck" protocol. Don't wait for failure to check in.

---

## When stuck

Stop after **3 failed attempts** on the same problem. Output:

1. What I'm trying to do
2. What I tried (brief bullets)
3. Exact error or unexpected behavior
4. Best current hypothesis

Wait for input. Don't silently change scope, interface, or approach.

---

## Self-review (before declaring done)

After non-trivial work, switch to adversary mode:

- What inputs crash this? Boundaries: empty, single element, max size, wrong type.
- What invariants are assumed but not validated?
- What's the most obvious bug a reviewer would catch?
- **Pen-test:** actively attempt to break the code as an adversary, not just a clumsy user.

Add ≥2 adversarial test cases per non-trivial function.

---

## Definition of done

- Code implemented and tests pass
- Adversarial tests written and passing
- Type hints on all public functions
- Committed with a conventional message
- `NOTES.md` updated with a one-paragraph task summary
- Task prompt re-read; every requirement confirmed met

"Looks right" or "should work" is not done.

---

## Coding style

### Python

- Python 3.11+. Type hints on every public function.
- No `from x import `*.
- Functions > 60 lines: split.
- Imports: stdlib → third-party → local, blank line between groups.
- `dataclass(frozen=True)` for immutable data containers; `pydantic` for data crossing external boundaries (file, network, API).
- `pathlib.Path` over `os.path`. F-strings only — no `%` or `.format()`.
- `pytest` for all tests.

### Naming

- `snake_case` functions/variables, `PascalCase` classes, `SCREAMING_SNAKE_CASE` module constants.
- Booleans/predicates: `is_`, `has_`, `should_`, `can_`.
- No abbreviations except well-known domain terms (`id`, `url`, `api`).
- Tests: `test_<thing>_<condition>_<expected>`.

### Errors

- Raise specific exception types. Include the bad value: `f"Invalid color {color!r}, expected 'w' or 'b'"`.
- Validate at external boundaries; trust internal callers.
- Never bare `except:` or `except Exception:` without re-raising or logging the full traceback.

### Tests

- One concept per test. `and` in the name → split it.
- Arrange–act–assert, blank lines between sections.
- `pytest.parametrize` for multiple cases of the same logic.
- Deterministic: seed any RNG. Independent: no shared mutable fixtures.
- > 5 lines of setup usually means the code is too coupled.

---

## Git workflow

- Branch per feature. Commit only when tests pass.
- Conventional commits: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`. Optional scope: `feat(search): add quiescence`.
- Messages: *what changed and why* — the diff shows how.
- Never force-push `main`. Never commit secrets, keys, large data files, or `__pycache__`.

---

## Interface stability

Shared interfaces (function signatures, dataclasses, file formats) are locked. Changing one requires explicit human approval. If your code doesn't fit the interface, change your code.

When inventing a new interface: design it once at the start, document it at the top of the file or in `docs/interfaces.md`, and hold it.

---

## Output discipline

- No decorative banners or emoji unless asked.
- One progress bar per long-running operation, not per-item logs.
- Outputs go to the path specified in the task prompt.

---

## Never do without asking

- Change a shared interface or spec
- Add a new top-level dependency
- Force-push a shared branch
- Delete files you didn't create this session
- Touch another track's tests
- Expand scope beyond the task prompt
- Spend > 30 min on a single failing test

---

## Task workflow

1. Read `SPEC.md` (if it exists), then the task prompt. Re-read both.
2. **Checkpoint:** confirm plan with human before writing any code.
3. Plan: 3–6 bullets.
4. Write failing tests.
5. Implement minimum code to pass.
6. Run all tests in your area.
7. **Checkpoint:** confirm implementation with human before adversarial review.
8. Self-review. Pen-test. Add adversarial tests. Run again.
9. Commit.
10. Update `NOTES.md`.
11. Confirm every requirement against spec and task prompt before declaring done.

