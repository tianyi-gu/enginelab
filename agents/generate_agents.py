"""Agent generation for EngineLab.

Dual-mode generation:
- Exhaustive if 2^n - 1 <= max_agents
- Stratified sampling otherwise (all singles, all pairs, full set,
  random larger subsets)
"""

import random
from itertools import combinations

from agents.feature_subset_agent import FeatureSubsetAgent


def generate_feature_subset_agents(
    feature_names: list[str],
    max_agents: int = 100,
    seed: int = 42,
) -> list[FeatureSubsetAgent]:
    """Generate feature-subset agents.

    Exhaustive if 2^n - 1 <= max_agents, else stratified sample.
    Weights = 1/len(subset). Names: sorted features joined by '__',
    prefixed 'Agent_'.
    """
    n = len(feature_names)
    total_subsets = (2 ** n) - 1

    if total_subsets <= max_agents:
        return _exhaustive(feature_names)
    else:
        return _stratified(feature_names, max_agents, seed)


def _exhaustive(feature_names: list[str]) -> list[FeatureSubsetAgent]:
    """Generate all nonempty subsets."""
    agents: list[FeatureSubsetAgent] = []
    n = len(feature_names)
    sorted_names = sorted(feature_names)

    for size in range(1, n + 1):
        for combo in combinations(sorted_names, size):
            agents.append(_make_agent(combo))

    return agents


def _stratified(
    feature_names: list[str], max_agents: int, seed: int,
) -> list[FeatureSubsetAgent]:
    """Stratified sampling: all singles, all pairs, full set, random fill."""
    rng = random.Random(seed)
    sorted_names = sorted(feature_names)
    n = len(sorted_names)

    seen: set[tuple[str, ...]] = set()
    agents: list[FeatureSubsetAgent] = []

    def _add(combo: tuple[str, ...]) -> None:
        if combo not in seen and len(agents) < max_agents:
            seen.add(combo)
            agents.append(_make_agent(combo))

    # All singles
    for name in sorted_names:
        _add((name,))

    # All pairs
    for combo in combinations(sorted_names, 2):
        _add(combo)

    # Full set
    _add(tuple(sorted_names))

    # Fill remaining with random subsets (size 3 to n-1)
    attempts = 0
    while len(agents) < max_agents and attempts < max_agents * 10:
        size = rng.randint(3, max(3, n - 1))
        combo = tuple(sorted(rng.sample(sorted_names, min(size, n))))
        _add(combo)
        attempts += 1

    return agents


def _make_agent(features: tuple[str, ...]) -> FeatureSubsetAgent:
    """Create an agent from a sorted feature tuple."""
    name = "Agent_" + "__".join(features)
    weights = {f: 1.0 / len(features) for f in features}
    return FeatureSubsetAgent(name=name, features=features, weights=weights)
