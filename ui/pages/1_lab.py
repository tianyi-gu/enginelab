from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pathlib
import json

import pandas as pd
import streamlit as st

from ui.constants import ALL_FEATURES, FEATURE_DISPLAY_NAMES, SESSION_DEFAULTS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ANALOGY_DATA: dict[str, list[str]] = {
    "EngineLab": [
        "Evaluation feature",
        "Feature-subset agent",
        "Tournament win rate",
        "Marginal feature contribution",
        "Pairwise feature synergy",
        "Best feature subset",
    ],
    "Quant Finance": [
        "Risk factor",
        "Factor-model portfolio",
        "Backtest return",
        "Factor alpha",
        "Factor correlation / interaction",
        "Optimal factor model",
    ],
}

_DEBUG_FEATURES: list[str] = ["material", "mobility", "king_safety"]
_DEMO_FEATURES: list[str] = [
    "material", "mobility", "king_safety", "enemy_king_danger", "capture_threats"
]

_OUTPUTS_DATA_DIR = pathlib.Path(__file__).parents[3] / "outputs" / "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_results_from_file(path: pathlib.Path) -> None:
    """Load tournament JSON into session state."""
    try:
        from tournament.results_io import load_results_json
        from tournament.leaderboard import compute_leaderboard
        from analysis.feature_marginals import compute_feature_marginals
        from analysis.synergy import compute_pairwise_synergies
        from agents.feature_subset_agent import FeatureSubsetAgent

        results = load_results_json(str(path))
        names = list(
            {r.white_agent for r in results} | {r.black_agent for r in results}
        )
        agents = [
            FeatureSubsetAgent(name=n, features=tuple(), weights={}) for n in names
        ]
        leaderboard = compute_leaderboard(results, agents)
        marginals = compute_feature_marginals(leaderboard, ALL_FEATURES)
        synergies = compute_pairwise_synergies(leaderboard, ALL_FEATURES)
        st.session_state.update(
            {
                "results": results,
                "agents": agents,
                "leaderboard": leaderboard,
                "marginals": marginals,
                "synergies": synergies,
            }
        )
        st.success(f"Loaded {len(results)} games from {path.name}")
    except Exception as e:
        st.error(f"Failed to load {path.name}: {e}")


def _scan_output_files() -> list[pathlib.Path]:
    """Return sorted list of *.json files from outputs/data/."""
    if not _OUTPUTS_DATA_DIR.exists():
        return []
    return sorted(_OUTPUTS_DATA_DIR.glob("*.json"))


def _read_file_meta(path: pathlib.Path) -> dict:
    """Read basic metadata from a tournament JSON file without raising."""
    try:
        with open(path) as f:
            data = json.load(f)
        # Accept both a list of results or a dict wrapping them
        if isinstance(data, list):
            games = len(data)
            variant = "unknown"
            date_str = path.stem
        else:
            games = len(data.get("results", []))
            variant = data.get("variant", "unknown")
            date_str = data.get("date", path.stem)
        agents_set: set[str] = set()
        results_list = data if isinstance(data, list) else data.get("results", [])
        for r in results_list:
            if isinstance(r, dict):
                agents_set.add(r.get("white_agent", ""))
                agents_set.add(r.get("black_agent", ""))
        return {
            "variant": variant,
            "date": date_str,
            "agents": len(agents_set),
            "games": games,
        }
    except Exception:
        return {"variant": "?", "date": path.stem, "agents": "?", "games": "?"}


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_header() -> None:
    """Render page title and subtitle."""
    st.title("EngineLab")
    st.subheader("Feature-Subset Strategy Discovery for Chess Variants")


def _render_analogy_panel() -> None:
    """Render the quant finance analogy table."""
    st.subheader("The Analogy")
    st.caption(
        "EngineLab is a factor-model laboratory — but for chess strategy "
        "instead of financial returns."
    )
    df = pd.DataFrame(_ANALOGY_DATA)
    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_quick_start() -> None:
    """Render Quick Start preset buttons."""
    st.subheader("Quick Start")
    col_debug, col_demo, col_full = st.columns(3)

    with col_debug:
        st.markdown("**⚡ Debug**")
        st.caption("3 features · 7 agents · 42 games")
        if st.button("⚡ Debug (3 features)", use_container_width=True, key="qs_debug"):
            st.session_state["selected_features"] = _DEBUG_FEATURES[:]
            st.rerun()

    with col_demo:
        st.markdown("**Demo**")
        st.caption("5 features · 31 agents · 930 games")
        if st.button("Demo (5 features)", use_container_width=True, key="qs_demo"):
            st.session_state["selected_features"] = _DEMO_FEATURES[:]
            st.rerun()

    with col_full:
        st.markdown("**Full**")
        st.caption("10 features · ~87 agents · ~7,500 games")
        if st.button("Full (10 features)", use_container_width=True, key="qs_full"):
            st.session_state["selected_features"] = ALL_FEATURES[:]
            st.rerun()


def _render_pipeline_diagram() -> None:
    """Render a static 5-step pipeline diagram using st.columns."""
    st.subheader("How It Works")
    # 9 columns: 5 content + 4 arrows
    cols = st.columns(9)
    steps = [
        ("Features", "10"),
        ("Agents", "2^n–1"),
        ("Tournament", "Round-robin"),
        ("Analysis", "Marginals"),
        ("Report", "Markdown"),
    ]
    step_indices = [0, 2, 4, 6, 8]
    arrow_indices = [1, 3, 5, 7]

    for col_idx, (label, sublabel) in zip(step_indices, steps):
        with cols[col_idx]:
            st.markdown(f"**{label}**")
            st.caption(sublabel)

    for col_idx in arrow_indices:
        with cols[col_idx]:
            st.markdown("→")


def _render_previous_results() -> None:
    """Scan outputs/data/ and display a table of past tournament JSON files."""
    st.subheader("Previous Results")
    files = _scan_output_files()

    if not files:
        st.caption(
            "No saved results yet. Run a tournament to generate results."
        )
        return

    rows: list[dict] = []
    for path in files:
        meta = _read_file_meta(path)
        rows.append(
            {
                "_path": path,
                "Variant": meta["variant"],
                "Date": meta["date"],
                "Agents": meta["agents"],
                "Games": meta["games"],
                "File": path.name,
            }
        )

    display_df = pd.DataFrame(
        [{k: v for k, v in r.items() if k != "_path"} for r in rows]
    )
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    st.caption("Load a result set into session state:")
    for row in rows:
        path: pathlib.Path = row["_path"]
        if st.button(f"Load  {path.name}", key=f"load_{path.stem}"):
            _load_results_from_file(path)
            st.rerun()


def _render_mock_data_button() -> None:
    """Render the Load Mock Data development button."""
    st.divider()
    if st.button("Load Mock Data (dev)"):
        from ui.mock_data import generate_mock_session_state

        mock = generate_mock_session_state()
        st.session_state.update(mock)
        st.success("Mock data loaded. Navigate to Analysis or Tournament pages.")
        st.rerun()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Render Page 1: Lab home."""
    # Initialise session state defaults on first load
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default

    _render_header()
    st.divider()
    _render_analogy_panel()
    st.divider()
    _render_quick_start()
    st.divider()
    _render_pipeline_diagram()
    st.divider()
    _render_previous_results()
    _render_mock_data_button()


try:
    main()
except Exception as exc:
    st.error(str(exc))
