# EngineLab

Interpretable strategy-discovery system for chess variants via exhaustive
feature-subset testing with alpha-beta engines.

## Quick Reference

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run all tests
pytest

# Run Foundation tests
pytest tests/test_board.py tests/test_move_generation.py tests/test_standard.py

# Run Area 1 (ENGINE) tests
pytest tests/test_atomic.py tests/test_features.py tests/test_agents.py tests/test_alpha_beta.py

# Run Area 2 (HARNESS) tests
pytest tests/test_tournament.py tests/test_analysis.py

# Run the full pipeline
python main.py full-pipeline --variant atomic --depth 2 --max-moves 80
```

## Conventions (MUST follow)

- **Pieces:** FEN chars. Uppercase = white (`P N B R Q K`), lowercase = black (`p n b r q k`), empty = `None`
- **Colors:** Always `"w"` or `"b"`. Never `"white"` / `"black"` in data structures.
- **Coordinates:** `grid[row][col]`. Row 0 = rank 1 (white side). Col 0 = file a.
- **Board.copy():** Must deep-copy. Modifying copy must not affect original.
- **Board fields:** `castling_rights` (dict), `en_passant_square` (Square | None)
- **Agent names:** `Agent_{feat1}__{feat2}` -- double underscore separator, features sorted alphabetically.
- **10 features:** material, piece_position, center_control, king_safety, enemy_king_danger, mobility, pawn_structure, bishop_pair, rook_activity, capture_threats

## Architecture

Foundation (on `main`) + two parallel development areas:

| Component   | Scope                                    | Key files                              |
|-------------|------------------------------------------|----------------------------------------|
| Foundation  | Working standard chess engine            | `core/`, `variants/standard.py`        |
| Area 1      | Variants + features + agents + search    | `variants/atomic.py`, `features/`, `agents/`, `search/` |
| Area 2      | Tournament + analysis + reporting + CLI  | `simulation/`, `tournament/`, `analysis/`, `reports/`, `main.py` |

## Key Rules

- **Do not edit files outside your area.** See `docs/agent_definitions.md` for ownership.
- **Do not change shared interfaces** without updating `docs/interfaces.md` first.
- **Full chess rules required:** castling, en passant, promotion to all pieces, check legality.
- **Self-preservation rule is REQUIRED:** Filter out captures that would explode own king (atomic).
- **Area 2 uses `mock_play_game()`** during development for zero ENGINE dependency.
- Read `Instructions.MD` for the full PRD. Read `docs/interfaces.md` for exact signatures.
- Read `docs/harness_engineering.md` for agent operation best practices and validation protocol.

## Determinism

All output must be deterministic given the same seed. Move generation must iterate
pieces in fixed order (row 0-7, col 0-7). Use `random.Random(seed)` (local instance),
never `random.seed()` on the global RNG. Run the pipeline twice with the same seed
and diff the outputs to verify.
