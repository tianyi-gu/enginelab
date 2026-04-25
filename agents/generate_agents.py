"""Agent generation for EngineLab.

Dual-mode generation:
- Exhaustive if 2^n - 1 <= max_agents
- Stratified sampling otherwise (all singles, all pairs, full set,
  random larger subsets)
- LLM-guided: OpenAI selects best n features, then exhaustive over all subsets
"""

import random
from itertools import combinations

from agents.feature_subset_agent import FeatureSubsetAgent


def generate_feature_subset_agents(
    feature_names: list[str],
    max_agents: int = 127,
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


def generate_llm_selected_agents(
    feature_names: list[str],
    feature_descriptions: dict[str, str],
    variant: str,
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
    n_select: int = 7,
    cache_path: str = "outputs/llm_feature_cache.json",
    refresh: bool = False,
) -> list[FeatureSubsetAgent]:
    """Use OpenAI to pick the best n_select features, then exhaustively generate all subsets.

    With n_select=7: produces 2^7 - 1 = 127 agents.
    api_key defaults to OPENAI_API_KEY env var if not provided.
    Caches the selection to avoid repeated API calls; pass refresh=True to force a new call.
    """
    selected = _llm_select_features(
        feature_names, feature_descriptions, variant,
        api_key, model, n_select, cache_path, refresh,
    )
    return _exhaustive(selected)


def _llm_select_features(
    feature_names: list[str],
    feature_descriptions: dict[str, str],
    variant: str,
    api_key: str | None,
    model: str,
    n_select: int,
    cache_path: str,
    refresh: bool,
) -> list[str]:
    """Call OpenAI to select the best n_select features."""
    import json
    import os

    # Check cache
    if not refresh and os.path.exists(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)
        cached = cache.get(variant, [])
        if all(f in feature_names for f in cached) and len(cached) == n_select:
            return cached

    # Build prompt
    feature_list = "\n".join(
        f"- {name}: {feature_descriptions.get(name, '')}"
        for name in sorted(feature_names)
    )
    prompt = (
        f"You are a chess strategy expert helping select evaluation features for a chess engine.\n\n"
        f"Variant: {variant} chess\n"
        f"Available features ({len(feature_names)} total):\n{feature_list}\n\n"
        f"Select exactly {n_select} features that together provide the most strategic coverage "
        f"and value for {variant} chess. Consider:\n"
        f"- Feature complementarity (avoid redundant features)\n"
        f"- Variant-specific importance (e.g. for atomic chess, king explosion risk and "
        f"capture threats matter most; for antichess, material loss is the goal)\n"
        f"- Balance between offense, defense, and positional understanding\n\n"
        f"Respond with a JSON object with key \"features\" containing a list of exactly "
        f"{n_select} feature names chosen from the available list.\n"
        f"Example: {{\"features\": [\"material\", \"mobility\", \"king_safety\"]}}"
    )

    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package required for LLM feature selection: pip install openai"
        )

    # api_key=None → OpenAI client reads OPENAI_API_KEY from environment
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    selected = data.get("features", [])

    # Validate — keep only names that exist in feature_names
    valid = [f for f in selected if f in feature_names]
    if len(valid) != n_select:
        # Fallback: alphabetical first n_select
        valid = sorted(feature_names)[:n_select]

    # Write cache
    cache: dict = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)
    cache[variant] = valid
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    return valid


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
