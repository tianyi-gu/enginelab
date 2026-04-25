# 5-Minute Pitch Outline — EngineLab

---

## Hook (30s)

"We didn't build a chess engine. We built a factory for chess engines — and then ran a controlled experiment to figure out which chess strategies actually work."

---

## Problem (45s)

Chess strategy is opaque. Even grandmasters can't fully articulate *why* certain positional concepts matter. The naive solution — build one engine with all strategic features active — can't isolate causation. You don't know if material counting is helping, or whether king safety is doing all the work.

We wanted a rigorous answer: given a chess variant, which strategic features matter, and how do they interact?

---

## Solution (60s)

We define 10 evaluation features — material, mobility, king safety, capture threats, and more. Then we generate one alpha-beta engine per feature subset: 127 agents, each using a different combination. Run a full round-robin tournament where every agent plays every other agent. Statistically measure which features produce winning play, both individually (marginal contribution) and in combination (pairwise synergy).

The output is not a chess engine. It's a strategy report: a ranked, data-backed answer to "what works in this variant?"

---

## Dev Process (90s) — spend most time here

Three design choices made this tractable in a weekend:

**1. Frozen interface contract.**
Before writing a single line of logic, we defined every shared function signature in `docs/interfaces.md` — a lockfile for the API between modules. Two developers built the chess engine (ENGINE) and the tournament harness (HARNESS) simultaneously for hours with zero coordination. Integration was a one-line swap: replace `mock_play_game()` with the real implementation. No merge conflicts. No integration debugging.

**2. LLM-guided feature selection.**
Instead of exhaustively testing all 1,023 subsets of 10 features (prohibitive), we ask OpenAI to identify the 7 most strategically relevant features for the specific variant being tested. Then we exhaustively test all 127 subsets of those 7. The LLM acts as a domain expert narrowing the search space before the experiment runs.

**3. Parallelized tournament.**
Each game is a pure function: `(white_agent, black_agent, variant, depth, seed) → GameResult`. No shared state. We replaced the sequential loop with `ProcessPoolExecutor`, saturating all CPU cores. 15,876 games run in parallel across the machine.

---

## Results (45s)

For atomic chess at depth 3: `capture_threats + enemy_king_danger` goes undefeated — 87.5% score rate. At depth 2, the winner shifts to `bishop_pair + mobility`.

That shift is itself a finding: **the optimal feature set changes with search depth.** Tactical depth changes which strategic concepts matter. This is the kind of insight that would be hard to derive analytically — but falls out naturally from the tournament structure.

---

## Close (30s)

"What this project demonstrates is that a small team with disciplined AI tooling can run a controlled strategy experiment at scale, in a weekend. The chess variant is interchangeable. The framework is the point."

---

## Q&A Prep

**"Did you control for feature weighting?"**
No — uniform weights (1/n per feature) are a known limitation. Larger subsets are systematically disadvantaged because each feature gets diluted. Addressing this with weight optimization is a direct next step.

**"How do you know the LLM picks better features than random?"**
We don't yet — it's an untested hypothesis. The validation experiment is simple: run the pipeline once with LLM selection, once with random 7-feature selection, compare leaderboard positions. We haven't done this yet.

**"Does this generalize beyond chess?"**
Yes. Any domain where you can define a set of evaluation features and a deterministic scoring function (game, simulation, optimization) could use this structure. Chess is just a convenient, well-understood test bed.
