# Agent Definitions

This document defines the exact scope, prompts, and acceptance criteria for
each developer (or Claude Code agent) working on EngineLab. Each agent
operates on a dedicated branch and owns a specific set of files.

---

## Developer 1: Core Chess State + Atomic Variant

### Branch

`area-1-core-variant`

### Files Owned

```
core/__init__.py
core/types.py
core/board.py
core/move.py
core/coordinates.py
core/move_generation.py
core/apply_move.py
variants/__init__.py
variants/base.py
variants/atomic.py
tests/test_board.py
tests/test_move_generation.py
tests/test_atomic.py
```

### Must Not Edit

`features/`, `agents/`, `search/`, `simulation/`, `tournament/`,
`analysis/`, `reports/`, `ui/`, `main.py`

### Prompt

```
You are implementing Area 1 of EngineLab: core chess state and Atomic
Chess rules.

Read Instructions.MD and docs/interfaces.md completely before starting.

Implement:
1. Board class in core/board.py (8x8 grid, FEN piece chars, deep copy)
2. Move dataclass in core/move.py (frozen, UCI output)
3. Square type alias and color helpers in core/types.py
4. Square-to-algebraic conversion in core/coordinates.py
5. Pseudo-legal move generation in core/move_generation.py:
   - Pawn (single push, double push, diagonal capture, queen promotion)
   - Knight, Bishop, Rook, Queen, King
   - generate_moves(board) and generate_moves_for_color(board, color)
6. Standard move application in core/apply_move.py
7. Atomic Chess in variants/atomic.py:
   - apply_atomic_move: explosion on capture (removes capturing piece,
     captured piece, adjacent non-pawn pieces; pawns immune)
   - generate_atomic_moves: filter captures that would explode own king
   - Winner detection on king explosion

Conventions (CRITICAL):
- FEN piece chars: uppercase=white, lowercase=black, None=empty
- Colors: "w" / "b" only
- Coordinates: grid[row][col], row 0 = rank 1, col 0 = file a
- Board.copy() must be a deep copy
- Do NOT implement castling, en passant, or underpromotion

Verify:
- Starting position generates exactly 20 white moves
- pytest tests/test_board.py tests/test_move_generation.py tests/test_atomic.py
```

### Acceptance Criteria

| ID  | Test                                                     |
|-----|----------------------------------------------------------|
| 1A  | Board starting position is correct                       |
| 1B  | 20 pseudo-legal white moves from starting position       |
| 1C  | Atomic explosion removes correct pieces, pawns survive   |
| 1D  | Self-destructive captures are filtered out               |
| 1E  | 100 random atomic plies without crash                    |
| 1F  | All 3 test files pass                                    |

---

## Developer 2: Feature Library + Registry

### Branch

`area-2-features`

### Files Owned

```
features/__init__.py
features/registry.py
features/material.py
features/mobility.py
features/king_danger.py
features/king_safety.py
features/capture_threats.py
tests/test_features.py
```

### Must Not Edit

`core/`, `variants/`, `agents/`, `search/`, `simulation/`, `tournament/`,
`analysis/`, `reports/`, `ui/`, `main.py`

### May Import From

`core`, `variants`

### Prompt

```
You are implementing Area 2 of EngineLab: evaluation features and
feature registry.

Read Instructions.MD and docs/interfaces.md completely before starting.

Implement 5 features, each with signature:
    feature(board: Board, color: str) -> float
    Positive = good for color. Must not mutate the board.

1. material: own material - opponent material
   Piece values: P=1, N=3, B=3, R=5, Q=9, K=0
   Use piece_type(piece).upper() for lookup.

2. mobility: own move count - opponent move count
   Use generate_moves_for_color(board, color).

3. enemy_king_danger: pressure near opponent king
   For each own piece: += 1/max(chebyshev_distance, 1)
   For each adjacent square of enemy king attacked by own piece: += 1
   If enemy king missing: return 10.0

4. own_king_safety: -enemy_king_danger(board, opponent)
   If own king missing: return -10.0

5. capture_threats: value of available captures
   For each capture: += captured piece value
                     += 3 * adjacent enemy non-pawn pieces that would explode
                     += 100 if enemy king would explode

Registry in features/registry.py:
- FEATURES dict mapping name -> function
- FEATURE_DESCRIPTIONS dict mapping name -> description string
- get_feature_names(), get_feature_function(name), get_feature_description(name)

Conventions:
- Colors: "w" / "b"
- FEN pieces: uppercase=white, lowercase=black
- Chebyshev distance: max(abs(r1-r2), abs(c1-c2))

Verify: pytest tests/test_features.py
```

### Acceptance Criteria

| ID  | Test                                                 |
|-----|------------------------------------------------------|
| 2A  | material returns 0.0 at starting position            |
| 2B  | All 5 functions return float                         |
| 2C  | No feature mutates the board                         |
| 2D  | Features handle missing kings gracefully             |
| 2E  | test_features.py passes                              |

---

## Developer 3: Agents + Evaluation + Alpha-Beta Search

### Branch

`area-3-agents-search`

### Files Owned

```
agents/__init__.py
agents/feature_subset_agent.py
agents/generate_agents.py
agents/evaluation.py
search/__init__.py
search/alpha_beta.py
tests/test_agents.py
tests/test_alpha_beta.py
```

### Must Not Edit

`core/`, `variants/`, `features/`, `simulation/`, `tournament/`,
`analysis/`, `reports/`, `ui/`, `main.py`

### May Import From

`core`, `variants`, `features`

### Prompt

```
You are implementing Area 3 of EngineLab: feature-subset agents,
evaluation, and alpha-beta search.

Read Instructions.MD and docs/interfaces.md completely before starting.

Implement:

1. FeatureSubsetAgent (frozen dataclass):
   - name: str (e.g. "Agent_material__mobility")
   - features: tuple[str, ...] (sorted alphabetically)
   - weights: dict[str, float] (sum to 1.0)

2. generate_feature_subset_agents(feature_names):
   - One agent per nonempty subset (2^n - 1 agents)
   - Weights = 1.0 / len(subset)
   - Names: features sorted alphabetically, joined by "__", prefixed "Agent_"

3. evaluate(board, color, agent):
   - Terminal: return WIN_SCORE (10000) or LOSS_SCORE (-10000)
   - Otherwise: sum of weight * normalize(feature(board, color))
   - normalize: clip to [-10, 10], divide by 10

4. contributions(board, color, agent):
   - Per-feature weighted contribution dict

5. AlphaBetaEngine:
   - Negamax with alpha-beta pruning
   - Depth-limited with leaf evaluation
   - Move ordering: captures first
   - choose_move(board) -> Move (must always return a legal move)
   - Track nodes_searched and search_time_seconds

Verify:
- 5 features -> exactly 31 agents, all names unique, weights sum to 1.0
- Alpha-beta returns legal move at depth 1 and depth 2
- pytest tests/test_agents.py tests/test_alpha_beta.py
```

### Acceptance Criteria

| ID  | Test                                               |
|-----|----------------------------------------------------|
| 3A  | 5 features -> 31 agents                           |
| 3B  | All agent names unique                             |
| 3C  | Weights sum to 1.0 (within float tolerance)        |
| 3D  | evaluate returns numeric float                     |
| 3E  | Alpha-beta returns legal move at depth 1 and 2     |
| 3F  | test_agents.py and test_alpha_beta.py pass         |

---

## Developer 4: Game Simulation + Tournament Harness

### Branch

`area-4-simulation-tournament`

### Files Owned

```
simulation/__init__.py
simulation/game.py
simulation/random_agent.py
tournament/__init__.py
tournament/round_robin.py
tournament/leaderboard.py
tournament/results_io.py
tests/test_tournament.py
```

### Must Not Edit

`core/`, `variants/`, `features/`, `agents/`, `search/`,
`analysis/`, `reports/`, `ui/`, `main.py`

### May Import From

`core`, `variants`, `agents`, `search`

### Prompt

```
You are implementing Area 4 of EngineLab: game simulation, random
agent, round-robin tournament, leaderboard, and result I/O.

Read Instructions.MD and docs/interfaces.md completely before starting.

Implement:

1. RandomAgent: choose_move returns random legal atomic move

2. GameResult dataclass:
   white_agent, black_agent, winner ("w"/"b"/None), moves,
   termination_reason, avg nodes/time per side

3. play_game(white_agent, black_agent, variant, depth, max_moves, seed):
   - White moves first
   - Use AlphaBetaEngine for FeatureSubsetAgent
   - Use RandomAgent directly
   - Apply atomic moves
   - Terminate on: king explosion, no legal moves, move cap
   - Track nodes/time per side
   - Seed random for reproducibility

4. run_round_robin(agents, variant, depth, max_moves, seed):
   - Every ordered pair (A as white, B as black), A != B
   - N agents -> N*(N-1) games
   - Show tqdm progress bar
   - Per-game seed = tournament_seed + game_index

5. save_results_json, load_results_json, save_results_csv

6. compute_leaderboard(results, agents):
   - win=1, draw=0.5, loss=0
   - score_rate = (wins + 0.5*draws) / games_played
   - Sort descending by score_rate

Verify: pytest tests/test_tournament.py
```

### Acceptance Criteria

| ID  | Test                                                   |
|-----|--------------------------------------------------------|
| 4A  | Random vs random game completes                        |
| 4B  | FeatureSubsetAgent vs FeatureSubsetAgent game completes|
| 4C  | 3 agents -> 6 games                                   |
| 4D  | Leaderboard contains all agents, correct game counts   |
| 4E  | JSON save/load roundtrip produces identical data       |
| 4F  | test_tournament.py passes                              |

---

## Developer 5: Analysis + Reporting + CLI

### Branch

`area-5-analysis-cli`

### Files Owned

```
analysis/__init__.py
analysis/feature_marginals.py
analysis/synergy.py
analysis/interpretation.py
reports/__init__.py
reports/markdown_report.py
main.py
ui/app.py (optional)
tests/test_analysis.py
```

### Must Not Edit

`core/`, `variants/`, `features/`, `agents/`, `search/`,
`simulation/`, `tournament/`

### May Import From

All modules.

### Prompt

```
You are implementing Area 5 of EngineLab: analysis, reporting, CLI,
and optional Streamlit UI.

Read Instructions.MD and docs/interfaces.md completely before starting.

Implement:

1. compute_feature_marginals(leaderboard, feature_names, top_k=10):
   - avg_score_with: mean score_rate of agents containing feature
   - avg_score_without: mean score_rate of agents excluding feature
   - marginal: avg_score_with - avg_score_without
   - top_k_frequency: fraction of top-k agents containing feature

2. compute_pairwise_synergies(leaderboard, feature_names):
   - synergy(a,b) = avg_with_both - avg_with_a - avg_with_b + overall_avg
   - This is the standard ANOVA interaction term

3. generate_interpretation(best_agent, marginals, synergies, variant):
   - Natural-language paragraph about findings

4. generate_markdown_report(...):
   - Sections: title, summary, variant, features, config, top-10
     leaderboard, best subset, marginals, synergies, interpretation,
     limitations

5. CLI with Typer (main.py):
   - random-game: play random vs random
   - match: play specific feature sets against each other
   - tournament: run round-robin
   - analyze: analyze existing results JSON
   - full-pipeline: end-to-end pipeline

6. Optional: Streamlit UI in ui/app.py

Test your analysis functions on synthetic data first:
- Create fake LeaderboardRow lists with known values
- Verify marginals and synergies compute correctly

Verify:
- pytest tests/test_analysis.py
- python main.py --help
```

### Acceptance Criteria

| ID  | Test                                                   |
|-----|--------------------------------------------------------|
| 5A  | Marginals correct on synthetic data                    |
| 5B  | Synergies correct on synthetic data                    |
| 5C  | Markdown report generates without error                |
| 5D  | python main.py --help shows all commands               |
| 5E  | full-pipeline orchestrates all components              |
| 5F  | test_analysis.py passes                                |
