# EngineLab Strategy Report: Atomic Chess

## Summary

Best agent: **Agent_bishop_pair__mobility** (score rate: 0.819)
Total games played: 870
Number of agents: 30

## Variant

**Atomic** chess rules were used for all games.

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
| variant | atomic |
| depth | 2 |
| max_moves | 60 |
| seed | 42 |
| agents | 30 |
| games | 870 |

## Leaderboard (Top 10)

| Rank | Agent | Features | Score Rate | W | L | D | Games |
|------|-------|----------|------------|---|---|---|-------|
| 1 | Agent_bishop_pair__mobility | bishop_pair, mobility | 0.819 | 41 | 4 | 13 | 58 |
| 2 | Agent_mobility | mobility | 0.776 | 37 | 5 | 16 | 58 |
| 3 | Agent_capture_threats__enemy_king_danger | capture_threats, enemy_king_danger | 0.733 | 36 | 9 | 13 | 58 |
| 4 | Agent_bishop_pair__enemy_king_danger | bishop_pair, enemy_king_danger | 0.707 | 32 | 8 | 18 | 58 |
| 5 | Agent_capture_threats__mobility | capture_threats, mobility | 0.681 | 23 | 2 | 33 | 58 |
| 6 | Agent_center_control__material | center_control, material | 0.681 | 32 | 11 | 15 | 58 |
| 7 | Agent_center_control__enemy_king_danger | center_control, enemy_king_danger | 0.664 | 28 | 9 | 21 | 58 |
| 8 | Agent_enemy_king_danger | enemy_king_danger | 0.612 | 28 | 15 | 15 | 58 |
| 9 | Agent_center_control__king_safety | center_control, king_safety | 0.578 | 23 | 14 | 21 | 58 |
| 10 | Agent_capture_threats__material | capture_threats, material | 0.560 | 13 | 6 | 39 | 58 |

## Best Feature Subset

**Agent_bishop_pair__mobility**

- Features: bishop_pair, mobility
- Score rate: 0.819
- Record: 41W / 4L / 13D
- Avg game length: 25.8 plies

## Feature Contributions

| Feature | Avg With | Avg Without | Marginal | Top-K Freq |
|---------|----------|-------------|----------|------------|
| mobility | 0.759 | 0.471 | +0.287 | 0.30 |
| enemy_king_danger | 0.679 | 0.472 | +0.206 | 0.40 |
| center_control | 0.568 | 0.483 | +0.084 | 0.30 |
| capture_threats | 0.504 | 0.498 | +0.006 | 0.30 |
| material | 0.500 | 0.500 | +0.000 | 0.20 |
| bishop_pair | 0.478 | 0.511 | -0.034 | 0.20 |
| piece_position | 0.454 | 0.505 | -0.051 | 0.00 |
| rook_activity | 0.431 | 0.508 | -0.077 | 0.00 |
| king_safety | 0.409 | 0.514 | -0.104 | 0.10 |
| pawn_structure | 0.371 | 0.514 | -0.144 | 0.00 |

## Top Synergies

| Feature A | Feature B | Avg Both | Synergy |
|-----------|-----------|----------|---------|
| center_control | material | 0.681 | +0.114 |
| center_control | king_safety | 0.578 | +0.101 |
| bishop_pair | mobility | 0.819 | +0.083 |
| capture_threats | pawn_structure | 0.431 | +0.056 |
| capture_threats | material | 0.560 | +0.056 |
| bishop_pair | enemy_king_danger | 0.707 | +0.050 |
| capture_threats | enemy_king_danger | 0.733 | +0.050 |
| bishop_pair | pawn_structure | 0.379 | +0.031 |
| bishop_pair | rook_activity | 0.440 | +0.031 |
| capture_threats | piece_position | 0.483 | +0.024 |

## Interpretation

In atomic chess, the best-performing agent was Agent_bishop_pair__mobility (features: bishop_pair, mobility) with a score rate of 0.819 over 58 games. The most valuable features were mobility (+0.287), enemy_king_danger (+0.206), center_control (+0.084). The least valuable feature was pawn_structure (-0.144). The strongest synergy was between center_control and material (synergy=0.114), meaning these features are more valuable together than their individual contributions suggest. The most redundant pair was enemy_king_danger and mobility (synergy=-0.938).

## Limitations

- Equal weights only; does not optimize weight values.
- Results depend on search depth and move cap.
- Feature interactions beyond pairs are not analyzed.
- Stratified sampling may miss some feature subsets when >6 features are used.
