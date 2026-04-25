from __future__ import annotations

import os
import sys
import threading
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
/* ── Inter font ───────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body, .stApp, p, label, div, span, button, input,
.stMarkdown, [class*="st-"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* ── Global background ───────────────────────────────────── */
body, .stApp { background: #161512 !important; }

.block-container {
    padding-top: 0.4rem !important;
    max-width: 100% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* ── Typography ──────────────────────────────────────────── */
h3 {
    color: #d0cfc8 !important;
    border-left: 3px solid #629924;
    padding-left: 9px !important;
    margin-bottom: 10px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
}
p, label, .stMarkdown { color: #bababa !important; }
.stCaption, small { color: #888 !important; font-size: 12px !important; }

/* ── Primary button (Lichess green) ─────────────────────── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: #629924 !important;
    color: #fff !important;
    font-weight: 600 !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #4e7a1b !important;
}

/* ── Secondary buttons ───────────────────────────────────── */
div[data-testid="stButton"] > button {
    background: #272522 !important;
    border: 1px solid #3a3a38 !important;
    color: #bababa !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] > button:hover {
    background: #3a3a38 !important;
    border-color: #629924 !important;
}

/* ── Tabs ────────────────────────────────────────────────── */
div[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-size: 12.5px !important;
    color: #888 !important;
    font-weight: 500 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #d0cfc8 !important;
    border-bottom-color: #629924 !important;
}

/* ── Dataframes ──────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border: 1px solid #3a3a38;
    border-radius: 6px;
    overflow: hidden;
}

/* ── Metric cards ────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: #272522;
    border: 1px solid #3a3a38;
    border-radius: 8px;
    padding: 12px 16px !important;
}

/* ── Alerts ──────────────────────────────────────────────── */
div[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Dividers & misc ─────────────────────────────────────── */
hr { border-color: #3a3a38 !important; }

/* ── Move list (play panel) ──────────────────────────────── */
.move-list-scroll {
    background: #1f1e1c;
    border: 1px solid #3a3a38;
    border-radius: 6px;
    padding: 8px 12px;
    height: 200px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #bababa;
    line-height: 1.9;
}

/* ── Scrollable container override ──────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] > div > div[style*="overflow"] {
    scrollbar-width: thin;
    scrollbar-color: #3a3a38 #161512;
}
</style>
"""

# ---------------------------------------------------------------------------
# Header HTML
# ---------------------------------------------------------------------------

HEADER_HTML = """
<div style="background:#272522;border-left:4px solid #629924;
            padding:10px 20px;margin-bottom:12px;display:flex;
            align-items:center;gap:10px;">
    <span style="font-size:1.5rem;">♟</span>
    <span style="font-size:1.2rem;font-weight:700;color:#bababa;
                 letter-spacing:-0.3px;">EngineLab</span>
    <span style="font-size:0.8rem;color:#888;margin-left:6px;">
        Feature-subset strategy discovery for chess variants
    </span>
</div>
"""

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
            f'<span style="background:#1f1e1c;border:1px solid #629924;'
            f'color:#bababa;border-radius:4px;padding:2px 7px;'
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

def _run_tournament(config: dict) -> None:
    try:
        import pathlib
        from agents.generate_agents import generate_feature_subset_agents
        from analysis.feature_marginals import compute_feature_marginals
        from analysis.interpretation import generate_interpretation
        from analysis.synergy import compute_pairwise_synergies
        from reports.markdown_report import generate_markdown_report
        from tournament.leaderboard import compute_leaderboard
        from tournament.round_robin import run_round_robin

        st.session_state["start_time"] = time.time()

        agents = generate_feature_subset_agents(
            config["selected_features"], max_agents=100, seed=config["seed"]
        )
        st.session_state["agents"] = agents
        total = len(agents) * (len(agents) - 1)
        st.session_state["total_games"] = total

        def _on_game(done: int, total: int) -> None:
            st.session_state["games_completed"] = done
            st.session_state["progress"] = done / total if total else 0.0

        results = run_round_robin(
            agents=agents,
            variant=config["variant"],
            depth=config["depth"],
            max_moves=config["max_moves"],
            seed=config["seed"],
            workers=config["workers"],
            on_game_complete=_on_game,
        )
        st.session_state["results"] = results

        leaderboard = compute_leaderboard(results, agents)
        marginals = compute_feature_marginals(leaderboard, config["selected_features"])
        synergies = compute_pairwise_synergies(leaderboard, config["selected_features"])
        interpretation = generate_interpretation(
            leaderboard[0] if leaderboard else None, marginals, synergies, config["variant"]
        )

        out = pathlib.Path("outputs/reports")
        out.mkdir(parents=True, exist_ok=True)
        report_path = str(out / f"{config['variant']}_strategy_report.md")
        generate_markdown_report(
            variant=config["variant"],
            feature_names=config["selected_features"],
            leaderboard=leaderboard,
            marginals=marginals,
            synergies=synergies,
            interpretation=interpretation,
            output_path=report_path,
            config=config,
        )
        report_md = pathlib.Path(report_path).read_text()

        st.session_state.update(
            leaderboard=leaderboard,
            marginals=marginals,
            synergies=synergies,
            interpretation=interpretation,
            report_md=report_md,
            config_snapshot=config,
            duration_seconds=time.time() - st.session_state["start_time"],
            view="analysis",
        )
    except Exception as exc:
        import traceback
        st.session_state["error"] = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
    finally:
        st.session_state["running"] = False


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
    st.session_state.update(running=True, games_completed=0, progress=0.0, view="live")
    threading.Thread(target=_run_tournament, args=(config,), daemon=True).start()
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

def _render_board_area() -> None:
    view = st.session_state.get("view", "build")

    if view == "analysis":
        moves = st.session_state.get("sample_game_moves")
        if moves:
            white = _agent_short_name(st.session_state.get("sample_game_white", "White"))
            black = _agent_short_name(st.session_state.get("sample_game_black", "Black"))
            result = st.session_state.get("sample_game_result", "")
            chess_game_viewer(moves=moves, white_name=white, black_name=black,
                              result=result, board_size=380, height=560)
            return

    if view == "play":
        fen = st.session_state.get("play_fen", chess.STARTING_FEN)
        flipped = st.session_state.get("play_flipped", False)
        last_move = (st.session_state.get("play_moves") or [None])[-1]
        svg = render_board(fen, last_move_uci=last_move, size=480, flipped=flipped)
        st.image(svg, use_container_width=True)
        return

    # Build / Live: static starting position
    svg = render_board(starting_fen(), size=480)
    st.image(svg, use_container_width=True)


# ---------------------------------------------------------------------------
# Build panel
# ---------------------------------------------------------------------------

def _render_build_panel() -> None:
    st.markdown("### Build Engine")

    # Variant selector
    variants = ["standard", "atomic", "antichess"]
    v_cols = st.columns(3)
    for col, v in zip(v_cols, variants):
        active = st.session_state["variant"] == v
        border_color = "#629924" if active else "#3a3a38"
        col.markdown(
            f'<div style="border:2px solid {border_color};border-radius:8px;'
            f'padding:8px 12px;background:#272522;margin-bottom:4px;">'
            f'<div style="font-weight:600;color:#bababa;">{v.title()}</div>'
            f'<div style="font-size:11px;color:#888;">{VARIANT_DESCRIPTIONS[v]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if col.button(
            "✓ Selected" if active else "Select",
            key=f"variant_btn_{v}",
            use_container_width=True,
        ):
            st.session_state["variant"] = v
            st.rerun()

    st.divider()

    # Preset buttons
    st.markdown("**Select Features**")
    p_cols = st.columns(3)
    for col, (label, feats) in zip(p_cols, PRESETS.items()):
        if col.button(label, key=f"preset_{label}", use_container_width=True):
            st.session_state["selected_features"] = list(feats)
            st.rerun()

    # Feature checkboxes — 2-col grid
    selected: list[str] = []
    cb_cols = st.columns(2)
    for i, feat in enumerate(ALL_FEATURES):
        checked = feat in st.session_state["selected_features"]
        if cb_cols[i % 2].checkbox(
            FEATURE_DISPLAY_NAMES[feat],
            value=checked,
            key=f"feat_{feat}",
        ):
            selected.append(feat)
    st.session_state["selected_features"] = selected

    n_agents, n_games = _est_agents_games(selected)
    st.caption(f"Est. **{n_agents}** agents · **{n_games:,}** games")
    if n_games > 5000:
        st.warning("Over 5,000 games — this may take a while.")

    st.divider()

    # Depth radio
    depth_labels = ["Fast (1)", "Normal (2)", "Deep (3)"]
    depth_choice = st.radio(
        "Search Depth",
        depth_labels,
        index=st.session_state["depth"] - 1,
        horizontal=True,
        key="depth_radio",
    )
    st.session_state["depth"] = depth_labels.index(depth_choice) + 1

    st.divider()

    can_run = len(selected) >= 2
    if not can_run:
        st.caption("Select at least 2 features to build.")

    build_col, demo_col = st.columns([3, 2])
    if build_col.button(
        "Build Engine",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    ):
        _start_tournament()

    if demo_col.button("Load Demo", use_container_width=True):
        from ui.mock_data import generate_mock_session_state
        state = generate_mock_session_state()
        state["view"] = "analysis"
        st.session_state.update(state)
        st.rerun()


# ---------------------------------------------------------------------------
# Live panel
# ---------------------------------------------------------------------------

def _render_live_panel() -> None:
    snap = st.session_state.get("config_snapshot") or {}
    variant = snap.get("variant", st.session_state.get("variant", "standard"))
    n_agents = len(st.session_state.get("agents") or [])
    total = st.session_state.get("total_games", 0)
    done = st.session_state.get("games_completed", 0)
    progress = st.session_state.get("progress", 0.0)
    start = st.session_state.get("start_time") or time.time()
    elapsed = time.time() - start
    remaining = (elapsed / progress - elapsed) if progress > 0.01 else 0.0

    with st.spinner("Building…"):
        st.markdown("### Building…")
        st.progress(progress)
        st.caption(
            f"Games **{done}** / **{total}**  ·  "
            f"Elapsed: **{elapsed:.0f}s**  ·  "
            f"Est. remaining: **{remaining:.0f}s**"
        )
        st.caption(f"Variant: **{variant.title()}** · **{n_agents}** agents")

        st.divider()

        lb = st.session_state.get("leaderboard")
        if lb:
            st.markdown("**Top 5 so far**")
            top5 = [
                {
                    "Agent": _agent_short_name(r.agent_name)[:40],
                    "Score Rate": round(r.score_rate, 4),
                    "W": r.wins,
                    "D": r.draws,
                    "L": r.losses,
                }
                for r in lb[:5]
            ]
            st.dataframe(
                pd.DataFrame(top5),
                use_container_width=True,
                hide_index=True,
                column_config={"Score Rate": st.column_config.NumberColumn(format="%.4f")},
            )
        else:
            st.info("Waiting for first results…")

        if st.button("Cancel", use_container_width=True):
            st.session_state["running"] = False
            st.session_state["view"] = "build"
            st.rerun()

    time.sleep(2)
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
                height=310,
                margin=dict(l=0, r=10, t=10, b=0),
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
                height=200, margin=dict(l=0, r=10, t=4, b=0),
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
                height=200, margin=dict(l=0, r=10, t=4, b=0),
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
                height=340,
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

    st.markdown(f"### You vs {best_name}")

    fen = st.session_state.get("play_fen", chess.STARTING_FEN)
    play_moves: list[str] = st.session_state.get("play_moves", [])
    play_status: str = st.session_state.get("play_status", "ongoing")

    # Build SAN move list from UCI history
    board_replay = chess.Board()
    san_moves: list[str] = []
    for uci in play_moves:
        try:
            move = chess.Move.from_uci(uci)
            san_moves.append(board_replay.san(move))
            board_replay.push(move)
        except Exception:
            break

    # Render move list as paired rows
    pairs: list[str] = []
    for i in range(0, len(san_moves), 2):
        white_san = san_moves[i]
        black_san = san_moves[i + 1] if i + 1 < len(san_moves) else ""
        pairs.append(f"{i // 2 + 1}. {white_san}  {black_san}")
    move_html = "<br>".join(pairs) if pairs else "<span style='color:#888'>No moves yet</span>"
    st.markdown(
        f'<div class="move-list-scroll">{move_html}</div>',
        unsafe_allow_html=True,
    )

    # Status
    board_now = chess.Board(fen)
    if play_status == "checkmate":
        status_text = "Checkmate!"
    elif play_status in ("stalemate", "draw"):
        status_text = "Game drawn."
    elif board_now.turn == chess.WHITE:
        status_text = "Your turn (White)"
        if board_now.is_check():
            status_text += " — Check!"
    else:
        status_text = "Engine thinking…"

    st.markdown(
        f'<div style="color:#629924;font-weight:600;margin:8px 0;">{status_text}</div>',
        unsafe_allow_html=True,
    )

    # Move input
    if play_status == "ongoing" and board_now.turn == chess.WHITE:
        col_in, col_btn = st.columns([3, 1])
        move_input = col_in.text_input(
            "Your move",
            placeholder="e4, Nf3, O-O …",
            key="play_move_input",
            label_visibility="collapsed",
        )
        if col_btn.button("Move", type="primary", use_container_width=True):
            if move_input.strip():
                try:
                    new_fen, uci = apply_san_move(fen, move_input.strip())
                    play_moves = play_moves + [uci]
                    status = game_status(new_fen)
                    if status == "ongoing":
                        reply_uci = _engine_reply(new_fen)
                        if reply_uci:
                            board_reply = chess.Board(new_fen)
                            board_reply.push(chess.Move.from_uci(reply_uci))
                            play_moves = play_moves + [reply_uci]
                            new_fen = board_reply.fen()
                            status = game_status(new_fen)
                    st.session_state.update(
                        play_fen=new_fen,
                        play_moves=play_moves,
                        play_status=status,
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.divider()

    # Controls row
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    if ctrl1.button("New Game", use_container_width=True):
        st.session_state.update(
            play_fen=chess.STARTING_FEN,
            play_moves=[],
            play_status="ongoing",
        )
        st.rerun()

    flip_label = "Flip Board ✓" if st.session_state.get("play_flipped") else "Flip Board"
    if ctrl2.button(flip_label, use_container_width=True):
        st.session_state["play_flipped"] = not st.session_state.get("play_flipped", False)
        st.rerun()

    if ctrl3.button("← Back to Analysis", use_container_width=True):
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

    # Auto-transition: if running flag dropped but view is still "live", push to analysis
    if not st.session_state.get("running") and st.session_state.get("view") == "live":
        if st.session_state.get("leaderboard") is not None:
            st.session_state["view"] = "analysis"

    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    board_col, panel_col = st.columns([11, 8])

    with board_col:
        _render_board_area()

    with panel_col:
        with st.container(height=700, border=False):
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
