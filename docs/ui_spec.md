# EngineLab UI Spec v3 — React / Lovable Base

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | React 19 + Vite |
| Router | TanStack Router |
| Styling | Tailwind CSS v4 + shadcn/ui |
| Chess | chess.js (engine) + react-chessboard v5 (board) |
| State | React `useState` / `useRef` — no external store |
| Entry point | `webapp/` directory at repo root |

Run with:
```bash
cd webapp
npm install      # or: bun install
npm run dev      # vite dev server → http://localhost:5173
npm run build    # production build
```

---

## Layout

```
┌────────────────────────────────────────────────────────────────┐
│  ♟ EngineLab                        ● Configure / Train / …   │  ← header
├────────────────────────────────────┬───────────────────────────┤
│                                    │                           │
│         CHESS BOARD                │      RIGHT PANEL          │
│   (always visible, responsive)     │  (changes by phase)       │
│                                    │                           │
│   + Training scoreboard below      │                           │
│     (only during training phase)   │                           │
│   + Move list below                │                           │
│     (only during play phase)       │                           │
└────────────────────────────────────┴───────────────────────────┘
```

- **Left column**: Chessboard (`react-chessboard`, max 560px, Lichess brown squares). Static in configure/training/analysis phases; interactive drag-and-drop in play phase.
- **Right column (400px)**: Phase-controlled panel.
- **Max width**: 1280px (`max-w-7xl`), centered.

---

## Phases (right panel states)

### Phase 1 — Configure  (default)

**Right panel:**
- Header: "Evaluation Features" + active-count badge
- Depth selector: Fast (1) / Normal (2) / Deep (3) pill buttons
- Agent count estimate: `N agents · K games`
- Scrollable feature list (10 features): each has toggle (Switch) + weight slider (0.1–3×)
- "Run Training Tournament" primary button (disabled if < 2 features active)
- "How it works" explainer card below

**Board:** Starting position, static (no dragging).

---

### Phase 2 — Training

**Right panel:** Minimal — progress bar, agent count, note pointing to left column.

**Left column (below board):**
- Progress bar + game counter
- Live leaderboard (top 8 agents, W/D/L/score, updates each game)
- Game log (scrollable, last 30 results)

**Board:** Starting position, static.

---

### Phase 3 — Analysis  (auto-enters after training completes)

**Right panel (scrollable):**
- **Champion card** — name, score rate, W/D/L, feature pills, "Play vs [name]" primary button
- **Feature Contributions** — horizontal bar chart (green = positive, red = negative), sorted by marginal win-rate impact
- **Feature Synergy** — top-4 best pairs + top-4 worst pairs (percentage deltas)
- **Leaderboard** — all agents ranked, score %, W/D/L
- **Actions row** — "Export JSON" + "← Reconfigure" buttons

**Board:** Showing starting position, static.

---

### Phase 4 — Play

**Right panel:**
- Engine name (black) vs You (white) header
- Status line (your move / engine thinking / checkmate / draw)
- Engine feature pills
- New Game + Back to Analysis buttons

**Left column (below board):**
- Move list (PGN-style pairs, scrollable)

**Board:** Interactive. User drags white pieces. Engine plays black automatically with ~350ms delay.

---

## Agent Generation

Instead of hand-crafted variants, agents are generated as feature subsets — this enables proper marginal contribution analysis.

For `n` selected features the tournament runs:

| Subset type | Count | Purpose |
|-------------|-------|---------|
| Singletons | n | Isolates each feature's solo value |
| Full set | 1 | Baseline with everything enabled |
| Leave-one-out | n (if n ≥ 3) | Measures each feature's removal impact |
| **Total** | **2n+1** (or n+1 if n<3) | |

For 10 features: **21 agents → 420 games** (~5–10s at depth 1).

Each agent uses the user's configured weights for its active features.

---

## Analysis Computations

### Feature Marginals
For each feature `f`:
```
marginal(f) = avg_score_rate(agents with f) − avg_score_rate(agents without f)
```
Displayed as sorted horizontal bar chart (green = positive contribution).

### Synergy
For each feature pair `(f_i, f_j)`:
```
synergy = avg_score_rate(both) − (avg_score_rate(f_i only) + avg_score_rate(f_j only)) / 2
```
Top-4 positive (best pairs) and top-4 negative (redundant/counterproductive) shown.

---

## Colors — Lichess Dark Theme

| Token | Value | Use |
|-------|-------|-----|
| `--background` | `oklch(0.16 0.005 90)` ≈ `#161512` | Page bg |
| `--card` | `oklch(0.20 0.005 90)` | Card bg |
| `--primary` | `oklch(0.68 0.17 130)` ≈ `#759900` | Lichess green |
| `--border` | `oklch(0.30 0.005 90)` | Borders |
| `--muted-foreground` | `oklch(0.68 0.005 90)` | Secondary text |
| Board dark | `#b58863` | Dark squares |
| Board light | `#f0d9b5` | Light squares |

---

## File Map

| File | Role |
|------|------|
| `webapp/src/components/chess/ChessLab.tsx` | Single-file main component — all phases |
| `webapp/src/lib/chess/engine.ts` | Alpha-beta negamax, `pickBestMove`, `playGame` |
| `webapp/src/lib/chess/features.ts` | 10 feature definitions + PST tables + `makeEvaluator` |
| `webapp/src/lib/chess/analysis.ts` | `computeMarginals`, `computeSynergies`, `generateAgentDefs` |
| `webapp/src/routes/index.tsx` | TanStack route → renders `<ChessLab />` |
| `webapp/src/styles.css` | Tailwind v4 + custom properties (Lichess palette) |
| `webapp/src/components/ui/` | shadcn/ui component library |

---

## Acceptance Criteria

| # | Test |
|---|------|
| U1 | `npm run dev` starts without errors; board and Configure panel visible |
| U2 | Enabling/disabling features updates agent count estimate live |
| U3 | "Run Training Tournament" disabled when < 2 features active |
| U4 | Training phase shows live leaderboard updating each game |
| U5 | After training completes, analysis phase appears automatically |
| U6 | Champion card shows correct name, score, features |
| U7 | Feature marginals chart shows all active features sorted by impact |
| U8 | Synergy section shows best/worst pairs |
| U9 | "Export JSON" downloads valid JSON with leaderboard + marginals |
| U10 | "Play vs [Champion]" switches to interactive board |
| U11 | Player can drag white pieces; engine responds as black |
| U12 | Game over (checkmate/draw) updates status correctly |
| U13 | "New Game" resets the board |
| U14 | "Back to Analysis" returns to analysis view |
| U15 | "← Reconfigure" returns to configure phase |

---

## Out of Scope (v3)

- Atomic / Antichess variants (standard chess only)
- Weight persistence across sessions
- Multiplayer / user accounts
- Mobile layout optimization
- Server-side engine (all runs client-side in browser)
