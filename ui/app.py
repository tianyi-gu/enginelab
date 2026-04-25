from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.constants import (
    ALL_FEATURES,
    COLOR_NEGATIVE,
    COLOR_NEUTRAL,
    COLOR_POSITIVE,
    FEATURE_DISPLAY_NAMES,
    SESSION_DEFAULTS,
    VARIANT_DESCRIPTIONS,
)

st.set_page_config(
    page_title="EngineLab",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS: list[dict] = [
    {
        "label": "⚡ Debug",
        "desc": "3 features · 7 agents · 42 games",
        "features": ["material", "mobility", "king_safety"],
    },
    {
        "label": "Demo",
        "desc": "5 features · 31 agents · 930 games",
        "features": ["material", "mobility", "king_safety", "enemy_king_danger", "capture_threats"],
    },
    {
        "label": "Full",
        "desc": "10 features · ~87 agents · ~7,500 games",
        "features": list(ALL_FEATURES),
    },
]

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = list(default) if isinstance(default, list) else default


# ---------------------------------------------------------------------------
# Tournament thread
# ---------------------------------------------------------------------------

def _run_tournament(config: dict) -> None:
    try:
        from agents.generate_agents import generate_feature_subset_agents
        from analysis.feature_marginals import compute_feature_marginals
        from analysis.interpretation import generate_interpretation
        from analysis.synergy import compute_pairwise_synergies
        from reports.markdown_report import generate_markdown_report
        from tournament.leaderboard import compute_leaderboard
        from tournament.round_robin import run_round_robin
        import pathlib

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
        )
    except Exception as exc:
        import traceback
        st.session_state["error"] = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
    finally:
        st.session_state["running"] = False


# ---------------------------------------------------------------------------
# Phase 1 — Configure
# ---------------------------------------------------------------------------

def _render_setup() -> None:
    st.title("EngineLab")
    st.caption("Feature-subset strategy discovery for chess variants")
    st.divider()

    # Variant cards
    st.subheader("Select Variant")
    cols = st.columns(3)
    variants = ["standard", "atomic", "antichess"]
    for col, v in zip(cols, variants):
        selected = st.session_state["variant"] == v
        border = f"2px solid {COLOR_POSITIVE}" if selected else "2px solid #30363d"
        col.markdown(
            f"""<div style="border:{border};border-radius:8px;padding:12px 16px;
            cursor:pointer;background:#161b22">
            <div style="font-size:1rem;font-weight:600;color:#e6edf3">{v.title()}</div>
            <div style="font-size:0.8rem;color:#8b949e;margin-top:4px">
            {VARIANT_DESCRIPTIONS[v]}</div></div>""",
            unsafe_allow_html=True,
        )
        if col.button("Select", key=f"variant_{v}", use_container_width=True):
            st.session_state["variant"] = v
            st.rerun()

    st.divider()

    # Feature selection
    st.subheader("Select Features")
    preset_cols = st.columns(len(PRESETS) + 2)
    for i, preset in enumerate(PRESETS):
        if preset_cols[i].button(preset["label"], help=preset["desc"], use_container_width=True):
            st.session_state["selected_features"] = list(preset["features"])
            st.rerun()
    if preset_cols[len(PRESETS)].button("All", use_container_width=True):
        st.session_state["selected_features"] = list(ALL_FEATURES)
        st.rerun()
    if preset_cols[len(PRESETS) + 1].button("Clear", use_container_width=True):
        st.session_state["selected_features"] = []
        st.rerun()

    feat_cols = st.columns(5)
    selected: list[str] = []
    for i, feat in enumerate(ALL_FEATURES):
        checked = feat in st.session_state["selected_features"]
        if feat_cols[i % 5].checkbox(
            FEATURE_DISPLAY_NAMES[feat], value=checked, key=f"feat_{feat}"
        ):
            selected.append(feat)
    st.session_state["selected_features"] = selected

    n = len(selected)
    n_agents = min(2 ** n - 1, 100) if n >= 1 else 0
    n_games = n_agents * (n_agents - 1)
    st.caption(f"Est. **{n_agents}** agents · **{n_games:,}** games")
    if n_games > 9000:
        st.warning("Long runtime — consider reducing features or using the Debug preset.")

    st.divider()

    # Config row
    st.subheader("Configuration")
    c1, c2, c3, c4 = st.columns(4)
    st.session_state["depth"] = c1.slider("Search Depth", 1, 3, st.session_state["depth"])
    st.session_state["max_moves"] = c2.slider("Max Moves", 20, 150, st.session_state["max_moves"], step=10)
    st.session_state["workers"] = c3.slider("Workers", 1, 8, st.session_state["workers"])
    st.session_state["seed"] = c4.number_input("Seed", 0, 999999, st.session_state["seed"])

    st.divider()

    can_run = n >= 2
    if not can_run:
        st.warning("Select at least 2 features to run.")

    col_run, col_mock = st.columns([3, 1])
    if col_run.button(
        "▶ Run Tournament",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    ):
        _start_tournament()

    if col_mock.button("Load Mock Data", use_container_width=True, help="Load fake data for UI testing"):
        from ui.mock_data import generate_mock_session_state
        st.session_state.update(generate_mock_session_state())
        st.rerun()


def _start_tournament() -> None:
    config = {
        "variant": st.session_state["variant"],
        "selected_features": list(st.session_state["selected_features"]),
        "depth": st.session_state["depth"],
        "max_moves": st.session_state["max_moves"],
        "workers": st.session_state["workers"],
        "seed": st.session_state["seed"],
    }
    for k in ["results", "agents", "leaderboard", "marginals", "synergies",
              "interpretation", "report_md", "config_snapshot", "duration_seconds", "error"]:
        st.session_state[k] = None
    st.session_state.update(running=True, games_completed=0, progress=0.0)
    threading.Thread(target=_run_tournament, args=(config,), daemon=True).start()
    st.rerun()


# ---------------------------------------------------------------------------
# Phase 2 — Live
# ---------------------------------------------------------------------------

def _render_live() -> None:
    snap = st.session_state.get("config_snapshot") or {}
    variant = snap.get("variant", st.session_state["variant"])
    n_agents = len(st.session_state.get("agents") or [])
    total = st.session_state.get("total_games", 0)
    done = st.session_state.get("games_completed", 0)
    progress = st.session_state.get("progress", 0.0)
    elapsed = time.time() - (st.session_state.get("start_time") or time.time())
    remaining = (elapsed / progress - elapsed) if progress > 0.01 else 0.0

    st.title("Tournament Running")
    st.caption(f"{variant.title()} · {n_agents} agents · {total:,} games")
    st.progress(progress)
    st.caption(
        f"Game **{done}** / **{total}**  ·  "
        f"Elapsed: **{elapsed:.0f}s**  ·  "
        f"Est. remaining: **{remaining:.0f}s**"
    )
    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Live Leaderboard")
        lb = st.session_state.get("leaderboard")
        if lb:
            rows = [
                {
                    "Agent": r.agent_name.replace("Agent_", "")[:45],
                    "Score Rate": round(r.score_rate, 4),
                    "W": r.wins,
                    "D": r.draws,
                    "L": r.losses,
                    "Games": r.games_played,
                }
                for r in lb[:15]
            ]
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                height=380,
                column_config={"Score Rate": st.column_config.NumberColumn(format="%.4f")},
            )
            st.plotly_chart(_build_ranking_chart(lb), use_container_width=True)
        else:
            st.info("Waiting for first results...")

    with right:
        st.subheader("Stats")
        results = st.session_state.get("results") or []
        if results:
            avg_len = sum(r.moves for r in results) / len(results)
            draws = sum(1 for r in results if r.winner is None)
            st.metric("Games complete", done)
            st.metric("Avg game length", f"{avg_len:.1f} plies")
            st.metric("Draw rate", f"{draws / len(results):.1%}")
        else:
            st.metric("Games complete", done)
            st.caption("Stats will appear as games complete.")

    # Auto-refresh every 2s while running
    time.sleep(2)
    st.rerun()


def _build_ranking_chart(lb: list) -> go.Figure:
    top5 = lb[:5]
    fig = go.Figure()
    colors = [COLOR_POSITIVE, "#00b0ff", "#ff9800", "#e040fb", COLOR_NEUTRAL]
    for row, color in zip(top5, colors):
        name = row.agent_name.replace("Agent_", "")[:30]
        fig.add_trace(go.Scatter(
            x=[0, row.games_played],
            y=[0.5, row.score_rate],
            mode="lines",
            name=name,
            line=dict(color=color, width=2),
        ))
    fig.update_layout(
        title="Ranking Evolution (top 5)",
        xaxis_title="Games played",
        yaxis_title="Score rate",
        yaxis=dict(range=[0, 1]),
        height=260,
        margin=dict(l=0, r=0, t=36, b=0),
        paper_bgcolor="#161b22",
        plot_bgcolor="#0e1117",
        font=dict(color="#e6edf3"),
        legend=dict(font=dict(size=10)),
    )
    return fig


# ---------------------------------------------------------------------------
# Phase 3 — Results
# ---------------------------------------------------------------------------

def _render_results() -> None:
    lb = st.session_state["leaderboard"]
    marginals = st.session_state["marginals"]
    synergies = st.session_state["synergies"]
    interpretation = st.session_state.get("interpretation", "")
    report_md = st.session_state.get("report_md", "")
    snap = st.session_state.get("config_snapshot") or {}
    duration = st.session_state.get("duration_seconds")

    st.success("Tournament complete!")

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Variant", snap.get("variant", "—").title())
    c2.metric("Agents", len(st.session_state.get("agents") or []))
    c3.metric("Games", len(st.session_state.get("results") or []))
    c4.metric("Duration", f"{duration:.0f}s" if duration else "—")

    # Best agent
    if lb:
        best = lb[0]
        st.info(
            f"**Best agent:** `{best.agent_name.replace('Agent_', '')}`  ·  "
            f"Score rate: **{best.score_rate:.4f}**  ·  "
            f"W {best.wins} / D {best.draws} / L {best.losses}"
        )

    st.divider()

    # Results sections
    _render_leaderboard_section(lb)
    st.divider()
    _render_features_section(marginals, snap.get("selected_features", ALL_FEATURES))
    st.divider()
    _render_synergy_section(synergies, snap.get("selected_features", ALL_FEATURES))
    st.divider()
    _render_interpretation_section(interpretation)
    st.divider()
    _render_download_section(report_md)

    st.divider()
    if st.button("↺ Run Again", use_container_width=False):
        for k in ["results", "agents", "leaderboard", "marginals", "synergies",
                  "interpretation", "report_md", "config_snapshot", "duration_seconds", "error"]:
            st.session_state[k] = None
        st.rerun()


def _render_leaderboard_section(lb: list) -> None:
    st.subheader("Leaderboard")
    rows = [
        {
            "Rank": i + 1,
            "Agent": r.agent_name.replace("Agent_", "")[:50],
            "Features": len(r.features),
            "Score Rate": round(r.score_rate, 4),
            "W": r.wins,
            "D": r.draws,
            "L": r.losses,
            "Avg Length": round(r.avg_game_length, 1),
        }
        for i, r in enumerate(lb)
    ]
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        height=400,
        column_config={"Score Rate": st.column_config.NumberColumn(format="%.4f")},
    )

    # Score vs feature count scatter
    fig = go.Figure()
    xs = [len(r.features) for r in lb]
    ys = [r.score_rate for r in lb]
    names = [r.agent_name.replace("Agent_", "") for r in lb]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers", text=names,
        marker=dict(color=ys, colorscale="RdYlGn", size=8, showscale=True,
                    colorbar=dict(title="Score Rate")),
        hovertemplate="%{text}<br>Features: %{x}<br>Score: %{y:.4f}<extra></extra>",
    ))
    import numpy as np
    if len(xs) > 1:
        m, b = np.polyfit(xs, ys, 1)
        x_range = list(range(min(xs), max(xs) + 1))
        fig.add_trace(go.Scatter(
            x=x_range, y=[m * x + b for x in x_range],
            mode="lines", name="trend", line=dict(color=COLOR_NEUTRAL, dash="dash"),
        ))
    fig.update_layout(
        title="Does adding more features help?",
        xaxis_title="Number of features", yaxis_title="Score rate",
        height=300, margin=dict(l=0, r=0, t=36, b=0),
        paper_bgcolor="#161b22", plot_bgcolor="#0e1117", font=dict(color="#e6edf3"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_features_section(marginals: list, feature_names: list[str]) -> None:
    st.subheader("Feature Intelligence")
    st.caption("How much does each feature improve win rate when present?")

    sorted_m = sorted(marginals, key=lambda r: r.marginal, reverse=True)
    labels = [FEATURE_DISPLAY_NAMES.get(r.feature, r.feature) for r in sorted_m]
    values = [r.marginal for r in sorted_m]
    colors = [COLOR_POSITIVE if v > 0.01 else COLOR_NEGATIVE if v < -0.01 else COLOR_NEUTRAL for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors,
        hovertemplate="%{y}: %{x:+.4f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Marginal contribution to win rate",
        height=max(300, len(labels) * 36),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#161b22", plot_bgcolor="#0e1117", font=dict(color="#e6edf3"),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    rows = [
        {
            "Feature": FEATURE_DISPLAY_NAMES.get(r.feature, r.feature),
            "Marginal": round(r.marginal, 4),
            "Avg With": round(r.avg_score_with, 4),
            "Avg Without": round(r.avg_score_without, 4),
            "Top-10 Freq": f"{r.top_k_frequency:.0%}",
        }
        for r in sorted_m
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_synergy_section(synergies: list, feature_names: list[str]) -> None:
    st.subheader("Feature Synergy")
    st.caption(
        "synergy(A, B) = avg_with_both − avg_with_A − avg_with_B + overall_avg. "
        "Positive = features more valuable together than separately."
    )

    n = len(feature_names)
    names = [FEATURE_DISPLAY_NAMES.get(f, f) for f in feature_names]
    matrix: list[list[float | None]] = [[None] * n for _ in range(n)]
    idx = {f: i for i, f in enumerate(feature_names)}

    for row in synergies:
        i, j = idx.get(row.feature_a), idx.get(row.feature_b)
        if i is not None and j is not None:
            matrix[i][j] = round(row.synergy, 4)
            matrix[j][i] = round(row.synergy, 4)

    fig = go.Figure(go.Heatmap(
        z=matrix, x=names, y=names,
        colorscale="RdYlGn", zmid=0,
        text=[[f"{v:.3f}" if v is not None else "" for v in row] for row in matrix],
        texttemplate="%{text}",
        hovertemplate="%{y} + %{x}<br>Synergy: %{z:.4f}<extra></extra>",
    ))
    fig.update_layout(
        height=max(420, n * 48),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#161b22", plot_bgcolor="#0e1117", font=dict(color="#e6edf3"),
        xaxis=dict(tickangle=45),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top/bottom pairs bar
    sorted_s = sorted(synergies, key=lambda r: r.synergy, reverse=True)
    top = sorted_s[:5]
    bottom = sorted_s[-5:]
    pairs = top + bottom
    pair_labels = [
        f"{FEATURE_DISPLAY_NAMES.get(r.feature_a, r.feature_a)} + "
        f"{FEATURE_DISPLAY_NAMES.get(r.feature_b, r.feature_b)}"
        for r in pairs
    ]
    pair_values = [r.synergy for r in pairs]
    pair_colors = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in pair_values]
    fig2 = go.Figure(go.Bar(
        x=pair_values, y=pair_labels, orientation="h",
        marker_color=pair_colors,
        hovertemplate="%{y}: %{x:+.4f}<extra></extra>",
    ))
    fig2.update_layout(
        title="Most synergistic and redundant pairs",
        height=360, margin=dict(l=0, r=0, t=36, b=0),
        paper_bgcolor="#161b22", plot_bgcolor="#0e1117", font=dict(color="#e6edf3"),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig2, use_container_width=True)


def _render_interpretation_section(interpretation: str) -> None:
    st.subheader("Interpretation")
    if interpretation:
        st.markdown(f"> {interpretation}")
    else:
        st.caption("No interpretation available.")


def _render_download_section(report_md: str) -> None:
    st.subheader("Export")
    col1, col2 = st.columns(2)
    snap = st.session_state.get("config_snapshot") or {}
    variant = snap.get("variant", "results")
    col1.download_button(
        "⬇ Download Report (Markdown)",
        data=report_md or "",
        file_name=f"{variant}_strategy_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
    results = st.session_state.get("results") or []
    if results:
        import json, dataclasses
        col2.download_button(
            "⬇ Download Results (JSON)",
            data=json.dumps([dataclasses.asdict(r) for r in results], indent=2),
            file_name=f"{variant}_results.json",
            mime="application/json",
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_session_state()

    if st.session_state.get("error"):
        st.error(st.session_state["error"])
        if st.button("Clear error and reset"):
            st.session_state["error"] = None
            st.session_state["running"] = False
            st.rerun()
        return

    try:
        if st.session_state.get("running"):
            _render_live()
        elif st.session_state.get("leaderboard") is not None:
            _render_results()
        else:
            _render_setup()
    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
