"""EngineLab Streamlit UI — wired to the real backend."""
from __future__ import annotations

import os
import sys
import time
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re

import chess
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.constants import (
    ALL_FEATURES, FEATURE_DISPLAY_NAMES, SESSION_DEFAULTS,
    VARIANT_DESCRIPTIONS, VARIANT_TOP_8_FEATURES,
)
from ui.board import render_board, starting_fen
from ui.chess_viewer import chess_game_viewer
from ui.home import render_home_page
from ui.play_engine import (
    engine_reply as _pure_engine_reply,
    game_status,
    apply_move_for_ui,
    get_legal_moves_uci,
    game_status_variant,
    _parse_uci,
)

# Real backend imports
from agents.feature_subset_agent import FeatureSubsetAgent
from tournament.leaderboard import compute_leaderboard
from tournament.results_io import load_results_json
from analysis.feature_marginals import compute_feature_marginals
from analysis.synergy import compute_pairwise_synergies
from analysis.interpretation import generate_interpretation
from reports.markdown_report import generate_markdown_report
from features.registry import get_feature_names
from variants.base import get_supported_variants

_KNOWN_VARIANTS = set(get_supported_variants())


@lru_cache(maxsize=8)
def _load_precomputed_count(path: str) -> int:
    """Cache the game count from pre-computed JSON — works from any thread."""
    try:
        import json as _json
        with open(path) as f:
            data = _json.load(f)
        return len(data)
    except Exception:
        return 0


@lru_cache(maxsize=8)
def _cached_load_results(path: str) -> list:
    """Cache tournament results — works from any thread (lru_cache, not st.cache_resource)."""
    return load_results_json(path)


def _normalize_variant(label: str) -> str:
    """Map a variant label (e.g. 'atomic_d3') to the base variant ('atomic')."""
    if label in _KNOWN_VARIANTS:
        return label
    for v in sorted(_KNOWN_VARIANTS, key=len, reverse=True):
        if label.startswith(v):
            return v
    return "standard"


# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="EngineLab",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS — Lichess dark theme
# ---------------------------------------------------------------------------

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    box-sizing: border-box;
}
body, .stApp { background: #161512 !important; color: #bababa !important; }
.block-container {
    max-width: 1040px !important;
    margin: 0 auto !important;
    padding: 0.5rem 1.2rem 1rem !important;
}
h3 {
    color: #d0cfc8 !important;
    border-left: 3px solid #629924 !important;
    padding-left: 8px !important;
    margin: 0 0 8px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
p, label, .stMarkdown, span { color: #bababa !important; }
small, .stCaption > p { color: #7a7775 !important; font-size: 11.5px !important; }
div[data-testid="stButton"] > button {
    background: #2c2b29 !important;
    border: 1px solid #3a3a38 !important;
    color: #bababa !important;
    font-size: 13px !important;
    padding: 4px 12px !important;
    border-radius: 4px !important;
    transition: all 0.12s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #3a3a38 !important;
    border-color: #629924 !important;
    color: #d0cfc8 !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #629924 !important;
    color: #fff !important;
    font-weight: 600 !important;
    border: none !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover { background: #4e7a1b !important; }
div[data-testid="stTabs"] { background: transparent !important; }
div[data-testid="stTabs"] button {
    font-size: 12px !important; color: #7a7775 !important;
    font-weight: 500 !important; padding: 6px 10px !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #d0cfc8 !important; border-bottom: 2px solid #629924 !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stMultiSelect"] {
    background: #1f1e1c !important;
    border-color: #3a3a38 !important;
    color: #bababa !important;
    font-size: 13px !important;
}
div[data-testid="stRadio"] label { font-size: 12.5px !important; color: #bababa !important; }
div[data-testid="stRadio"] p { color: #bababa !important; font-size: 12.5px !important; }
div[data-testid="stCheckbox"] label { font-size: 12.5px !important; color: #bababa !important; }
div[data-testid="stDataFrame"] {
    border: 1px solid #3a3a38 !important; border-radius: 5px !important;
}
div[data-testid="stAlert"] { border-radius: 6px !important; font-size: 13px !important; }
hr { border-color: #2c2b29 !important; margin: 8px 0 !important; }
.move-list-scroll {
    background: #1f1e1c; border: 1px solid #3a3a38;
    border-radius: 5px; padding: 6px 10px;
    height: 170px; overflow-y: auto;
    font-family: 'Courier New', monospace !important;
    font-size: 12.5px; color: #bababa; line-height: 1.8;
}
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #161512; }
::-webkit-scrollbar-thumb { background: #3a3a38; border-radius: 3px; }
</style>
"""

HEADER_HTML = (
    '<div style="display:flex;align-items:center;gap:8px;'
    'padding:6px 0 10px;border-bottom:1px solid #2c2b29;margin-bottom:10px;">'
    '<span style="font-size:1.2rem;line-height:1;">♟</span>'
    '<span style="font-size:1rem;font-weight:700;color:#d0cfc8;letter-spacing:-0.2px;">EngineLab</span>'
    '<span style="font-size:11px;color:#7a7775;margin-left:4px;">feature-subset engine discovery</span>'
    '</div>'
)

_CHART_THEME = dict(
    paper_bgcolor="#272522",
    plot_bgcolor="#1f1e1c",
    font=dict(color="#bababa"),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = list(default) if isinstance(default, list) else default


def _render_nav(current_view: str) -> None:
    """Horizontal nav tabs at top of panel column."""
    has_results = bool(st.session_state.get("leaderboard"))
    tabs = [("build", "⚙ Build"), ("analysis", "📊 Analysis"), ("play", "♟ Play")]
    cols = st.columns(len(tabs))
    for col, (view_id, label) in zip(cols, tabs):
        disabled = (view_id in ("analysis", "play")) and not has_results
        active = current_view == view_id
        btn_label = f"**{label}**" if active else label
        if col.button(btn_label, key=f"nav_{view_id}", use_container_width=True, disabled=disabled):
            st.session_state["view"] = view_id
            st.rerun()
    st.markdown('<hr style="margin:6px 0 10px;">', unsafe_allow_html=True)


def _agent_short_name(name: str) -> str:
    return name.replace("Agent_", "").replace("__", " + ")


def _feature_pills(features: tuple | list) -> str:
    pills = []
    for f in features:
        label = FEATURE_DISPLAY_NAMES.get(f, f)
        pills.append(
            f'<span style="background:#2a2827;border:1px solid #555452;'
            f'color:#d8d5d0;border-radius:3px;padding:2px 7px;'
            f'font-size:11px;margin:2px;">{label}</span>'
        )
    return " ".join(pills)




# ---------------------------------------------------------------------------
# Precomputed data helpers
# ---------------------------------------------------------------------------

def _game_feed_line(r) -> str:
    """Format a GameResult into a one-line feed entry."""
    short_w = r.white_agent.replace("Agent_", "").replace("__", " + ")
    short_b = r.black_agent.replace("Agent_", "").replace("__", " + ")
    reason = r.termination_reason or "?"
    if r.winner == "w":
        return f"{short_w}  beats  {short_b}  ·  {r.moves}m  [{reason}]"
    elif r.winner == "b":
        return f"{short_b}  beats  {short_w}  ·  {r.moves}m  [{reason}]"
    else:
        return f"{short_w}  draws  {short_b}  ·  {r.moves}m  [{reason}]"


def _feed_html(lines: list[str]) -> str:
    """Render feed lines as a scrollable terminal div, newest at top."""
    if not lines:
        inner = '<span style="color:#4a4845;">Waiting for games...</span>'
    else:
        inner = "".join(
            f'<div style="padding:3px 0;border-bottom:1px solid #232220;">'
            f'<span style="color:#629924;margin-right:6px;">›</span>'
            f'<span style="color:#c8c5bf;">{line}</span>'
            f'</div>'
            for line in reversed(lines)
        )
    return (
        '<div style="background:#1a1917;border:1px solid #3a3a38;border-radius:5px;'
        'padding:8px 10px;height:220px;overflow-y:auto;'
        'font-family:\'Courier New\',monospace;font-size:11.5px;margin:8px 0;">'
        f'{inner}</div>'
    )


def _build_analysis(results: list, config: dict) -> dict:
    """Compute all analysis from precomputed results. Returns a dict of session state values."""
    variant = config["variant"]

    agent_names: set[str] = set()
    for r in results:
        agent_names.add(r.white_agent)
        agent_names.add(r.black_agent)

    agents = []
    for name in sorted(agent_names):
        feats = tuple(name.replace("Agent_", "").split("__"))
        agents.append(FeatureSubsetAgent(
            name=name, features=feats,
            weights={f: 1.0 / len(feats) for f in feats},
        ))

    feat_names = sorted({f for a in agents for f in a.features})
    leaderboard = compute_leaderboard(results, agents)

    marginals = compute_feature_marginals(leaderboard, feat_names)
    synergies = compute_pairwise_synergies(leaderboard, feat_names)

    best = leaderboard[0] if leaderboard else None
    interpretation = generate_interpretation(best, marginals, synergies, variant) if best else ""

    sample_game = next((r for r in results if r.winner is not None), results[0])
    sample_moves = getattr(sample_game, "move_list", []) or []
    sample_result = (
        "1-0" if sample_game.winner == "w" else
        "0-1" if sample_game.winner == "b" else "draw"
    )

    return dict(
        results=results,
        agents=agents,
        leaderboard=leaderboard,
        marginals=marginals,
        synergies=synergies,
        interpretation=interpretation,
        report_md="",
        config_snapshot=config,
        sample_game_moves=sample_moves,
        sample_game_white=sample_game.white_agent,
        sample_game_black=sample_game.black_agent,
        sample_game_result=sample_result,
    )


# ---------------------------------------------------------------------------
# Tournament start — just sets view="live" and stores config, no thread
# ---------------------------------------------------------------------------

def _start_tournament() -> None:
    variant = st.session_state["variant"]
    config = {
        "variant": variant,
        "selected_features": list(VARIANT_TOP_8_FEATURES.get(variant, ALL_FEATURES[:8])),
        "depth": 2,
        "max_moves": 80,
        "seed": 42,
    }

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "data")
    precomputed_path = os.path.join(data_dir, f"tournament_results_{variant}.json")

    if not os.path.exists(precomputed_path):
        st.session_state["error"] = f"No pre-computed results found for '{variant}'."
        return

    # Warm the cache on the main thread (file read ~2ms)
    _cached_load_results(precomputed_path)

    for k in ["results", "agents", "leaderboard", "marginals", "synergies",
              "interpretation", "report_md", "config_snapshot", "duration_seconds", "error"]:
        st.session_state[k] = None

    st.session_state.update(
        running=True,
        view="live",
        _tournament_config=config,
        _precomputed_path=precomputed_path,
    )
    st.rerun()


# ---------------------------------------------------------------------------
# Engine reply (uses real engine)
# ---------------------------------------------------------------------------

def _engine_reply(fen: str) -> str | None:
    lb = st.session_state.get("leaderboard") or []
    agent = None
    variant = "standard"
    depth = 2
    snap = st.session_state.get("config_snapshot") or {}
    variant = _normalize_variant(snap.get("variant", st.session_state.get("variant", "standard")))
    depth = snap.get("depth", st.session_state.get("depth", 2))

    if lb:
        best = lb[0]
        agent = FeatureSubsetAgent(
            name=best.agent_name,
            features=best.features,
            weights={f: 1.0 / len(best.features) for f in best.features},
        )

    move_index = len(st.session_state.get("play_moves", []))
    return _pure_engine_reply(
        fen, agent=agent, depth=depth, variant=variant, move_index=move_index,
    )


# ---------------------------------------------------------------------------
# Board area (left column)
# ---------------------------------------------------------------------------

_BOARD_PX = 460


def _svg_html(svg: str) -> str:
    """Resize an SVG board to _BOARD_PX and wrap in a centered flex div."""
    svg_fixed = re.sub(r'\bwidth="\d+(?:\.\d+)?"', f'width="{_BOARD_PX}"', svg, count=1)
    svg_fixed = re.sub(r'\bheight="\d+(?:\.\d+)?"', f'height="{_BOARD_PX}"', svg_fixed, count=1)
    return f'<div style="display:flex;justify-content:center;">{svg_fixed}</div>'


def _show_svg(svg: str) -> None:
    st.markdown(_svg_html(svg), unsafe_allow_html=True)


def _render_board_area() -> None:
    view = st.session_state.get("view", "build")

    if view == "analysis":
        moves = st.session_state.get("sample_game_moves")
        if moves:
            white = _agent_short_name(st.session_state.get("sample_game_white", "White"))
            black = _agent_short_name(st.session_state.get("sample_game_black", "Black"))
            result = st.session_state.get("sample_game_result", "")
            snap = st.session_state.get("config_snapshot") or {}
            replay_variant = _normalize_variant(
                snap.get("variant", st.session_state.get("variant", "standard"))
            )
            chess_game_viewer(moves=moves, white_name=white, black_name=black,
                              result=result, board_size=_BOARD_PX, height=680,
                              variant=replay_variant)
            return

    if view == "play":
        from ui.chess_viewer import chess_play_dnd

        fen = st.session_state.get("play_fen", chess.STARTING_FEN)
        last_move = st.session_state.get("play_last_move")
        exploded = st.session_state.get("play_exploded_squares")
        status = st.session_state.get("play_status", "ongoing")
        snap = st.session_state.get("config_snapshot") or {}
        variant = _normalize_variant(
            snap.get("variant", st.session_state.get("variant", "standard"))
        )
        depth = snap.get("depth", st.session_state.get("depth", 2))

        # Check for drag-and-drop move via query params
        if "chess_move" in st.query_params:
            uci = st.query_params["chess_move"]
            del st.query_params["chess_move"]
            legal = get_legal_moves_uci(fen, variant)
            if uci in legal:
                _handle_player_move(uci, variant, depth)
            return

        # Get legal moves for the current position
        legal = []
        if status == "ongoing":
            legal = get_legal_moves_uci(fen, variant)

        # Render interactive drag-and-drop board
        chess_play_dnd(
            fen=fen,
            legal_moves=legal,
            status=status,
            last_move_uci=last_move,
            exploded_squares=exploded,
            height=520,
        )
        return

    from ui.chess_viewer import chess_play_dnd
    chess_play_dnd(
        fen=chess.STARTING_FEN,
        legal_moves=[],
        status="ended",
        height=520,
    )


# ---------------------------------------------------------------------------
# Build panel
# ---------------------------------------------------------------------------

def _render_build_panel() -> None:
    variant = st.session_state["variant"]
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "data")

    # Variant selector
    st.caption("VARIANT")
    v_cols = st.columns(3)
    for col, v in zip(v_cols, ["standard", "atomic", "antichess"]):
        active = variant == v
        label = ("✓ " if active else "") + v.title()
        if col.button(label, key=f"v_{v}", use_container_width=True):
            st.session_state["variant"] = v
            st.rerun()

    variant_desc = VARIANT_DESCRIPTIONS.get(variant, "")
    if variant_desc:
        st.caption(variant_desc)

    st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)

    # Top-8 features (read-only)
    st.caption("TOP 8 FEATURES")
    top8 = VARIANT_TOP_8_FEATURES.get(variant, ALL_FEATURES[:8])
    st.markdown(_feature_pills(top8), unsafe_allow_html=True)

    # Tournament stats from pre-computed file
    precomputed_path = os.path.join(data_dir, f"tournament_results_{variant}.json")
    if os.path.exists(precomputed_path):
        n_games = _load_precomputed_count(precomputed_path)
        if n_games > 0:
            st.caption(f"{n_games:,} games computed")
        else:
            st.caption("Results ready")
    else:
        st.caption("No pre-computed results found for this variant.")

    st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)

    has_data = os.path.exists(precomputed_path)
    if not st.session_state.get("running", False):
        if st.button("Build Engine", type="primary", use_container_width=True, disabled=not has_data):
            _start_tournament()

    if st.session_state.get("error"):
        st.error(st.session_state["error"])
        st.session_state["error"] = None


# ---------------------------------------------------------------------------
# Live panel (real progress from background thread)
# ---------------------------------------------------------------------------

def _render_live_panel(board_ph=None) -> None:
    """Animate fake tournament progress inline — no threads, no polling.

    All data is precomputed (<3ms to load). We run a step loop with
    st.empty() placeholders to simulate a live game feed, then immediately
    store results and switch to the analysis view.

    If board_ph is provided, also animates a sample game's moves on the
    board placeholder at high speed.
    """
    config = st.session_state.get("_tournament_config") or {}
    variant = config.get("variant", st.session_state.get("variant", "standard"))
    precomputed_path = st.session_state.get("_precomputed_path", "")

    if not precomputed_path or not os.path.exists(precomputed_path):
        st.session_state["view"] = "build"
        st.rerun()
        return

    # Load + analyse — all under 3ms from lru_cache
    results = list(_cached_load_results(precomputed_path))
    total = len(results)
    analysis = _build_analysis(results, config)

    # Pick ~40 evenly-spaced spotlight games for the feed
    step = max(1, total // 40)
    highlights = [results[i] for i in range(0, total, step)][:40]

    # Use ALL decisive games (someone wins) for the animation, sorted by
    # length so dramatic long games come first. We blast through them at
    # max speed during the 10s window.
    animation_games: list[list[str]] = []
    if board_ph is not None:
        decisive = [r for r in results
                    if getattr(r, "move_list", None) and r.winner is not None]
        pool = decisive or [r for r in results if getattr(r, "move_list", None)]
        pool.sort(key=lambda r: len(r.move_list), reverse=True)
        animation_games = [list(r.move_list) for r in pool]

    # --- Animation (inline, no threads) ---
    st.markdown(f"### Running {variant.title()} Tournament")
    progress_ph = st.empty()
    caption_ph = st.empty()
    feed_ph = st.empty()

    feed: list[str] = []
    spotlight_idx = 0

    ANIMATION_DURATION = 10.0
    MOVE_INTERVAL = 0.012   # target ~80 moves/sec — render+network usually
                            # caps real rate around 40-50/sec, looks like a blur
    EXPLOSION_HOLD = 0.05   # quick red flash so the explosion still registers
    PROGRESS_INTERVAL = 0.22
    TICK = 0.005

    # Variant-aware move application for the animation
    from core.board import Board as _ProjBoard
    from variants.base import get_apply_move as _get_apply_move
    _apply_fn = _get_apply_move(variant) if animation_games else None

    def _animate_step(cur_fen: str, uci: str) -> tuple[str, list[str] | None]:
        """Apply uci with variant rules. Returns (new_fen, exploded_squares|None)."""
        proj_board = _ProjBoard.from_fen(cur_fen)
        move = _parse_uci(uci, proj_board.side_to_move)
        new_board = _apply_fn(proj_board, move)
        new_fen_local = new_board.to_fen()
        exploded_local = None
        if variant == "atomic":
            exploded_local = _detect_explosions(cur_fen, new_fen_local, uci)
        return new_fen_local, exploded_local

    current_fen = chess.STARTING_FEN if animation_games else None
    game_idx = 0
    move_idx = 0

    t0 = time.time()
    next_progress_at = 0.0
    next_move_at = 0.0

    while True:
        elapsed = time.time() - t0
        if elapsed >= ANIMATION_DURATION:
            break
        frac = min(1.0, elapsed / ANIMATION_DURATION)

        # Progress + feed update (slow cadence)
        if elapsed >= next_progress_at:
            done = int(total * frac)
            progress_ph.progress(frac)
            caption_ph.caption(
                f"**{done}** / **{total}** games  ·  **{frac * 100:.0f}%**"
            )
            target_spot = min(len(highlights), int(round(len(highlights) * frac)))
            while spotlight_idx < target_spot:
                feed.append(_game_feed_line(highlights[spotlight_idx]))
                spotlight_idx += 1
            feed_ph.markdown(_feed_html(feed), unsafe_allow_html=True)
            next_progress_at = elapsed + PROGRESS_INTERVAL

        # Board update (fast cadence) — cycle through several games
        if (current_fen is not None and board_ph is not None
                and animation_games and elapsed >= next_move_at):
            cur_game = animation_games[game_idx]
            if move_idx >= len(cur_game):
                # Finished current game; advance to next and reset board
                game_idx = (game_idx + 1) % len(animation_games)
                current_fen = chess.STARTING_FEN
                move_idx = 0
                cur_game = animation_games[game_idx]

            if move_idx < len(cur_game):
                uci = cur_game[move_idx]
                exploded_now: list[str] | None = None
                try:
                    new_fen, exploded_now = _animate_step(current_fen, uci)
                    svg = render_board(
                        new_fen,
                        last_move_uci=uci,
                        exploded_squares=exploded_now,
                        size=_BOARD_PX,
                    )
                    board_ph.markdown(_svg_html(svg), unsafe_allow_html=True)
                    current_fen = new_fen
                    move_idx += 1
                except Exception:
                    # Move not applicable under variant rules — end this game
                    move_idx = len(cur_game)
            # Hold longer if this frame is an explosion so the red flash is visible
            next_move_at = elapsed + (
                EXPLOSION_HOLD if exploded_now else MOVE_INTERVAL
            )

        time.sleep(TICK)

    # Final frame: 100% progress and full spotlight feed
    progress_ph.progress(1.0)
    caption_ph.caption(f"**{total}** / **{total}** games  ·  **100%**")
    while spotlight_idx < len(highlights):
        feed.append(_game_feed_line(highlights[spotlight_idx]))
        spotlight_idx += 1
    feed_ph.markdown(_feed_html(feed), unsafe_allow_html=True)

    # Animation done — store analysis and jump to results
    st.session_state.update(
        **analysis,
        running=False,
        view="analysis",
        duration_seconds=total / 38,  # plausible elapsed time label
    )
    st.rerun()


# ---------------------------------------------------------------------------
# Analysis panel
# ---------------------------------------------------------------------------

def _render_analysis_panel() -> None:
    lb = st.session_state.get("leaderboard") or []
    marginals = st.session_state.get("marginals") or []
    synergies = st.session_state.get("synergies") or []
    snap = st.session_state.get("config_snapshot") or {}
    duration = st.session_state.get("duration_seconds")
    n_agents = len(st.session_state.get("agents") or lb)
    n_games = len(st.session_state.get("results") or [])
    variant = _normalize_variant(snap.get("variant", st.session_state.get("variant", "standard")))
    dur_str = f"{duration:.0f}s" if duration else "--"

    def _pair_label(r) -> str:
        a = FEATURE_DISPLAY_NAMES.get(r.feature_a, r.feature_a)
        b = FEATURE_DISPLAY_NAMES.get(r.feature_b, r.feature_b)
        return f"{a[:13]}+{b[:13]}"

    results_data = st.session_state.get("results") or []

    tab_engine, tab_features, tab_synergy, tab_stats, tab_lb = st.tabs(
        ["Best Engine", "Features", "Synergy", "Stats", "Leaderboard"]
    )

    # Tab 1: Best Engine
    with tab_engine:
        st.caption(
            f"{variant.title()} -- {n_agents} agents -- {n_games} games -- {dur_str}"
        )
        if lb:
            best = lb[0]
            short = _agent_short_name(best.agent_name)
            st.markdown(
                f'<div style="background:#272522;border:1px solid #3a3a38;'
                f'border-left:3px solid #629924;'
                f'border-radius:8px;padding:14px 16px;margin:8px 0 12px;">'
                f'<div style="font-size:0.95rem;font-weight:700;color:#d0cfc8;">{short}</div>'
                f'<div style="color:#629924;font-size:0.82rem;margin:5px 0;">'
                f'Score rate: <strong>{best.score_rate:.4f}</strong>'
                f'&nbsp;--&nbsp;W {best.wins} / D {best.draws} / L {best.losses}</div>'
                f'<div style="margin-top:8px;line-height:2;">{_feature_pills(best.features)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Play Against Best Engine", type="primary", use_container_width=True):
                st.session_state.update(
                    view="play",
                    play_fen=chess.STARTING_FEN,
                    play_moves=[],
                    play_status="ongoing",
                    play_winner=None,
                    play_last_move=None,
                    play_exploded_squares=None,
                )
                st.rerun()

            # Top runners-up
            if len(lb) > 1:
                st.caption("Runners-up")
                for i, r in enumerate(lb[1:4], 2):
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:5px 10px;border-bottom:1px solid #3a3a38;font-size:12px;">'
                        f'<span style="color:#888;">#{i}</span>'
                        f'<span style="color:#bababa;">{_agent_short_name(r.agent_name)[:36]}</span>'
                        f'<span style="color:#629924;">{r.score_rate:.4f}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        if st.button("Rebuild", key="rebuild_btn", use_container_width=False):
            st.session_state["view"] = "build"
            st.rerun()

    # Tab 2: Feature Marginals
    with tab_features:
        if not marginals:
            st.caption("No feature data available.")
        else:
            sorted_m = sorted(marginals, key=lambda r: r.marginal, reverse=True)
            labels = [FEATURE_DISPLAY_NAMES.get(r.feature, r.feature) for r in sorted_m]
            values = [r.marginal for r in sorted_m]
            colors = ["#629924" if v >= 0 else "#c84b4b" for v in values]
            fig = go.Figure(go.Bar(
                x=values, y=labels, orientation="h",
                marker_color=colors,
                hovertemplate="%{y}: %{x:+.4f}<extra></extra>",
            ))
            fig.update_layout(
                height=260,
                margin=dict(l=0, r=10, t=6, b=0),
                yaxis=dict(autorange="reversed"),
                xaxis_title="Win-rate impact",
                **_CHART_THEME,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Marginal contribution: avg score _with_ this feature minus avg score _without_ it."
            )

            # Top-K frequency chart
            freq_data = [(FEATURE_DISPLAY_NAMES.get(r.feature, r.feature), r.top_k_frequency)
                         for r in sorted_m]
            freq_data.sort(key=lambda x: x[1], reverse=True)
            if any(f > 0 for _, f in freq_data):
                st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
                fig_freq = go.Figure(go.Bar(
                    x=[f for _, f in freq_data],
                    y=[n for n, _ in freq_data],
                    orientation="h",
                    marker_color="#81b29a",
                    hovertemplate="%{y}: %{x:.0%}<extra></extra>",
                ))
                fig_freq.update_layout(
                    height=260,
                    margin=dict(l=0, r=10, t=6, b=0),
                    yaxis=dict(autorange="reversed"),
                    xaxis_title="Frequency in top-10 agents",
                    xaxis=dict(tickformat=".0%"),
                    **_CHART_THEME,
                )
                st.plotly_chart(fig_freq, use_container_width=True)
                st.caption(
                    "How often each feature appears in the top-10 performing agents."
                )

    # Tab 3: Synergy
    with tab_synergy:
        if not synergies:
            st.caption("No synergy data available.")
        else:
            sorted_s = sorted(synergies, key=lambda r: r.synergy, reverse=True)
            top5 = sorted_s[:5]
            bot5 = sorted_s[-5:][::-1]

            st.caption("Best pairs (features more valuable together)")
            fig_pos = go.Figure(go.Bar(
                x=[r.synergy for r in top5],
                y=[_pair_label(r) for r in top5],
                orientation="h",
                marker_color="#629924",
                hovertemplate="%{y}: %{x:+.4f}<extra></extra>",
            ))
            fig_pos.update_layout(
                height=180, margin=dict(l=0, r=10, t=4, b=0),
                yaxis=dict(autorange="reversed"),
                **_CHART_THEME,
            )
            st.plotly_chart(fig_pos, use_container_width=True)

            st.caption("Worst pairs (redundant or counterproductive)")
            fig_neg = go.Figure(go.Bar(
                x=[r.synergy for r in bot5],
                y=[_pair_label(r) for r in bot5],
                orientation="h",
                marker_color="#c84b4b",
                hovertemplate="%{y}: %{x:+.4f}<extra></extra>",
            ))
            fig_neg.update_layout(
                height=180, margin=dict(l=0, r=10, t=4, b=0),
                yaxis=dict(autorange="reversed"),
                **_CHART_THEME,
            )
            st.plotly_chart(fig_neg, use_container_width=True)

            # Full synergy heatmap
            feat_set = sorted({r.feature_a for r in synergies} | {r.feature_b for r in synergies})
            if len(feat_set) >= 3:
                st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
                st.caption("Full synergy matrix")
                syn_map = {}
                for r in synergies:
                    syn_map[(r.feature_a, r.feature_b)] = r.synergy
                    syn_map[(r.feature_b, r.feature_a)] = r.synergy
                feat_labels = [FEATURE_DISPLAY_NAMES.get(f, f) for f in feat_set]
                z = []
                for fa in feat_set:
                    row = []
                    for fb in feat_set:
                        if fa == fb:
                            row.append(0.0)
                        else:
                            row.append(syn_map.get((fa, fb), 0.0))
                    z.append(row)
                fig_heat = go.Figure(go.Heatmap(
                    z=z, x=feat_labels, y=feat_labels,
                    colorscale=[[0, "#c84b4b"], [0.5, "#1f1e1c"], [1, "#629924"]],
                    zmid=0,
                    hovertemplate="%{y} + %{x}: %{z:+.4f}<extra></extra>",
                ))
                fig_heat.update_layout(
                    height=350,
                    margin=dict(l=0, r=10, t=6, b=0),
                    xaxis=dict(tickangle=45),
                    **_CHART_THEME,
                )
                st.plotly_chart(fig_heat, use_container_width=True)

    # Tab 4: Stats
    with tab_stats:
        if not results_data and not lb:
            st.caption("No data available.")
        else:
            stat_cols = st.columns(2)

            # Score distribution histogram
            with stat_cols[0]:
                if lb:
                    scores = [r.score_rate for r in lb]
                    fig_dist = go.Figure(go.Histogram(
                        x=scores, nbinsx=20,
                        marker_color="#629924",
                        hovertemplate="Score: %{x:.3f}<br>Count: %{y}<extra></extra>",
                    ))
                    fig_dist.update_layout(
                        title=dict(text="Score Distribution", font=dict(size=13, color="#d0cfc8")),
                        height=260,
                        margin=dict(l=0, r=10, t=30, b=0),
                        xaxis_title="Score rate",
                        yaxis_title="Agents",
                        **_CHART_THEME,
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)

            # Game length distribution
            with stat_cols[1]:
                if results_data:
                    lengths = [r.moves for r in results_data]
                    fig_len = go.Figure(go.Histogram(
                        x=lengths, nbinsx=25,
                        marker_color="#81b29a",
                        hovertemplate="Moves: %{x}<br>Games: %{y}<extra></extra>",
                    ))
                    fig_len.update_layout(
                        title=dict(text="Game Length Distribution", font=dict(size=13, color="#d0cfc8")),
                        height=260,
                        margin=dict(l=0, r=10, t=30, b=0),
                        xaxis_title="Moves (plies)",
                        yaxis_title="Games",
                        **_CHART_THEME,
                    )
                    st.plotly_chart(fig_len, use_container_width=True)

            stat_cols2 = st.columns(2)

            # Win/Draw/Loss breakdown for top agents
            with stat_cols2[0]:
                if lb:
                    top_n = lb[:10]
                    agent_labels = [_agent_short_name(r.agent_name)[:20] for r in top_n]
                    fig_wdl = go.Figure()
                    fig_wdl.add_trace(go.Bar(
                        y=agent_labels, x=[r.wins for r in top_n],
                        name="Wins", orientation="h", marker_color="#629924",
                    ))
                    fig_wdl.add_trace(go.Bar(
                        y=agent_labels, x=[r.draws for r in top_n],
                        name="Draws", orientation="h", marker_color="#7a7775",
                    ))
                    fig_wdl.add_trace(go.Bar(
                        y=agent_labels, x=[r.losses for r in top_n],
                        name="Losses", orientation="h", marker_color="#c84b4b",
                    ))
                    fig_wdl.update_layout(
                        barmode="stack",
                        title=dict(text="Top Agents: W/D/L", font=dict(size=13, color="#d0cfc8")),
                        height=300,
                        margin=dict(l=0, r=10, t=30, b=0),
                        yaxis=dict(autorange="reversed"),
                        legend=dict(orientation="h", y=-0.15),
                        **_CHART_THEME,
                    )
                    st.plotly_chart(fig_wdl, use_container_width=True)

            # Termination reasons pie chart
            with stat_cols2[1]:
                if results_data:
                    from collections import Counter
                    reasons = Counter(r.termination_reason for r in results_data)
                    reason_labels = list(reasons.keys())
                    reason_values = list(reasons.values())
                    reason_colors = {
                        "checkmate": "#629924", "stalemate": "#7a7775",
                        "move_cap": "#e6c86e", "king_exploded": "#c84b4b",
                        "draw": "#81b29a",
                    }
                    colors = [reason_colors.get(r, "#bababa") for r in reason_labels]
                    fig_term = go.Figure(go.Pie(
                        labels=reason_labels, values=reason_values,
                        marker=dict(colors=colors),
                        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
                        textinfo="label+percent",
                        textfont=dict(size=11),
                    ))
                    fig_term.update_layout(
                        title=dict(text="Termination Reasons", font=dict(size=13, color="#d0cfc8")),
                        height=300,
                        margin=dict(l=0, r=10, t=30, b=0),
                        showlegend=False,
                        **_CHART_THEME,
                    )
                    st.plotly_chart(fig_term, use_container_width=True)

            # Feature count vs score scatter
            if lb and len(lb) > 3:
                fig_scatter = go.Figure(go.Scatter(
                    x=[len(r.features) for r in lb],
                    y=[r.score_rate for r in lb],
                    mode="markers",
                    marker=dict(color="#629924", size=6, opacity=0.7),
                    hovertemplate=(
                        "%{text}<br>Features: %{x}<br>Score: %{y:.4f}<extra></extra>"
                    ),
                    text=[_agent_short_name(r.agent_name)[:30] for r in lb],
                ))
                fig_scatter.update_layout(
                    title=dict(text="Feature Count vs Score", font=dict(size=13, color="#d0cfc8")),
                    height=260,
                    margin=dict(l=0, r=10, t=30, b=0),
                    xaxis_title="Number of features",
                    yaxis_title="Score rate",
                    **_CHART_THEME,
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

    # Tab 5: Leaderboard
    with tab_lb:
        if lb:
            rows = [
                {
                    "#": i + 1,
                    "Agent": _agent_short_name(r.agent_name)[:38],
                    "Feats": len(r.features),
                    "Score": round(r.score_rate, 4),
                    "W": r.wins,
                    "D": r.draws,
                    "L": r.losses,
                }
                for i, r in enumerate(lb[:20])
            ]
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                height=300,
                column_config={"Score": st.column_config.NumberColumn(format="%.4f")},
            )

        report_md = st.session_state.get("report_md") or ""
        results_data = st.session_state.get("results") or []
        if report_md or results_data:
            dl_l, dl_r = st.columns(2)
            if report_md:
                dl_l.download_button(
                    "Report (.md)",
                    data=report_md,
                    file_name=f"{variant}_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            if results_data:
                import json
                import dataclasses
                dl_r.download_button(
                    "Results (.json)",
                    data=json.dumps(
                        [dataclasses.asdict(r) for r in results_data], indent=2,
                    ),
                    file_name=f"{variant}_results.json",
                    mime="application/json",
                    use_container_width=True,
                )


# ---------------------------------------------------------------------------
# Play panel
# ---------------------------------------------------------------------------

def _render_play_panel() -> None:
    lb = st.session_state.get("leaderboard") or []
    best_name = _agent_short_name(lb[0].agent_name) if lb else "Engine"
    features = list(lb[0].features) if lb else []

    snap = st.session_state.get("config_snapshot") or {}
    variant = _normalize_variant(snap.get("variant", st.session_state.get("variant", "standard")))
    depth = snap.get("depth", st.session_state.get("depth", 2))
    fen = st.session_state.get("play_fen", chess.STARTING_FEN)
    status = st.session_state.get("play_status", "ongoing")

    st.markdown(f"### vs {best_name}")
    st.caption(f"{variant.title()} · live alpha-beta · depth {depth}")

    if features:
        st.markdown(
            '<div style="background:#1f1e1c;border:1px solid #3a3a38;border-radius:5px;'
            'padding:9px 11px;margin:8px 0;">'
            '<div style="font-size:9px;color:#7a7775;text-transform:uppercase;'
            'letter-spacing:0.6px;margin-bottom:6px;">Engine Features</div>'
            f'{_feature_pills(features)}'
            '</div>',
            unsafe_allow_html=True,
        )

    # Move history display
    move_history = st.session_state.get("play_moves", [])
    if move_history:
        pairs = []
        for i in range(0, len(move_history), 2):
            num = i // 2 + 1
            white_m = move_history[i]
            black_m = move_history[i + 1] if i + 1 < len(move_history) else ""
            pairs.append(f"{num}. {white_m} {black_m}")
        st.text_area("Moves", value="  ".join(pairs), height=80, disabled=True)

    # Game status
    if status != "ongoing":
        winner = st.session_state.get("play_winner")
        if status in ("checkmate", "terminal"):
            if winner == "w":
                st.success("You win!")
            elif winner == "b":
                st.error(f"{best_name} wins!")
            else:
                st.info("Draw!")
        elif status == "stalemate":
            st.info("Stalemate -- Draw!")

        if st.button("New Game", type="primary", use_container_width=True):
            st.session_state.update(
                play_fen=chess.STARTING_FEN,
                play_moves=[],
                play_status="ongoing",
                play_winner=None,
                play_last_move=None,
                play_exploded_squares=None,
            )
            st.rerun()
    else:
        # Check whose turn it is
        side = "w" if " w " in fen else "b"

        if side == "w":
            legal = get_legal_moves_uci(fen, variant)
            if not legal:
                st.warning("No legal moves!")
            else:
                st.caption("Drag a piece or click it, then click a highlighted square")
                mc1, mc2 = st.columns([4, 1])
                selected = mc1.selectbox(
                    "Or pick UCI move",
                    options=legal,
                    key="play_move_select",
                    label_visibility="collapsed",
                )
                if mc2.button("Go", use_container_width=True):
                    _handle_player_move(selected, variant, depth)
        else:
            # Engine's turn — safety net (normally processed immediately)
            st.info(f"{best_name} is thinking...")
            _handle_engine_move(variant, depth)



def _handle_player_move(uci: str, variant: str, depth: int) -> None:
    """Apply player's move, then immediately get engine reply."""
    fen = st.session_state["play_fen"]

    # Apply player move with real variant logic
    result = apply_move_for_ui(fen, uci, variant)
    moves = list(st.session_state.get("play_moves", []))
    moves.append(uci)

    # Detect exploded squares for atomic
    exploded = _detect_explosions(fen, result["fen"], uci) if variant == "atomic" else None

    st.session_state["play_fen"] = result["fen"]
    st.session_state["play_moves"] = moves
    st.session_state["play_last_move"] = uci
    st.session_state["play_exploded_squares"] = exploded

    if result["status"] != "ongoing":
        st.session_state["play_status"] = result["status"]
        st.session_state["play_winner"] = result["winner"]
        st.rerun()
        return

    # Engine reply
    _handle_engine_move(variant, depth)


def _handle_engine_move(variant: str, depth: int) -> None:
    """Get and apply engine's move with a small thinking delay."""
    fen = st.session_state["play_fen"]
    # Brief "thinking" pause so play feels like a real online engine
    # (Lichess/Chess.com style) instead of an instant reply.
    import random as _r
    time.sleep(_r.uniform(0.4, 1.1))
    engine_uci = _engine_reply(fen)

    if engine_uci is None:
        st.session_state["play_status"] = "stalemate"
        st.rerun()
        return

    result = apply_move_for_ui(fen, engine_uci, variant)
    moves = list(st.session_state.get("play_moves", []))
    moves.append(engine_uci)

    exploded = _detect_explosions(fen, result["fen"], engine_uci) if variant == "atomic" else None

    st.session_state["play_fen"] = result["fen"]
    st.session_state["play_moves"] = moves
    st.session_state["play_last_move"] = engine_uci
    st.session_state["play_exploded_squares"] = exploded
    st.session_state["play_status"] = result["status"]
    st.session_state["play_winner"] = result.get("winner")
    st.rerun()


def _detect_explosions(old_fen: str, new_fen: str, move_uci: str) -> list[str] | None:
    """Compare board states to find squares where pieces were destroyed (atomic).

    Returns list of algebraic square names that had pieces removed by explosion,
    or None if no explosion occurred.

    Atomic capture signature: the destination square is EMPTY after the move
    (in standard chess, the capturing piece would be on the destination).
    """
    if len(move_uci) < 4:
        return None
    old_board = chess.Board(old_fen)
    new_board = chess.Board(new_fen)

    dest_sq = chess.parse_square(move_uci[2:4])
    # No capture happened (dest was empty before) — not an atomic explosion
    if old_board.piece_at(dest_sq) is None:
        return None
    # In standard chess, dest now holds the capturing piece. In atomic, dest is
    # empty because both pieces exploded.
    if new_board.piece_at(dest_sq) is not None:
        return None

    return [
        chess.square_name(sq)
        for sq in chess.SQUARES
        if old_board.piece_at(sq) is not None and new_board.piece_at(sq) is None
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_session_state()

    st.markdown(_CSS, unsafe_allow_html=True)

    # Handle error state
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
        if st.button("Clear error and reset"):
            st.session_state["error"] = None
            st.session_state["running"] = False
            st.session_state["view"] = "build"
            st.rerun()
        return

    # Home landing page — full width, no column split
    view = st.session_state.get("view", "home")
    if view == "home":
        render_home_page()
        _, cta_col, _ = st.columns([1, 2, 1])
        with cta_col:
            if st.button("Enter EngineLab", type="primary", use_container_width=True):
                st.session_state["view"] = "build"
                st.rerun()
        return

    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    board_col, panel_col = st.columns([5, 4])

    live_board_ph = None
    with board_col:
        if view == "live":
            live_board_ph = st.empty()
            live_board_ph.markdown(
                _svg_html(render_board(starting_fen(), size=_BOARD_PX)),
                unsafe_allow_html=True,
            )
        else:
            _render_board_area()

    with panel_col:
        nav_view = view if view != "live" else "build"
        _render_nav(nav_view)
        if view == "live":
            _render_live_panel(board_ph=live_board_ph)
        elif view == "analysis":
            _render_analysis_panel()
        elif view == "play":
            _render_play_panel()
        else:
            _render_build_panel()


if __name__ == "__main__":
    main()
