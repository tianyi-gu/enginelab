# SPEC: EngineLab Streamlit UI (`ui/app.py`)

## 1. Purpose & Scope

`ui/app.py` is the interactive dashboard for EngineLab. It wraps the full
pipeline — agent generation, tournament, analysis, and reporting — in a
browser-based UI built entirely with Streamlit.

The primary audiences are:

1. **Researcher / operator** — configures and launches tournaments, loads
   prior results, digs into marginal contributions and synergies.
2. **Demo viewer / judge** — watches the story of a tournament play out: how
   engines competed, which feature combinations dominated, and *why*.

The interface tells a single narrative: *"We built every possible engine,
ran a tournament, and discovered which strategies actually win."* Every page
is a chapter of that story. The most important thing to communicate is
**process** — not just the final leaderboard, but how the best engine emerged
from the competition.

The app operates in two distinct modes:

- **Live mode** — tournament is running. Show it happening: progress, a live
  leaderboard reshuffling in real time, and a chess game playing out in the
  corner. This is the demo's centrepiece.
- **Results mode** — tournament is done. Let the user explore the data:
  leaderboard, marginals, synergies, cross-variant comparison, report.

This spec is the single source of truth for all UI behavior. Where it
conflicts with `AGENTS.md`, the more restrictive rule wins.

---

## 2. Technology Constraints

- **Framework:** Streamlit only. No React, no Flask, no additional web
  frameworks.
- **Charts:** Plotly (`st.plotly_chart`) preferred over matplotlib for
  interactivity (hover, zoom, click). Use `matplotlib` / `st.pyplot` only
  where Plotly cannot achieve the required effect.
- **State management:** `st.session_state` exclusively. No global
  module-level mutable variables.
- **Backend calls:** All heavy computation (tournament, analysis) runs in a
  background thread via `threading.Thread`. The UI must never block the main
  thread for more than ~100 ms without a spinner.
- **Board rendering:** Use `python-chess` (`chess.svg`) for all non-interactive
  boards. Use `chessboard.js` embedded via `st.components.v1.html()` for the
  interactive human-vs-engine mode only. Do not build boards from scratch.
- **Imports:** The UI imports only from `simulation`, `tournament`,
  `analysis`, `reports`, and `agents` public APIs. Do **not** import from
  `core/`, `variants/`, `features/`, or `search/` directly.
- **No CLI subprocess calls.** Call Python functions directly.
- **No Plotly/Altair** if not already in `requirements.txt` — add
  `plotly>=5.0.0` to `requirements.txt` as part of this task.

---

## 3. Page Architecture

The app uses Streamlit's multi-page structure:

```
ui/
├── app.py                   # Entry point — sidebar config + page routing
└── pages/
    ├── 1_lab.py             # Home / configure / load previous results
    ├── 2_tournament.py      # Live tournament progress + emerging leaderboard
    ├── 3_analysis.py        # All analysis charts and tables (tabbed)
    ├── 4_explorer.py        # Build-your-own-engine interactive tool
    └── 5_play_watch.py      # Human vs engine + game replay / live matchup
```

`ui/app.py` must begin with:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

to ensure the repo root is on the Python path regardless of working
directory. The app is launched with:

```bash
streamlit run ui/app.py
```

---

## 4. Design Direction

**Aesthetic:** Industrial / utilitarian — like a research instrument, not a
consumer app. Think chess engine GUIs, quant trading terminals, and
scientific dashboards. Dark background (`#0e1117` or similar), tight
monospace labels, dense data tables, aggressive use of green/red for
positive/negative signals. Every pixel is functional. No decorative
gradients, no rounded cards for their own sake.

**Typography:** Monospace or semi-monospace for data values, labels, and
agent names (they contain `__` separators — they look like code). A
condensed sans-serif for headings (e.g., IBM Plex Mono for data, IBM Plex
Sans Condensed for headings). Avoid Inter, Roboto, Arial.

**Color system (CSS variables / Streamlit theme config):**

```toml
# .streamlit/config.toml
[theme]
base = "dark"
primaryColor = "#00e676"       # signal green
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#161b22"
textColor = "#e6edf3"
font = "monospace"
```

Positive values → `#00e676` (green). Negative values → `#ff4d4d` (red).
Neutral / near-zero → `#8b949e` (muted gray). Explosion highlights in
Atomic Chess → `#ff6b35` (orange).

**The one thing people remember:** The live tournament page. Watching 30+
engines compete in real time — a leaderboard reshuffling as games complete,
a live chess game unfolding in the corner, eval bars shifting — is the
demo's centerpiece. Build this first and build it well.

---

## 5. Persistent Sidebar

The sidebar is visible on all pages and controls the experiment parameters.

```
─────────────────────────────
  🧪 EngineLab
  Interpretable Strategy Discovery
─────────────────────────────
  Chess Variant
    ○ Standard Chess
    ● Atomic Chess
    ○ Antichess

  [variant description, one sentence]

  Strategic Features    [Select All]
    ☑ Material Balance          (material)
    ☑ Piece Position            (piece_position)
    ☑ Center Control            (center_control)
    ☑ King Safety               (king_safety)
    ☑ Enemy King Danger         (enemy_king_danger)
    ☑ Mobility                  (mobility)
    ☑ Pawn Structure            (pawn_structure)
    ☑ Bishop Pair               (bishop_pair)
    ☑ Rook Activity             (rook_activity)
    ☑ Capture Threats           (capture_threats)

  Search Depth      [2] ──────●──
  Max Moves per Game [80] ────────●
  Parallel Workers   [1] ●────────
  Random Seed        [42]  __________

  [▶ Run Tournament]
─────────────────────────────
  Est. agents:   87
  Est. games:  7,482
  Est. runtime: ~15 min (1 worker)
  ⚠ Runtime may exceed 30 min
─────────────────────────────
  ── Load Existing Results ──
  [Upload tournament JSON]
─────────────────────────────
```

### 5.1 Variant Selector

- Widget: `st.radio` (not `st.selectbox` — radio makes all options visible,
  better for a 3-item list in a research tool).
- Options (display → internal key):
  - `"Standard Chess"` → `"standard"`
  - `"Atomic Chess"` → `"atomic"`
  - `"Antichess"` → `"antichess"`
- Default: `"atomic"`.
- Variant description (one sentence, rendered as `st.caption`):
  - standard: *"Win by checkmating the king. Material and mobility dominate."*
  - atomic: *"Captures cause explosions. King danger and explosion threats dominate."*
  - antichess: *"Lose all your pieces to win. Material is a liability."*
- State key: `st.session_state["variant"]`

### 5.2 Feature Checkboxes

- `st.subheader("Strategic Features")` with a `[Select All]` / `[Clear All]`
  toggle link next to it (rendered via `st.button` in a `st.columns([3,1])`
  row).
- One `st.checkbox` per feature, fixed display order as shown above.
- All 10 checked by default on first load.
- A live estimate below the checkboxes:
  ```
  Est. agents:   87    Est. games:  7,482
  ```
  Formula: `agents = min(2^n - 1, 100)`, `games = agents * (agents - 1)`.
  Updates live as checkboxes change. Use `st.caption`.
- If runtime estimate > 30 min (games > ~9,000 at depth 2): show
  `st.warning("⚠ Long runtime — consider reducing features or using more workers.")`.
- If < 2 features selected: show `st.warning("Select at least 2 features.")`
  and disable Run button.
- State key: `st.session_state["selected_features"]` — `list[str]` of
  selected internal keys.

### 5.3 Sliders and Seed

| Widget | Label | Range | Default | Step | State key |
|--------|-------|-------|---------|------|-----------|
| `st.slider` | Search Depth | 1–3 | 2 | 1 | `depth` |
| `st.slider` | Max Moves per Game | 20–150 | 80 | 10 | `max_moves` |
| `st.slider` | Parallel Workers | 1–8 | 1 | 1 | `workers` |
| `st.number_input` | Random Seed | 0–999999 | 42 | 1 | `seed` |

- Depth caption: *"Depth 1: fast (~seconds). Depth 2: standard (~minutes). Depth 3: slow (~hours)."*
- Workers caption: *"Workers > 1 enables multiprocessing. Use 1 for deterministic debugging."*

### 5.4 Run Tournament Button

- `st.button("▶ Run Tournament", type="primary", use_container_width=True)`
- Disabled when: < 2 features selected, or `st.session_state["running"]
  is True`.
- On click: snapshot config, clear all results keys, set `running = True`,
  launch background tournament thread, navigate to Page 2.
- While running: replace button area with a `st.progress` bar and
  `st.caption("Game N / M  ·  elapsed Xm Ys  ·  est. remaining Ym Zs")`.
  Progress updates at most once per 50 games.

### 5.5 Load Results

- `st.divider()`
- `st.subheader("Load Existing Results")`
- `st.file_uploader("Upload tournament JSON", type=["json"])`
- On upload: call `load_results_json(file)`, run analysis pipeline,
  populate session state. Show `st.success("Results loaded.")` or
  `st.error(...)` on failure.

---

## 6. Session State Schema

```python
# Configuration (set by sidebar)
st.session_state["variant"]              # str
st.session_state["selected_features"]   # list[str]
st.session_state["depth"]               # int
st.session_state["max_moves"]           # int
st.session_state["workers"]             # int
st.session_state["seed"]                # int

# Runtime state
st.session_state["running"]             # bool
st.session_state["progress"]            # float: 0.0–1.0
st.session_state["games_completed"]     # int
st.session_state["total_games"]         # int
st.session_state["start_time"]          # float: time.time() at tournament start
st.session_state["error"]               # str | None
st.session_state["skipped_games"]       # int

# Results
st.session_state["results"]             # list[GameResult] | None
st.session_state["agents"]              # list[FeatureSubsetAgent] | None
st.session_state["leaderboard"]         # list[LeaderboardRow] | None
st.session_state["marginals"]           # list[FeatureContributionRow] | None
st.session_state["synergies"]           # list[SynergyRow] | None
st.session_state["interpretation"]      # str | None
st.session_state["report_md"]           # str | None
st.session_state["config_snapshot"]     # dict
st.session_state["duration_seconds"]    # float: wall-clock tournament time

# Per-page transient state
st.session_state["viewer_game_index"]   # int: selected game in Match Viewer
st.session_state["viewer_move_index"]   # int: current ply in Match Viewer
st.session_state["live_game_board"]     # Board | None: board in live tournament viewer
st.session_state["live_game_moves"]     # list[str]: UCI move strings for current live game
```

---

## 7. Tournament Execution Flow

When Run is clicked:

1. Snapshot config into `config_snapshot`. Navigate to Page 2.
2. Clear all results keys to `None`. Set `running = True`.
3. Launch `threading.Thread(target=_run_tournament, daemon=True)`.
4. Inside `_run_tournament`:
   a. `agents = generate_feature_subset_agents(features, max_agents=100, seed=seed)`
   b. `results = run_round_robin(agents, variant, depth, max_moves, seed, workers, on_game_complete=_progress_callback)`
   c. Compute leaderboard, marginals, synergies, interpretation, report.
   d. Populate session state atomically (write all result keys at once).
   e. Set `running = False`. Call `st.rerun()`.
5. `_progress_callback(games_done, total)`: updates `games_completed`,
   `progress`, calls `st.rerun()` if `games_done % 50 == 0`.
6. On any exception: set `error = str(e)`, `running = False`, `st.rerun()`.

---

## 8. Page Specifications

### Page 1: Lab (Home)

*Purpose:* Orient the user, pre-populate config, load prior results.

**Sections:**

**Header:**
```
🧪 EngineLab
Feature-Subset Strategy Discovery for Chess Variants
```

**The Analogy Panel** — render the quant finance mapping table from SPEC.md
Section 1. Use `st.dataframe` or a custom HTML table. This is the conceptual
hook — show it prominently.

| EngineLab | Finance |
|---|---|
| Evaluation feature | Risk factor |
| Feature-subset agent | Factor-model portfolio |
| Tournament win rate | Backtest return |
| Marginal feature contribution | Factor alpha |
| Pairwise feature synergy | Factor correlation |

**Quick Start Buttons** — three pre-configured presets rendered as
`st.columns(3)` with `st.button`:

| Button | Features | Est. agents | Est. games |
|---|---|---|---|
| ⚡ Debug (3 features) | material, mobility, king\_safety | 7 | 42 |
| 🔬 Demo (5 features) | material, mobility, king\_safety, enemy\_king\_danger, capture\_threats | 31 | 930 |
| 🧪 Full (10 features) | all 10 | ~87 | ~7,500 |

Each button pre-populates the sidebar and navigates to Page 2.

**Pipeline Diagram** — a static 5-step diagram using `st.columns` with
arrows:

```
Features  →  Agents  →  Tournament  →  Analysis  →  Report
   10       2^n – 1     Round-robin    Marginals    Markdown
```

**Previous Results** — scan `outputs/data/` for `*.json` files on disk.
List each as a clickable row:

| Variant | Date | Agents | Games | Load |
|---|---|---|---|---|
| atomic | 2025-04-20 | 87 | 7,482 | [Load] |

Clicking Load calls `load_results_json`, runs analysis pipeline, populates
session state, navigates to Page 3.

---

### Page 2: Tournament (The Process)

*Purpose:* Visualize the tournament as it runs. This is the centrepiece
demo page.

**Two states: Live (running) and Completed.**

#### Live State

**Status bar** (top, full width):
```
Running: Atomic Chess  ·  31 agents  ·  930 games
[████████████████░░░░░░░░░░░░░░░░] 54%   502 / 930 games
Time elapsed: 4:32  ·  Est. remaining: 3:51
```

`st.progress(progress_value)` + `st.caption` with elapsed / remaining.

**Two-column layout** — `st.columns([3, 2])`:

**Left column: Live Leaderboard**

A `st.dataframe` (height=400) updating every ~50 games. Columns:

| Rank | Agent | Score Rate | Games | Trend |
|---|---|---|---|---|
| 1 | `capture_threats__king_danger` | 0.71 | 60 | ↑ |
| 2 | `enemy_king_danger__mobility` | 0.64 | 58 | → |
| 3 | `material__king_safety` | 0.61 | 62 | ↓ |

- Trend arrow compares to rank 25 games ago: `↑` = climbing (green),
  `↓` = falling (red), `→` = stable (gray).
- Agent names shortened to feature subset only (strip `Agent_` prefix).
- Color Score Rate column green-to-red.

Below the leaderboard, a **Ranking Evolution Chart** (Plotly line chart):
- x = games played so far, y = score rate for top 5 agents.
- One line per agent. Renders curves converging as more games complete.
- Shows when rankings "settle." Updates every ~50 games.
- `plotly.graph_objects.Scatter` with `mode='lines'`.

**Live stats bar** (below chart):
```
Fastest game: 12 plies  ·  Longest: 80 plies  ·
Draws: 8%  ·  Avg nodes/move: 187
```

**Right column: Live Game Viewer**

While the tournament runs, one game plays out in real time.

```
Currently Playing           Move 14 / ~60
White: capture_threats + king_safety
Black: material + mobility

[chess board SVG]

Eval:  ████████░░░░░░░░  White +0.34
Last move: Nd5 (capture)
Features firing: capture_threats ↑↑  king_safety ↓
```

- Board: `chess.svg.board()` → `st.image(svg.encode())`. Re-renders after
  each move with ~0.3s delay.
- For Atomic Chess: pass `fill={square: "#ff6b3560"}` for exploded squares.
- Last move: use `chess.svg.board(board, lastmove=move)` for automatic arrow.
- **Eval bar:** a thin Plotly horizontal bar chart
  (`plotly.graph_objects.Bar`) with a single bar from –1 to +1, pointer at
  current eval. White side left (green), black side right (red).
- **"Features firing":** top 2 features by absolute contribution on this
  move, shown as text.
- Game cycles automatically (next game starts when current finishes).
  `[← Prev game]` / `[Next game →]` buttons to pin a specific matchup.

#### Completed State

Progress bar replaced by a green `st.success("Tournament complete!")` banner.

**Summary metrics** — `st.columns(4)`:

| Variant | Agents | Games | Duration |
|---|---|---|---|
| Atomic Chess | 87 | 7,482 | 23m 14s |

**Best agent card** (`st.success` with custom content):
```
Best Agent: Agent_capture_threats__enemy_king_danger__king_safety
Score Rate: 0.68  ·  Wins: 54  ·  Draws: 3  ·  Losses: 21
Features: capture_threats, enemy_king_danger, king_safety
```

**Top 5 features bar chart** (Plotly horizontal bar, green/red):
Features sorted by marginal contribution, top 5 shown.

**Navigation button:** `st.button("Explore Full Results →", type="primary")`
navigates to Page 3.

---

### Page 3: Analysis

*Purpose:* Full data exploration. Tabbed layout.

Tabs: `st.tabs(["Leaderboard", "Feature Intelligence", "Synergy", "Cross-Variant", "Report"])`

#### Tab A: Leaderboard

**Controls row** (`st.columns([3, 1, 1])`):
- `st.multiselect("Filter: agents containing features", options=feature_names)`
  — filters to agents whose feature set contains ALL selected features.
- `st.number_input("Show top N", min_value=5, value=20, step=5)`
- `st.download_button("⬇ CSV", ...)` exports filtered leaderboard.

**Main table** (`st.dataframe`, `use_container_width=True`, `height=500`):

| Column | Format |
|---|---|
| Rank | int, 1-indexed |
| Agent | `str`, strip `Agent_` prefix, truncate at 40 chars + `...` |
| Features | comma-separated display names, truncated |
| Score Rate | float, 4 dp, colored (Plotly-style via `column_config`) |
| W / D / L | int |
| Games | int |
| Avg Length | float, 1 dp |

Use `st.dataframe` with `column_config` to color Score Rate. Highlight top
row via pandas Styler `highlight_max`.

**Win Rate Distribution** (Plotly histogram, below table):
- x = score rate bins, y = agent count.
- Vertical dashed line at 0.5 ("random baseline").
- Title: *"How competitive is the field?"*

**Win Rate vs Feature Count** (Plotly scatter):
- x = feature count, y = score rate.
- Each point = one agent. Color = score rate (green-to-red).
- Trend line (linear fit via numpy). Hover shows agent name.
- Annotate best single-feature agent and best overall agent.
- Title: *"Does adding features help?"*

#### Tab B: Feature Intelligence

**Feature Marginal Contributions** (Plotly horizontal bar):
- One bar per feature, sorted descending by marginal.
- Green if marginal > 0, red if < 0, gray if |marginal| < 0.01.
- Hover shows: `avg_with`, `avg_without`, `marginal`.
- Title: *"How much does each feature help win rate?"*

**Feature Frequency in Top-K** (Plotly grouped bar):
- For K = 5, 10, 20: fraction of top-K agents containing each feature.
- 3 bars per feature, grouped.
- Title: *"Which features appear in top agents?"*

**Detailed marginals table** (`st.dataframe`):

| Feature | Avg Score With | Avg Score Without | Marginal | Top-10 Freq |
|---|---|---|---|---|
| enemy\_king\_danger | 0.6123 | 0.4471 | +0.1652 | 90% |

**Variant comparison callout:**
```python
st.info("Run the same pipeline on a different variant to compare feature "
        "rankings across rule sets. The cross-variant comparison will appear "
        "in the Cross-Variant tab.")
```

#### Tab C: Synergy

**Section header + explanation:**
```python
st.subheader("Pairwise Feature Synergy")
st.caption(
    "Synergy(A, B) = avg_with_both − avg_with_A − avg_with_B + overall_avg. "
    "Positive = features more valuable together than predicted individually."
)
```

**Synergy Heatmap** (Plotly `go.Heatmap`):
- N×N matrix (N = selected features).
- Color scale: diverging `RdYlGn`, centered at 0.
- Diagonal = `None` (blank).
- Axis labels: feature display names, rotated 45°.
- Annotate cells with 2 dp values.
- Hover: *"synergy(A, B) = X"* plus a one-line interpretation.
- `figsize` equivalent: at least 600×500px.

**Top/Bottom Synergies** (Plotly horizontal bar, single chart):
- Top 5 positive pairs (green) + top 5 negative pairs (red) in one chart.
- Label: *"↑ Synergistic"* / *"↓ Redundant"*.

**Top synergies table** (`st.dataframe`):

| Feature A | Feature B | Synergy | Direction |
|---|---|---|---|
| enemy\_king\_danger | capture\_threats | +0.08 | ↑ Synergistic |

#### Tab D: Cross-Variant

Active only if ≥ 2 variants have been run (stored in session state as
`st.session_state["all_results"]` — a dict keyed by variant name).

For MVP with only 1 variant: show `st.info("Run a second variant to unlock cross-variant comparison.")` and disable the tab content.

When active:

**Feature Rankings Across Variants** (Plotly grouped bar):
- x = feature names, groups = variants, y = marginal contribution.
- This is THE key chart. Side-by-side bars show how rankings shift.
- Title: *"Which strategies win depends on the rules."*

**Rank Change Table:**

| Feature | Standard Rank | Atomic Rank | Δ |
|---|---|---|---|
| material | 1 | 7 | −6 ↓ |
| enemy\_king\_danger | 6 | 1 | +5 ↑ |

Sorted by `|Δ|` descending.

**Best Agent Per Variant** — `st.columns(n_variants)`, one card per variant:
```
Atomic Chess
Best: capture_threats + king_danger + king_safety
Score Rate: 0.68
"Atomic chess rewards explosion pressure near the enemy king..."
```

#### Tab E: Report

- `st.subheader("Strategy Report")`
- `st.download_button("⬇ Download Markdown Report", ...)` — saves `.md` file.
- `st.download_button("⬇ Download Raw Results (JSON)", ...)` — saves `.json`.
- `st.markdown(st.session_state["report_md"])` — renders report inline.

---

### Page 4: Engine Explorer

*Purpose:* Interactive tool for building hypothetical agents and predicting
their performance from tournament data.

**Requires:** results in session state. If none: `st.warning("Run a tournament first.")` and return.

#### Build Your Engine

`st.subheader("Build Your Engine")`

Feature checkboxes (same list as sidebar, default all unchecked).
As the user checks/unchecks:

- If the exact feature subset was in the tournament: show **actual** win rate
  + W/D/L.
- If not: show **interpolated estimate** (sum of feature marginals + baseline
  of 0.5). Clearly label as `(estimated)`.

```
Selected features: capture_threats, king_safety

Predicted win rate:  0.63  (estimated)
If in tournament:    —  (this exact subset was not played)

Leaderboard rank:   top 8% of all agents (if played)
Similar agents:     12 agents with 2 of these 3 features
                    avg score: 0.61
```

#### Waterfall Chart

Plotly `go.Waterfall` showing feature contribution breakdown:

```
Baseline             0.50
+ capture_threats   +0.11  ████
+ king_safety       +0.07  ███
= Predicted          0.68
```

Each bar = the marginal contribution of that feature. Positive bars green,
negative red, total bar blue.

#### "What If I Add/Remove One Feature?"

Two-column layout. Left: current predicted rate. Right: table of feature
deltas:

| Feature | Add → New Rate | Delta |
|---|---|---|
| mobility | 0.68 | +0.05 ↑ |
| pawn\_structure | 0.64 | +0.01 ↑ |
| bishop\_pair | 0.61 | −0.02 ↓ |

Sorted by delta descending.

#### Compare Two Agents

`st.selectbox` × 2 (white agent, black agent). Side-by-side `st.columns(2)`:
- Win rates, W/D/L records.
- Head-to-head record from tournament (if they played).
- Feature diff: features unique to each agent, features shared.

---

### Page 5: Play & Watch

*Purpose:* Watch individual games and play against an engine.

Two sub-modes, toggled by `st.radio(["Watch a Matchup", "Play vs Engine"])`.

#### Mode A: Watch a Matchup

Two sub-modes: **Replay a stored game** and **Run a new live game**.

`st.radio(["Replay stored game", "Run new live game"], horizontal=True)`

**Replay stored game:**

- `st.selectbox("Select a game", options=game_labels)` where
  `game_labels` format: `"Game 42: capture_threats vs material (Winner: w, 34 moves)"`.
- `st.multiselect("Filter by agent", ...)` narrows the dropdown.

**Run new live game:**

- Agent selectors: `st.selectbox` for white, `st.selectbox` for black
  (includes `RandomAgent` option).
- `st.button("▶ Play")` launches the game in a background thread,
  renders moves as they are computed.

**Shared layout for both sub-modes** — `st.columns([2, 1])`:

**Left column:**

```
[chess board SVG — 400px]

[ ⏮ Start ]  [ ◀ Prev ]   Move 22 / 47   [ Next ▶ ]  [ End ⏭ ]
[Auto-play  ●──  speed]

White: Agent_capture_threats__king_safety
Black: Agent_material
```

- Board rendered via `chess.svg.board(board, lastmove=move)`.
- For Atomic Chess: pass `fill={sq: "#ff6b3560"}` for exploded squares.
- Playback controls update `viewer_move_index` and call `st.rerun()`.
- Auto-play: a `st.toggle("Auto-play")` + speed slider (0.2–2.0s per move).

**Right column:**

*Eval over time* (Plotly line chart, x = move number, y = eval from white's
perspective). Clicking a point on the chart jumps the board to that move
(via `plotly_events` or a slider bridge).

*Feature contribution bars* for current position — split white / black. Two
small Plotly horizontal bar charts stacked vertically.

*Move list* (PGN-style, scrollable, current move highlighted):
```
1. e4   e5
2. Nf3  Nc6
...
```

*Game info:*
```
Outcome: White wins
Termination: no_legal_moves
Total plies: 47
Avg nodes/move (W): 342.1  (B): 287.4
```

#### Mode B: Play vs Engine

**Requires:** tournament results in session state (to pick an agent).

```
You are playing as:   ○ White  ● Black

Opponent:  [Agent_capture_threats__enemy_king_danger ▾]  Rank #1 · 0.71 win rate
Depth:     [2]

[interactive chess board — chessboard.js via st.components.v1.html]

Engine is thinking...  (312 nodes, 0.04s)
```

**Board:** `chessboard.js` embedded via `st.components.v1.html()`. Handles
drag-and-drop natively. `onDrop` posts `{move: "e2e4"}` to parent window;
capture via a hidden `st.text_input` bridge.

**Engine transparency panel** (sidebar during play — rendered as a
`st.container` in the right column):
```
Engine eval: +0.42 (White is better)

What it's thinking:
  capture_threats   ██████████░░  +0.38
  enemy_king_danger ████████░░░░  +0.21
  material          ████░░░░░░░░  +0.09
```

Updates after every engine move.

**Post-game breakdown** (shown when game ends):
- Full algebraic move list (scrollable).
- Eval chart (line chart, your moves vs engine moves).
- *"Where it went wrong"* annotation — the move where your eval dropped most.
- Feature contribution breakdown for the engine's 3 most decisive moves.

---

## 9. Board Rendering Reference

```python
import chess
import chess.svg

# Non-interactive board (all pages except Mode B)
board = chess.Board(fen_string)
svg = chess.svg.board(
    board,
    lastmove=last_move,           # draws green arrow automatically
    fill={sq: "#ff6b3560"},       # orange tint for Atomic explosion squares
    size=400,
)
st.image(svg.encode(), use_container_width=False)
# Or: st.components.v1.html(svg, height=420)

# Interactive board (Mode B only)
html = f"""
<link rel="stylesheet"
      href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<div id="board" style="width:400px"></div>
<script>
  Chessboard('board', {{
    position: '{fen}',
    draggable: true,
    onDrop: function(from, to) {{
      window.parent.postMessage({{move: from + to}}, '*');
    }}
  }});
</script>
"""
st.components.v1.html(html, height=440)
```

---

## 10. Error Handling

Every data-loading and computation step must be wrapped in `try/except`. On
error:

- Set `st.session_state["error"] = str(e)`.
- Set `running = False`.
- Show `st.error(f"Error: {st.session_state['error']}")` at the top of the
  main panel.
- Do not crash the app. Leave prior results intact.

If `play_game` raises on a specific game: log to stderr, skip that game,
increment `skipped_games`. Show `st.warning("X games skipped due to errors.")`
in the Overview/Tournament completed view.

All page code must be wrapped in a top-level `try/except Exception as e: st.error(str(e))` that prevents a traceback from ever reaching the user.

---

## 11. Performance & Responsiveness

- Tournament runs in `threading.Thread(daemon=True)`.
- Progress callbacks fire at most once per 50 games.
- All Plotly charts: `st.plotly_chart(fig, use_container_width=True)`.
- All dataframes: `st.dataframe(df, use_container_width=True)`.
- Apply `@st.cache_data(ttl=3600)` to `compute_leaderboard`,
  `compute_feature_marginals`, `compute_pairwise_synergies` where inputs are
  hashable (convert lists to tuples for cache keys).
- Board SVG re-renders are cheap; no caching needed.

---

## 12. `requirements.txt` Additions

Add to the existing `requirements.txt`:

```
plotly>=5.0.0
chess>=1.10.0
```

`chess` provides `chess.svg` for board rendering and `chess.Board` for FEN
parsing in Page 5.

---

## 13. Build Priority Order

Build in this sequence — each step is independently testable:

1. **Sidebar config + session state wiring** — base of everything.
2. **Page 3, Tabs A–C** (static — loads from JSON, no live updates needed).
3. **Board rendering first** — implement `render_board(fen, last_move, exploded_squares) -> str`
   as a standalone helper in `ui/board.py` using `chess.svg`. This is shared by
   Page 2 live viewer, Page 5 Mode A, and Page 5 Mode B. Build it once here.
4. **Page 5, Mode A (Watch)** — board + controls + eval chart.
5. **Page 2, Completed State** — static summary after tournament.
6. **Page 2, Live State** — adds progress bar + live leaderboard update loop.
7. **Page 1 (Lab)** — home page with quick-start + load previous.
8. **Page 4 (Explorer)** — waterfall chart + what-if analysis.
9. **Page 5, Mode B (Play)** — chessboard.js + engine transparency panel.
10. **Page 3, Tab D (Cross-Variant)** — only activates with ≥ 2 runs.

---

## 14. Acceptance Criteria

| ID | Criterion |
|---|---|
| U1 | `streamlit run ui/app.py` starts without error when no results exist |
| U2 | Sidebar variant selector, feature checkboxes, and sliders render with correct defaults |
| U3 | Estimated agent and game counts update live as checkboxes change |
| U4 | Run button is disabled when < 2 features selected or tournament is running |
| U5 | Clicking Run starts tournament thread, navigates to Page 2, shows progress |
| U6 | Page 2 live board renders correctly and updates move-by-move during tournament |
| U7 | Page 2 completed state shows correct summary metrics and best agent card |
| U8 | Page 3 Leaderboard tab shows correct row count and supports feature filtering |
| U9 | Page 3 Feature Intelligence tab shows one bar per selected feature |
| U10 | Page 3 Synergy tab shows N×N heatmap where N = selected feature count |
| U11 | Page 3 Cross-Variant tab shows stub until 2nd variant is run |
| U12 | Page 3 Report tab renders Markdown and both download buttons work |
| U13 | Page 4 predicted win rate updates live as features are checked |
| U14 | Page 4 waterfall chart renders correctly for any valid feature subset |
| U15 | Page 5 Mode A board navigation (prev/next/start/end) works correctly |
| U16 | Page 5 Mode B board accepts drag-and-drop moves and engine responds |
| U17 | Load Results uploader correctly loads a JSON from `save_results_json` |
| U18 | All errors caught via `st.error`; no Python tracebacks reach the user |
| U19 | Same config + seed produces identical leaderboard on two runs (determinism) |
| U20 | `pytest tests/test_tournament.py tests/test_analysis.py` still passes |

---

## 15. Out of Scope for MVP

Explicitly deferred — do **not** implement for the initial merge:

- Elo rating computation
- Threefold-repetition or 50-move draw detection
- Opening book visualization
- Per-move eval graph in post-game breakdown (Mode B)
- User authentication
- Persistent database storage (no writes beyond `outputs/` directory)
- Synergy network graph (stretch goal from Plan B)
