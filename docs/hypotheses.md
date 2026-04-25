# EngineLab — Underlying Hypotheses

This document enumerates the assumptions baked into EngineLab's methodology.
Some are validated, some are acknowledged limitations, and one is falsified
(and reframed as a finding).

---

## H1 — Feature Decomposability

**Claim:** Strategic value can be decomposed into independent, addable scalar features.

**Status:** Partially violated — and the project measures this.

The evaluation function sums weighted feature scores linearly. This assumes features
contribute independently. In practice they don't: `capture_threats` and
`enemy_king_danger` together are more powerful than their individual contributions
predict. The pairwise synergy analysis exists precisely because this assumption breaks
down. The synergies are a finding, not a flaw.

---

## H2 — Uniform Weight Validity (known limitation, addressable)

**Claim:** Equal weighting (1/n per feature) is a fair comparison baseline across subsets.

**Status:** Systematic bias, currently unaddressed.

A 2-feature agent weights each feature at 0.50. A 7-feature agent weights each at 0.14.
Adding features dilutes each one — this means larger subsets are systematically
disadvantaged in head-to-head play, independent of how good those features actually are.
The current leaderboard conflates "good features" with "fewer features."

**Fix:** Normalize scores before weighting, or run a grid search over weights within
each subset. This would make feature comparisons cleaner.

---

## H3 — Alpha-Beta Faithfulness

**Claim:** The alpha-beta engine at depth 2–3 reflects feature strategic value rather
than search artifacts (horizon effect, transposition, move ordering bias).

**Status:** Shaky at depth 2, more trustworthy at depth 3.

At depth 2, the engine sees only two plies ahead. The horizon effect is significant —
the engine may make moves that look good at the surface but set up immediate bad
positions it can't see. Results at depth 2 reflect a mix of feature value and search
artifact. Depth 3 results are more trustworthy but computationally more expensive.

---

## H4 — Round-Robin Validity

**Claim:** Win rate against other feature-subset agents is a meaningful proxy for
"this strategy is good at chess."

**Status:** Valid within the experimental frame, not an absolute claim.

The tournament measures which feature subsets beat other feature subsets. It does not
measure performance against a traditional evaluation function, Stockfish, or human
players. The claim is comparative ("feature set A is more effective than B for this
variant") not absolute ("this is strong chess").

---

## H5 — LLM Domain Knowledge (untested)

**Claim:** OpenAI's chess knowledge is sufficient to select a better-than-random
7-feature subset for a given variant.

**Status:** Assumed, not validated. No baseline comparison exists.

We call OpenAI to narrow 10 features to 7 before exhaustive testing. We assume this
produces a better selection than picking 7 randomly. We have not run the validation
experiment: two identical pipeline runs — one with LLM selection, one with random
7-feature selection — and compared leaderboard outcomes. Until we do, this step is a
plausible heuristic, not an empirically grounded one.

---

## H6 — Variant Sensitivity

**Claim:** Optimal feature subsets differ significantly across chess variants — atomic,
antichess, and standard each reward different strategies.

**Status:** Plausible, partially validated within atomic chess.

The entire motivation for multi-variant support rests on this hypothesis. We have not
yet run full comparable experiments across all three variants to confirm it. Within
atomic chess, we already see that *depth* changes the winner (depth 2 vs depth 3),
which hints that variant rules would too — but this remains to be demonstrated.

---

## H7 — Depth-Transferability (falsified — reframe as finding)

**Claim:** The relative ranking of feature subsets is stable across search depths.

**Status:** Falsified by our own results. Present this as a finding.

Depth 2 winner: `bishop_pair + mobility` (81.9% score rate).
Depth 3 winner: `capture_threats + enemy_king_danger` (87.5%, undefeated).

These are different agents. The optimal strategy changes with search depth. At depth 2,
positional concepts (mobility, bishop pair) dominate. At depth 3, tactical concepts
(explosion threats, king proximity) dominate — because deeper search reveals the
consequences of captures that shallower search misses.

This is the most interesting result in the project: **strategic depth and search depth
are intertwined.** An engine that "thinks further ahead" needs a fundamentally different
strategic vocabulary.

---

## H8 — Determinism Equals Reproducibility

**Claim:** Running the pipeline twice with the same seed produces identical outputs,
which constitutes scientific reproducibility.

**Status:** True for the chess engine; papered over for the LLM step.

The chess engine is fully deterministic: fixed piece iteration order, local
`random.Random(seed)` instances, per-game seeds derived from `tournament_seed +
game_index`. Two identical runs produce byte-identical output.

The LLM feature selection step is not independently reproducible — we cache the API
response so repeat runs return the same selection, but the underlying model reasoning
is not guaranteed to be stable across API calls or model updates. The cache makes it
*consistent*, not *reproducible* in the scientific sense. Clearing the cache and
re-running may produce different feature selections.
