import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time

import streamlit as st

from ui.constants import (
    ALL_FEATURES,
    FEATURE_DISPLAY_NAMES,
    VARIANT_DESCRIPTIONS,
    SESSION_DEFAULTS,
)

st.set_page_config(
    page_title="EngineLab",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    """Initialise all session state keys to their defaults on first load."""
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = (
                list(default) if isinstance(default, list) else default
            )


# ---------------------------------------------------------------------------
# Estimation helpers
# ---------------------------------------------------------------------------

def _estimate_agents(n_features: int, max_agents: int = 100) -> int:
    """Estimate agent count as min(2^n - 1, max_agents)."""
    exhaustive = 2 ** n_features - 1
    return min(exhaustive, max_agents)


def _estimate_games(n_agents: int) -> int:
    """Estimate game count as n_agents * (n_agents - 1)."""
    return n_agents * (n_agents - 1)


# ---------------------------------------------------------------------------
# Tournament background thread
# ---------------------------------------------------------------------------

def _run_tournament_thread(config: dict) -> None:
    """Background thread: run tournament and populate session state."""
    try:
        _execute_tournament(config)
    except Exception as e:
        import traceback

        st.session_state["error"] = (
            f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        )
    finally:
        st.session_state["running"] = False


def _execute_tournament(config: dict) -> None:
    """Inner tournament execution — imports and runs the full pipeline."""
    import pathlib

    from agents.generate_agents import generate_feature_subset_agents
    from tournament.round_robin import run_round_robin
    from tournament.leaderboard import compute_leaderboard
    from analysis.feature_marginals import compute_feature_marginals
    from analysis.synergy import compute_pairwise_synergies
    from analysis.interpretation import generate_interpretation
    from reports.markdown_report import generate_markdown_report

    st.session_state["start_time"] = time.time()

    agents = generate_feature_subset_agents(
        config["selected_features"],
        max_agents=100,
        seed=config["seed"],
    )
    st.session_state["agents"] = agents
    total = len(agents) * (len(agents) - 1)
    st.session_state["total_games"] = total

    results = _run_round_robin_with_progress(agents, config)
    st.session_state["results"] = results

    leaderboard = compute_leaderboard(results, agents)
    marginals = compute_feature_marginals(leaderboard, config["selected_features"])
    synergies = compute_pairwise_synergies(leaderboard, config["selected_features"])
    interpretation = generate_interpretation(
        leaderboard[0] if leaderboard else None,
        marginals,
        synergies,
        config["variant"],
    )
    report_md = _write_markdown_report(
        config, leaderboard, marginals, synergies, interpretation,
        generate_markdown_report, pathlib,
    )

    st.session_state.update({
        "leaderboard": leaderboard,
        "marginals": marginals,
        "synergies": synergies,
        "interpretation": interpretation,
        "report_md": report_md,
        "config_snapshot": config,
        "duration_seconds": time.time() - st.session_state["start_time"],
    })


def _run_round_robin_with_progress(agents: list, config: dict) -> list:
    """Run round-robin tournament with a progress callback."""
    from tournament.round_robin import run_round_robin

    total = st.session_state.get("total_games", 1)

    def on_game_complete(done: int, total: int) -> None:
        st.session_state["games_completed"] = done
        st.session_state["progress"] = done / total if total else 0.0

    return run_round_robin(
        agents=agents,
        variant=config["variant"],
        depth=config["depth"],
        max_moves=config["max_moves"],
        seed=config["seed"],
        workers=config["workers"],
        on_game_complete=on_game_complete,
    )


def _write_markdown_report(
    config: dict,
    leaderboard: list,
    marginals: list,
    synergies: list,
    interpretation: str,
    generate_markdown_report: object,
    pathlib: object,
) -> str:
    """Write the markdown report to disk and return its contents."""
    out_dir = pathlib.Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = str(
        out_dir / f"reports/{config['variant']}_strategy_report.md"
    )
    pathlib.Path(report_path).parent.mkdir(parents=True, exist_ok=True)
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
    with open(report_path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Sidebar helpers
# ---------------------------------------------------------------------------

def _render_variant_selector() -> None:
    """Render variant radio buttons and description caption."""
    st.subheader("Chess Variant")
    variant = st.radio(
        "variant_radio",
        options=["standard", "atomic", "antichess"],
        format_func=lambda v: v.title(),
        index=["standard", "atomic", "antichess"].index(
            st.session_state["variant"]
        ),
        label_visibility="collapsed",
    )
    st.session_state["variant"] = variant
    st.caption(VARIANT_DESCRIPTIONS[variant])


def _render_feature_checkboxes() -> int:
    """Render feature checkboxes and Select All button. Returns selected count."""
    col1, col2 = st.columns([3, 1])
    col1.subheader("Features")
    if col2.button("All", key="select_all", use_container_width=True):
        st.session_state["selected_features"] = list(ALL_FEATURES)
        st.rerun()

    selected: list[str] = []
    for feat in ALL_FEATURES:
        checked = feat in st.session_state["selected_features"]
        if st.checkbox(FEATURE_DISPLAY_NAMES[feat], value=checked, key=f"feat_{feat}"):
            selected.append(feat)
    st.session_state["selected_features"] = selected
    return len(selected)


def _render_estimates(n_feat: int) -> None:
    """Render agent/game estimates and warnings."""
    n_agents = _estimate_agents(n_feat)
    n_games = _estimate_games(n_agents)
    st.caption(f"Est. agents: **{n_agents}**  ·  Est. games: **{n_games:,}**")
    if n_games > 9000:
        st.warning("Long runtime — reduce features or increase workers.")


def _render_sliders() -> None:
    """Render depth, max_moves, workers, and seed inputs."""
    st.session_state["depth"] = st.slider(
        "Search Depth", 1, 3, st.session_state["depth"]
    )
    st.caption("Depth 1: fast. Depth 2: standard. Depth 3: slow.")
    st.session_state["max_moves"] = st.slider(
        "Max Moves", 20, 150, st.session_state["max_moves"], step=10
    )
    st.session_state["workers"] = st.slider(
        "Parallel Workers", 1, 8, st.session_state["workers"]
    )
    st.session_state["seed"] = st.number_input(
        "Random Seed", 0, 999999, st.session_state["seed"]
    )


def _render_run_button(n_feat: int) -> None:
    """Render Run Tournament button and progress bar while running."""
    is_running = st.session_state.get("running", False)
    can_run = n_feat >= 2 and not is_running

    if n_feat < 2:
        st.warning("Select at least 2 features.")

    if st.button(
        "▶ Run Tournament",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    ):
        _start_tournament()

    if is_running:
        _render_progress()


def _start_tournament() -> None:
    """Snapshot config, clear results, launch background thread."""
    config = {
        "variant": st.session_state["variant"],
        "selected_features": list(st.session_state["selected_features"]),
        "depth": st.session_state["depth"],
        "max_moves": st.session_state["max_moves"],
        "workers": st.session_state["workers"],
        "seed": st.session_state["seed"],
    }
    for k in [
        "results", "agents", "leaderboard", "marginals", "synergies",
        "interpretation", "report_md", "config_snapshot",
        "duration_seconds", "error",
    ]:
        st.session_state[k] = None

    st.session_state["running"] = True
    st.session_state["games_completed"] = 0
    st.session_state["progress"] = 0.0

    t = threading.Thread(
        target=_run_tournament_thread,
        args=(config,),
        daemon=True,
    )
    t.start()
    st.rerun()


def _render_progress() -> None:
    """Render progress bar and elapsed time caption."""
    done = st.session_state.get("games_completed", 0)
    total = st.session_state.get("total_games", 1)
    st.progress(st.session_state.get("progress", 0.0))
    elapsed = time.time() - (
        st.session_state.get("start_time") or time.time()
    )
    st.caption(f"Game {done} / {total}  ·  {elapsed:.0f}s elapsed")


def _render_load_results() -> None:
    """Render the Load Results section with JSON file uploader."""
    st.subheader("Load Results")
    uploaded = st.file_uploader("Upload tournament JSON", type=["json"])
    if uploaded:
        _handle_upload(uploaded)


def _handle_upload(uploaded: object) -> None:
    """Parse an uploaded JSON file and populate session state."""
    try:
        results, agents = _load_results_from_upload(uploaded)
        _run_analysis_pipeline(results, agents)
        st.success("Results loaded.")
    except Exception as e:
        st.error(f"Failed to load: {e}")


def _load_results_from_upload(uploaded: object) -> tuple:
    """Deserialise an uploaded JSON into (results, agents)."""
    import json
    import tempfile
    import pathlib

    from tournament.results_io import load_results_json
    from agents.feature_subset_agent import FeatureSubsetAgent

    data = json.loads(uploaded.read())
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        tmp_path = f.name

    results = load_results_json(tmp_path)
    pathlib.Path(tmp_path).unlink(missing_ok=True)

    all_agent_names = list(
        {r.white_agent for r in results} | {r.black_agent for r in results}
    )
    agents = [
        FeatureSubsetAgent(name=n, features=tuple(), weights={})
        for n in all_agent_names
    ]
    return results, agents


def _run_analysis_pipeline(results: list, agents: list) -> None:
    """Run leaderboard, marginals, synergies, interpretation and store results."""
    from tournament.leaderboard import compute_leaderboard
    from analysis.feature_marginals import compute_feature_marginals
    from analysis.synergy import compute_pairwise_synergies
    from analysis.interpretation import generate_interpretation

    leaderboard = compute_leaderboard(results, agents)
    features_used = list(
        {f for a in agents for f in a.features} or ALL_FEATURES
    )
    marginals = compute_feature_marginals(
        leaderboard, features_used or ALL_FEATURES
    )
    synergies = compute_pairwise_synergies(
        leaderboard, features_used or ALL_FEATURES
    )
    interpretation = generate_interpretation(
        leaderboard[0] if leaderboard else None,
        marginals,
        synergies,
        "standard",
    )
    st.session_state.update({
        "results": results,
        "agents": agents,
        "leaderboard": leaderboard,
        "marginals": marginals,
        "synergies": synergies,
        "interpretation": interpretation,
    })


# ---------------------------------------------------------------------------
# Sidebar — public entry point
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    """Render the full persistent sidebar."""
    with st.sidebar:
        st.title("EngineLab")
        st.caption("Interpretable Strategy Discovery")
        st.divider()

        _render_variant_selector()
        st.divider()

        n_feat = _render_feature_checkboxes()
        _render_estimates(n_feat)
        st.divider()

        _render_sliders()
        st.divider()

        _render_run_button(n_feat)
        st.divider()

        _render_load_results()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Streamlit entry point."""
    _init_session_state()
    render_sidebar()

    if st.session_state.get("error"):
        st.error(st.session_state["error"])

    st.title("EngineLab")
    st.caption("Feature-Subset Strategy Discovery for Chess Variants")
    st.info(
        "Use the sidebar to configure and run a tournament, "
        "or navigate to a page using the left menu."
    )


if __name__ == "__main__":
    main()
