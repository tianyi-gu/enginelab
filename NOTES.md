# NOTES.md

Running log of decisions, problems, and work summaries. Updated by agents after each completed task. Most recent entries at the top of each section.

---

## Architecture & key decisions

_Decisions with non-obvious rationale. Include rejected alternatives and why._

| Date | Decision | Rationale | Alternatives rejected |
|------|----------|-----------|-----------------------|
| 2026-04-25 | Terminal detection in game loop, not apply_move | Avoids expensive generate_legal_moves call inside every apply_move | Checking checkmate/stalemate inside apply_move (too costly, redundant with search) |
| 2026-04-25 | Lazy import of apply_move in generate_legal_moves | Breaks circular dependency between move_generation and apply_move | Merging the two modules (too large), creating a third module (unnecessary) |
| 2026-04-25 | Leaderboard uses input order for top-k, not re-sorted | compute_feature_marginals takes leaderboard as-is; caller sorts | Re-sorting inside marginals (hides assumption) |

---

## Problems & mitigations

_Non-trivial bugs, blockers, or surprises. Skip obvious stuff._

| Date | Problem | Root cause | Fix / workaround |
|------|---------|------------|-----------------|
| | | | |

---

## Task log

_One paragraph per completed task: what was built, what tradeoffs were made, what's left._

### Area 2 (HARNESS) — 2026-04-25

Built the complete tournament/analysis/reporting/CLI pipeline on `area-2-harness`. Implemented mock_play_game for zero-ENGINE development, RandomAgent with seeded RNG, round-robin tournament with tqdm progress, leaderboard scoring (win=1/draw=0.5/loss=0), JSON/CSV I/O with lossless round-trip, feature marginals (with/without difference + top-k frequency), pairwise synergy (ANOVA interaction formula), natural-language interpretation, Markdown report with all required sections, and Typer CLI with 5 commands (random-game, match, tournament, analyze, full-pipeline). 31 Area 2 tests pass, 105 total including Foundation. All acceptance criteria 2A-2K met. The pipeline falls back to material-only agent when the full feature registry isn't available.

### Foundation — 2026-04-25

Built the complete standard chess engine on `main`. Full move generation for all piece types with castling (5 conditions checked inline), en passant, promotion to all 4 pieces, check detection via reverse-lookup, legal move filtering. Material-only evaluation, alpha-beta negamax with captures-first ordering at depth 1, variant dispatch, and play_game(). 74 tests pass. Acceptance test: two Agent_material at depth 1, seed 42, 40 plies -> draw by move cap.

---

## What worked / what didn't

_Patterns, tools, approaches. Useful signal for future agents and humans on this project._

**Worked:**
-

**Didn't work / avoid:**
-

---

## Harness & agent observations

_Meta-observations about agent behavior, reliability, and harness setup. Contradictions with conventional wisdom go here._

-
