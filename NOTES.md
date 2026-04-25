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
