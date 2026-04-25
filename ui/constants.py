# Shared constants imported by app.py and all pages

ALL_FEATURES: list[str] = [
    "material", "piece_position", "center_control", "king_safety",
    "enemy_king_danger", "mobility", "pawn_structure", "bishop_pair",
    "rook_activity", "capture_threats",
]

FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "material": "Material Balance",
    "piece_position": "Piece Position",
    "center_control": "Center Control",
    "king_safety": "King Safety",
    "enemy_king_danger": "Enemy King Danger",
    "mobility": "Mobility",
    "pawn_structure": "Pawn Structure",
    "bishop_pair": "Bishop Pair",
    "rook_activity": "Rook Activity",
    "capture_threats": "Capture Threats",
}

VARIANT_DESCRIPTIONS: dict[str, str] = {
    "standard": "Win by checkmating the king. Material and mobility dominate.",
    "atomic": "Captures cause explosions. King danger and explosion threats dominate.",
    "antichess": "Lose all your pieces to win. Material is a liability.",
}

# Colors (matches .streamlit/config.toml)
COLOR_POSITIVE = "#00e676"
COLOR_NEGATIVE = "#ff4d4d"
COLOR_NEUTRAL = "#8b949e"
COLOR_EXPLOSION = "#ff6b35"

# Session state defaults
SESSION_DEFAULTS: dict = {
    "variant": "atomic",
    "selected_features": list(ALL_FEATURES),  # all 10 selected
    "depth": 2,
    "max_moves": 80,
    "workers": 1,
    "seed": 42,
    "running": False,
    "progress": 0.0,
    "games_completed": 0,
    "total_games": 0,
    "start_time": None,
    "error": None,
    "skipped_games": 0,
    "results": None,
    "agents": None,
    "leaderboard": None,
    "marginals": None,
    "synergies": None,
    "interpretation": None,
    "report_md": None,
    "config_snapshot": None,
    "duration_seconds": None,
    "viewer_game_index": 0,
    "viewer_move_index": 0,
    "live_game_board": None,
    "live_game_moves": [],
}
