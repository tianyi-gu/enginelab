"""Shared constants for the EngineLab Streamlit UI."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess

from features.registry import get_feature_names, FEATURE_DESCRIPTIONS

# Pull feature list from the real registry
ALL_FEATURES: list[str] = get_feature_names()

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
    "negative_material": "Negative Material ★",
    "king_proximity": "King Proximity ★",
}

# Curated top-8 features per variant (ordered by importance)
# Atomic/antichess-specific features are placed near the top for their respective variants.
VARIANT_TOP_8_FEATURES: dict[str, list[str]] = {
    "standard": [
        "material", "mobility", "king_safety", "enemy_king_danger",
        "capture_threats", "center_control", "piece_position", "pawn_structure",
    ],
    "atomic": [
        "mobility", "capture_threats", "center_control", "enemy_king_danger",
        "king_proximity", "piece_position", "bishop_pair", "material",
    ],
    "antichess": [
        "negative_material", "center_control", "mobility", "enemy_king_danger",
        "pawn_structure", "material", "piece_position", "king_safety",
    ],
    "kingofthehill": [
        "material", "center_control", "king_safety", "mobility",
        "piece_position", "enemy_king_danger", "capture_threats", "pawn_structure",
    ],
    "threecheck": [
        "enemy_king_danger", "capture_threats", "mobility", "king_safety",
        "material", "center_control", "piece_position", "pawn_structure",
    ],
    "chess960": [
        "material", "mobility", "king_safety", "enemy_king_danger",
        "capture_threats", "center_control", "piece_position", "pawn_structure",
    ],
    "horde": [
        "material", "pawn_structure", "center_control", "mobility",
        "piece_position", "capture_threats", "king_safety", "enemy_king_danger",
    ],
}

VARIANT_DESCRIPTIONS: dict[str, str] = {
    "standard": "Win by checkmating the king. Material and mobility dominate.",
    "atomic": "Captures cause explosions. King danger and explosion threats dominate.",
    "antichess": "Lose all your pieces to win. Material is a liability.",
    "kingofthehill": "Move your king to the center (d4/d5/e4/e5) to win.",
    "threecheck": "Deliver three checks to win. Aggressive play rewarded.",
    "chess960": "Randomized starting position. No opening theory advantage.",
    "horde": "White has 36 pawns, no king. Black must capture them all.",
}

# Colors (matches .streamlit/config.toml)
COLOR_POSITIVE = "#00e676"
COLOR_NEGATIVE = "#ff4d4d"
COLOR_NEUTRAL = "#8b949e"
COLOR_EXPLOSION = "#ff6b35"

# Session state defaults
SESSION_DEFAULTS: dict = {
    "variant": "standard",
    "selected_features": list(ALL_FEATURES),
    "depth": 2,
    "view": "home",
    "running": False,
    "progress": 0.0,
    "games_completed": 0,
    "total_games": 0,
    "start_time": None,
    "error": None,
    "results": None,
    "agents": None,
    "leaderboard": None,
    "marginals": None,
    "synergies": None,
    "interpretation": None,
    "report_md": None,
    "config_snapshot": None,
    "duration_seconds": None,
    "sample_game_moves": None,
    "sample_game_white": "White",
    "sample_game_black": "Black",
    "sample_game_result": "",
    "play_fen": chess.STARTING_FEN,
    "play_moves": [],
    "play_status": "ongoing",
    "play_winner": None,
    "play_last_move": None,
    "play_exploded_squares": None,
    "play_flipped": False,
    "live_feed": [],
    "custom_variant_description": "",
    "custom_variant_code": None,
    "custom_variant_status": None,
    "custom_variant_error": None,
    "custom_variant_name": None,
}
