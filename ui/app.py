from __future__ import annotations

import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re

import chess
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.constants import ALL_FEATURES, FEATURE_DISPLAY_NAMES
from ui.board import render_board, starting_fen
from ui.chess_viewer import chess_game_viewer
from ui.play_engine import engine_reply as _pure_engine_reply, apply_san_move, game_status

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
/* ── Font ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    box-sizing: border-box;
}

/* ── Page ─────────────────────────────────────────────────── */
body, .stApp { background: #161512 !important; color: #bababa !important; }

/* Key: constrain width like a real chess site, center it */
.block-container {
    max-width: 1040px !important;
    margin: 0 auto !important;
    padding: 0.5rem 1.2rem 1rem !important;
}

/* ── Typography ──────────────────────────────────────────── */
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

/* ── Buttons ─────────────────────────────────────────────── */
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

/* ── Tabs ─────────────────────────────────────────────────── */
div[data-testid="stTabs"] { background: transparent !important; }
div[data-testid="stTabs"] button {
    font-size: 12px !important; color: #7a7775 !important;
    font-weight: 500 !important; padding: 6px 10px !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #d0cfc8 !important; border-bottom: 2px solid #629924 !important;
}

/* ── Inputs ───────────────────────────────────────────────── */
div[data-testid="stTextInput"] input,
div[data-testid="stMultiSelect"] {
    background: #1f1e1c !important;
    border-color: #3a3a38 !important;
    color: #bababa !important;
    font-size: 13px !important;
}

/* ── Radio ────────────────────────────────────────────────── */
div[data-testid="stRadio"] label { font-size: 12.5px !important; color: #bababa !important; }
div[data-testid="stRadio"] p { color: #bababa !important; font-size: 12.5px !important; }

/* ── Checkbox ─────────────────────────────────────────────── */
div[data-testid="stCheckbox"] label { font-size: 12.5px !important; color: #bababa !important; }

/* ── Dataframe ────────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border: 1px solid #3a3a38 !important; border-radius: 5px !important;
}

/* ── Alerts ───────────────────────────────────────────────── */
div[data-testid="stAlert"] { border-radius: 6px !important; font-size: 13px !important; }

/* ── Dividers ─────────────────────────────────────────────── */
hr { border-color: #2c2b29 !important; margin: 8px 0 !important; }

/* ── Move list ────────────────────────────────────────────── */
.move-list-scroll {
    background: #1f1e1c; border: 1px solid #3a3a38;
    border-radius: 5px; padding: 6px 10px;
    height: 170px; overflow-y: auto;
    font-family: 'Courier New', monospace !important;
    font-size: 12.5px; color: #bababa; line-height: 1.8;
}

/* ── Scrollbars ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #161512; }
::-webkit-scrollbar-thumb { background: #3a3a38; border-radius: 3px; }
</style>
"""

# ---------------------------------------------------------------------------
# Header HTML
# ---------------------------------------------------------------------------

HEADER_HTML = (
    '<div style="display:flex;align-items:center;gap:8px;'
    'padding:6px 0 10px;border-bottom:1px solid #2c2b29;margin-bottom:10px;">'
    '<span style="font-size:1.2rem;line-height:1;">♟</span>'
    '<span style="font-size:1rem;font-weight:700;color:#d0cfc8;letter-spacing:-0.2px;">EngineLab</span>'
    '<span style="font-size:11px;color:#7a7775;margin-left:4px;">feature-subset engine discovery</span>'
    '</div>'
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

SESSION_DEFAULTS: dict = {
    "variant": "standard",
    "selected_features": list(ALL_FEATURES),
    "depth": 2,
    "view": "build",
    "running": False,
    "progress": 0.0,
    "games_completed": 0,
    "total_games": 0,
    "start_time": None,
    "error": None,
    "results": None,
    "agents": None,
    "leaderboard": None,
    "marginals": None,
    "synergies": None,
    "interpretation": None,
    "report_md": None,
    "config_snapshot": None,
    "duration_seconds": None,
    "sample_game_moves": None,
    "sample_game_white": "White",
    "sample_game_black": "Black",
    "sample_game_result": "",
    "play_fen": chess.STARTING_FEN,
    "play_moves": [],
    "play_status": "ongoing",
    "play_flipped": False,
}

VARIANT_DESCRIPTIONS = {
    "standard": "Win by checkmating the king.",
    "atomic": "Captures cause explosions.",
    "antichess": "Lose all your pieces to win.",
}

PRESETS = {
    "Quick":    ["material", "king_safety", "capture_threats"],
    "Standard": ["material", "king_safety", "capture_threats", "mobility", "enemy_king_danger"],
    "Full":     list(ALL_FEATURES),
}

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


def _agent_short_name(name: str) -> str:
    return name.replace("Agent_", "").replace("__", " + ")


def _feature_pills(features: tuple | list) -> str:
    """Return HTML pill spans for a list of feature keys."""
    pills = []
    for f in features:
        label = FEATURE_DISPLAY_NAMES.get(f, f)
        pills.append(
            f'<span style="background:#2a2827;border:1px solid #555452;'
            f'color:#d8d5d0;border-radius:3px;padding:2px 7px;'
            f'font-size:11px;margin:2px;">{label}</span>'
        )
    return " ".join(pills)


def _est_agents_games(features: list[str]) -> tuple[int, int]:
    n = len(features)
    n_agents = min(2 ** n - 1, 100) if n >= 1 else 0
    n_games = n_agents * (n_agents - 1)
    return n_agents, n_games


# ---------------------------------------------------------------------------
# Tournament thread
# ---------------------------------------------------------------------------

def _start_tournament() -> None:
    config = {
        "variant": st.session_state["variant"],
        "selected_features": list(st.session_state["selected_features"]),
        "depth": st.session_state["depth"],
        "max_moves": 80,
        "workers": min(4, os.cpu_count() or 1),
        "seed": 42,
    }
    for k in ["results", "agents", "leaderboard", "marginals", "synergies",
              "interpretation", "report_md", "config_snapshot", "duration_seconds", "error"]:
        st.session_state[k] = None
    n = len(config["selected_features"])
    n_agents = min(2**n - 1, 100) if n >= 1 else 0
    st.session_state.update(
        running=True, view="live",
        games_completed=0, progress=0.0,
        total_games=n_agents * max(n_agents - 1, 0),
        agents=[],
        start_time=time.time(),
        _tournament_config=config,
    )
    st.rerun()


# ---------------------------------------------------------------------------
# Engine reply (mock)
# ---------------------------------------------------------------------------

def _engine_reply(fen: str) -> str | None:
    move_index = len(st.session_state.get("play_moves", []))
    return _pure_engine_reply(fen, move_index=move_index)


# ---------------------------------------------------------------------------
# Board area (left column)
# ---------------------------------------------------------------------------

_BOARD_PX = 460  # fixed board size in pixels


def _show_svg(svg: str) -> None:
    """Render a python-chess SVG at exactly _BOARD_PX, centered."""
    # Override the SVG's own width/height attrs so it respects our size
    svg_fixed = re.sub(r'\bwidth="\d+(?:\.\d+)?"', f'width="{_BOARD_PX}"', svg, count=1)
    svg_fixed = re.sub(r'\bheight="\d+(?:\.\d+)?"', f'height="{_BOARD_PX}"', svg_fixed, count=1)
    st.markdown(
        f'<div style="display:flex;justify-content:center;">{svg_fixed}</div>',
        unsafe_allow_html=True,
    )


def _render_board_area() -> None:
    view = st.session_state.get("view", "build")

    if view == "analysis":
        moves = st.session_state.get("sample_game_moves")
        if moves:
            white = _agent_short_name(st.session_state.get("sample_game_white", "White"))
            black = _agent_short_name(st.session_state.get("sample_game_black", "Black"))
            result = st.session_state.get("sample_game_result", "")
            chess_game_viewer(moves=moves, white_name=white, black_name=black,
                              result=result, board_size=_BOARD_PX, height=680)
            return

    if view == "play":
        from ui.chess_viewer import chess_play_interactive
        lb = st.session_state.get("leaderboard") or []
        engine_name = _agent_short_name(lb[0].agent_name) if lb else "Best Engine"
        chess_play_interactive(
            engine_name=engine_name,
            height=640,
        )
        return

    _show_svg(render_board(starting_fen(), size=_BOARD_PX))


# ---------------------------------------------------------------------------
# Build panel
# ---------------------------------------------------------------------------

def _render_build_panel() -> None:
    st.markdown("### Build Your Engine")

    # ── Variant selector (pill buttons) ──────────────────────────
    st.caption("VARIANT")
    v_cols = st.columns(3)
    for col, v in zip(v_cols, ["standard", "atomic", "antichess"]):
        active = st.session_state["variant"] == v
        label = ("✓ " if active else "") + v.title()
        if col.button(label, key=f"v_{v}", use_container_width=True):
            st.session_state["variant"] = v
            st.rerun()

    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

    # ── Feature multiselect + preset row ─────────────────────────
    st.caption("FEATURES")
    p_cols = st.columns(3)
    for col, (label, feats) in zip(p_cols, PRESETS.items()):
        if col.button(label, key=f"p_{label}", use_container_width=True):
            st.session_state["selected_features"] = list(feats)
            st.rerun()

    selected = st.multiselect(
        "features",
        options=ALL_FEATURES,
        default=st.session_state["selected_features"],
        format_func=lambda f: FEATURE_DISPLAY_NAMES[f],
        label_visibility="collapsed",
        key="features_multiselect",
    )
    st.session_state["selected_features"] = selected

    n_agents, n_games = _est_agents_games(selected)
    warn = " ⚠ long run" if n_games > 5000 else ""
    st.caption(f"{n_agents} agents · {n_games:,} games{warn}")

    st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)

    # ── Depth ─────────────────────────────────────────────────────
    st.caption("SEARCH DEPTH")
    depth_labels = ["Fast (1)", "Normal (2)", "Deep (3)"]
    depth_choice = st.radio(
        "depth",
        depth_labels,
        index=st.session_state["depth"] - 1,
        horizontal=True,
        label_visibility="collapsed",
        key="depth_radio",
    )
    st.session_state["depth"] = depth_labels.index(depth_choice) + 1

    st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)

    # ── Action buttons ────────────────────────────────────────────
    can_run = len(selected) >= 2
    if st.button("Build Engine", type="primary", use_container_width=True, disabled=not can_run):
        _start_tournament()
    if not can_run:
        st.caption("Select at least 2 features.")


# ---------------------------------------------------------------------------
# Live panel
# ---------------------------------------------------------------------------

_FAKE_BUILD_DURATION = 5.0


def _render_live_panel() -> None:
    config = st.session_state.get("_tournament_config") or {}
    variant = config.get("variant", st.session_state.get("variant", "standard"))
    total = st.session_state.get("total_games", 0)
    start = st.session_state.get("start_time") or time.time()
    elapsed = time.time() - start

    # When time is up, load mock results and switch to analysis — all in main thread
    if elapsed >= _FAKE_BUILD_DURATION:
        from ui.mock_data import generate_mock_session_state
        mock = generate_mock_session_state(seed=config.get("seed", 42))
        mock["duration_seconds"] = round(elapsed, 1)
        mock["config_snapshot"] = config
        st.session_state.update(mock)
        st.session_state["running"] = False
        st.session_state["view"] = "analysis"
        st.rerun()
        return

    progress = elapsed / _FAKE_BUILD_DURATION
    done = int(progress * total)
    remaining = max(_FAKE_BUILD_DURATION - elapsed, 0.0)

    st.markdown("### Building…")
    st.progress(progress)
    st.caption(
        f"Games **{done}** / **{total}**  ·  "
        f"Elapsed: **{elapsed:.0f}s**  ·  "
        f"Est. remaining: **{remaining:.0f}s**"
    )
    st.caption(f"Variant: **{variant.title()}**")

    if st.button("Cancel", use_container_width=True):
        st.session_state["running"] = False
        st.session_state["view"] = "build"
        st.rerun()

    time.sleep(0.3)
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
    variant = snap.get("variant", st.session_state.get("variant", "standard"))
    dur_str = f"{duration:.0f}s" if duration else "—"

    def _pair_label(r) -> str:
        a = FEATURE_DISPLAY_NAMES.get(r.feature_a, r.feature_a)
        b = FEATURE_DISPLAY_NAMES.get(r.feature_b, r.feature_b)
        return f"{a[:13]}+{b[:13]}"

    tab_engine, tab_features, tab_synergy, tab_lb = st.tabs(
        ["Best Engine", "Features", "Synergy", "Leaderboard"]
    )

    # ── Tab 1: Best Engine ───────────────────────────────────────
    with tab_engine:
        st.caption(
            f"{variant.title()} · {n_agents} agents · {n_games} games · {dur_str}"
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
                f'&nbsp;·&nbsp;W {best.wins} / D {best.draws} / L {best.losses}</div>'
                f'<div style="margin-top:8px;line-height:2;">{_feature_pills(best.features)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Play Against Best Engine ▶", type="primary", use_container_width=True):
                st.session_state.update(
                    view="play",
                    play_fen=chess.STARTING_FEN,
                    play_moves=[],
                    play_status="ongoing",
                )
                st.rerun()

            # Top 3 runners-up
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

        st.markdown(
            '<div style="margin-top:16px;">'
            '<a href="#" onclick="void(0)" style="color:#888;font-size:12px;">← Rebuild</a>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("← Rebuild", key="rebuild_btn", use_container_width=False):
            st.session_state["view"] = "build"
            st.rerun()

    # ── Tab 2: Feature Marginals ─────────────────────────────────
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

    # ── Tab 3: Synergy ───────────────────────────────────────────
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

    # ── Tab 4: Leaderboard ───────────────────────────────────────
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
                    "⬇ Report (.md)",
                    data=report_md,
                    file_name=f"{variant}_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            if results_data:
                import json, dataclasses
                dl_r.download_button(
                    "⬇ Results (.json)",
                    data=json.dumps([dataclasses.asdict(r) for r in results_data], indent=2),
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

    st.markdown(f"### vs {best_name}")
    st.caption("Drag pieces on the board to make your move. You play White.")

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

    snap = st.session_state.get("config_snapshot") or {}
    variant = snap.get("variant", "standard")
    depth = snap.get("depth", 2)
    st.caption(f"{variant.title()} · depth {depth}")

    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Analysis", use_container_width=True):
        st.session_state["view"] = "analysis"
        st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_session_state()

    # Apply global CSS
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

    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    board_col, panel_col = st.columns([5, 4])

    with board_col:
        _render_board_area()

    with panel_col:
        view = st.session_state.get("view", "build")
        if view == "live":
            _render_live_panel()
        elif view == "analysis":
            _render_analysis_panel()
        elif view == "play":
            _render_play_panel()
        else:
            _render_build_panel()


if __name__ == "__main__":
    main()
