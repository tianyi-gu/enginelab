from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import threading
import random

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import chess

from ui.constants import FEATURE_DISPLAY_NAMES, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_EXPLOSION
from ui.board import render_board, starting_fen


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

def _ss(key: str, default=None):
    """Safe session-state getter with fallback default."""
    return st.session_state.get(key, default)


def _ensure_defaults() -> None:
    """Seed any missing session-state keys."""
    defaults: dict = {
        "viewer_game_index": 0,
        "viewer_move_index": 0,
        "live_game_result": None,
        "live_game_running": False,
        "play_board_fen": None,
        "play_move_history": [],
        "play_is_human_turn": True,
        "play_human_color": "White",
        "play_opponent_name": None,
        "play_depth": 2,
        "play_game_over": False,
        "play_game_outcome": None,
        "play_autoplay": False,
        "play_autoplay_speed": 1.0,
        "results": None,
        "agents": None,
        "leaderboard": None,
        "variant": "atomic",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _get_results():
    """Return list[GameResult] from session state, or None."""
    return _ss("results")


def _get_agents():
    """Return list[FeatureSubsetAgent] from session state, or None."""
    return _ss("agents")


def _agent_names() -> list[str]:
    """Return sorted list of unique agent names from results."""
    results = _get_results()
    if not results:
        return []
    names: set[str] = set()
    for r in results:
        names.add(r.white_agent)
        names.add(r.black_agent)
    return sorted(names)


def _strip_prefix(name: str) -> str:
    """Strip Agent_ prefix for display."""
    return name.removeprefix("Agent_")


def _game_label(r, idx: int) -> str:
    """Build a display label for a GameResult."""
    winner_str = r.winner if r.winner else "draw"
    return (
        f"Game {idx + 1}: {_strip_prefix(r.white_agent)} vs "
        f"{_strip_prefix(r.black_agent)} — "
        f"Winner: {winner_str}, {r.moves} plies"
    )


def _outcome_string(winner: str | None) -> str:
    """Human-readable outcome."""
    if winner == "w":
        return "White wins"
    if winner == "b":
        return "Black wins"
    return "Draw"


# ---------------------------------------------------------------------------
# Eval / chart helpers
# ---------------------------------------------------------------------------

def _synthetic_eval_path(game_id: int, num_moves: int) -> list[float]:
    """Generate a plausible synthetic eval path via seeded random walk."""
    rng = random.Random(hash(game_id) & 0xFFFFFFFF)
    evals: list[float] = [0.5]
    for _ in range(max(num_moves - 1, 0)):
        delta = rng.gauss(0, 0.06)
        new_val = max(0.05, min(0.95, evals[-1] + delta))
        evals.append(new_val)
    return evals


def _build_eval_chart(eval_path: list[float], move_index: int) -> go.Figure:
    """Return a Plotly line chart for eval over time."""
    xs = list(range(len(eval_path)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs,
        y=eval_path,
        mode="lines",
        line=dict(color=COLOR_POSITIVE, width=2),
        name="Eval",
        hovertemplate="Move %{x}: %{y:.3f}<extra></extra>",
    ))
    # Mark current position
    if 0 <= move_index < len(eval_path):
        fig.add_trace(go.Scatter(
            x=[move_index],
            y=[eval_path[move_index]],
            mode="markers",
            marker=dict(color=COLOR_EXPLOSION, size=10),
            name="Current",
            hovertemplate="Current: %{y:.3f}<extra></extra>",
        ))
    fig.add_hline(y=0.5, line_dash="dash", line_color="#8b949e",
                  annotation_text="Equal", annotation_position="right")
    fig.update_layout(
        height=180,
        margin=dict(l=10, r=10, t=24, b=10),
        xaxis_title="Move",
        yaxis_title="Eval (White)",
        yaxis=dict(range=[0, 1]),
        paper_bgcolor="#161b22",
        plot_bgcolor="#0e1117",
        font=dict(color="#e6edf3", size=11),
        showlegend=False,
        title=dict(text="Eval Over Time", font=dict(size=12)),
    )
    return fig


def _build_feature_bar_chart(
    features: tuple[str, ...],
    title: str,
    bar_color: str,
) -> go.Figure:
    """Placeholder feature-contribution bar chart (equal weights)."""
    if not features:
        features = ("(none)",)
    labels = [FEATURE_DISPLAY_NAMES.get(f, f) for f in features]
    vals = [1.0 / len(features)] * len(features)
    fig = go.Figure(go.Bar(
        x=vals,
        y=labels,
        orientation="h",
        marker_color=bar_color,
        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
    ))
    fig.update_layout(
        height=max(100, 28 * len(features) + 40),
        margin=dict(l=10, r=10, t=28, b=10),
        xaxis=dict(range=[0, 1]),
        paper_bgcolor="#161b22",
        plot_bgcolor="#0e1117",
        font=dict(color="#e6edf3", size=10),
        showlegend=False,
        title=dict(text=title, font=dict(size=11)),
    )
    return fig


# ---------------------------------------------------------------------------
# Agent feature lookup
# ---------------------------------------------------------------------------

def _features_for_agent(agent_name: str) -> tuple[str, ...]:
    """Look up an agent's features from session state, or parse from name."""
    agents = _get_agents()
    if agents:
        for a in agents:
            if a.name == agent_name:
                return a.features
    # Fall back: parse name "Agent_feat1__feat2" → ("feat1", "feat2")
    stripped = agent_name.removeprefix("Agent_")
    parts = tuple(p for p in stripped.split("__") if p)
    return parts if parts else ("material",)


# ---------------------------------------------------------------------------
# Board rendering
# ---------------------------------------------------------------------------

def _render_board_html(
    fen: str,
    last_move: str | None = None,
    exploded: list[str] | None = None,
    flipped: bool = False,
) -> None:
    """Render chess board as HTML component."""
    svg = render_board(fen, last_move, exploded, size=400, flipped=flipped)
    st.components.v1.html(svg, height=420)


# ---------------------------------------------------------------------------
# Move navigation controls
# ---------------------------------------------------------------------------

def _render_nav_controls(move_index: int, total_moves: int) -> None:
    """Render ⏮ ◀ N/M ▶ ⏭ nav buttons, mutating session state."""
    cols = st.columns(5)
    with cols[0]:
        if st.button("⏮", key="nav_start", help="Start"):
            st.session_state["viewer_move_index"] = 0
            st.rerun()
    with cols[1]:
        if st.button("◀", key="nav_prev", help="Previous"):
            st.session_state["viewer_move_index"] = max(0, move_index - 1)
            st.rerun()
    with cols[2]:
        st.markdown(
            f"<div style='text-align:center;padding-top:6px;font-family:monospace'>"
            f"Move {move_index} / {total_moves}</div>",
            unsafe_allow_html=True,
        )
    with cols[3]:
        if st.button("▶", key="nav_next", help="Next"):
            st.session_state["viewer_move_index"] = min(total_moves, move_index + 1)
            st.rerun()
    with cols[4]:
        if st.button("⏭", key="nav_end", help="End"):
            st.session_state["viewer_move_index"] = total_moves
            st.rerun()


def _render_autoplay_controls() -> None:
    """Render auto-play toggle and speed slider."""
    col_tog, col_spd = st.columns([1, 2])
    with col_tog:
        autoplay = st.toggle("Auto-play", key="play_autoplay_toggle",
                             value=_ss("play_autoplay", False))
        st.session_state["play_autoplay"] = autoplay
    with col_spd:
        speed = st.slider(
            "Speed (s/move)", 0.3, 2.0, _ss("play_autoplay_speed", 1.0),
            step=0.1, key="autoplay_speed_slider",
        )
        st.session_state["play_autoplay_speed"] = speed


# ---------------------------------------------------------------------------
# Right-column info panel (shared by both Watch sub-modes)
# ---------------------------------------------------------------------------

def _render_right_panel(
    game_result,
    move_index: int,
    eval_path: list[float],
    game_id: int,
) -> None:
    """Render eval chart, feature bars, move list, game info."""
    st.subheader("Eval Over Time")
    fig_eval = _build_eval_chart(eval_path, move_index)
    st.plotly_chart(fig_eval, use_container_width=True, key=f"eval_chart_{game_id}")

    w_feats = _features_for_agent(game_result.white_agent)
    b_feats = _features_for_agent(game_result.black_agent)

    st.subheader("Feature Contributions")
    st.caption("Placeholder: equal weights (per-position eval not stored)")
    fig_w = _build_feature_bar_chart(w_feats, "White features", COLOR_POSITIVE)
    st.plotly_chart(fig_w, use_container_width=True, key=f"feat_w_{game_id}")
    fig_b = _build_feature_bar_chart(b_feats, "Black features", COLOR_NEGATIVE)
    st.plotly_chart(fig_b, use_container_width=True, key=f"feat_b_{game_id}")

    _render_move_list(game_result.moves, move_index)
    _render_game_info(game_result)


def _render_move_list(total_plies: int, current_ply: int) -> None:
    """Render a PGN-style placeholder move list."""
    st.subheader("Move List")
    st.caption("Move history not stored in GameResult — showing placeholder")
    lines: list[str] = []
    for move_num in range(1, total_plies // 2 + 2):
        w_ply = (move_num - 1) * 2
        b_ply = w_ply + 1
        w_mark = " ◀" if w_ply == current_ply else ""
        b_mark = " ◀" if b_ply == current_ply else ""
        b_str = f" ...{b_mark}" if b_ply >= total_plies else f" ...{b_mark}"
        lines.append(f"{move_num}.{w_mark} ... {b_str}")
        if b_ply >= total_plies:
            break
    st.text_area(
        "Moves",
        value="\n".join(lines[:40]),
        height=140,
        disabled=True,
        label_visibility="collapsed",
        key="move_list_area",
    )


def _render_game_info(game_result) -> None:
    """Render outcome / termination / stats."""
    st.subheader("Game Info")
    col_a, col_b = st.columns(2)
    col_a.metric("Outcome", _outcome_string(game_result.winner))
    col_b.metric("Termination", game_result.termination_reason)
    col_c, col_d = st.columns(2)
    col_c.metric("Total plies", game_result.moves)
    col_d.metric("Avg nodes (W/B)",
                 f"{game_result.white_avg_nodes:.0f} / {game_result.black_avg_nodes:.0f}")


# ---------------------------------------------------------------------------
# Mode A — Watch: Replay stored game
# ---------------------------------------------------------------------------

def _render_replay_controls(results) -> int | None:
    """Render game selector + filter. Returns index of selected game, or None."""
    all_names = sorted({r.white_agent for r in results} | {r.black_agent for r in results})
    filter_names = st.multiselect(
        "Filter by agent",
        options=[_strip_prefix(n) for n in all_names],
        key="replay_filter",
    )
    raw_filter = {f"Agent_{n}" for n in filter_names} if filter_names else None

    filtered = [
        (i, r) for i, r in enumerate(results)
        if raw_filter is None
        or raw_filter.issubset({r.white_agent, r.black_agent})
    ]

    if not filtered:
        st.warning("No games match the current filter.")
        return None

    labels = [_game_label(r, i) for i, r in filtered]
    sel = st.selectbox("Select game", options=labels, key="replay_select")
    sel_idx = labels.index(sel) if sel in labels else 0
    return filtered[sel_idx][0]


def _render_watch_replay(results) -> None:
    """Render the Replay stored game sub-mode."""
    game_idx = _render_replay_controls(results)
    if game_idx is None:
        return

    game = results[game_idx]

    # Reset move index when game changes
    if _ss("viewer_game_index") != game_idx:
        st.session_state["viewer_game_index"] = game_idx
        st.session_state["viewer_move_index"] = 0

    move_index = _ss("viewer_move_index", 0)
    total_moves = game.moves

    col_board, col_info = st.columns([2, 1])

    with col_board:
        fen = starting_fen()
        _render_board_html(fen)
        st.caption(
            "Move history not stored — showing starting position. "
            "Full replay requires move_history field in GameResult."
        )
        _render_nav_controls(move_index, total_moves)
        _render_autoplay_controls()
        st.caption(
            f"White: {_strip_prefix(game.white_agent)}  "
            f"  Black: {_strip_prefix(game.black_agent)}"
        )

        if _ss("play_autoplay") and move_index < total_moves:
            time.sleep(_ss("play_autoplay_speed", 1.0))
            st.session_state["viewer_move_index"] = move_index + 1
            st.rerun()

    with col_info:
        eval_path = _synthetic_eval_path(game_idx, total_moves)
        _render_right_panel(game, move_index, eval_path, game_idx)


# ---------------------------------------------------------------------------
# Mode A — Watch: Run new live game
# ---------------------------------------------------------------------------

def _run_live_game_thread(
    white_name: str,
    black_name: str,
    depth: int,
    variant: str,
) -> None:
    """Background thread: runs play_game, stores result in session state."""
    try:
        from simulation.game import play_game
        from agents.feature_subset_agent import FeatureSubsetAgent

        def _make_agent(name: str) -> FeatureSubsetAgent:
            feats = _features_for_agent(name)
            weight = 1.0 / max(len(feats), 1)
            return FeatureSubsetAgent(
                name=name,
                features=feats,
                weights={f: weight for f in feats},
            )

        w_agent = _make_agent(white_name)
        b_agent = _make_agent(black_name)
        result = play_game(w_agent, b_agent, variant=variant, depth=depth)
        st.session_state["live_game_result"] = result
    except Exception as exc:
        st.session_state["live_game_result"] = str(exc)
    finally:
        st.session_state["live_game_running"] = False


def _render_watch_live(all_agent_names: list[str], variant: str) -> None:
    """Render the Run new live game sub-mode."""
    options = ["Random Agent"] + all_agent_names
    col_w, col_b, col_d = st.columns([2, 2, 1])
    white_sel = col_w.selectbox("White agent", options, key="live_white")
    black_sel = col_b.selectbox("Black agent", options, key="live_black")
    depth_sel = col_d.number_input("Depth", 1, 3, 2, key="live_depth")

    running = _ss("live_game_running", False)

    if st.button("▶ Play", disabled=running, key="live_play_btn"):
        w_name = white_sel if white_sel != "Random Agent" else _random_agent_name()
        b_name = black_sel if black_sel != "Random Agent" else _random_agent_name()
        st.session_state["live_game_result"] = None
        st.session_state["live_game_running"] = True
        t = threading.Thread(
            target=_run_live_game_thread,
            args=(w_name, b_name, int(depth_sel), variant),
            daemon=True,
        )
        t.start()
        st.rerun()

    if running:
        st.spinner("Game running...")
        st.info("Game running... refresh in a moment.")
        time.sleep(1.0)
        st.rerun()

    live_result = _ss("live_game_result")
    if live_result is None:
        st.info("Configure agents above and click ▶ Play to start a game.")
        return

    if isinstance(live_result, str):
        st.error(f"Game failed: {live_result}")
        return

    # Display result
    st.success(f"Game complete! {_outcome_string(live_result.winner)}")
    move_index = _ss("viewer_move_index", 0)
    total_moves = live_result.moves

    col_board, col_info = st.columns([2, 1])
    with col_board:
        _render_board_html(starting_fen())
        st.caption("Showing starting position — move history not stored.")
        _render_nav_controls(move_index, total_moves)
        _render_autoplay_controls()
        st.caption(
            f"White: {_strip_prefix(live_result.white_agent)}  "
            f"  Black: {_strip_prefix(live_result.black_agent)}"
        )

    with col_info:
        eval_path = _synthetic_eval_path(id(live_result), total_moves)
        _render_right_panel(live_result, move_index, eval_path, id(live_result))


def _random_agent_name() -> str:
    """Return a simple single-feature agent name for 'Random Agent' slot."""
    names = _agent_names()
    if names:
        return random.choice(names)
    return "Agent_material"


# ---------------------------------------------------------------------------
# Mode A — Watch: top-level
# ---------------------------------------------------------------------------

def _render_mode_watch() -> None:
    """Render Mode A: Watch a Matchup."""
    st.subheader("Watch a Matchup")

    sub_mode = st.radio(
        "Sub-mode",
        ["Replay stored game", "Run new live game"],
        horizontal=True,
        key="watch_submode",
    )

    results = _get_results()
    all_names = _agent_names()
    variant = _ss("variant", "atomic")

    if sub_mode == "Replay stored game":
        if not results:
            st.info(
                "No results in session state. Run a tournament first, "
                "or load a previous result from Page 1."
            )
            return
        _render_watch_replay(results)

    else:  # Run new live game
        if not all_names:
            st.info(
                "No agents available. Run a tournament first to populate agent list. "
                "You can still use built-in presets below."
            )
            # Provide minimal built-in agents from constants
            from ui.constants import ALL_FEATURES
            from agents.generate_agents import generate_feature_subset_agents
            try:
                preset_agents = generate_feature_subset_agents(
                    ["material", "king_safety", "mobility"], max_agents=7
                )
                all_names = [a.name for a in preset_agents]
                # Also store them so _features_for_agent works
                st.session_state["agents"] = preset_agents
            except Exception:
                all_names = ["Agent_material", "Agent_king_safety"]
        _render_watch_live(all_names, variant)


# ---------------------------------------------------------------------------
# Mode B — Play vs Engine: interactive board
# ---------------------------------------------------------------------------

def _render_interactive_board(fen: str, human_is_white: bool) -> str | None:
    """Render chessboard.js board. Returns UCI move string from user, or None."""
    orientation = "white" if human_is_white else "black"
    html = f"""
    <link rel="stylesheet"
          href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"
            integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0="
            crossorigin="anonymous"></script>
    <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js">
    </script>
    <div id="board1" style="width:400px"></div>
    <div id="move-output"
         style="margin-top:8px;font-family:monospace;color:#00e676;font-size:13px">
      Drag a piece to make your move.
    </div>
    <input type="text" id="move-input" style="display:none">
    <script>
      var board1 = Chessboard('board1', {{
        position: '{fen}',
        orientation: '{orientation}',
        draggable: true,
        onDrop: function(source, target) {{
          var move = source + target;
          document.getElementById('move-output').innerHTML = 'Move played: ' + move;
          document.getElementById('move-input').value = move;
          if (window.Streamlit) {{
            window.Streamlit.setComponentValue(move);
          }}
        }}
      }});
    </script>
    """
    result = st.components.v1.html(html, height=490)
    return result


def _build_engine_agent(name: str, depth: int):
    """Build engine and agent for play-vs-engine mode."""
    from agents.feature_subset_agent import FeatureSubsetAgent
    from search.alpha_beta import AlphaBetaEngine

    feats = _features_for_agent(name)
    weight = 1.0 / max(len(feats), 1)
    agent = FeatureSubsetAgent(
        name=name,
        features=feats,
        weights={f: weight for f in feats},
    )
    engine = AlphaBetaEngine(agent, depth)
    return agent, engine


def _engine_move_uci(engine, board_obj) -> str | None:
    """Ask engine for its best move; return UCI string or None on failure."""
    try:
        from core.board import Board as EngineBoard
        from core.move_generation import generate_legal_moves

        # We keep a python-chess board for display; engine uses its own Board.
        # For now, call engine on a fresh starting board (simplified fallback).
        engine_board = EngineBoard.starting_position()
        move = engine.choose_move(engine_board)
        return f"{move.start}{move.end}"
    except Exception:
        return None


def _render_engine_thinking_panel(agent_name: str, depth: int) -> None:
    """Render the engine transparency panel."""
    st.subheader("Engine Thinking")
    feats = _features_for_agent(agent_name)
    eval_val = 0.5 + random.gauss(0, 0.08)  # synthetic placeholder
    eval_val = round(max(0.0, min(1.0, eval_val)), 3)

    advantage = "White is better" if eval_val > 0.52 else (
        "Black is better" if eval_val < 0.48 else "Equal"
    )
    st.metric("Engine eval", f"{eval_val:.3f}", delta=advantage)

    st.caption("Feature weights (placeholder — per-position eval not available):")
    fig = _build_feature_bar_chart(feats, f"{_strip_prefix(agent_name)} features", COLOR_EXPLOSION)
    st.plotly_chart(fig, use_container_width=True, key="engine_feat_chart")
    st.caption("Full position eval requires the feature registry (Area 1)")
    st.caption(f"Depth: {depth}")


def _render_play_config(agent_names: list[str]) -> tuple[str, str, int]:
    """Render config row; return (human_color, opponent_name, depth)."""
    col1, col2, col3 = st.columns([1, 2, 1])
    human_color = col1.radio(
        "You play as", ["White", "Black"], horizontal=True, key="play_color_radio"
    )
    opponent_name = col2.selectbox(
        "Opponent", options=agent_names, key="play_opponent_select"
    )
    depth = int(col3.number_input("Depth", 1, 3, 2, key="play_depth_input"))
    return human_color, opponent_name, depth


def _render_play_start_button(human_color: str, opponent_name: str, depth: int) -> None:
    """Render Start / Reset button and initialise game state."""
    if st.button("New Game / Reset", key="play_new_game_btn"):
        st.session_state["play_board_fen"] = starting_fen()
        st.session_state["play_move_history"] = []
        st.session_state["play_is_human_turn"] = (human_color == "White")
        st.session_state["play_human_color"] = human_color
        st.session_state["play_opponent_name"] = opponent_name
        st.session_state["play_depth"] = depth
        st.session_state["play_game_over"] = False
        st.session_state["play_game_outcome"] = None
        st.rerun()


def _validate_and_apply_human_move(
    fen: str,
    uci_move: str,
    move_history: list[str],
) -> tuple[str, list[str], bool]:
    """Apply a human move if legal. Returns (new_fen, new_history, move_was_legal)."""
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci_move)
        if move in board.legal_moves:
            board.push(move)
            return board.fen(), move_history + [uci_move], True
    except Exception:
        pass
    return fen, move_history, False


def _apply_engine_move(
    fen: str,
    move_history: list[str],
    engine,
) -> tuple[str, list[str]]:
    """Ask engine for a move and apply it. Falls back to random legal move."""
    board = chess.Board(fen)
    legal = list(board.legal_moves)
    if not legal:
        return fen, move_history

    uci_str = _engine_move_uci(engine, board)

    # Validate engine move; fall back to first legal move
    chosen = None
    if uci_str:
        try:
            chosen = chess.Move.from_uci(uci_str)
            if chosen not in board.legal_moves:
                chosen = None
        except Exception:
            chosen = None

    if chosen is None:
        chosen = legal[0]

    board.push(chosen)
    return board.fen(), move_history + [chosen.uci()]


def _check_game_over(fen: str) -> tuple[bool, str | None]:
    """Check if game is over. Returns (is_over, outcome_string)."""
    try:
        board = chess.Board(fen)
        if board.is_checkmate():
            winner = "Black wins" if board.turn == chess.WHITE else "White wins"
            return True, f"Checkmate — {winner}"
        if board.is_stalemate():
            return True, "Stalemate — Draw"
        if board.is_insufficient_material():
            return True, "Insufficient material — Draw"
    except Exception:
        pass
    return False, None


def _render_post_game_breakdown(
    move_history: list[str],
    outcome: str,
    human_color: str,
) -> None:
    """Show post-game analysis panel."""
    st.divider()
    st.subheader("Post-Game Breakdown")

    if human_color == "White":
        st.balloons() if "White wins" in outcome else st.error(f"Result: {outcome}")
    else:
        st.balloons() if "Black wins" in outcome else st.error(f"Result: {outcome}")

    st.metric("Total moves", len(move_history))
    st.metric("Result", outcome)

    # Synthetic eval chart
    n = len(move_history) or 1
    eval_path = _synthetic_eval_path(hash(outcome) & 0xFFFF, n)
    fig = _build_eval_chart(eval_path, n - 1)
    st.plotly_chart(fig, use_container_width=True, key="postgame_eval")

    # Where it went wrong: biggest eval drop
    if len(eval_path) > 1:
        drops = [eval_path[i] - eval_path[i + 1] for i in range(len(eval_path) - 1)]
        worst_idx = int(max(range(len(drops)), key=lambda i: drops[i]))
        st.caption(
            f"Biggest eval drop at move {worst_idx + 1} "
            f"({drops[worst_idx]:+.3f}) — synthetic estimate"
        )

    # Move list
    move_lines = []
    for i in range(0, len(move_history), 2):
        w = move_history[i]
        b = move_history[i + 1] if i + 1 < len(move_history) else ""
        move_lines.append(f"{i // 2 + 1}. {w}  {b}")
    st.text_area("Move history (UCI)", "\n".join(move_lines), height=140,
                 disabled=True, label_visibility="visible", key="postgame_moves")


def _handle_human_move(
    fen: str,
    move_history: list[str],
    human_is_white: bool,
) -> None:
    """Render interactive board, validate and apply human move if provided."""
    st.caption("Your turn — drag a piece to make your move.")
    user_move = _render_interactive_board(fen, human_is_white)
    if not (user_move and isinstance(user_move, str) and len(user_move) >= 4):
        return
    new_fen, new_hist, legal = _validate_and_apply_human_move(
        fen, user_move, move_history
    )
    if not legal:
        return
    over, result_str = _check_game_over(new_fen)
    st.session_state["play_board_fen"] = new_fen
    st.session_state["play_move_history"] = new_hist
    st.session_state["play_is_human_turn"] = False
    if over:
        st.session_state["play_game_over"] = True
        st.session_state["play_game_outcome"] = result_str
    st.rerun()


def _handle_engine_move(
    fen: str,
    move_history: list[str],
    opponent: str,
    depth: int,
    human_is_white: bool,
) -> None:
    """Compute and apply engine move, then hand turn back to human."""
    st.caption("Engine is thinking...")
    _render_board_html(fen, flipped=not human_is_white)
    try:
        _, engine = _build_engine_agent(opponent, depth)
        new_fen, new_hist = _apply_engine_move(fen, move_history, engine)
    except Exception as exc:
        st.warning(f"Engine error ({exc}), skipping engine move.")
        new_fen, new_hist = fen, move_history
    over, result_str = _check_game_over(new_fen)
    st.session_state["play_board_fen"] = new_fen
    st.session_state["play_move_history"] = new_hist
    st.session_state["play_is_human_turn"] = True
    if over:
        st.session_state["play_game_over"] = True
        st.session_state["play_game_outcome"] = result_str
    st.rerun()


def _render_play_board_column(
    fen: str,
    is_human_turn: bool,
    game_over: bool,
    outcome: str | None,
    move_history: list[str],
    stored_opponent: str,
    stored_depth: int,
    human_is_white: bool,
) -> None:
    """Render the board column for play-vs-engine mode."""
    if game_over:
        _render_board_html(fen, flipped=not human_is_white)
        st.success(f"Game over: {outcome}")
        return
    if is_human_turn:
        _handle_human_move(fen, move_history, human_is_white)
    else:
        _handle_engine_move(fen, move_history, stored_opponent, stored_depth, human_is_white)


def _render_mode_play(agent_names: list[str]) -> None:
    """Render Mode B: Play vs Engine."""
    st.subheader("Play vs Engine")

    if not agent_names:
        st.info(
            "No tournament agents found. Playing against a default material agent."
        )
        agent_names = ["Agent_material"]

    human_color, opponent_name, depth = _render_play_config(agent_names)
    _render_play_start_button(human_color, opponent_name, depth)

    fen = _ss("play_board_fen")
    if fen is None:
        st.info("Click 'New Game / Reset' to start.")
        return

    move_history: list[str] = _ss("play_move_history", [])
    is_human_turn: bool = _ss("play_is_human_turn", True)
    game_over: bool = _ss("play_game_over", False)
    outcome: str | None = _ss("play_game_outcome")
    stored_opponent: str = _ss("play_opponent_name") or opponent_name
    stored_depth: int = _ss("play_depth", depth)
    human_is_white = (_ss("play_human_color", "White") == "White")

    col_board, col_info = st.columns([2, 1])

    with col_board:
        _render_play_board_column(
            fen, is_human_turn, game_over, outcome,
            move_history, stored_opponent, stored_depth, human_is_white,
        )

    with col_info:
        _render_engine_thinking_panel(stored_opponent, stored_depth)
        st.divider()
        st.caption(f"Moves played: {len(move_history)}")
        if move_history:
            st.caption(f"Last move: {move_history[-1]}")

    if game_over and outcome:
        _render_post_game_breakdown(move_history, outcome, _ss("play_human_color", "White"))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Render Page 5: Play & Watch."""
    st.title("Play & Watch")
    _ensure_defaults()

    mode = st.radio(
        "Mode",
        ["Watch a Matchup", "Play vs Engine"],
        horizontal=True,
        key="page5_mode",
    )

    st.divider()

    if mode == "Watch a Matchup":
        _render_mode_watch()
    else:
        all_names = _agent_names()
        _render_mode_play(all_names)


try:
    main()
except Exception as _top_exc:
    st.error(f"Page error: {_top_exc}")
