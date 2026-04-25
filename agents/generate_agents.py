"""Agent generation for EngineLab — produces FeatureSubsetAgent instances."""

from __future__ import annotations

import itertools
import random

from agents.feature_subset_agent import FeatureSubsetAgent


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _make_agent(subset: tuple[str, ...]) -> FeatureSubsetAgent:
    """Build a single FeatureSubsetAgent from a non-empty tuple of feature names."""
    sorted_features: tuple[str, ...] = tuple(sorted(subset))
    name: str = "Agent_" + "__".join(sorted_features)
    weight: float = 1.0 / len(sorted_features)
    weights: dict[str, float] = {f: weight for f in sorted_features}
    return FeatureSubsetAgent(name=name, features=sorted_features, weights=weights)


def _exhaustive_subsets(feature_names: list[str]) -> list[tuple[str, ...]]:
    """Return every nonempty subset of feature_names as a list of sorted tuples."""
    subsets: list[tuple[str, ...]] = []
    n = len(feature_names)
    for size in range(1, n + 1):
        for combo in itertools.combinations(feature_names, size):
            subsets.append(tuple(sorted(combo)))
    return subsets


def _stratified_subsets(
    feature_names: list[str],
    max_agents: int,
    rng: random.Random,
) -> list[tuple[str, ...]]:
    """Return a stratified collection of subsets capped at max_agents.

    Always includes: all singletons, all pairs, the full set.
    Fills remaining slots with random subsets of sizes 3..n-1 (shuffled).
    """
    n = len(feature_names)
    seen: set[tuple[str, ...]] = set()
    result: list[tuple[str, ...]] = []

    def _add(subset: tuple[str, ...]) -> None:
        key = tuple(sorted(subset))
        if key not in seen:
            seen.add(key)
            result.append(key)

    # Singletons
    for f in feature_names:
        _add((f,))

    # Pairs
    for combo in itertools.combinations(feature_names, 2):
        _add(combo)

    # Full set
    if n >= 1:
        _add(tuple(feature_names))

    # Random subsets of intermediate sizes until max_agents reached
    if len(result) < max_agents and n > 3:
        intermediate_sizes = list(range(3, n))  # sizes 3 .. n-1
        candidates: list[tuple[str, ...]] = []
        for size in intermediate_sizes:
            for combo in itertools.combinations(feature_names, size):
                key = tuple(sorted(combo))
                if key not in seen:
                    candidates.append(key)
        rng.shuffle(candidates)
        for subset in candidates:
            if len(result) >= max_agents:
                break
            _add(subset)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_feature_subset_agents(
    feature_names: list[str],
    max_agents: int = 100,
    seed: int = 42,
) -> list[FeatureSubsetAgent]:
    """Generate a list of FeatureSubsetAgent instances from feature_names.

    Strategy
    --------
    - Exhaustive when ``2**n - 1 <= max_agents``: every nonempty subset.
    - Stratified otherwise: all singletons + all pairs + full set + random
      intermediate subsets until *max_agents* is reached.

    Weights are uniform: ``1.0 / len(subset)`` for each feature.

    Parameters
    ----------
    feature_names:
        Non-empty list of unique feature name strings.
    max_agents:
        Upper bound on the number of agents returned.
    seed:
        Seed for the local :class:`random.Random` instance (stratified only).

    Returns
    -------
    list[FeatureSubsetAgent]
        Agents sorted alphabetically by name.

    Raises
    ------
    ValueError
        If *feature_names* is empty or *max_agents* is less than 1.
    """
    if not feature_names:
        raise ValueError(f"feature_names must not be empty; got {feature_names!r}")
    if max_agents < 1:
        raise ValueError(f"max_agents must be >= 1; got {max_agents!r}")

    n = len(feature_names)
    use_exhaustive: bool = (2**n - 1) <= max_agents

    if use_exhaustive:
        subsets = _exhaustive_subsets(feature_names)
    else:
        rng = random.Random(seed)
        subsets = _stratified_subsets(feature_names, max_agents, rng)

    agents: list[FeatureSubsetAgent] = [_make_agent(s) for s in subsets]
    agents.sort(key=lambda a: a.name)
    return agents
