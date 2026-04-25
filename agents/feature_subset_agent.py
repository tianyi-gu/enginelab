"""Feature-subset agent definition for EngineLab."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureSubsetAgent:
    """An agent defined by a subset of features and their weights."""

    name: str                      # "Agent_material__mobility"
    features: tuple[str, ...]      # ("material", "mobility")
    weights: dict[str, float]      # {"material": 0.5, "mobility": 0.5}
