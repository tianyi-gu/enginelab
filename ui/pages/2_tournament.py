from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ui.constants import FEATURE_DISPLAY_NAMES, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_NEUTRAL
from ui.board import render_board, starting_fen
from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _ss(key: str, default=None):
    """Safe session state getter with fallback default."""
    return st.session_state.get(key, default)


def _ensure_defaults() -> None:
    """Ensure all required session state keys exist."""
    defaults = {
        "running": False,
        "progress": 0.0,
        "games_completed": 0,
        "total_games": 0,
        "start_time": None,
        "error": None,
        "leaderboard": None,
        "marginals": None,
        "variant": "atomic",
        "agents": None,
        "duration_seconds": None,
        "live_game_board": None,
        "live_game_moves": [],
        "viewer_game_index": 0,
        "config_snapshot": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    if minutes > 0:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _strip_agent_prefix(name: str) -> str:
    """Strip the 'Agent_' prefix from an agent name."""
    return name.removeprefix("Agent_")


def _feature_display_list(features: tuple[str, ...]) -> str:
    """Convert feature tuple to comma-separated display names."""
    return ", ".join(FEATURE_DISPLAY_NAMES.get(f, f) for f in features)


def _estimate_remaining(start_time: float, progress: float) -> float:
    """Estimate remaining seconds based on elapsed time and progress."""
    if progress <= 0.0 or start_time is None:
        return 0.0
    elapsed = time.time() - start_time
    if progress >= 1.0:
        return 0.0
    return elapsed / progress * (1.0 - progress)


# ---------------------------------------------------------------------------
# Leaderboard dataframe builder
# ---------------------------------------------------------------------------

def _build_leaderboard_df(leaderboard: list[LeaderboardRow]) -> pd.DataFrame:
    """Convert a list of LeaderboardRow to a display DataFrame."""
    rows = []
    for rank, row in enumerate(leaderboard, start=1):
        rows.append(
            {
                "Rank": rank,
                "Agent": _strip_agent_prefix(row.agent_name),
                "Score Rate": row.score_rate,
                "W": row.wins,
                "D": row.draws,
                "L": row.losses,
                "Games": row.games_played,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Ranking evolution chart
# ---------------------------------------------------------------------------

def _build_ranking_evolution_chart(
    leaderboard: list[LeaderboardRow],
    games_completed: int,
) -> go.Figure:
    """Build a Plotly line chart showing mock score-rate evolution for top 5 agents."""
    top5 = leaderboard[:5]
    fig = go.Figure()

    x_vals = list(range(0, max(games_completed, 1) + 1, max(games_completed // 10, 1)))
    if not x_vals or x_vals[-1] != games_completed:
        x_vals.append(games_completed)

    colors = [COLOR_POSITIVE, "#4fc3f7", "#ffb74d", COLOR_NEGATIVE, COLOR_NEUTRAL]

    for i, row in enumerate(top5):
        # Generate a mock convergence curve: starts near 0.5, converges to final score_rate
        final = row.score_rate
        y_vals = [
            0.5 + (final - 0.5) * (xi / max(games_completed, 1)) ** 0.6
            for xi in x_vals
        ]
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name=_strip_agent_prefix(row.agent_name)[:30],
                line={"color": colors[i % len(colors)], "width": 2},
            )
        )

    fig.update_layout(
        title="Ranking Evolution (Top 5)",
        xaxis_title="Games Completed",
        yaxis_title="Score Rate",
        yaxis={"range": [0.0, 1.0]},
        height=280,
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e6edf3"},
        legend={"font": {"size": 10}},
    )
    return fig


# ---------------------------------------------------------------------------
# Eval bar chart
# ---------------------------------------------------------------------------

def _build_eval_bar(eval_value: float) -> go.Figure:
    """Build a horizontal eval bar from -1 to +1."""
    clamped = max(-1.0, min(1.0, eval_value))
    # White bar: positive side (green), Black bar: negative side (red)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[clamped],
            y=["Eval"],
            orientation="h",
            marker_color=COLOR_POSITIVE if clamped >= 0 else COLOR_NEGATIVE,
            width=0.4,
        )
    )
    fig.update_layout(
        xaxis={"range": [-1.0, 1.0], "zeroline": True, "zerolinecolor": "#8b949e"},
        yaxis={"visible": False},
        height=60,
        margin={"l": 10, "r": 10, "t": 5, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Top-5 features bar chart (completed state)
# ---------------------------------------------------------------------------

def _build_top_features_chart(marginals: list[FeatureContributionRow]) -> go.Figure:
    """Build a horizontal bar chart of top-5 features by absolute marginal."""
    sorted_by_abs = sorted(marginals, key=lambda r: abs(r.marginal), reverse=True)[:5]
    sorted_by_marginal = sorted(sorted_by_abs, key=lambda r: r.marginal)

    names = [FEATURE_DISPLAY_NAMES.get(r.feature, r.feature) for r in sorted_by_marginal]
    values = [r.marginal for r in sorted_by_marginal]
    bar_colors = [
        COLOR_POSITIVE if v > 0.01 else (COLOR_NEGATIVE if v < -0.01 else COLOR_NEUTRAL)
        for v in values
    ]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:+.4f}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Top 5 Features by Marginal Contribution",
        xaxis_title="Marginal Win Rate Contribution",
        height=300,
        margin={"l": 40, "r": 60, "t": 40, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e6edf3"},
    )
    return fig


# ---------------------------------------------------------------------------
# Live state: left column
# ---------------------------------------------------------------------------

def _render_live_left_column(
    leaderboard: list[LeaderboardRow] | None,
    games_completed: int,
) -> None:
    """Render the live leaderboard and ranking evolution in the left column."""
    st.subheader("Live Leaderboard")

    if leaderboard:
        df = _build_leaderboard_df(leaderboard)
        st.dataframe(
            df,
            use_container_width=True,
            height=280,
            hide_index=True,
        )
        fig = _build_ranking_evolution_chart(leaderboard, games_completed)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tournament starting...")

    _render_live_stats_bar()


def _render_live_stats_bar() -> None:
    """Render the live stats caption row below the leaderboard."""
    results = _ss("results")
    if results:
        move_counts = [r.moves for r in results]
        fastest = min(move_counts)
        longest = max(move_counts)
        total = len(results)
        draws = sum(1 for r in results if r.winner is None)
        draw_pct = draws / total * 100 if total else 0
        avg_nodes = (
            sum(
                (r.white_avg_nodes + r.black_avg_nodes) / 2
                for r in results
            )
            / total
            if total
            else 0
        )
        st.caption(
            f"Fastest game: {fastest} plies  ·  "
            f"Longest: {longest} plies  ·  "
            f"Draws: {draw_pct:.0f}%  ·  "
            f"Avg nodes/move: {avg_nodes:.0f}"
        )
    else:
        st.caption(
            "Fastest game: —  ·  Longest: —  ·  Draws: —  ·  Avg nodes/move: —"
        )


# ---------------------------------------------------------------------------
# Live state: right column
# ---------------------------------------------------------------------------

def _render_live_right_column() -> None:
    """Render the live game viewer in the right column."""
    st.subheader("Live Game")

    live_board = _ss("live_game_board")
    fen = live_board.fen() if live_board is not None else starting_fen()

    svg = render_board(fen, size=340)
    st.image(svg.encode(), use_container_width=False)

    # Eval bar (mock eval of 0.0 when live board has no eval stored)
    eval_val: float = 0.0
    fig_eval = _build_eval_bar(eval_val)
    st.plotly_chart(fig_eval, use_container_width=True)

    st.caption("Features firing: —")

    _render_game_nav_buttons()


def _render_game_nav_buttons() -> None:
    """Render Prev/Next game navigation buttons."""
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Prev game", key="live_prev_game"):
            idx = max(0, _ss("viewer_game_index", 0) - 1)
            st.session_state["viewer_game_index"] = idx
            st.rerun()
    with col_next:
        if st.button("Next game →", key="live_next_game"):
            results = _ss("results")
            max_idx = len(results) - 1 if results else 0
            idx = min(max_idx, _ss("viewer_game_index", 0) + 1)
            st.session_state["viewer_game_index"] = idx
            st.rerun()


# ---------------------------------------------------------------------------
# Live state: status bar
# ---------------------------------------------------------------------------

def _render_live_status_bar(
    variant: str,
    n_agents: int,
    total: int,
    done: int,
    progress_value: float,
    start_time: float | None,
) -> None:
    """Render the top status bar for the live tournament state."""
    elapsed = time.time() - start_time if start_time else 0.0
    remaining = _estimate_remaining(start_time, progress_value) if start_time else 0.0

    st.write(f"Running: {variant.title()}  ·  {n_agents} agents  ·  {total} games")
    st.progress(progress_value)
    st.caption(
        f"Game {done} / {total}  ·  "
        f"{elapsed:.0f}s elapsed  ·  "
        f"Est. remaining: {remaining:.0f}s"
    )


# ---------------------------------------------------------------------------
# Live state: main renderer
# ---------------------------------------------------------------------------

def _render_live_state() -> None:
    """Render the full live-tournament state of Page 2."""
    variant: str = _ss("variant", "atomic")
    agents = _ss("agents")
    n_agents: int = len(agents) if agents else 0
    total: int = _ss("total_games", 0)
    done: int = _ss("games_completed", 0)
    progress_value: float = float(_ss("progress", 0.0))
    start_time: float | None = _ss("start_time")
    leaderboard: list[LeaderboardRow] | None = _ss("leaderboard")

    _render_live_status_bar(variant, n_agents, total, done, progress_value, start_time)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        _render_live_left_column(leaderboard, done)

    with col_right:
        _render_live_right_column()

    # Auto-refresh every 2 seconds while running
    placeholder = st.empty()
    with placeholder:
        time.sleep(2)
    st.rerun()


# ---------------------------------------------------------------------------
# Completed state: summary metrics
# ---------------------------------------------------------------------------

def _render_summary_metrics(
    variant: str,
    n_agents: int,
    n_games: int,
    duration: float | None,
) -> None:
    """Render the four top-level metric cards for the completed state."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Variant", variant.title())
    with col2:
        st.metric("Agents", str(n_agents))
    with col3:
        st.metric("Games", str(n_games))
    with col4:
        dur_str = _fmt_duration(duration) if duration else "—"
        st.metric("Duration", dur_str)


# ---------------------------------------------------------------------------
# Completed state: best agent card
# ---------------------------------------------------------------------------

def _render_best_agent_card(best: LeaderboardRow) -> None:
    """Render the best-agent summary card."""
    feat_str = _feature_display_list(best.features)
    st.success(
        f"**Best Agent:** {_strip_agent_prefix(best.agent_name)}\n\n"
        f"**Score Rate:** {best.score_rate:.4f}  ·  "
        f"W: {best.wins}  ·  D: {best.draws}  ·  L: {best.losses}\n\n"
        f"**Features:** {feat_str}"
    )


# ---------------------------------------------------------------------------
# Completed state: main renderer
# ---------------------------------------------------------------------------

def _render_completed_state(leaderboard: list[LeaderboardRow]) -> None:
    """Render the completed-tournament state of Page 2."""
    st.success("Tournament complete!")

    # Gather config from snapshot or session state
    config = _ss("config_snapshot") or {}
    variant: str = config.get("variant", _ss("variant", "atomic"))
    agents = _ss("agents")
    n_agents: int = len(agents) if agents else len(leaderboard)
    # Total unique games: each LeaderboardRow carries games_played (counts
    # both sides), so sum / 2 gives unique game count.
    total_games_played = sum(r.games_played for r in leaderboard) // 2
    duration: float | None = _ss("duration_seconds")

    _render_summary_metrics(variant, n_agents, total_games_played, duration)

    st.divider()

    best = leaderboard[0]
    _render_best_agent_card(best)

    st.divider()

    marginals: list[FeatureContributionRow] | None = _ss("marginals")
    if marginals:
        fig = _build_top_features_chart(marginals)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Feature marginal data not available.")

    st.divider()

    if st.button("Explore Full Results →", type="primary"):
        st.switch_page("pages/3_analysis.py")


# ---------------------------------------------------------------------------
# No-results state
# ---------------------------------------------------------------------------

def _render_no_results_state() -> None:
    """Render the placeholder shown when no tournament has been run yet."""
    st.info(
        "No tournament results yet. "
        "Configure and run a tournament from the sidebar, or load existing results."
    )


# ---------------------------------------------------------------------------
# Page entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the Tournament page."""
    st.set_page_config(
        page_title="Tournament — EngineLab",
        page_icon="♟",
        layout="wide",
    )

    _ensure_defaults()

    st.title("Tournament")

    error: str | None = _ss("error")
    if error:
        st.error(f"Error: {error}")

    running: bool = bool(_ss("running", False))
    leaderboard: list[LeaderboardRow] | None = _ss("leaderboard")

    if running:
        _render_live_state()
    elif leaderboard:
        _render_completed_state(leaderboard)
    else:
        _render_no_results_state()


try:
    main()
except Exception as e:
    st.error(str(e))
