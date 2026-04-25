from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ui.constants import (
    ALL_FEATURES,
    FEATURE_DISPLAY_NAMES,
    COLOR_POSITIVE,
    COLOR_NEGATIVE,
)
from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from simulation.game import GameResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_marginal(
    feature: str,
    marginals: list[FeatureContributionRow],
) -> float:
    """Return the marginal contribution for a given feature, or 0.0."""
    for row in marginals:
        if row.feature == feature:
            return row.marginal
    return 0.0


def _predict_score(
    selected_features: list[str],
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
) -> tuple[float, bool]:
    """Return (predicted_score, is_exact).

    If the exact feature subset exists in leaderboard -> return (actual score_rate, True).
    Else estimate: 0.5 + sum of marginals for selected features.
    """
    selected_set = frozenset(selected_features)
    for row in leaderboard:
        if frozenset(row.features) == selected_set:
            return row.score_rate, True

    estimated = 0.5 + sum(_get_marginal(f, marginals) for f in selected_features)
    return estimated, False


def _find_leaderboard_row(
    selected_features: list[str],
    leaderboard: list[LeaderboardRow],
) -> LeaderboardRow | None:
    """Find an exact match in the leaderboard, or None."""
    selected_set = frozenset(selected_features)
    for row in leaderboard:
        if frozenset(row.features) == selected_set:
            return row
    return None


def _rank_of_score(score: float, leaderboard: list[LeaderboardRow]) -> int:
    """Return the 1-based rank position where `score` would fall."""
    rank = 1
    for row in leaderboard:
        if row.score_rate > score:
            rank += 1
    return rank


# ---------------------------------------------------------------------------
# Section 1 — Build Your Engine
# ---------------------------------------------------------------------------


def _render_build_section(
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
) -> list[str]:
    """Render feature checkboxes + predicted score card. Returns selected features."""
    st.subheader("Build Your Engine")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("**Select features:**")
        selected: list[str] = []
        for feat in ALL_FEATURES:
            if st.checkbox(FEATURE_DISPLAY_NAMES[feat], key=f"explorer_{feat}"):
                selected.append(feat)

    with right:
        _render_score_card(selected, leaderboard, marginals)

    return selected


def _render_score_card(
    selected: list[str],
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
) -> None:
    """Render the predicted / actual win rate card."""
    n = len(selected)
    total_agents = len(leaderboard)
    st.markdown(f"**Selected: {n} feature{'s' if n != 1 else ''}**")

    if n == 0:
        st.caption("Check features on the left to see a prediction.")
        return

    score, is_exact = _predict_score(selected, leaderboard, marginals)
    exact_row = _find_leaderboard_row(selected, leaderboard) if is_exact else None

    if is_exact and exact_row is not None:
        label = "Actual win rate"
        delta_label = f"rank #{_rank_of_score(score, leaderboard)} of {total_agents}"
        st.metric(
            label=label,
            value=f"{score:.4f}",
            delta=delta_label,
        )
        st.caption(
            f"W {exact_row.wins} / D {exact_row.draws} / L {exact_row.losses}"
            f"  over {exact_row.games_played} games"
        )
    else:
        label = "Predicted win rate"
        rank = _rank_of_score(score, leaderboard)
        delta_label = f"approx rank #{rank} of {total_agents}"
        st.metric(
            label=f"{label} (estimated)",
            value=f"{score:.4f}",
            delta=delta_label,
        )
        st.caption("Estimate = 0.5 + sum of individual feature marginals.")


# ---------------------------------------------------------------------------
# Section 2 — Waterfall Chart
# ---------------------------------------------------------------------------


def _render_waterfall(
    selected: list[str],
    marginals: list[FeatureContributionRow],
) -> None:
    """Render a Plotly Waterfall chart of feature contributions."""
    st.subheader("Feature Contribution Breakdown")

    if not selected:
        st.caption("Select features above to see the breakdown.")
        return

    baseline = 0.5
    feature_marginals = [_get_marginal(f, marginals) for f in selected]

    measure = ["absolute"] + ["relative"] * len(selected) + ["total"]
    x_labels = (
        ["Baseline"]
        + [FEATURE_DISPLAY_NAMES[f] for f in selected]
        + ["Predicted"]
    )
    y_values: list[float | None] = [baseline] + feature_marginals + [None]

    # Build per-bar colors
    bar_colors = (
        ["#4c72b0"]
        + [COLOR_POSITIVE if m >= 0 else COLOR_NEGATIVE for m in feature_marginals]
        + ["#4c72b0"]
    )

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measure,
            x=x_labels,
            y=y_values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": COLOR_POSITIVE}},
            decreasing={"marker": {"color": COLOR_NEGATIVE}},
            totals={"marker": {"color": "#4c72b0"}},
            textposition="outside",
            text=[
                f"{v:+.3f}" if v is not None else ""
                for v in y_values
            ],
        )
    )

    fig.update_layout(
        title="Feature Contribution to Predicted Win Rate",
        xaxis_title="",
        yaxis_title="Win Rate",
        yaxis=dict(range=[0.0, 1.0]),
        showlegend=False,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#e6edf3"),
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Section 3 — What If Analysis
# ---------------------------------------------------------------------------


def _build_what_if_tables(
    selected: list[str],
    marginals: list[FeatureContributionRow],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build add/remove DataFrames for the What If section."""
    selected_set = set(selected)

    add_rows: list[dict] = []
    for feat in ALL_FEATURES:
        if feat not in selected_set:
            delta = _get_marginal(feat, marginals)
            add_rows.append({
                "Feature": FEATURE_DISPLAY_NAMES[feat],
                "Delta": round(delta, 4),
            })

    remove_rows: list[dict] = []
    for feat in selected:
        delta = -_get_marginal(feat, marginals)
        remove_rows.append({
            "Feature": FEATURE_DISPLAY_NAMES[feat],
            "Delta": round(delta, 4),
        })

    df_add = pd.DataFrame(add_rows).sort_values("Delta", ascending=False).reset_index(drop=True)
    df_remove = pd.DataFrame(remove_rows).sort_values("Delta", ascending=True).reset_index(drop=True)

    return df_add, df_remove


def _color_delta(val: float) -> str:
    """Return a CSS color string based on sign of val."""
    if val > 0:
        return f"color: {COLOR_POSITIVE}"
    if val < 0:
        return f"color: {COLOR_NEGATIVE}"
    return "color: #8b949e"


def _render_what_if(
    selected: list[str],
    marginals: list[FeatureContributionRow],
) -> None:
    """Render the What If? add/remove analysis."""
    st.subheader("What If? Add or Remove One Feature")

    if not selected:
        st.caption("Select features above to see the what-if analysis.")
        return

    df_add, df_remove = _build_what_if_tables(selected, marginals)

    left, right = st.columns(2)

    with left:
        st.markdown("**Features to add** (sorted by gain)")
        if df_add.empty:
            st.caption("All features are already selected.")
        else:
            styled_add = df_add.style.map(_color_delta, subset=["Delta"])
            st.dataframe(styled_add, use_container_width=True, hide_index=True)

    with right:
        st.markdown("**Features to remove** (most damaging at top)")
        if df_remove.empty:
            st.caption("No features selected.")
        else:
            styled_remove = df_remove.style.map(_color_delta, subset=["Delta"])
            st.dataframe(styled_remove, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Section 4 — Compare Two Agents
# ---------------------------------------------------------------------------


def _get_head_to_head(
    name_a: str,
    name_b: str,
    results: list[GameResult] | None,
) -> tuple[int, int, int]:
    """Return (a_wins, draws, b_wins) from head-to-head results."""
    if not results:
        return 0, 0, 0

    a_wins = draws = b_wins = 0
    for r in results:
        involves_both = (
            (r.white_agent == name_a and r.black_agent == name_b)
            or (r.white_agent == name_b and r.black_agent == name_a)
        )
        if not involves_both:
            continue

        if r.winner is None:
            draws += 1
        elif (r.winner == "w" and r.white_agent == name_a) or (
            r.winner == "b" and r.black_agent == name_a
        ):
            a_wins += 1
        else:
            b_wins += 1

    return a_wins, draws, b_wins


def _render_agent_card(
    row: LeaderboardRow,
    rank: int,
    label: str,
) -> None:
    """Render a single agent stats card."""
    short_name = row.agent_name.replace("Agent_", "").replace("__", " + ")
    st.markdown(f"**{label}: {short_name}**")
    st.metric("Score Rate", f"{row.score_rate:.4f}", delta=f"rank #{rank}")
    st.caption(
        f"W {row.wins} / D {row.draws} / L {row.losses}"
        f"  ({row.games_played} games)"
    )


def _render_feature_diff(
    row_a: LeaderboardRow,
    row_b: LeaderboardRow,
    label_a: str,
    label_b: str,
) -> None:
    """Render the feature overlap and diff between two agents."""
    set_a = set(row_a.features)
    set_b = set(row_b.features)

    only_a = sorted(set_a - set_b)
    only_b = sorted(set_b - set_a)
    shared = sorted(set_a & set_b)

    def _display(feats: list[str]) -> str:
        if not feats:
            return "—"
        return ", ".join(FEATURE_DISPLAY_NAMES.get(f, f) for f in feats)

    st.caption(f"Only in {label_a}: {_display(only_a)}")
    st.caption(f"Only in {label_b}: {_display(only_b)}")
    st.caption(f"Shared: {_display(shared)}")


def _select_compare_agents(
    leaderboard: list[LeaderboardRow],
) -> tuple[str, str, dict[str, str], list[str]]:
    """Render agent selectors; return (name_a, name_b, name_map, display_names)."""
    display_names = [
        row.agent_name.replace("Agent_", "").replace("__", " + ")
        for row in leaderboard
    ]
    name_map = {
        disp: row.agent_name
        for disp, row in zip(display_names, leaderboard)
    }

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        choice_a = st.selectbox(
            "Agent 1",
            options=display_names,
            index=0,
            key="compare_agent_a",
        )
    with col_sel2:
        default_b = 1 if len(display_names) > 1 else 0
        choice_b = st.selectbox(
            "Agent 2",
            options=display_names,
            index=default_b,
            key="compare_agent_b",
        )

    return name_map[choice_a], name_map[choice_b], name_map, display_names


def _render_h2h_and_diff(
    row_a: LeaderboardRow,
    row_b: LeaderboardRow,
    choice_a: str,
    choice_b: str,
    results: list[GameResult] | None,
) -> None:
    """Render head-to-head record and feature diff for two agents."""
    st.markdown("---")

    a_wins, draws, b_wins = _get_head_to_head(row_a.agent_name, row_b.agent_name, results)
    total_h2h = a_wins + draws + b_wins
    st.markdown("**Head-to-Head Record**")
    if total_h2h == 0:
        st.caption("These agents did not play each other in the tournament.")
    else:
        st.caption(
            f"{choice_a}: {a_wins}W  |  Draws: {draws}  |  {choice_b}: {b_wins}W"
            f"  ({total_h2h} games)"
        )

    st.markdown("---")
    st.markdown("**Feature Comparison**")
    _render_feature_diff(row_a, row_b, "Agent 1", "Agent 2")


def _render_compare_section(
    leaderboard: list[LeaderboardRow],
    results: list[GameResult] | None,
) -> None:
    """Render the Compare Two Agents section."""
    st.subheader("Compare Two Agents")

    if len(leaderboard) < 2:
        st.caption("Need at least 2 agents in the leaderboard.")
        return

    name_a, name_b, name_map, display_names = _select_compare_agents(leaderboard)

    row_a = next((r for r in leaderboard if r.agent_name == name_a), None)
    row_b = next((r for r in leaderboard if r.agent_name == name_b), None)

    if row_a is None or row_b is None:
        st.warning("Could not find agent data.")
        return

    rank_a = next(
        (i + 1 for i, r in enumerate(leaderboard) if r.agent_name == name_a), 0
    )
    rank_b = next(
        (i + 1 for i, r in enumerate(leaderboard) if r.agent_name == name_b), 0
    )

    col_a, col_b = st.columns(2)
    with col_a:
        _render_agent_card(row_a, rank_a, "Agent 1")
    with col_b:
        _render_agent_card(row_b, rank_b, "Agent 2")

    choice_a = next(d for d, n in name_map.items() if n == name_a)
    choice_b = next(d for d, n in name_map.items() if n == name_b)
    _render_h2h_and_diff(row_a, row_b, choice_a, choice_b, results)


# ---------------------------------------------------------------------------
# Main page entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Render Page 4: Engine Explorer."""
    st.title("Engine Explorer")
    st.caption(
        "Build hypothetical engines and predict their performance based on tournament data."
    )

    leaderboard: list[LeaderboardRow] | None = st.session_state.get("leaderboard")
    marginals: list[FeatureContributionRow] | None = st.session_state.get("marginals")
    results: list[GameResult] | None = st.session_state.get("results")

    if not leaderboard:
        st.info(
            "No tournament results available. "
            "Run a tournament on the Lab page first, or load existing results."
        )
        st.stop()

    if not marginals:
        marginals = []

    selected = _render_build_section(leaderboard, marginals)

    st.divider()
    _render_waterfall(selected, marginals)

    st.divider()
    _render_what_if(selected, marginals)

    st.divider()
    _render_compare_section(leaderboard, results)


try:
    main()
except Exception as e:
    st.error(f"Page error: {e}")
