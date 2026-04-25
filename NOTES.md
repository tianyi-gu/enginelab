# NOTES.md

Running log of decisions, problems, and work summaries. Updated by agents after each completed task. Most recent entries at the top of each section.

---

## Architecture & key decisions

_Decisions with non-obvious rationale. Include rejected alternatives and why._

| Date | Decision | Rationale | Alternatives rejected |
|------|----------|-----------|-----------------------|
| 2026-04-25 | AlphaBetaEngine takes `variant` param (default "standard") | Allows same engine class for standard, atomic, antichess via dispatch | Separate engine subclasses per variant — too much duplication |
| 2026-04-25 | Antichess uses pseudo-legal moves (no check filter) | King has no special status in antichess — check doesn't exist | Reusing generate_legal_moves — would incorrectly filter king captures |
| 2026-04-25 | Feature normalization: clip [-10,10], divide by 10 | Keeps features on comparable scale without requiring per-feature tuning | Min-max normalization (needs dataset), z-score (needs running stats) |
| 2026-04-25 | Dual-mode agent generation: exhaustive vs stratified | Exhaustive is tractable for ≤6 features, stratified guarantees coverage of singles/pairs/full set for larger sets | Always exhaustive (explodes at 10 features: 1023 agents), always random (misses important small subsets) |
| 2026-04-25 | Terminal detection in game loop, not apply_move | Avoids expensive generate_legal_moves call inside every apply_move | Checking checkmate/stalemate inside apply_move (too costly, redundant with search) |
| 2026-04-25 | Lazy import of apply_move in generate_legal_moves | Breaks circular dependency between move_generation and apply_move | Merging the two modules (too large), creating a third module (unnecessary) |
| 2026-04-25 | Leaderboard uses input order for top-k, not re-sorted | compute_feature_marginals takes leaderboard as-is; caller sorts | Re-sorting inside marginals (hides assumption) |

---

## Problems & mitigations

_Non-trivial bugs, blockers, or surprises. Skip obvious stuff._

| Date | Problem | Root cause | Fix / workaround |
|------|---------|------------|-----------------|
| 2026-04-25 | Antichess win detection only checked mover's pieces | `apply_antichess_move` only scanned for the side that just moved | Check both colors after every move — either side losing all pieces triggers a win |
| 2026-04-25 | Alpha-beta used int constants for bounds causing issues with WIN/LOSS comparison | `float("-inf")` and `float("inf")` safer than arbitrary large ints when WIN_SCORE=10000 | Switched to `float("-inf")`/`float("inf")` for alpha-beta bounds |

---

## Task log

_One paragraph per completed task: what was built, what tradeoffs were made, what's left._

### Area 1 (ENGINE) — 2026-04-25

Built the complete ENGINE layer across 5 phases. **Phase 1**: Atomic chess variant with explosion mechanics (captures destroy capturing piece, captured piece, and adjacent non-pawn pieces) and self-preservation filter (captures that would explode own king are illegal). **Phase 2**: All 10 evaluation features — material, piece_position (piece-square tables), center_control, king_safety, enemy_king_danger, mobility, pawn_structure, bishop_pair, rook_activity, capture_threats — each registered in the feature registry with descriptions. **Phase 3**: Dual-mode agent generation (exhaustive for ≤6 features, stratified sampling for larger sets guaranteeing all singles, all pairs, and full set) plus registry-backed evaluation with normalization. **Phase 4**: Production alpha-beta with negamax formulation, move ordering (captures sorted by victim value descending), variant-aware dispatch, and instrumentation (node count + timing). **Phase 5**: Antichess variant with forced capture rule and win-by-losing condition. Total: 157 tests, all passing. No tradeoffs deferred — all acceptance criteria met including optional antichess.

### Area 2 (HARNESS) — 2026-04-25

Built the complete tournament/analysis/reporting/CLI pipeline on `area-2-harness`. Implemented mock_play_game for zero-ENGINE development, RandomAgent with seeded RNG, round-robin tournament with tqdm progress, leaderboard scoring (win=1/draw=0.5/loss=0), JSON/CSV I/O with lossless round-trip, feature marginals (with/without difference + top-k frequency), pairwise synergy (ANOVA interaction formula), natural-language interpretation, Markdown report with all required sections, and Typer CLI with 5 commands (random-game, match, tournament, analyze, full-pipeline). 31 Area 2 tests pass, 105 total including Foundation. All acceptance criteria 2A-2K met. The pipeline falls back to material-only agent when the full feature registry isn't available.

### Foundation — 2026-04-25

Built the complete standard chess engine on `main`. Full move generation for all piece types with castling (5 conditions checked inline), en passant, promotion to all 4 pieces, check detection via reverse-lookup, legal move filtering. Material-only evaluation, alpha-beta negamax with captures-first ordering at depth 1, variant dispatch, and play_game(). 74 tests pass. Acceptance test: two Agent_material at depth 1, seed 42, 40 plies -> draw by move cap.

---

## What worked / what didn't

_Patterns, tools, approaches. Useful signal for future agents and humans on this project._

**Worked:**
- Phase-by-phase development with tests before moving on caught bugs early (e.g., antichess win check)
- Variant dispatch pattern (VARIANT_DISPATCH dict) cleanly separates rules from search logic
- Move ordering (captures by victim value) works well for alpha-beta pruning efficiency
- Deterministic move generation (row 0-7, col 0-7) ensures reproducible results across runs

**Didn't work / avoid:**
- Initial antichess win detection only checked the mover — must check both sides after every move

---

## Harness & agent observations

_Meta-observations about agent behavior, reliability, and harness setup. Contradictions with conventional wisdom go here._

-
