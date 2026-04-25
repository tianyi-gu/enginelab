# EngineLab Strategy Report: Standard Chess

## Summary

Best agent: **Agent_bishop_pair** (score rate: 0.500)
Total games played: 90
Number of agents: 10

## Variant

**Standard** chess rules were used for all games.

## Features

- bishop_pair
- capture_threats
- center_control
- enemy_king_danger
- king_safety
- material
- mobility
- pawn_structure
- piece_position
- rook_activity

## Configuration

| Parameter | Value |
|-----------|-------|
| variant | standard |
| depth | 1 |
| max_moves | 40 |
| seed | 42 |
| agents | 10 |
| games | 90 |

## Leaderboard (Top 10)

| Rank | Agent | Features | Score Rate | W | L | D | Games |
|------|-------|----------|------------|---|---|---|-------|
| 1 | Agent_bishop_pair | bishop_pair | 0.500 | 0 | 0 | 18 | 18 |
| 2 | Agent_capture_threats | capture_threats | 0.500 | 0 | 0 | 18 | 18 |
| 3 | Agent_center_control | center_control | 0.500 | 0 | 0 | 18 | 18 |
| 4 | Agent_enemy_king_danger | enemy_king_danger | 0.500 | 0 | 0 | 18 | 18 |
| 5 | Agent_king_safety | king_safety | 0.500 | 0 | 0 | 18 | 18 |
| 6 | Agent_material | material | 0.500 | 0 | 0 | 18 | 18 |
| 7 | Agent_mobility | mobility | 0.500 | 0 | 0 | 18 | 18 |
| 8 | Agent_pawn_structure | pawn_structure | 0.500 | 0 | 0 | 18 | 18 |
| 9 | Agent_piece_position | piece_position | 0.500 | 0 | 0 | 18 | 18 |
| 10 | Agent_rook_activity | rook_activity | 0.500 | 0 | 0 | 18 | 18 |

## Best Feature Subset

**Agent_bishop_pair**

- Features: bishop_pair
- Score rate: 0.500
- Record: 0W / 0L / 18D
- Avg game length: 40.0 plies

## Feature Contributions

| Feature | Avg With | Avg Without | Marginal | Top-K Freq |
|---------|----------|-------------|----------|------------|
| bishop_pair | 0.500 | 0.500 | +0.000 | 0.10 |
| capture_threats | 0.500 | 0.500 | +0.000 | 0.10 |
| center_control | 0.500 | 0.500 | +0.000 | 0.10 |
| enemy_king_danger | 0.500 | 0.500 | +0.000 | 0.10 |
| king_safety | 0.500 | 0.500 | +0.000 | 0.10 |
| material | 0.500 | 0.500 | +0.000 | 0.10 |
| mobility | 0.500 | 0.500 | +0.000 | 0.10 |
| pawn_structure | 0.500 | 0.500 | +0.000 | 0.10 |
| piece_position | 0.500 | 0.500 | +0.000 | 0.10 |
| rook_activity | 0.500 | 0.500 | +0.000 | 0.10 |

## Top Synergies

| Feature A | Feature B | Avg Both | Synergy |
|-----------|-----------|----------|---------|
| bishop_pair | capture_threats | 0.000 | -0.500 |
| bishop_pair | center_control | 0.000 | -0.500 |
| bishop_pair | enemy_king_danger | 0.000 | -0.500 |
| bishop_pair | king_safety | 0.000 | -0.500 |
| bishop_pair | material | 0.000 | -0.500 |
| bishop_pair | mobility | 0.000 | -0.500 |
| bishop_pair | pawn_structure | 0.000 | -0.500 |
| bishop_pair | piece_position | 0.000 | -0.500 |
| bishop_pair | rook_activity | 0.000 | -0.500 |
| capture_threats | center_control | 0.000 | -0.500 |

## Interpretation

In standard chess, the best-performing agent was Agent_bishop_pair (features: bishop_pair) with a score rate of 0.500 over 18 games. The most redundant pair was piece_position and rook_activity (synergy=-0.500).

## Limitations

- Equal weights only; does not optimize weight values.
- Results depend on search depth and move cap.
- Feature interactions beyond pairs are not analyzed.
- Stratified sampling may miss some feature subsets when >6 features are used.
