# Harness Engineering: Operating AI Agents Effectively

This document captures hard-won operational knowledge about using AI coding
agents (Claude Code, etc.) for parallel development. It addresses seven
concerns the team identified as critical to success.

---

## 1. The Spec File as Control Surface

**Problem:** Agents with vague instructions produce vague code. The quality
of agent output is bounded by the quality of the specification it receives.

**Our approach:**

The spec is not a suggestion -- it is a control surface. We have four layers:

| Layer                  | File                        | Purpose                        |
|------------------------|-----------------------------|--------------------------------|
| Product requirements   | `Instructions.MD`           | What to build, why, constraints|
| Interface contracts    | `docs/interfaces.md`        | Exact function signatures      |
| Per-agent scope        | `docs/agent_definitions.md` | What each agent owns and tests |
| Quick reference        | `CLAUDE.md`                 | Conventions at a glance        |

**Best practices:**

- **Front-load all specs before spinning up agents.** The spec documents must
  be committed to `main` before any agent starts work. An agent that starts
  without reading the spec will invent its own conventions.
- **Ask agents to restate the plan.** Before an agent begins coding, have it
  produce a brief implementation plan. If the plan misses key requirements
  (e.g., determinism, self-preservation rule), correct it before it writes
  any code. This catches misunderstandings early.
- **Spec changes require a commit.** If the spec evolves during development,
  update the document and commit it. Agents should re-read the spec file
  after major changes.

---

## 2. AI Reliability: What Actually Works

**Problem:** Blog posts and tutorials often present AI agents as fully
autonomous systems that reliably follow complex instructions. In practice,
agents follow skill/prompt definitions roughly 50% of the time without
reinforcement. Instructions that seem clear to a human may be interpreted
differently or partially ignored by an agent.

**What we have observed:**

- Agents reliably follow **concrete, testable instructions** ("generate
  exactly 31 agents", "weights must sum to 1.0").
- Agents unreliably follow **abstract principles** ("write clean code",
  "follow best practices").
- Agents tend to **drift from conventions** over long sessions, especially
  naming conventions and coordinate systems.
- Agents sometimes **invent plausible-looking code** that does not match the
  spec (e.g., using `"white"` instead of `"w"` for colors).

**Mitigation strategies:**

1. **Checkpoints with concrete tests.** Every area has numbered checkpoints
   (1A, 1B, ..., 5F) with specific pass/fail criteria. The agent must run
   these and report results before moving on.

2. **Convention anchoring.** Put the most critical conventions (piece format,
   color strings, coordinate system) in CLAUDE.md where agents see them first.
   Repeat them in the area-specific prompts. Redundancy is intentional.

3. **Small, verifiable steps.** Do not ask an agent to "implement Area 1."
   Instead: "Implement Board class and run test_board.py. Then implement
   move generation and run test_move_generation.py. Then implement atomic
   rules and run test_atomic.py." Each step has a verification gate.

4. **Post-hoc validation.** After an agent claims to be done, independently
   verify. See Section 3.

---

## 3. Quality Validation: Double-Check, Pen-Test, Independent Review

**Problem:** An agent that writes code and its own tests can produce code
that passes tests but is subtly wrong. The agent may not think to test edge
cases, adversarial inputs, or off-by-one errors. It may "forget" to try to
break its own code.

**Three-layer validation protocol:**

### Layer 1: Self-Test (agent runs its own tests)

Every agent must run pytest for its area before declaring done. This is the
minimum bar. It catches obvious bugs but not subtle ones.

### Layer 2: Cross-Review (a different agent reviews the code)

After an area is implemented, have a separate Claude Code session (or a
different developer) review the code. The review prompt should be adversarial:

```
Review the code in core/ and variants/ for correctness. Specifically:

1. Does Board.copy() produce a true deep copy? Write a test that mutates
   the copy and verifies the original is unchanged.
2. Does move generation produce exactly 20 moves from the starting position?
   List them all and verify manually.
3. Does the atomic explosion correctly handle ALL 8 adjacent squares?
   Test a capture in the center, on an edge, and in a corner.
4. Does the self-preservation filter work? Set up a position where the
   king is adjacent to a capture square and verify the capture is filtered.
5. Try to find a sequence of moves that crashes the game or produces an
   impossible board state.
```

### Layer 3: Pen-Test (actively try to break it)

After integration, run a dedicated pen-testing session:

```
You are a QA engineer trying to break EngineLab. Your job is to find bugs,
crashes, and incorrect behavior. Try:

1. Edge cases: games that end in 1 move, games that hit the move cap,
   boards where one side has no pieces.
2. Adversarial positions: kings adjacent to each other, pawns on promotion
   rank at start, all pieces clustered in one corner.
3. Determinism: run the same pipeline twice with the same seed and diff
   the outputs. Any difference is a bug.
4. Numeric correctness: manually compute feature values and synergy scores
   for a known position and compare against the code's output.
5. Boundary conditions: depth 0, depth 1, max_moves 1, max_moves 0,
   empty feature list, single-feature agents.
```

### When to Validate

| Phase            | Validation Layers | Who                        |
|------------------|-------------------|----------------------------|
| Per-checkpoint   | Layer 1           | Owning agent               |
| Area complete    | Layers 1 + 2      | Owning agent + reviewer    |
| Post-integration | Layers 1 + 2 + 3  | Dedicated review session   |
| Pre-demo         | Layer 3           | Human or independent agent |

---

## 4. Human-in-the-Loop: When and How to Intervene

**Problem:** Agents can run autonomously for extended periods, but quality
degrades without periodic human oversight. Too much autonomy leads to drift;
too little wastes the speed advantage of AI agents.

**Guidelines:**

### When to Let the Agent Run

- When it is implementing a well-specified function with clear tests.
- When it is writing tests for existing code.
- When the task maps directly to a checkpoint in `docs/agent_definitions.md`.

Typical autonomous run: **15-30 minutes** for a single checkpoint, or up to
**1 hour** for a full area if the spec is very clear.

### When to Intervene

- **After each checkpoint.** Review the test output. If tests pass, glance
  at the code for convention violations. If tests fail, diagnose whether the
  agent is stuck in a loop before letting it retry.
- **When the agent asks a question.** Answer it precisely. Vague answers
  ("do whatever makes sense") lead to vague implementations.
- **When the agent produces a plan that looks wrong.** Correct the plan
  before it writes code. Fixing a plan is 10x cheaper than fixing an
  implementation.
- **At integration boundaries.** When merging areas, a human should review
  the merge for interface mismatches.

### Types of Human Input

| Input Type          | When                              | Example                          |
|---------------------|-----------------------------------|----------------------------------|
| Course correction   | Agent drifts from spec            | "Use 'w'/'b', not 'white'/'black'" |
| Disambiguation      | Spec is ambiguous                 | "Stalemate = loss, not draw"     |
| Priority call       | Multiple valid approaches         | "Skip castling, focus on explosions"|
| Quality gate        | Checkpoint completed              | "Tests pass, code looks correct, proceed" |
| Abort               | Agent is stuck or looping         | "Stop. Let me look at this."     |

### Conversational vs. Batch Style

Two valid approaches -- choose based on team preference:

**Batch style (recommended for hackathon):**
- Write a detailed prompt with full context upfront.
- Let the agent run to completion.
- Review output, provide feedback, iterate.
- Best when specs are clear and agents work independently.

**Conversational style:**
- Interactive back-and-forth as the agent works.
- Good for exploratory work or unclear requirements.
- More human time per area but higher quality per line of code.

For EngineLab, use **batch style for Areas 1-4** (well-specified) and
**conversational style for Area 5** (CLI/report polish requires judgment).

---

## 5. Parallelization: Managing Multiple Agents

**Problem:** The project has 5 areas. It is tempting to run 5 agents
simultaneously, but managing more than 2-3 concurrent agents is difficult
for a human operator. Each agent may need intervention, and context-switching
between 5 agents degrades the quality of human oversight.

**Optimal agent count: 2-3 concurrent agents.**

Research on cognitive load and management span supports this. Miller (1956)
established that working memory holds roughly 7 items; when managing agents,
each agent's state (what it is doing, what it last produced, what it needs
next) consumes 2-3 working memory slots. This puts the practical ceiling at
2-3 agents for effective oversight.

### Recommended Parallelization Schedule

```
Phase 1 (hour 0-1):    Build Foundation together on main
                        (working standard chess engine)

Phase 2 (hours 1-6):   Run Area 1 (ENGINE) + Area 2 (HARNESS) in parallel
                        (Area 2 uses mock_play_game, zero ENGINE dependency)

Phase 3 (hours 6-8):   Integration: merge Area 1, rebase Area 2, merge Area 2
                        Run full pipeline end-to-end

Phase 4 (hours 8-10):  Polish, pen-test, demo prep
                        (1 agent + human review)
```

### Managing Agent "Reports"

Treat each agent like a direct report:

- **Give clear, written instructions** (the area prompt).
- **Check in at defined milestones** (checkpoints).
- **Do not micromanage** between milestones.
- **Review deliverables** (test output, code diff) before signing off.
- **Provide feedback once** and expect it to stick (save to spec if needed).

### When Agents Conflict

If two agents edit the same file (which should not happen under the ownership
rules), the merge will create a conflict. Resolution:

1. Identify which agent owns the file (see `docs/agent_definitions.md`).
2. Keep that agent's version.
3. Have the other agent adapt.

---

## 6. Source Control: Git Worktrees for Parallel Agents

**Problem:** Running multiple agents on the same checkout causes file
conflicts. Agents may overwrite each other's work or see partially-written
files from another agent.

**Solution: Git worktrees.**

Git worktrees let you check out multiple branches simultaneously in separate
directories, all sharing the same `.git` database. Each agent operates in
its own directory with its own branch.

### Setup

```bash
# From the main repo directory
cd /path/to/engine-lab

# Create worktrees for each area
git worktree add ../engine-lab-area1 area-1-engine
git worktree add ../engine-lab-area2 area-2-harness
```

Each agent gets its own working directory:

```
/path/to/engine-lab/           # main checkout (integration)
/path/to/engine-lab-area1/     # Developer 1's workspace (ENGINE)
/path/to/engine-lab-area2/     # Developer 2's workspace (HARNESS)
```

### Agent Commit Discipline

- Agents should **commit frequently** (after each checkpoint passes).
- Commit messages should be descriptive: `"Area 1: implement Board class,
  test_board.py passes (checkpoint 1A)"`.
- Do NOT let agents push to `main` directly. They push to their area branch.
- Integration (merging to `main`) is done by a human or a dedicated
  integration session.

### Cleanup

```bash
# After integration, remove worktrees
git worktree remove ../engine-lab-area1
git worktree remove ../engine-lab-area2
# etc.
```

### Alternative: Simpler Approach (2-3 agents)

If running only 2-3 agents, worktrees are optional. You can use separate
terminal sessions with each agent on a different branch:

```bash
# Terminal 1 (Developer 1 - ENGINE)
git checkout area-1-engine

# Terminal 2 (Developer 2 - HARNESS)
# Use a separate clone or worktree
git checkout area-2-harness
```

The key rule: **no two agents should operate on the same directory
simultaneously**.

---

## 7. Determinism: Same Input, Same Output

**Problem:** If the system produces different results on different runs, the
"strategic insights" are meaningless noise. The team specifically requires:
given the same rules and configuration, the program must return the same
engine outputs every time.

**See `Instructions.MD` Section 12 for full technical requirements.**

Summary of determinism guarantees:

| Component         | Determinism Source                          |
|-------------------|---------------------------------------------|
| Agent generation  | Sorted feature names + itertools.combinations|
| Move generation   | Fixed piece iteration order (row, col)      |
| Alpha-beta search | Deterministic move ordering + no randomness |
| Random agent      | Seeded `random.Random(seed)` per game       |
| Tournament order  | Deterministic game iteration + seeded RNG   |
| Analysis          | Deterministic iteration over leaderboard    |

### Verification

After the pipeline is working, run it twice with the same seed and diff:

```bash
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80 --seed 42
mv outputs/reports/atomic_strategy_report.md /tmp/report_run1.md
mv outputs/data/tournament_results_atomic.json /tmp/results_run1.json

python main.py full-pipeline --variant atomic --depth 2 --max-moves 80 --seed 42
diff outputs/reports/atomic_strategy_report.md /tmp/report_run1.md
diff outputs/data/tournament_results_atomic.json /tmp/results_run1.json
```

Both diffs must be empty. If they are not, there is a determinism bug.

---

## Summary: Operational Checklist

Before the hackathon:

- [ ] All spec files committed to `main` (Instructions.MD, interfaces,
      agent definitions, this document)
- [ ] Stub files created and committed
- [ ] Area branches created
- [ ] Worktrees set up (if using >2 agents)
- [ ] Each developer has read `CLAUDE.md` and their area prompt

During the hackathon:

- [ ] Run 2-3 agents max concurrently
- [ ] Check in at each checkpoint (review test output)
- [ ] Cross-review each area before merging
- [ ] Merge in dependency order (Area 1 -> Area 2)
- [ ] Run pen-test session after integration
- [ ] Verify determinism (two identical runs, diff outputs)
- [ ] Run full pipeline with 3 features before attempting 10 features

---

## References

- Miller, G. A. (1956). "The Magical Number Seven, Plus or Minus Two."
  *Psychological Review*, 63(2), 81-97. -- Cognitive load limits relevant
  to managing concurrent agents.

- Brooks, F. P. (1975). *The Mythical Man-Month.* Addison-Wesley. --
  Communication overhead scales quadratically with team size; applies
  equally to human and AI agent teams.

- Xu, F. et al. (2024). "Benchmarking Large Language Models for Automated
  Program Repair." *ACM SIGSOFT*. -- Empirical evidence on LLM reliability
  for code generation tasks; validates checkpoint-based verification approach.
