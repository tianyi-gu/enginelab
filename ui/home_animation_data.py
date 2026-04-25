"""Pre-bake chess animation data for the home page background grid.

Loads precomputed tournament JSONs, picks decisive games biased toward
atomic + horde, and pre-computes the full FEN sequence for each game using
variant-aware Board + apply_fn (so atomic explosions, antichess captures,
etc. produce real positions).

Output is JSON-serializable list of dicts:
    [{"variant": "atomic", "fens": [...], "exploded": [null, ["e4","d5"], ...]}, ...]
"""

from __future__ import annotations

import json
import os
import random
from functools import lru_cache
from typing import Any

from core.board import Board
from variants.base import get_apply_move
from ui.play_engine import _parse_uci

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "outputs", "data")


def _starting_position(variant: str) -> Board:
    """Return the variant-correct starting position."""
    if variant == "horde":
        from variants.horde import horde_starting_position
        return horde_starting_position()
    if variant == "chess960":
        from variants.chess960 import chess960_starting_position
        return chess960_starting_position(seed=0)
    return Board.starting_position()


def _bake_game(variant: str, move_list: list[str]) -> dict[str, Any] | None:
    """Replay a game, returning {"fens": [...], "exploded": [null|[sqs]...]}."""
    try:
        board = _starting_position(variant)
        apply_fn = get_apply_move(variant)
    except Exception:
        return None

    fens = [board.to_fen()]
    exploded: list[list[str] | None] = [None]

    for uci in move_list:
        try:
            move = _parse_uci(uci, board.side_to_move)
            new_board = apply_fn(board, move)
        except Exception:
            break
        new_fen = new_board.to_fen()
        # Atomic explosion detection: dest square empty after move = explosion
        exp_squares = None
        if variant == "atomic" and len(uci) >= 4:
            import chess
            try:
                dest = chess.parse_square(uci[2:4])
                from ui.board import _strip_extended_fen
                old_b = chess.Board(_strip_extended_fen(fens[-1]))
                new_b = chess.Board(_strip_extended_fen(new_fen))
                if (old_b.piece_at(dest) is not None
                        and new_b.piece_at(dest) is None):
                    exp_squares = [
                        chess.square_name(sq) for sq in chess.SQUARES
                        if old_b.piece_at(sq) is not None
                        and new_b.piece_at(sq) is None
                    ]
            except Exception:
                pass
        fens.append(new_fen)
        exploded.append(exp_squares)
        board = new_board

    if len(fens) < 6:
        return None
    return {"variant": variant, "fens": fens, "exploded": exploded}


@lru_cache(maxsize=1)
def bake_animation_payload(target_count: int = 18) -> str:
    """Build the JSON payload for the home-page board grid.

    Mix: ~1/3 atomic, ~1/3 horde, ~1/3 mixed (standard/antichess/koth/threecheck/chess960).
    Returns a JSON string ready to inject into the iframe template.
    """
    rng = random.Random(42)

    def _decisive_games(variant: str, max_games: int) -> list[list[str]]:
        path = os.path.join(_DATA_DIR, f"tournament_results_{variant}.json")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            data = json.load(f)
        decisive = [g for g in data
                    if g.get("winner") is not None and g.get("move_list")]
        rng.shuffle(decisive)
        # Prefer games with at least 12 moves so animation lasts long enough
        decisive = [g for g in decisive if len(g["move_list"]) >= 12]
        return [g["move_list"] for g in decisive[:max_games]]

    # Roughly even thirds: 1/3 atomic, 1/3 horde, 1/3 mixed
    n_atomic_target = target_count // 3
    n_horde_target = target_count // 3
    n_mixed_target = target_count - n_atomic_target - n_horde_target

    atomic_games = _decisive_games("atomic", n_atomic_target + 4)
    horde_games = _decisive_games("horde", n_horde_target + 4)
    mixed_pools = []
    for v in ("standard", "antichess", "kingofthehill", "threecheck", "chess960"):
        mixed_pools.append((v, _decisive_games(v, max(2, n_mixed_target // 4))))

    boards: list[dict[str, Any]] = []

    n_atomic = min(n_atomic_target, len(atomic_games))
    n_horde = min(n_horde_target, len(horde_games))

    for moves in atomic_games[:n_atomic]:
        baked = _bake_game("atomic", moves)
        if baked:
            boards.append(baked)
    for moves in horde_games[:n_horde]:
        baked = _bake_game("horde", moves)
        if baked:
            boards.append(baked)

    # Round-robin through mixed variants
    mixed_added = 0
    while mixed_added < n_mixed_target:
        progressed = False
        for variant, moves_pool in mixed_pools:
            if mixed_added >= n_mixed_target:
                break
            if moves_pool:
                moves = moves_pool.pop(0)
                baked = _bake_game(variant, moves)
                if baked:
                    boards.append(baked)
                    mixed_added += 1
                    progressed = True
        if not progressed:
            break

    # Top up with extra atomic games if we're short
    while len(boards) < target_count and atomic_games[n_atomic:]:
        moves = atomic_games[n_atomic]
        n_atomic += 1
        baked = _bake_game("atomic", moves)
        if baked:
            boards.append(baked)

    rng.shuffle(boards)
    return json.dumps(boards[:target_count], separators=(",", ":"))
