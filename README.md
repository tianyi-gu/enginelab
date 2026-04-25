# EngineLab

Interpretable strategy-discovery system for chess variants via exhaustive feature-subset testing with alpha-beta search engines.

Given a chess variant and a set of evaluation features, EngineLab creates one alpha-beta engine per feature subset, runs a full round-robin tournament, and analyzes which strategic concepts -- alone and in combination -- produce winning play. The system includes a CLI pipeline, an interactive Streamlit UI, and automated chart/report generation.

## How It Works

1. **Define features** -- 10 evaluation features capture different strategic concepts (material, mobility, king safety, etc.)
2. **Generate agents** -- Each agent uses a unique subset of features with equal weights. Default: 100 agents via stratified sampling (all 10 singletons + all 45 pairs + the full set + random larger subsets). For 5 or fewer features, all 2^n - 1 subsets are generated exhaustively.
3. **Run tournament** -- Full round-robin where every ordered pair plays one game (agent A as white vs B, and B as white vs A). With 100 agents, that's 9,900 games.
4. **Analyze results** -- Feature marginal contributions (average score with vs. without each feature), pairwise synergy (do two features perform better together than their individual contributions predict?), and top-k frequency analysis.
5. **Generate outputs** -- Markdown strategy report, 16 PNG charts with HTML dashboard, and exportable CSV data.

## Key Findings

### Atomic Chess (depth 3, 13 agents, 156 games)

**Champion: `capture_threats + enemy_king_danger` (87.5% score rate, undefeated)**

At depth 3, the combination of capture awareness and enemy king proximity dominance produced a dominant engine. This aligns with atomic chess theory: captures trigger explosions that destroy adjacent pieces, so controlling which captures happen (and threatening the enemy king via adjacent explosions) is the core strategic axis.

### Atomic Chess (depth 2, 30 agents, 870 games)

**Champion: `bishop_pair + mobility` (81.9% score rate)**

At depth 2, mobility (move count advantage) paired with the bishop pair bonus emerged as the strongest combination. This shifted at depth 3 as deeper search exposed the importance of tactical capture-based play over positional mobility.

## Quick Start

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline (atomic chess, depth 2)
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80

# Run tournament only
python main.py tournament --variant atomic --depth 2

# Play against the engine interactively (CLI)
python main.py play --variant atomic --depth 3 --features capture_threats,enemy_king_danger

# Launch the Streamlit UI
streamlit run ui/app.py --server.port 8502

# Generate charts (after running export_data.py)
python export_data.py
python generate_charts.py atomic
```

## CLI Commands

Built with Typer. Run `python main.py --help` for full usage.

| Command | Description |
|---------|-------------|
| `full-pipeline` | End-to-end: generate agents, run tournament, analyze, generate report |
| `tournament` | Run round-robin tournament only, save results JSON |
| `analyze` | Analyze existing results JSON (marginals, synergy, interpretation) |
| `match` | Single game between two feature-set agents |
| `random-game` | Random-vs-random game (for testing) |
| `play` | Interactive human-vs-engine mode in the terminal (UCI input) |

### Common Options

- `--variant`: `standard`, `atomic`, or `antichess` (default: `standard`)
- `--depth`: Search depth for alpha-beta (default: `2`)
- `--max-moves`: Maximum plies before draw (default: `80`)
- `--seed`: RNG seed for determinism (default: `42`)
- `--max-agents`: Cap on agent count for stratified sampling (default: `100`)

## Streamlit UI

The web interface provides a complete visual experience for running tournaments and exploring results.

```bash
streamlit run ui/app.py --server.port 8502
```

### Views

- **Home** -- Animated landing page with project overview.
- **Build** -- Configure a new tournament (variant, features, depth) or load existing results from `outputs/data/`.
- **Live** -- Real-time tournament progress with progress bar, game count, and time estimates. Tournament runs in a background thread.
- **Analysis** -- Five tabs of results:
  - **Best Engine**: Winning agent details, score rate, W/D/L, feature pills, runners-up, and "Play Against Best Engine" button.
  - **Features**: Marginal contribution bar chart + top-10 feature frequency chart (Plotly).
  - **Synergy**: Top synergy/redundancy pairs + full pairwise heatmap (Plotly).
  - **Stats**: Score distribution, game length histogram, W/D/L stacked bars, termination pie chart, feature count vs. performance scatter (Plotly).
  - **Leaderboard**: Sortable table of top 20 agents + download buttons for report and results.
- **Play** -- Interactive play against the tournament's best engine. Click-to-move chessboard (chessboard.js), legal move highlighting, last-move highlighting, atomic explosion highlighting, promotion modal. All game logic runs server-side using real variant dispatch (same engine as CLI/tournaments). Engine replies come from AlphaBetaEngine with the champion's feature weights.

### Play Mode Details

Moves are validated and applied server-side using the same variant-aware engine that powers tournaments:

- `get_legal_moves_uci()` -- generates legal moves via variant dispatch
- `apply_move_for_ui()` -- applies moves with real explosion/forced-capture logic
- `engine_reply()` -- uses `AlphaBetaEngine` with the tournament champion's features
- `game_status_variant()` -- detects checkmate, stalemate, and variant-specific terminal states (king explosion, piece depletion)

## Evaluation Features

All 10 features compute a differential score (positive = good for the side to move):

| Feature | Description |
|---------|-------------|
| `material` | Piece value sum (P=1, N=3, B=3, R=5, Q=9). Own minus opponent. |
| `piece_position` | Piece-square table bonuses. Rewards centralized knights, advanced pawns, etc. |
| `center_control` | Piece presence (+2.0) and attacks (+1.0) on the four center squares (d4/d5/e4/e5). |
| `king_safety` | Adjacent pawn shield (+1.0), penalizes open files near king (-1.0) and nearby enemy pieces (-0.5). |
| `enemy_king_danger` | Proximity of own pieces to enemy king (inverse Chebyshev distance) + attacks on squares adjacent to enemy king. |
| `mobility` | Pseudo-legal move count differential. |
| `pawn_structure` | Penalizes doubled (-0.5) and isolated (-0.5) pawns. Rewards passed (+1.0) and connected (+0.3) pawns. |
| `bishop_pair` | +0.5 bonus if side has two or more bishops. |
| `rook_activity` | Open file (+0.5), semi-open file (+0.25), and 7th rank (+0.5) bonuses for rooks. |
| `capture_threats` | Sum of values of pieces that can be captured this turn. |

## Search Engine

**Algorithm:** Negamax with alpha-beta pruning.

- Configurable search depth (1-3 typical).
- Move ordering: captures sorted by victim value (MVV) first, then quiet moves.
- Terminal detection: checkmate (returns loss score), stalemate (returns 0), variant-specific (king explosion, piece depletion).
- Instrumentation: tracks `nodes_searched` and `search_time_seconds` per move.

## Chess Variant Rules

### Standard Chess

Full implementation: castling (kingside/queenside, all 5 legality conditions), en passant, promotion (Q/R/B/N), check detection via reverse-lookup attack tables. Legal moves filtered to exclude self-check. Deterministic piece iteration order (row 0-7, col 0-7).

### Atomic Chess

- **Explosion on capture:** Both capturing and captured pieces are destroyed.
- **Adjacent destruction:** All non-pawn pieces within 1 square of the capture are destroyed. Pawns are immune to explosions.
- **King explosion:** If a king is destroyed in an explosion, that side loses immediately. If both kings are destroyed, the capturing side loses.
- **Self-preservation:** Captures that would explode the capturing side's own king are filtered as illegal.
- **Castling rights:** Updated after explosions (revoked if king or rook was destroyed in blast).

### Antichess

- **Forced captures:** If any capture is available, the player must capture.
- **Winning condition:** Lose all your pieces to win.

## Analysis Methods

### Feature Marginals

For each feature f:
- `avg_score_with` = mean score rate of all agents containing f
- `avg_score_without` = mean score rate of all agents not containing f
- `marginal` = difference (positive means the feature helps)
- `top_k_frequency` = fraction of top-k agents containing f

### Pairwise Synergy

For each pair (a, b):
- `synergy = avg_with_both - avg_with_a - avg_with_b + overall_avg`
- Positive synergy: the pair is worth more together than the sum of parts.
- Negative synergy: the features are redundant.

### Interpretation

Natural-language summary covering the best agent, top 3 positive-marginal features, least valuable feature, strongest synergy pair, and most redundant pair.

## Chart Generation

Two scripts generate publication-ready visualizations from tournament data:

```bash
python export_data.py          # Export tournament results to CSV/JSON
python generate_charts.py      # Generate all charts for all variants
python generate_charts.py atomic  # Generate charts for one variant
```

### 16 Charts Per Variant

| # | Chart | Description |
|---|-------|-------------|
| 01 | Leaderboard | Agent score rate bar chart |
| 02 | Win/Loss/Draw | Stacked bar chart per agent |
| 03 | Feature Importance | Marginal contribution bar chart |
| 04 | Feature Presence | Avg score with vs. without each feature |
| 05 | Synergy Heatmap | Pairwise synergy matrix |
| 06 | Matchup Heatmap | Head-to-head win rates |
| 07 | Termination Pie | Game outcome distribution |
| 08 | Game Length Dist | Game length histogram |
| 09 | Length by Winner | Game length by outcome (box plot) |
| 10 | Feature Count Perf | Performance by number of features |
| 11 | Top-K Frequency | Feature frequency among top agents |
| 12 | Nodes vs Length | Search complexity vs game length |
| 13 | White Advantage | First-move advantage analysis |
| 14 | Score Distribution | Agent score rate histogram |
| 15 | Top Synergies | Strongest synergy/redundancy pairs |
| 16 | Score vs Length | Score rate vs average game length |

Each variant also gets an `index.html` dashboard that displays all charts with summary stats.

## Project Structure

```
core/                   Board, Move, move generation, coordinate helpers
  board.py              8x8 board representation, FEN parsing, terminal detection
  move.py               Frozen Move dataclass with UCI conversion
  move_generation.py    Pseudo-legal and legal move generation (all piece types)
  apply_move.py         Standard move application (castling, en passant, promotion)
  coordinates.py        Algebraic <-> (row, col) conversion
  types.py              Square type alias, piece color/type helpers

variants/               Chess variant implementations
  base.py               Variant dispatch: get_apply_move(), get_generate_legal_moves()
  standard.py           Standard chess (delegates to core/)
  atomic.py             Atomic chess (explosions, self-preservation, king destruction)
  antichess.py          Antichess (forced captures, lose-all-pieces-to-win)

features/               Evaluation feature implementations
  registry.py           FEATURES dict mapping names to callables (10 features)
  material.py           Material balance
  mobility.py           Move count differential
  king_safety.py        Pawn shield + king exposure
  king_danger.py        Piece proximity to enemy king
  capture_threats.py    Capturable piece values
  piece_position.py     Piece-square table bonuses
  center_control.py     Center square control
  pawn_structure.py     Doubled/isolated/passed/connected pawns
  bishop_pair.py        Bishop pair bonus
  rook_activity.py      Open file and 7th rank bonuses

agents/                 Agent generation and evaluation
  feature_subset_agent.py   Frozen FeatureSubsetAgent dataclass
  generate_agents.py        Exhaustive or stratified subset generation
  evaluation.py             Board evaluation using agent's feature weights

search/                 Search engine
  alpha_beta.py         Negamax with alpha-beta pruning, MVV move ordering

simulation/             Game simulation
  game.py               play_game() and mock_play_game(), GameResult dataclass
  random_agent.py       RandomAgent for testing

tournament/             Tournament infrastructure
  round_robin.py        Full round-robin scheduling and execution
  leaderboard.py        Win/draw/loss scoring and ranking
  results_io.py         JSON and CSV serialization

analysis/               Statistical analysis
  feature_marginals.py  Marginal contribution of each feature
  synergy.py            Pairwise synergy computation
  interpretation.py     Natural-language result summary

reports/                Output generation
  markdown_report.py    Markdown strategy report with tables and interpretation

ui/                     Streamlit web interface
  app.py                Main app: build, live, analysis, play views
  chess_viewer.py       Game replay viewer + click-to-move play board (chessboard.js)
  play_engine.py        Server-side move application and engine reply
  board.py              SVG board renderer (python-chess)
  home.py               Animated landing page
  constants.py          Session state defaults, feature display names

main.py                 CLI entry point (Typer)
export_data.py          Export tournament data to CSV/JSON for charts
generate_charts.py      Generate 16 PNG charts + HTML dashboard per variant
run_depth3.py           Depth-3 atomic tournament script (13 agents)

tests/                  302 tests across 10 test files
  test_board.py         Board class: layout, copy, FEN
  test_move_generation.py   All piece types, castling, en passant, check
  test_standard.py      Standard variant: apply_move, full games
  test_atomic.py        Atomic: explosions, self-preservation, king destruction
  test_antichess.py     Antichess: forced captures, win condition
  test_features.py      All 10 features: registry, return types, starting values
  test_agents.py        Agent generation, naming, weight normalization
  test_alpha_beta.py    Search: depth-1 behavior, captures hanging pieces
  test_tournament.py    Round-robin, leaderboard, results I/O
  test_analysis.py      Marginals, synergy, interpretation, report generation

outputs/
  data/                 Tournament result JSONs + exported CSV/JSON per variant
  charts/               16 PNG charts + index.html dashboard per variant
  reports/              Markdown strategy reports per variant
```

## Dependencies

```
pytest>=8.0.0           Testing
pandas>=2.0.0           Data manipulation
numpy>=1.26.0           Numerical computation
tqdm>=4.66.0            CLI progress bars
typer>=0.12.0           CLI framework
rich>=13.0.0            Rich terminal output
pydantic>=2.0.0         Data validation
matplotlib>=3.8.0       Chart generation
streamlit>=1.33.0       Web UI
plotly>=5.0.0           Interactive charts (Streamlit)
chess>=1.10.0           SVG board rendering, standard game status
```

## Running Tests

```bash
pytest                                    # All 302 tests
pytest tests/test_board.py tests/test_move_generation.py tests/test_standard.py  # Foundation
pytest tests/test_atomic.py tests/test_features.py tests/test_agents.py tests/test_alpha_beta.py  # Engine
pytest tests/test_tournament.py tests/test_analysis.py                           # Harness
```

## Determinism

All output is deterministic given the same seed. Move generation iterates pieces in fixed order (row 0-7, col 0-7). Use `random.Random(seed)` (local instance), never `random.seed()` on the global RNG. Run the pipeline twice with the same seed and diff the outputs to verify.

## Conventions

- **Pieces:** FEN characters. Uppercase = white (`P N B R Q K`), lowercase = black (`p n b r q k`), empty = `None`
- **Colors:** Always `"w"` or `"b"`. Never `"white"` / `"black"` in data structures.
- **Coordinates:** `grid[row][col]`. Row 0 = rank 1 (white side). Col 0 = file a.
- **Agent names:** `Agent_{feat1}__{feat2}` -- double underscore separator, features sorted alphabetically, weights equal (1/N each).
