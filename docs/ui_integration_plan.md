# UI Integration & Deployment Plan (v2)

*Updated 2026-04-25 after full audit of `origin/ui` branch.*

---

## Context

The EngineLab backend on `main` is fully working -- chess engine, 3
variants, 10 features, agent generation, alpha-beta search, tournament,
analysis, and CLI all run end-to-end.

The `origin/ui` branch contains two separate frontends:

1. **Streamlit UI** (`ui/`) -- 6 files, ~1900 lines. Has the layout,
   views, charts, and chess viewer built out. But it is **fully mocked**:
   the "Build Engine" button fakes 5 seconds of progress, then loads
   synthetic data. Play mode uses random legal moves. Zero connection to
   the real backend.

2. **React webapp** (`webapp/`) -- TanStack Start + Vite + chess.js.
   Completely standalone client-side app that **reimplements the entire
   Python backend in TypeScript** (features, negamax, tournament, analysis).
   No Python backend needed. Deployable to Cloudflare Workers.

Additionally, the UI branch **regressed the backend**: feature registry
emptied, atomic/antichess reverted to stubs, alpha-beta lost variant
support, CLI gutted, RandomAgent removed.

**Strategy:** Use the Streamlit UI as a design/aesthetic base. Keep the
working backend from `main`. Replace mocks with real backend calls.

---

## 1. Current State (as of 2026-04-25)

### Backend on `main` (fully working)

| Component | Key Files | Status |
|-----------|-----------|--------|
| Chess engine | `core/board.py`, `core/move_generation.py`, `core/apply_move.py` | Done |
| Standard chess | `variants/standard.py` | Done |
| Atomic chess | `variants/atomic.py` | Done |
| Antichess | `variants/antichess.py` | Done |
| 10 features | `features/*.py`, `features/registry.py` | Done |
| Agent generation | `agents/generate_agents.py` | Done |
| Evaluation (all features) | `agents/evaluation.py` | Done |
| Alpha-beta (variant-aware) | `search/alpha_beta.py` | Done |
| Game simulation | `simulation/game.py` (supports RandomAgent + FeatureSubsetAgent) | Done |
| Round-robin tournament | `tournament/round_robin.py` | Done |
| Leaderboard | `tournament/leaderboard.py` | Done |
| Results I/O | `tournament/results_io.py` | Done |
| Feature marginals | `analysis/feature_marginals.py` | Done |
| Pairwise synergy | `analysis/synergy.py` | Done |
| Interpretation | `analysis/interpretation.py` | Done |
| Report generation | `reports/markdown_report.py` | Done |
| CLI | `main.py` (full-pipeline, tournament, match, play) | Done |

### Streamlit UI on `origin/ui` (design done, wiring mocked)

| File | Lines | What It Does | Backend Connection |
|------|-------|-------------|-------------------|
| `ui/app.py` | 705 | Main app: sidebar config, build/live/analysis/play views | Mocked -- fake 5s progress, loads `mock_data.py` |
| `ui/board.py` | 72 | FEN -> SVG via python-chess | Real (no backend dependency) |
| `ui/chess_viewer.py` | 574 | Game replay + interactive play via chessboard.js | Mocked -- random engine moves |
| `ui/constants.py` | 62 | Feature list, variant descriptions, session defaults | Hardcoded (duplicates `features/registry.py`) |
| `ui/mock_data.py` | 490 | Generates fake agents, results, leaderboard, marginals | Entirely synthetic |
| `ui/play_engine.py` | 71 | Random legal move generator | Mocked -- no real engine |

### React webapp on `origin/ui` (standalone)

| Component | Status |
|-----------|--------|
| `webapp/src/components/chess/ChessLab.tsx` | 956 lines, full UI |
| `webapp/src/lib/chess/features.ts` | All 10 features reimplemented in TS |
| `webapp/src/lib/chess/engine.ts` | Negamax alpha-beta in TS |
| `webapp/src/lib/chess/analysis.ts` | Marginals + synergy in TS |

Self-contained. Runs entirely in-browser. Deployable to Cloudflare Workers.
**No integration needed** -- this is an independent artifact.

### What the UI branch broke on the backend

| File | What was regressed | Impact |
|------|-------------------|--------|
| `features/registry.py` | Emptied -- all 10 features removed | Agents get 0.0 for all features |
| `features/*.py` (10 files) | Deleted | No feature implementations |
| `variants/atomic.py` | Reverted to `NotImplementedError` stub | Atomic chess broken |
| `variants/antichess.py` | Reverted to stub | Antichess broken |
| `search/alpha_beta.py` | Removed `variant` parameter, hardcoded standard | Can't search in variants |
| `agents/evaluation.py` | Only material feature works | Non-material agents are blind |
| `simulation/game.py` | Removed RandomAgent support | Random baseline games fail |
| `main.py` | Gutted to stub | CLI broken |

**These regressions are on the UI branch only.** The `main` branch backend
is intact. Integration must use `main`'s backend, not the UI branch's.

---

## 2. Integration Approach

### Merge Strategy

Do NOT merge the UI branch as-is -- it would destroy the working backend.
Instead:

1. **Cherry-pick the UI files only** from `origin/ui` into `main`:
   - `ui/app.py`
   - `ui/board.py`
   - `ui/chess_viewer.py`
   - `ui/constants.py`
   - `ui/mock_data.py`
   - `ui/play_engine.py`
   - `ui/__init__.py`
   - `.streamlit/config.toml`
2. **Add missing deps** to `requirements.txt`: `plotly>=5.0.0`, `chess>=1.10.0`
3. **Take useful backend improvements** from the UI branch:
   - `tournament/round_robin.py`: progress callback (`on_game_complete`)
   - `tournament/results_io.py`: improved error handling
4. **Do NOT take** the UI branch versions of: `features/`, `variants/`,
   `search/`, `agents/evaluation.py`, `simulation/game.py`, `main.py`
5. **Then rewire** the UI files to call the real backend instead of mocks

### What "Rewire" Means (file by file)

#### `ui/app.py` -- Replace mock pipeline with real pipeline

Current (mocked):
```python
# _start_tournament() just saves config to session_state
# _render_live_panel() fakes progress for 5 seconds
# After fake delay: generate_mock_session_state() fills in synthetic data
```

Rewired:
```python
# _start_tournament() launches real pipeline in threading.Thread:
#   1. generate_feature_subset_agents(selected_features, max_agents, seed)
#   2. run_round_robin(agents, variant, depth, max_moves, seed, on_game_complete=callback)
#   3. compute_leaderboard(results, agents)
#   4. compute_feature_marginals(leaderboard, feature_names, top_k)
#   5. compute_pairwise_synergies(leaderboard, feature_names)
#   6. generate_interpretation(best_agent, marginals, synergies, variant)
# callback updates st.session_state.progress behind a threading.Lock
```

Key changes:
- Import from `agents.generate_agents`, `tournament.round_robin`,
  `tournament.leaderboard`, `analysis.*` instead of `ui.mock_data`
- Replace `_FAKE_BUILD_DURATION` timer with real `on_game_complete` callback
- Wire sidebar feature checkboxes to `features.registry.get_feature_names()`
  instead of hardcoded `ui.constants.ALL_FEATURES`
- Use real `LeaderboardRow`, `FeatureContributionRow`, `SynergyRow` from
  backend instead of mock versions

#### `ui/constants.py` -- Replace hardcoded features with registry

Current:
```python
ALL_FEATURES = ["material", "king_safety", ...]  # hardcoded list
```

Rewired:
```python
from features.registry import get_feature_names, FEATURE_DESCRIPTIONS
ALL_FEATURES = get_feature_names()
```

#### `ui/play_engine.py` -- Replace random moves with real engine

Current:
```python
def engine_reply(fen, move_index):
    rng = random.Random(42 + move_index)
    return rng.choice(legal).uci()  # random legal move
```

Rewired:
```python
def engine_reply(fen, agent_features, depth=2, variant="standard"):
    board = board_from_fen(fen)
    agent = FeatureSubsetAgent(...)  # from selected features
    engine = AlphaBetaEngine(agent, depth, variant=variant)
    move = engine.choose_move(board)
    return move.to_uci()
```

This requires a `board_from_fen()` helper that converts a FEN string to
the custom `Board` object (inverse of `Board.to_fen()`).

#### `ui/mock_data.py` -- Delete or keep as fallback

Once rewired, this file is no longer needed. It could be kept as a
fallback for demo mode (when backend is unavailable), but the primary
path should use real data.

#### `ui/chess_viewer.py` -- No changes needed for replay

The game replay viewer (`chess_game_viewer()`) already accepts a move
list and replays it. It just needs real move data from `GameResult.move_list`
instead of randomly generated games.

The interactive play mode (`chess_play_interactive()`) currently uses
JavaScript random moves. To integrate with the real engine, the JS bridge
must send the current FEN to Python, call `engine_reply()` (rewired above),
and return the move to JavaScript. This is the most fragile integration
point.

---

## 3. Backend Gaps (on `main`)

Small additions needed to support the UI.

### Gap A: `Board.to_fen()` -- Export board state as FEN string

**File:** `core/board.py`
**Why:** UI renders boards via `chess.svg.board(chess.Board(fen))`
**Size:** ~20 lines

### Gap B: `Board.from_fen()` -- Import FEN string to Board

**File:** `core/board.py`
**Why:** Play mode receives FEN from JavaScript, needs to create a Board
for the engine to evaluate
**Size:** ~25 lines

### Gap C: `move_list` field on `GameResult`

**File:** `simulation/game.py`, `tournament/results_io.py`
**Why:** Game replay viewer needs the actual sequence of moves
**Size:** Add `move_list: list[str] = field(default_factory=list)` to
dataclass, append `move.to_uci()` in `play_game()` loop, update I/O

### Gap D: Progress callback in `run_round_robin()`

**File:** `tournament/round_robin.py`
**Why:** Live tournament view needs per-game progress updates
**Note:** The UI branch already implemented this. Cherry-pick it.

### Gap E: Missing dependencies

**File:** `requirements.txt`
**Add:** `plotly>=5.0.0`, `chess>=1.10.0`

### Gap F: `.streamlit/config.toml`

**Note:** Already exists on the UI branch. Cherry-pick it.

---

## 4. Build Sequence

### Phase 0: Setup (no UI changes)

| Step | Work | Files |
|------|------|-------|
| 0a | Add `plotly`, `chess` to `requirements.txt` | `requirements.txt` |
| 0b | Cherry-pick `.streamlit/config.toml` from UI branch | `.streamlit/config.toml` |
| 0c | Add `Board.to_fen()` and `Board.from_fen()` | `core/board.py` |
| 0d | Add `move_list` to `GameResult`, update `play_game()` and I/O | `simulation/game.py`, `tournament/results_io.py` |
| 0e | Add `on_game_complete` callback to `run_round_robin()` | `tournament/round_robin.py` |
| 0f | Regenerate tournament results with move lists | `outputs/data/*.json` |

### Phase 1: Bring UI files to main

| Step | Work |
|------|------|
| 1a | Cherry-pick `ui/app.py`, `ui/board.py`, `ui/chess_viewer.py`, `ui/constants.py`, `ui/mock_data.py`, `ui/play_engine.py`, `ui/__init__.py` |
| 1b | Verify `streamlit run ui/app.py` launches (still using mocks) |

### Phase 2: Rewire to real backend

| Step | Work | Priority |
|------|------|----------|
| 2a | `ui/constants.py`: import features from registry instead of hardcoding | High |
| 2b | `ui/app.py`: replace `generate_mock_session_state()` with real pipeline in background thread | High |
| 2c | `ui/app.py`: wire "Load Results" to `tournament.results_io.load_results_json()` + real analysis pipeline | High |
| 2d | `ui/play_engine.py`: replace random moves with `AlphaBetaEngine.choose_move()` | Medium |
| 2e | `ui/chess_viewer.py`: feed real `GameResult.move_list` to replay viewer | Medium |
| 2f | `ui/app.py`: wire play mode to use the tournament's best agent | Medium |
| 2g | Remove or gate `ui/mock_data.py` behind a fallback flag | Low |

### Phase 3: Deployment

| Step | Work |
|------|------|
| 3a | Create `Dockerfile` |
| 3b | Test Streamlit Cloud deployment with pre-computed data |
| 3c | Verify `pytest` still passes |

---

## 5. Deployment Options

### Streamlit Cloud (recommended for demo)

- Just needs GitHub repo + `requirements.txt` (already exists)
- Set entry point to `ui/app.py`
- Ship pre-computed `outputs/data/*.json` for "Load Results" mode
- CPU limits mean full tournaments may timeout -- limit live runs to
  small configs (2-3 features, depth 1)

### Docker (recommended for real usage)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

Deploy to Railway, Fly.io, Cloud Run, etc.

### React webapp (already deployable)

The `webapp/` directory is a self-contained React app that reimplements
the full pipeline in TypeScript. It can be deployed independently to
Cloudflare Workers, Vercel, or any static host. No Python backend needed.
This is a separate deployment artifact from the Streamlit app.

### Vercel (not recommended for Streamlit)

Streamlit requires persistent WebSocket connections. Vercel's serverless
model does not support this. The React `webapp/` works fine on Vercel,
but the Streamlit `ui/` does not.

---

## 6. What Exists vs What Needs Rewiring

| UI Feature | Current State (mocked) | What Rewiring Looks Like |
|-----------|----------------------|--------------------------|
| Feature selection | Hardcoded 10-item list in `constants.py` | Pull from `features.registry.get_feature_names()` |
| "Build Engine" button | Fakes 5s delay, loads `mock_data.py` | Launches real `generate_agents` + `run_round_robin` + analysis in background thread |
| Progress bar | Timer-based fake (0% to 100% over 5s) | Real `on_game_complete(done, total)` callback from tournament |
| Leaderboard table | Synthetic `LeaderboardRow` objects from mock | Real `compute_leaderboard(results, agents)` output |
| Feature marginals chart | Hardcoded marginal values per variant | Real `compute_feature_marginals(leaderboard, features)` |
| Synergy heatmap | Synthetic synergy matrix | Real `compute_pairwise_synergies(leaderboard, features)` |
| Interpretation text | Template string with mock values | Real `generate_interpretation(best, marginals, synergies, variant)` |
| Game replay viewer | Random game generated by `chess.Board()` | Real `GameResult.move_list` from tournament |
| Play vs engine | Random legal moves (`random.choice(legal)`) | Real `AlphaBetaEngine.choose_move(board)` using best agent |
| Load previous results | Not functional | `tournament.results_io.load_results_json()` + full analysis pipeline |

---

## 7. Risk Areas

1. **Background thread + Streamlit rerun** -- Streamlit's execution model
   reruns the script on every interaction. The background tournament thread
   must write to `st.session_state` behind a lock, and the main thread
   must poll for updates. This is the trickiest integration.

2. **Play mode JS bridge** -- `chess_viewer.py` embeds chessboard.js via
   HTML component. Getting the engine's move from Python back into JavaScript
   requires a postMessage bridge that's inherently fragile. Consider
   using SVG board + click-based input as a simpler alternative.

3. **FEN round-trip** -- The custom `Board` class uses a different internal
   representation than python-chess. `to_fen()` and `from_fen()` must be
   exact inverses. Edge cases: en passant squares, castling rights after
   rook capture, promotion states.

4. **Existing JSON results** -- The pre-computed `outputs/data/*.json`
   files don't have `move_list`. After adding the field, either regenerate
   them or make the replay viewer handle missing move lists gracefully.

---

## 8. Verification Checklist

- [ ] `pip install -r requirements.txt` succeeds (plotly + chess added)
- [ ] `streamlit run ui/app.py` launches without error on `main`
- [ ] Sidebar shows features from `features.registry`, not hardcoded list
- [ ] "Build Engine" runs a real tournament (2 features, depth 1, max 20 moves)
- [ ] Progress bar updates in real time during tournament
- [ ] Leaderboard shows real win rates (not all 0.500)
- [ ] Feature marginals chart shows non-zero marginals
- [ ] Synergy heatmap renders from real data
- [ ] "Load Results" loads `outputs/data/tournament_results_standard.json`
- [ ] Game replay steps through real moves on the board
- [ ] Play mode: engine makes intelligent moves (not random)
- [ ] Variant selector works: standard vs atomic produce different results
- [ ] `python main.py full-pipeline --variant standard --depth 1 --max-moves 40` still works
- [ ] `pytest` passes
