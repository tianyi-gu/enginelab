"""Page 3: Analysis — full tabbed exploration of tournament results."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
from dataclasses import asdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.constants import (
    ALL_FEATURES,
    COLOR_NEGATIVE,
    COLOR_NEUTRAL,
    COLOR_POSITIVE,
    FEATURE_DISPLAY_NAMES,
)

# ---------------------------------------------------------------------------
# Type aliases (runtime-safe)
# ---------------------------------------------------------------------------
from tournament.leaderboard import LeaderboardRow
from analysis.feature_marginals import FeatureContributionRow
from analysis.synergy import SynergyRow


# ---------------------------------------------------------------------------
# Guard — no results yet
# ---------------------------------------------------------------------------

def _check_results() -> bool:
    """Return True if leaderboard is available in session state."""
    return bool(st.session_state.get("leaderboard"))


# ---------------------------------------------------------------------------
# DataFrame builders
# ---------------------------------------------------------------------------

def _leaderboard_to_df(rows: list[LeaderboardRow]) -> pd.DataFrame:
    """Convert leaderboard rows to a display DataFrame."""
    records = []
    for rank, row in enumerate(rows, start=1):
        name = row.agent_name.removeprefix("Agent_")
        if len(name) > 40:
            name = name[:40] + "..."
        feature_labels = ", ".join(
            FEATURE_DISPLAY_NAMES.get(f, f) for f in row.features
        )
        records.append(
            {
                "Rank": rank,
                "Agent": name,
                "Features": feature_labels,
                "Score Rate": row.score_rate,
                "W": row.wins,
                "D": row.draws,
                "L": row.losses,
                "Games": row.games_played,
                "Avg Length": row.avg_game_length,
            }
        )
    return pd.DataFrame(records)


def _marginals_to_df(rows: list[FeatureContributionRow]) -> pd.DataFrame:
    """Convert marginals rows to a display DataFrame."""
    records = [
        {
            "Feature": FEATURE_DISPLAY_NAMES.get(r.feature, r.feature),
            "Avg Score With": round(r.avg_score_with, 4),
            "Avg Score Without": round(r.avg_score_without, 4),
            "Marginal": round(r.marginal, 4),
            "Top-10 Freq": f"{r.top_k_frequency:.0%}",
        }
        for r in rows
    ]
    return pd.DataFrame(records)


def _synergies_to_df(rows: list[SynergyRow], top_n: int = 20) -> pd.DataFrame:
    """Convert synergy rows to a display DataFrame (top_n rows)."""
    records = [
        {
            "Feature A": FEATURE_DISPLAY_NAMES.get(r.feature_a, r.feature_a),
            "Feature B": FEATURE_DISPLAY_NAMES.get(r.feature_b, r.feature_b),
            "Synergy": round(r.synergy, 4),
            "Direction": "Synergistic" if r.synergy >= 0 else "Redundant",
        }
        for r in rows[:top_n]
    ]
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def _apply_feature_filter(
    rows: list[LeaderboardRow],
    must_include: list[str],
) -> list[LeaderboardRow]:
    """Return rows whose feature set contains ALL of must_include."""
    if not must_include:
        return rows
    return [r for r in rows if all(f in r.features for f in must_include)]


# ---------------------------------------------------------------------------
# Chart builders — Leaderboard tab
# ---------------------------------------------------------------------------

def _build_win_rate_histogram(score_rates: list[float]) -> go.Figure:
    """Build a histogram of win rates with a 0.5 baseline dashed line."""
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=score_rates,
            nbinsx=20,
            marker_color=COLOR_POSITIVE,
            opacity=0.75,
            name="Agents",
        )
    )
    fig.add_vline(
        x=0.5,
        line_dash="dash",
        line_color=COLOR_NEUTRAL,
        annotation_text="Random baseline",
        annotation_position="top right",
    )
    fig.update_layout(
        title="Win Rate Distribution",
        xaxis_title="Score Rate",
        yaxis_title="Agent Count",
        template="plotly_dark",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def _build_score_vs_feature_count(rows: list[LeaderboardRow]) -> go.Figure:
    """Scatter of score_rate vs feature count with trend line."""
    x_vals = [len(r.features) for r in rows]
    y_vals = [r.score_rate for r in rows]
    names = [r.agent_name.removeprefix("Agent_") for r in rows]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers",
            marker=dict(
                color=y_vals,
                colorscale="RdYlGn",
                showscale=True,
                size=8,
                colorbar=dict(title="Score Rate"),
            ),
            text=names,
            hovertemplate="%{text}<br>Features: %{x}<br>Score: %{y:.4f}<extra></extra>",
            name="Agents",
        )
    )

    # Trend line via numpy polyfit
    if len(x_vals) >= 2:
        coeffs = np.polyfit(x_vals, y_vals, 1)
        x_trend = np.linspace(min(x_vals), max(x_vals), 100)
        y_trend = np.polyval(coeffs, x_trend)
        fig.add_trace(
            go.Scatter(
                x=x_trend.tolist(),
                y=y_trend.tolist(),
                mode="lines",
                line=dict(color=COLOR_NEUTRAL, dash="dash", width=2),
                name="Trend",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        title="Does adding features help?",
        xaxis_title="Feature Count",
        yaxis_title="Score Rate",
        template="plotly_dark",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart builders — Feature Intelligence tab
# ---------------------------------------------------------------------------

def _build_marginals_bar(rows: list[FeatureContributionRow]) -> go.Figure:
    """Horizontal bar chart of marginal contributions, sorted descending."""
    sorted_rows = sorted(rows, key=lambda r: r.marginal, reverse=True)

    labels = [FEATURE_DISPLAY_NAMES.get(r.feature, r.feature) for r in sorted_rows]
    values = [r.marginal for r in sorted_rows]
    hover = [
        f"Avg with: {r.avg_score_with:.4f}<br>"
        f"Avg without: {r.avg_score_without:.4f}<br>"
        f"Marginal: {r.marginal:+.4f}"
        for r in sorted_rows
    ]
    colors = [
        COLOR_POSITIVE if v > 0.01 else (COLOR_NEGATIVE if v < -0.01 else COLOR_NEUTRAL)
        for v in values
    ]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.4f}" for v in values],
            textposition="outside",
            hovertext=hover,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title="How much does each feature help win rate?",
        xaxis_title="Marginal Contribution",
        yaxis=dict(autorange="reversed"),
        template="plotly_dark",
        height=400,
        margin=dict(l=160, r=60, t=50, b=40),
    )
    return fig


def _build_top_k_frequency_bar(rows: list[LeaderboardRow]) -> go.Figure:
    """Grouped bar: fraction of top-K agents containing each feature."""
    k_values = [5, 10, 20]
    sorted_rows = sorted(rows, key=lambda r: r.score_rate, reverse=True)

    features = ALL_FEATURES
    feature_labels = [FEATURE_DISPLAY_NAMES[f] for f in features]

    fig = go.Figure()
    colors_map = {5: "#00e676", 10: "#ffb300", 20: "#42a5f5"}

    for k in k_values:
        top_k = sorted_rows[:k]
        if not top_k:
            continue
        fractions = [
            sum(1 for r in top_k if f in r.features) / len(top_k)
            for f in features
        ]
        fig.add_trace(
            go.Bar(
                name=f"Top {k}",
                x=feature_labels,
                y=fractions,
                marker_color=colors_map[k],
                opacity=0.85,
            )
        )

    fig.update_layout(
        title="Feature frequency in top agents",
        xaxis_title="Feature",
        yaxis_title="Fraction of Top-K Agents",
        yaxis=dict(tickformat=".0%"),
        barmode="group",
        template="plotly_dark",
        height=400,
        margin=dict(l=40, r=20, t=50, b=100),
        xaxis=dict(tickangle=-30),
    )
    return fig


# ---------------------------------------------------------------------------
# Chart builders — Synergy tab
# ---------------------------------------------------------------------------

def _build_synergy_heatmap(
    synergy_rows: list[SynergyRow],
    features: list[str],
) -> go.Figure:
    """Build N×N synergy heatmap from SynergyRow data."""
    n = len(features)
    matrix: list[list[float | None]] = [[None] * n for _ in range(n)]

    idx = {f: i for i, f in enumerate(features)}
    for row in synergy_rows:
        i = idx.get(row.feature_a)
        j = idx.get(row.feature_b)
        if i is not None and j is not None:
            matrix[i][j] = row.synergy
            matrix[j][i] = row.synergy

    labels = [FEATURE_DISPLAY_NAMES[f] for f in features]

    # Build annotation text (2 dp, blank on diagonal)
    annotations_text = []
    for r in range(n):
        row_text = []
        for c in range(n):
            val = matrix[r][c]
            row_text.append(f"{val:.2f}" if val is not None else "")
        annotations_text.append(row_text)

    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            colorscale="RdYlGn",
            zmid=0,
            text=annotations_text,
            texttemplate="%{text}",
            hovertemplate="Synergy(%{x}, %{y}) = %{z:.4f}<extra></extra>",
            colorbar=dict(title="Synergy"),
        )
    )
    fig.update_layout(
        title="Pairwise Feature Synergy",
        template="plotly_dark",
        height=550,
        margin=dict(l=20, r=20, t=50, b=120),
        xaxis=dict(tickangle=45),
    )
    return fig


def _build_top_bottom_synergies_bar(synergy_rows: list[SynergyRow]) -> go.Figure:
    """Horizontal bar of top-5 positive and bottom-5 negative synergy pairs."""
    sorted_all = sorted(synergy_rows, key=lambda r: r.synergy, reverse=True)
    top_5 = [r for r in sorted_all if r.synergy > 0][:5]
    bottom_5 = list(reversed([r for r in sorted_all if r.synergy < 0][-5:]))

    combined = top_5 + bottom_5

    labels = [
        f"{FEATURE_DISPLAY_NAMES.get(r.feature_a, r.feature_a)} + "
        f"{FEATURE_DISPLAY_NAMES.get(r.feature_b, r.feature_b)}"
        for r in combined
    ]
    values = [r.synergy for r in combined]
    colors = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.4f}" for v in values],
            textposition="outside",
            hovertemplate="%{y}<br>Synergy: %{x:+.4f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Most synergistic and redundant feature pairs",
        xaxis_title="Synergy Score",
        yaxis=dict(autorange="reversed"),
        template="plotly_dark",
        height=420,
        margin=dict(l=220, r=60, t=50, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Tab renderers
# ---------------------------------------------------------------------------

def _render_tab_leaderboard(
    leaderboard: list[LeaderboardRow],
) -> None:
    """Render Tab A: Leaderboard."""
    col_filter, col_topn, col_dl = st.columns([3, 1, 1])

    with col_filter:
        must_include = st.multiselect(
            "Filter: must include features",
            options=ALL_FEATURES,
            format_func=lambda f: FEATURE_DISPLAY_NAMES[f],
        )
    with col_topn:
        top_n = st.number_input(
            "Top N", min_value=5, max_value=200, value=20, step=5
        )

    filtered = _apply_feature_filter(leaderboard, must_include)
    filtered_top = filtered[:int(top_n)]

    df = _leaderboard_to_df(filtered_top)

    with col_dl:
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False),
            file_name="leaderboard.csv",
            mime="text/csv",
        )

    if df.empty:
        st.warning("No agents match the current filter.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        height=500,
        column_config={
            "Score Rate": st.column_config.NumberColumn(
                "Score Rate",
                format="%.4f",
                min_value=0.0,
                max_value=1.0,
            ),
        },
    )

    # Win rate distribution
    score_rates = [r.score_rate for r in filtered_top]
    if score_rates:
        st.plotly_chart(
            _build_win_rate_histogram(score_rates),
            use_container_width=True,
        )

    # Score vs feature count
    if filtered_top:
        st.plotly_chart(
            _build_score_vs_feature_count(filtered_top),
            use_container_width=True,
        )


def _render_tab_feature_intelligence(
    leaderboard: list[LeaderboardRow],
    marginals: list[FeatureContributionRow],
) -> None:
    """Render Tab B: Feature Intelligence."""
    if not marginals:
        st.info("No marginal data available.")
        return

    st.plotly_chart(_build_marginals_bar(marginals), use_container_width=True)
    st.plotly_chart(_build_top_k_frequency_bar(leaderboard), use_container_width=True)

    st.subheader("Marginal Contributions Detail")
    st.dataframe(_marginals_to_df(marginals), use_container_width=True)

    st.info(
        "Run the same pipeline on a different variant to compare feature "
        "rankings across rule sets. The cross-variant comparison will appear "
        "in the Cross-Variant tab."
    )


def _render_tab_synergy(
    synergy_rows: list[SynergyRow],
    features: list[str],
) -> None:
    """Render Tab C: Synergy."""
    st.subheader("Pairwise Feature Synergy")
    st.caption(
        "Synergy(A, B) = avg_with_both − avg_with_A − avg_with_B + overall_avg. "
        "Positive = features more valuable together than predicted individually."
    )

    if not synergy_rows or not features:
        st.info("No synergy data available.")
        return

    st.plotly_chart(
        _build_synergy_heatmap(synergy_rows, features),
        use_container_width=True,
    )
    st.plotly_chart(
        _build_top_bottom_synergies_bar(synergy_rows),
        use_container_width=True,
    )

    st.subheader("Top 20 Synergy Pairs")
    st.dataframe(_synergies_to_df(synergy_rows, top_n=20), use_container_width=True)


def _render_cross_variant_active(all_results: dict) -> None:
    """Render the cross-variant comparison when ≥2 variants are present."""
    variants = list(all_results.keys())

    st.subheader("Feature Rankings Across Variants")
    st.caption("Which strategies win depends on the rules.")

    # Build marginal data per variant
    variant_marginals: dict[str, dict[str, float]] = {}
    for var, data in all_results.items():
        if data.get("marginals"):
            variant_marginals[var] = {
                r.feature: r.marginal for r in data["marginals"]
            }

    if not variant_marginals:
        st.info("Marginal data not found for the loaded variants.")
        return

    # Grouped bar chart
    fig = go.Figure()
    for var, m_dict in variant_marginals.items():
        labels = [FEATURE_DISPLAY_NAMES.get(f, f) for f in ALL_FEATURES]
        vals = [m_dict.get(f, 0.0) for f in ALL_FEATURES]
        fig.add_trace(
            go.Bar(name=var.title(), x=labels, y=vals)
        )
    fig.update_layout(
        barmode="group",
        title="Feature Marginal Contributions by Variant",
        xaxis_title="Feature",
        yaxis_title="Marginal Contribution",
        template="plotly_dark",
        height=400,
        xaxis=dict(tickangle=-30),
        margin=dict(l=40, r=20, t=50, b=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Rank change table
    _render_rank_change_table(variant_marginals, variants)

    # Best agent per variant cards
    _render_best_agent_cards(all_results, variants)


def _render_rank_change_table(
    variant_marginals: dict[str, dict[str, float]],
    variants: list[str],
) -> None:
    """Render the rank-change comparison table."""
    if len(variants) < 2:
        return

    var_a, var_b = variants[0], variants[1]
    ma, mb = variant_marginals.get(var_a, {}), variant_marginals.get(var_b, {})

    # Rank by marginal within each variant
    def _rank_dict(m: dict[str, float]) -> dict[str, int]:
        sorted_feats = sorted(m, key=lambda f: m[f], reverse=True)
        return {f: i + 1 for i, f in enumerate(sorted_feats)}

    ranks_a = _rank_dict(ma)
    ranks_b = _rank_dict(mb)

    records = []
    for f in ALL_FEATURES:
        ra = ranks_a.get(f, len(ALL_FEATURES))
        rb = ranks_b.get(f, len(ALL_FEATURES))
        delta = ra - rb
        direction = f"+{delta} ↑" if delta > 0 else (f"{delta} ↓" if delta < 0 else "→")
        records.append(
            {
                "Feature": FEATURE_DISPLAY_NAMES.get(f, f),
                f"{var_a.title()} Rank": ra,
                f"{var_b.title()} Rank": rb,
                "Δ": direction,
                "|Δ|": abs(delta),
            }
        )

    df = pd.DataFrame(records).sort_values("|Δ|", ascending=False).drop(columns=["|Δ|"])
    st.subheader("Rank Change by Variant")
    st.dataframe(df, use_container_width=True)


def _render_best_agent_cards(all_results: dict, variants: list[str]) -> None:
    """Render one best-agent card per variant in columns."""
    st.subheader("Best Agent Per Variant")
    cols = st.columns(len(variants))
    for col, var in zip(cols, variants):
        data = all_results[var]
        lb = data.get("leaderboard", [])
        interp = data.get("interpretation", "")
        with col:
            st.markdown(f"**{var.title()} Chess**")
            if lb:
                best = lb[0]
                name = best.agent_name.removeprefix("Agent_")
                st.code(name)
                st.metric("Score Rate", f"{best.score_rate:.4f}")
                st.caption(f"W {best.wins} / D {best.draws} / L {best.losses}")
            if interp:
                st.caption(interp[:200] + "..." if len(interp) > 200 else interp)


def _render_tab_cross_variant() -> None:
    """Render Tab D: Cross-Variant comparison."""
    all_results = st.session_state.get("all_results")

    if not all_results or len(all_results) < 2:
        st.info(
            "Run a second variant to unlock cross-variant comparison. "
            "Re-run the tournament with a different variant selected in the sidebar."
        )
        return

    _render_cross_variant_active(all_results)


def _render_tab_report(
    report_md: str | None,
    results: list | None,
    variant: str,
) -> None:
    """Render Tab E: Report with download buttons and inline markdown."""
    st.subheader("Strategy Report")

    if report_md:
        st.download_button(
            "Download Markdown Report",
            data=report_md,
            file_name=f"{variant}_strategy_report.md",
            mime="text/markdown",
        )
    else:
        st.warning("Report not yet generated. Run a tournament first.")

    if results:
        try:
            results_json = json.dumps(
                [asdict(r) for r in results], indent=2
            )
            st.download_button(
                "Download Raw Results (JSON)",
                data=results_json,
                file_name=f"{variant}_results.json",
                mime="application/json",
            )
        except Exception:
            # Fallback: some fields may not be directly serialisable
            st.download_button(
                "Download Raw Results (JSON)",
                data=json.dumps(
                    [
                        {
                            "white_agent": r.white_agent,
                            "black_agent": r.black_agent,
                            "winner": r.winner,
                            "moves": r.moves,
                            "termination_reason": r.termination_reason,
                        }
                        for r in results
                    ],
                    indent=2,
                ),
                file_name=f"{variant}_results.json",
                mime="application/json",
            )

    st.divider()

    if report_md:
        st.markdown(report_md)
    else:
        st.caption("No report content to display.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Render Page 3: Analysis."""
    try:
        st.title("Analysis")
        st.caption("Full exploration of tournament results — leaderboard, marginals, synergy, and report.")

        if not _check_results():
            st.info(
                "No tournament results found. Run a tournament from the sidebar "
                "or load existing results to view analysis."
            )
            st.stop()

        leaderboard: list[LeaderboardRow] = st.session_state["leaderboard"] or []
        marginals: list[FeatureContributionRow] = st.session_state.get("marginals") or []
        synergy_rows: list[SynergyRow] = st.session_state.get("synergies") or []
        report_md: str | None = st.session_state.get("report_md")
        results = st.session_state.get("results")
        variant: str = st.session_state.get("variant", "unknown")

        # Derive the feature list from leaderboard data (preserves tournament's
        # selected_features ordering where possible, falls back to ALL_FEATURES).
        config_snap = st.session_state.get("config_snapshot") or {}
        features: list[str] = config_snap.get("selected_features") or list(
            {f for row in leaderboard for f in row.features}
        ) or ALL_FEATURES

        tab_a, tab_b, tab_c, tab_d, tab_e = st.tabs(
            ["Leaderboard", "Feature Intelligence", "Synergy", "Cross-Variant", "Report"]
        )

        with tab_a:
            _render_tab_leaderboard(leaderboard)

        with tab_b:
            _render_tab_feature_intelligence(leaderboard, marginals)

        with tab_c:
            _render_tab_synergy(synergy_rows, features)

        with tab_d:
            _render_tab_cross_variant()

        with tab_e:
            _render_tab_report(report_md, results, variant)

    except Exception as exc:
        st.error(f"Analysis page error: {exc}")
        raise


main()
