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
    "variant": "standard",
    "selected_features": list(ALL_FEATURES),
    "depth": 2,
    "view": "build",
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
    "play_flipped": False,
}
