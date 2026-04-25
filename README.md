# EngineLab

Interpretable strategy-discovery system for chess variants.

Given a variant (e.g., Atomic Chess) and a set of strategic evaluation features, EngineLab creates one alpha-beta engine for every nonempty feature subset, runs a round-robin tournament among all engines, and analyzes which strategic concepts -- alone and in combination -- lead to winning play.

## How It Works

1. Define 5 strategic features (material, mobility, king danger, king safety, capture threats)
2. Generate 31 engines (one per nonempty subset of features)
3. Run 930 tournament games (full round-robin, both colors)
4. Analyze feature importance via marginal contribution and pairwise synergy
5. Generate a human-readable strategy report

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

## Documentation

- [Instructions.MD](Instructions.MD) -- Full product requirements document
- [docs/interfaces.md](docs/interfaces.md) -- Shared interface specification
- [docs/development_workflow.md](docs/development_workflow.md) -- Parallel development process
- [docs/agent_definitions.md](docs/agent_definitions.md) -- Per-developer scope and prompts

## Project Structure

```
core/        -- Board, move, move generation (Area 1)
variants/    -- Atomic Chess rules (Area 1)
features/    -- Evaluation features + registry (Area 2)
agents/      -- Feature-subset agents + evaluation (Area 3)
search/      -- Alpha-beta engine (Area 3)
simulation/  -- Game simulation + random agent (Area 4)
tournament/  -- Round-robin, leaderboard, I/O (Area 4)
analysis/    -- Marginals, synergy, interpretation (Area 5)
reports/     -- Markdown report generation (Area 5)
main.py      -- CLI entry point (Area 5)
tests/       -- All test files
```
