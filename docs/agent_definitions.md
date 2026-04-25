# Agent Definitions

This document defines the exact scope, prompts, and acceptance criteria for
each developer (or Claude Code agent) working on EngineLab. The project is
split into a shared Foundation and two parallel development areas.

---

## Foundation: Working Chess Engine (Built First on `main`)

### Goal

Deliver a minimal but complete standard chess engine that both developers
can branch from. Includes full move generation (castling, en passant,
promotion to all pieces), check legality, standard variant, material-only
evaluation, basic alpha-beta at depth 1, and a working `play_game()`.

### Files

```
core/__init__.py, core/types.py, core/board.py, core/move.py
core/coordinates.py, core/move_generation.py, core/apply_move.py
variants/__init__.py, variants/base.py, variants/standard.py
agents/__init__.py, agents/feature_subset_agent.py, agents/evaluation.py
search/__init__.py, search/alpha_beta.py
simulation/__init__.py, simulation/game.py
+ all __init__.py files and stubs for remaining modules
```

### Prompt

```
You are building the Foundation of EngineLab: a complete, runnable standard
chess engine that other developers will build on.

Read Instructions.md and docs/interfaces.md completely before starting.

Implement:
1. Board class (core/board.py): 8x8 grid, FEN piece chars, deep copy,
   castling_rights dict, en_passant_square field.
2. Move dataclass (core/move.py): frozen, UCI output, promotion field.
3. Square type alias, color helpers (core/types.py).
4. Full pseudo-legal move generation (core/move_generation.py):
   - All piece types (pawn, knight, bishop, rook, queen, king)
   - Castling (kingside and queenside, with rights tracking)
   - En passant capture
   - Promotion to all 4 piece types (Q, R, B, N)
   - Deterministic order: iterate row 0-7, col 0-7
5. Check detection: is_square_attacked, is_in_check
6. Legal move generation: pseudo-legal filtered by check legality
7. Standard variant (variants/standard.py): apply move, generate legal
   moves, winner detection (king captured = opponent wins)
8. Variant dispatch (variants/base.py): register "standard"
9. Material-only evaluation: simple material difference eval
10. Basic AlphaBetaEngine at depth 1
11. Minimal play_game() in simulation/game.py
12. Stub files for ALL remaining interfaces (raise NotImplementedError)

CRITICAL conventions:
- FEN pieces: uppercase=white, lowercase=black, None=empty
- Colors: "w" / "b" only
- Coordinates: grid[row][col], row 0 = rank 1, col 0 = file a
- Board.copy() must be a deep copy
- Castling rights: {"K": True, "Q": True, "k": True, "q": True}
- En passant: set en_passant_square when pawn double-pushes, clear otherwise

Verify:
- Board starting position correct, copy is deep
- 20 pseudo-legal white moves from starting position
- Castling generates correctly
- En passant capture works
- Promotion to all 4 piece types works
- Legal move filter removes moves leaving king in check
- Standard game completes (material-only eval, depth 1)
```

### Acceptance Criteria

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 0A  | Board starting position correct, copy() is deep                  |
| 0B  | Starting position generates exactly 20 white pseudo-legal moves  |
| 0C  | Castling generates correctly (kingside and queenside)            |
| 0D  | En passant capture works                                         |
| 0E  | Promotion to all 4 piece types works                             |
| 0F  | Legal move filter removes moves that leave king in check         |
| 0G  | Standard game completes (material-only eval, depth 1)            |
| 0H  | Variant dispatch resolves "standard" correctly                   |

---

## Developer 1: Variants, Features & Search (ENGINE)

### Branch

`area-1-engine`

### Files Owned

```
core/move_generation.py        # extend for variant-specific filtering
core/apply_move.py             # extend for variant-specific application
variants/atomic.py
variants/antichess.py
variants/standard.py           # extend if needed
variants/base.py               # register new variants
features/__init__.py
features/registry.py
features/material.py
features/piece_position.py
features/center_control.py
features/king_safety.py
features/king_danger.py
features/mobility.py
features/pawn_structure.py
features/bishop_pair.py
features/rook_activity.py
features/capture_threats.py
agents/feature_subset_agent.py
agents/generate_agents.py
agents/evaluation.py
agents/__init__.py
search/alpha_beta.py
search/__init__.py
tests/test_board.py
tests/test_move_generation.py
tests/test_standard.py
tests/test_atomic.py
tests/test_antichess.py
tests/test_features.py
tests/test_agents.py
tests/test_alpha_beta.py
```

### Must Not Edit

`simulation/`, `tournament/`, `analysis/`, `reports/`, `ui/`, `main.py`

### Prompt

```
You are implementing Area 1 of EngineLab: the complete chess ENGINE --
variant rules, evaluation features, agent generation, and alpha-beta search.

Read Instructions.MD and docs/interfaces.md completely before starting.

PHASE 1 -- Atomic Chess:
1. Atomic variant (variants/atomic.py):
   - apply_atomic_move: explosion on capture (removes capturing piece,
     captured piece, and all adjacent non-pawn pieces; pawns immune)
   - generate_atomic_moves: filter captures that would explode own king
   - Winner detection on king explosion
   - Register "atomic" in VARIANT_DISPATCH

PHASE 2 -- Full Feature Library (10 features):
All features: feature(board, color) -> float. Positive = good for color.
Must not mutate board.

Material:
2. material: own material - opponent material (P=1, N=3, B=3, R=5, Q=9, K=0)

Positional:
3. piece_position: piece-square table bonus (standard tables from chess
   programming literature)
4. center_control: pieces on/attacking d4,d5,e4,e5 (center pieces count 2x)

Safety:
5. king_safety: +1 per adjacent own pawn, -1 per open file near king,
   -0.5 per enemy piece within Chebyshev distance 3
6. enemy_king_danger: per own piece += 1/max(chebyshev_dist, 1);
   per adjacent enemy king square attacked += 1

Dynamic:
7. mobility: own legal move count - opponent legal move count
8. pawn_structure: -0.5 doubled, -0.5 isolated, +1.0 passed, +0.3 connected
9. bishop_pair: +0.5 if 2+ bishops, else 0
10. rook_activity: +0.5 open file, +0.25 semi-open, +0.5 on 7th rank
11. capture_threats: sum capturable piece values; for atomic add 3x
    adjacent explosions + 100x king explosion

Registry: FEATURES dict, FEATURE_DESCRIPTIONS, get_feature_names(),
get_feature_function(), get_feature_description()

PHASE 3 -- Agent Generation & Evaluation:
12. Dual-mode agent generation:
    - Exhaustive if 2^n - 1 <= max_agents (default 100)
    - Stratified sampling otherwise (all singles, all pairs, full set,
      random larger subsets)
    - Uniform weights: 1/len(subset)
    - Names: sorted features joined by "__", prefixed "Agent_"
13. evaluate(board, color, agent): weighted normalized features, WIN/LOSS
    for terminals. normalize: clip [-10,10], divide by 10.
14. contributions(board, color, agent): per-feature weighted contribution

PHASE 4 -- Production Alpha-Beta:
15. Negamax with alpha-beta pruning
    - Move ordering: captures first (by victim value descending)
    - choose_move(board) -> Move (must always return legal move)
    - Track nodes_searched and search_time_seconds
    - Variant-aware: use get_apply_move(variant), get_generate_legal_moves(variant)

PHASE 5 -- Antichess (optional):
16. apply_antichess_move: same as standard, winner = no pieces left
17. generate_antichess_moves: if captures exist, return only captures

Verify each phase before moving to the next:
Phase 1: pytest tests/test_atomic.py
Phase 2: pytest tests/test_features.py
Phase 3: pytest tests/test_agents.py
Phase 4: pytest tests/test_alpha_beta.py
Phase 5: pytest tests/test_antichess.py
```

### Acceptance Criteria

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 1A  | Atomic explosion removes correct pieces, pawns survive           |
| 1B  | Self-preservation: captures exploding own king filtered          |
| 1C  | 100 random atomic plies without crash                            |
| 1D  | material at starting position returns 0.0                        |
| 1E  | All 10 feature functions return floats                           |
| 1F  | No feature mutates the board                                     |
| 1G  | pawn_structure detects doubled and passed pawns                  |
| 1H  | 5 features -> 31 agents, all names unique, weights sum to 1.0   |
| 1I  | evaluate returns numeric float for non-terminal boards           |
| 1J  | Alpha-beta returns legal move at depth 1 and depth 2            |
| 1K  | (Optional) Antichess forced capture and win condition work       |

---

## Developer 2: Tournament, Analysis & CLI (HARNESS)

### Branch

`area-2-harness`

### Files Owned

```
simulation/game.py
simulation/random_agent.py
simulation/__init__.py
tournament/round_robin.py
tournament/leaderboard.py
tournament/results_io.py
tournament/__init__.py
analysis/feature_marginals.py
analysis/synergy.py
analysis/interpretation.py
analysis/__init__.py
reports/markdown_report.py
reports/__init__.py
main.py
ui/app.py
tests/test_tournament.py
tests/test_analysis.py
```

### Must Not Edit

`core/`, `variants/`, `features/`, `agents/`, `search/`

### May Import From

All modules (at integration time). During development, use mock_play_game()
with zero ENGINE imports.

### Prompt

```
You are implementing Area 2 of EngineLab: the complete HARNESS --
tournament infrastructure, statistical analysis, reporting, and CLI.

Read Instructions.MD and docs/interfaces.md completely before starting.

CRITICAL: During development, use mock_play_game() that returns random
GameResults. This lets you build and test your ENTIRE pipeline with zero
imports from the ENGINE (Area 1). At integration time, swap the mock for
the real play_game -- a one-line change.

Implement:

1. mock_play_game(white, black, **kwargs) -> GameResult:
   Use random.Random(seed) for deterministic mock results.

2. RandomAgent: choose_move returns random legal move for given variant.

3. GameResult dataclass:
   white_agent, black_agent, winner ("w"/"b"/None), moves,
   termination_reason, avg nodes/time per side.

4. play_game(white, black, variant, depth, max_moves, seed) -> GameResult:
   White moves first. Use AlphaBetaEngine for FeatureSubsetAgent,
   RandomAgent directly. Apply variant-dispatched moves. Terminate on
   winner, no legal moves, or move cap. Seed with random.Random(seed).

5. run_round_robin(agents, variant, depth, max_moves, seed):
   Every ordered pair (A as white, B as black). N*(N-1) games.
   tqdm progress bar. Per-game seed = tournament_seed + game_index.
   Optional multiprocessing with --workers flag.

6. save_results_json, load_results_json, save_results_csv.

7. compute_leaderboard(results, agents):
   win=1, draw=0.5, loss=0. score_rate = (wins+0.5*draws)/games_played.
   Sort descending by score_rate.

8. compute_feature_marginals(leaderboard, feature_names, top_k=10):
   avg_score_with, avg_score_without, marginal, top_k_frequency.

9. compute_pairwise_synergies(leaderboard, feature_names):
   synergy(a,b) = avg_with_both - avg_with_a - avg_with_b + overall_avg

10. generate_interpretation(best_agent, marginals, synergies, variant):
    Natural-language paragraph about findings.

11. generate_markdown_report(...):
    Sections: title, summary, variant, features, config, top-10
    leaderboard, best subset, marginals, synergies, interpretation,
    limitations.

12. CLI with Typer (main.py):
    - random-game: play random vs random
    - match: play specific feature sets against each other
    - tournament: run round-robin
    - analyze: analyze existing results JSON
    - full-pipeline: end-to-end pipeline

13. Optional: Streamlit UI in ui/app.py

Test your analysis functions on synthetic data first:
- Create fake LeaderboardRow lists with known values
- Verify marginals and synergies compute correctly
- Use mock_play_game for tournament tests

Verify:
- pytest tests/test_tournament.py tests/test_analysis.py
- python main.py --help
```

### Acceptance Criteria

| ID  | Criterion                                                        |
|-----|------------------------------------------------------------------|
| 2A  | Random vs random game completes (with mock or real play_game)    |
| 2B  | FeatureSubsetAgent vs FeatureSubsetAgent game completes          |
| 2C  | 3 agents produce 6 ordered games                                 |
| 2D  | Leaderboard contains all agents with correct game counts         |
| 2E  | Results save to JSON and load back identically                   |
| 2F  | Feature marginals correct on synthetic leaderboard data          |
| 2G  | Synergy analysis correct on synthetic leaderboard data           |
| 2H  | Markdown report generates without error                          |
| 2I  | python main.py --help shows all commands                         |
| 2J  | full-pipeline calls all components end-to-end                    |
| 2K  | pytest tests/test_tournament.py tests/test_analysis.py passes    |
