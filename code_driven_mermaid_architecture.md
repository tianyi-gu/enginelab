# Code-Accurate Architecture Reference — EngineLab

This file is a concise, code-verified supplement to `enginelab_mermaid_architecture.md`.
All class fields match the actual dataclasses and interfaces in the codebase.

---

## 1. Accurate Class Diagram

```mermaid
classDiagram
    class Board {
        +grid: list[list[str|None]]
        +side_to_move: str
        +winner: str|None
        +move_count: int
        +castling_rights: dict[str, bool]
        +en_passant_square: Square|None
        +starting_position() Board
        +copy() Board
        +get_piece(square) str|None
        +set_piece(square, piece)
        +find_king(color) Square|None
        +is_terminal() bool
        +print_board()
    }

    class Move {
        +start: Square
        +end: Square
        +promotion: str|None
        +to_uci() str
        +__str__() str
    }

    class FeatureSubsetAgent {
        +name: str
        +features: tuple[str, ...]
        +weights: dict[str, float]
    }

    class AlphaBetaEngine {
        +agent: FeatureSubsetAgent
        +depth: int
        +variant: str
        +nodes_searched: int
        +search_time_seconds: float
        +choose_move(board) Move
        -_negamax(board, depth, alpha, beta, color) float
        -_order_moves(board, moves) list[Move]
    }

    class RandomAgent {
        +name: str
        +choose_move(board) Move
    }

    class GameResult {
        +white_agent: str
        +black_agent: str
        +winner: str|None
        +moves: int
        +termination_reason: str
        +white_avg_nodes: float
        +black_avg_nodes: float
        +white_avg_time: float
        +black_avg_time: float
    }

    class LeaderboardRow {
        +agent_name: str
        +features: tuple[str, ...]
        +games_played: int
        +wins: int
        +losses: int
        +draws: int
        +score_rate: float
        +avg_game_length: float
    }

    class FeatureContributionRow {
        +feature: str
        +avg_score_with: float
        +avg_score_without: float
        +marginal: float
        +top_k_frequency: float
    }

    class SynergyRow {
        +feature_a: str
        +feature_b: str
        +avg_score_with_both: float
        +synergy: float
    }

    AlphaBetaEngine --> FeatureSubsetAgent
    AlphaBetaEngine --> Board
    AlphaBetaEngine --> Move
    LeaderboardRow --> GameResult
    FeatureContributionRow --> LeaderboardRow
    SynergyRow --> LeaderboardRow
```

---

## 2. Alpha-Beta Search Path (code trace)

```mermaid
flowchart TD
    A[AlphaBetaEngine.choose_move board] --> B[gen_legal_fn board\nfrom variant dispatch]
    B --> C[_order_moves: captures first by victim value]
    C --> D[loop over legal moves]
    D --> E[apply_fn board move]
    E --> F[_negamax new_board depth-1 alpha beta opponent]
    F --> G{depth == 0 or\nterminal?}
    G -->|Yes| H[evaluate board color agent\nweighted sum of normalized features]
    G -->|No| I[gen_legal_fn new_board]
    I --> J[loop recursively]
    J --> F
    H --> K[alpha-beta pruning\nupdate best score]
    K --> L[return best Move]
```

---

## 3. Variant Dispatch

```mermaid
flowchart LR
    Call[get_apply_move variant\nget_generate_legal_moves variant] --> Dispatch[variants/base.py\nVARIANT_DISPATCH dict]
    Dispatch -->|standard| Std[apply_standard_move\ngenerate_standard_moves]
    Dispatch -->|atomic| Atom[apply_atomic_move\ngenerate_atomic_moves\nexplosion + self-preservation]
    Dispatch -->|antichess| Anti[apply_antichess_move\ngenerate_antichess_moves\nforced captures]
    Std --> Core[core/apply_move.py\ncore/move_generation.py]
    Atom --> Core
    Anti --> Core
```

---

## 4. Feature Registry

```mermaid
flowchart LR
    Registry[features/registry.py\nFEATURES dict\nFEATURE_DESCRIPTIONS dict] --> mat[material]
    Registry --> pos[piece_position]
    Registry --> cen[center_control]
    Registry --> ks[king_safety]
    Registry --> ekd[enemy_king_danger]
    Registry --> mob[mobility]
    Registry --> pawn[pawn_structure]
    Registry --> bish[bishop_pair]
    Registry --> rook[rook_activity]
    Registry --> cap[capture_threats]
    Eval[evaluation.evaluate board color agent] --> Registry
    Eval --> Norm[normalize: clip to -10..10 then divide by 10]
    Norm --> Sum[weighted sum over agent.weights]
```

---

## 5. Tournament + Analysis Pipeline

```mermaid
flowchart LR
    Agents[list of FeatureSubsetAgents] --> RR[run_round_robin\nN x N-1 games]
    RR --> Worker[_run_game per worker\nProcessPoolExecutor]
    Worker --> PG[play_game white black variant seed]
    PG --> GR[GameResult]
    GR --> LB[compute_leaderboard]
    GR --> IO[save_results_json\nsave_results_csv]
    LB --> FM[compute_feature_marginals]
    LB --> SY[compute_pairwise_synergies]
    FM --> INT[generate_interpretation]
    SY --> INT
    INT --> REP[generate_markdown_report]
```

---

## 6. LLM Agent Generation

```mermaid
flowchart TD
    Call[generate_llm_selected_agents\nfeature_names, descriptions, variant] --> Cache{outputs/llm_feature_cache.json\nhas entry for variant?}
    Cache -->|Hit| Skip[Use cached 7 features]
    Cache -->|Miss| Prompt[Prompt DeepSeek via Ollama\nlocalhost:11434/v1]
    Prompt --> Resp[Parse JSON response]
    Resp --> Valid{7 valid feature names?}
    Valid -->|Yes| Write[Write cache]
    Valid -->|No| Alpha[Fallback: first 7 alphabetically]
    Write --> Exh[_exhaustive: 2^7-1 = 127 agents]
    Skip --> Exh
    Alpha --> Exh
```
