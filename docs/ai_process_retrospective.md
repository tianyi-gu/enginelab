# AI-Assisted Development: Process Retrospective

This document describes how we actually used AI agents to build EngineLab,
mapped to the seven themes the Cubist hackathon organizers identified as
most important for evaluating the development process.

---

## 1. Spec File & Control Environment

**What we did:**

Before any coding started, we created a layered specification system:

| Layer | File | Purpose |
|-------|------|---------|
| Product requirements | `Instructions.MD` | Full PRD: what to build, constraints, acceptance criteria |
| Interface contracts | `docs/interfaces.md` | Exact Python signatures for every cross-module function — treated as a lockfile |
| Per-agent scope | `docs/agent_definitions.md` | File ownership per developer, explicit "do not touch" rules |
| Operating rules | `AGENTS.md` | How agents should plan, test, commit, and check in |
| Quick reference | `CLAUDE.md` | Critical conventions at a glance (piece chars, color strings, coordinates) |

The key insight: **the spec is a control surface, not documentation.** Agents were
told to read the spec before producing any implementation plan, and to produce a plan
before writing any code. This plan-first checkpoint caught multiple misunderstandings
before they became bugs.

The `docs/interfaces.md` lockfile was particularly effective. Because all function
signatures were defined upfront and frozen, two developers working in parallel
(Area 1: ENGINE; Area 2: HARNESS) could integrate their work without merge conflicts
on shared modules. Area 2 used `mock_play_game()` during development and swapped in
the real implementation in one line at integration time.

**Lesson:** Detailed specs upfront are worth the investment. The hour spent writing
`docs/interfaces.md` before any coding saved hours of integration debugging.

---

## 2. AI Reliability & What the Blogosphere Gets Wrong

**What we observed:**

Blog posts often portray AI agents as fully autonomous systems that reliably follow
complex instructions. In practice:

- **Agents reliably follow concrete, testable instructions.** "Generate exactly 127
  agents", "weights must sum to 1.0", "run pytest and report results" — these work.
- **Agents unreliably follow abstract principles.** "Write clean code", "follow best
  practices" — these are ignored or interpreted inconsistently.
- **Skill/agent definitions are invoked roughly 50% of the time** without active
  reinforcement. The agent may acknowledge a rule and then violate it two steps later.
- **Drift over long sessions is real.** Naming conventions (`"w"` vs `"white"`),
  coordinate conventions (`row 0 = rank 1`), and field names drifted in extended
  sessions. The solution was to repeat critical conventions in multiple places
  (CLAUDE.md, the area prompt, and inline comments).

**What worked to mitigate this:**

1. **Checkpoint gates.** Every area had numbered checkpoints with pass/fail test
   commands. The agent could not proceed until it ran pytest and reported results.
2. **Convention anchoring.** The most critical conventions (piece chars, color strings,
   board coordinates) appear in both CLAUDE.md and the area prompt — redundancy
   is intentional.
3. **Plan-first workflow.** Asking the agent to produce a brief plan before coding
   caught misunderstandings early. If the plan references `"white"` instead of `"w"`,
   correct it before 500 lines of code use the wrong string.

---

## 3. Pen Testing & Quality Validation

**Three-layer validation protocol we used:**

**Layer 1 — Self-test:** Each agent ran `pytest` for its area before declaring done.
Minimum bar, not sufficient alone.

**Layer 2 — Cross-review:** After each area was complete, a separate Claude Code
session reviewed the code with an adversarial prompt: "Try to find sequences that
crash the game or produce impossible board states." This caught the antichess win
detection bug (only checked the mover's pieces, not both sides).

**Layer 3 — Integration pen-test:** After merging, we ran a dedicated session
focused on edge cases:
- Games ending in 1 move
- Boards where one side has no pieces
- Determinism verification (run pipeline twice with same seed, diff outputs)
- Atomic captures in corners vs center vs edges

**What the agent missed without being explicitly asked:**
- The agent that wrote the atomic explosion code did not test corner/edge cases for
  the 8-adjacency radius. This was only caught by the cross-review session.
- The agent did not pen-test its own code. Adding an explicit "pen-test" step to the
  agent operating rules (now in `AGENTS.md`) made a significant difference.

---

## 4. Managing Autonomy (Human-in-the-Loop)

**Conversational vs. batch style:**

We used both approaches and found them appropriate for different phases:

- **Conversational style** was used for planning, brainstorming, and anything
  involving judgment calls (e.g., "what alternatives exist for agent generation?",
  "should we use LLM or not?"). Back-and-forth dialogue produced better decisions
  than upfront prompts.

- **Batch style** was used for well-specified implementation tasks (e.g., "implement
  `run_round_robin()` with `ProcessPoolExecutor`, here are the exact constraints").
  The agent ran for 15–30 minutes per checkpoint with minimal intervention.

**When we intervened:**
- After each checkpoint: reviewed test output, spot-checked code for convention drift
- When the agent produced a plan that diverged from the spec (corrected before coding)
- At integration boundaries: human reviewed merges for interface mismatches
- When the agent was looping on a failing test (diagnosed root cause, redirected)

**Effective intervention types:**
- Course correction: "Use `'w'/'b'`, not `'white'/'black'`"
- Disambiguation: "The `on_game_complete` callback should trigger sequential mode, not error"
- Priority call: "Don't implement the caching layer yet, get the API call working first"
- Quality gate: "Tests pass and the code looks correct — proceed to the next checkpoint"

**Autonomous run times:** Well-specified checkpoints ran for 15–30 minutes autonomously.
Full areas (10+ checkpoints) ran for up to 2 hours with check-ins at each checkpoint.

---

## 5. Parallelization & Agent Management

**Development parallelism:**

The project was split into two independent workstreams from the start:

- **Area 1 (ENGINE):** Variants, features, agents, alpha-beta search
- **Area 2 (HARNESS):** Tournament, analysis, reporting, CLI

These ran simultaneously with zero coordination because Area 2 used `mock_play_game()`
during development. The interface between them (the `GameResult` dataclass) was frozen
in `docs/interfaces.md` before either area started.

**Optimal agent count: 2–3 concurrent agents.**

We found this number consistently in practice. Beyond 3, the human operator cannot
effectively monitor output quality, catch convention drift, or respond to agent
check-ins. Each agent's state (what it's doing, what it last produced, what it needs)
consumes significant working memory. This aligns with Miller's Law (7±2 items in
working memory) and standard management research on span of control.

**Runtime parallelism (tournament games):**

Beyond development parallelism, we also parallelized the tournament itself. Games are
pure functions — `(white_agent, black_agent, variant, depth, max_moves, seed) → GameResult`
— with no shared state. We replaced the sequential `for` loop in `run_round_robin()`
with `ProcessPoolExecutor`, saturating all CPU cores. With 127 agents (15,876 games),
this produces approximately a linear speedup with core count.

The UI path (Streamlit with a live progress callback) remains sequential for
compatibility with the callback mechanism.

---

## 6. Source Control Integration

**Branch strategy:**

```
main                          # Foundation + merged implementations
area-1-engine                 # ENGINE workstream
area-2-harness                # HARNESS workstream
LLM-as-a-judge_deepseek       # LLM feature selection + parallelization
Pratzz1202-Workflow-diagrams  # Architecture diagrams
```

**What we did in practice:**

- All feature work happened on branches, never directly on `main`
- Agents committed after each passing checkpoint with descriptive messages
- Integration (merging to `main`) was done by a human after reviewing the diff
- Git worktrees were available but not needed for this project scale (2 concurrent agents)

**Lessons on commit discipline:**
- "Commit frequently after each checkpoint" is better advice than "commit when done"
- Descriptive commit messages matter: `"Add LLM-guided feature selection and parallelized tournament"` is recoverable; `"fix stuff"` is not
- Pushing to a branch immediately after committing is a good habit — it serves as a backup and lets collaborators see progress

**SSH vs. HTTPS authentication:**
In practice, SSH with a passphrase was more reliable than HTTPS with a personal access
token for pushing to a collaborator's repo. The token approach requires the token owner
to have write access, which is distinct from authentication.

---

## 7. Determinism

**Why this matters:**

If the system produces different results on different runs, the strategic insights
("feature X is most valuable") are noise. A non-deterministic system cannot be
scientifically validated.

**How we achieved it:**

| Component | Determinism mechanism |
|-----------|----------------------|
| Agent generation | `sorted()` on feature names + `itertools.combinations` in fixed order |
| Move generation | Fixed piece iteration order: row 0→7, col 0→7 |
| Alpha-beta search | Deterministic move ordering (captures by victim value) + no randomness |
| Stratified sampling | `random.Random(seed)` — local instance, not global `random.seed()` |
| Tournament scheduling | `seed + game_index` per game — deterministic per-game seeds |
| LLM feature selection | Results cached to `outputs/llm_feature_cache.json` — same variant always returns same features after first call |

**Verification command:**
```bash
python main.py full-pipeline --variant atomic --depth 2 --seed 42
# copy outputs
python main.py full-pipeline --variant atomic --depth 2 --seed 42
diff outputs/reports/atomic_strategy_report.md /tmp/run1_report.md
# must be empty
```

The LLM feature selection adds one non-deterministic step (the API call), which is
made deterministic by caching. The `--refresh-llm` flag bypasses the cache when
intentionally exploring different selections.

---

## Summary: What We Would Do Differently

1. **Write the spec first, always.** The time spent on `docs/interfaces.md` before
   any coding was the highest-leverage hour of the project.

2. **Build the mock before the real implementation.** `mock_play_game()` let Area 2
   develop and test completely independently for hours. This is underused in practice.

3. **Make "pen-test your own code" explicit in agent operating rules.** Agents do not
   do this by default. Adding it to `AGENTS.md` with a concrete checklist changed
   behavior noticeably.

4. **Cap concurrent agents at 2–3.** Running more is tempting but degrades oversight
   quality faster than it accelerates output.

5. **Use conversational style for decisions, batch style for implementation.** Mixing
   them produces worse results than choosing deliberately.

6. **Parallelize at the right level.** We parallelized both the development process
   (two workstreams) and the runtime computation (ProcessPoolExecutor). Both matter,
   but they are independent levers.
