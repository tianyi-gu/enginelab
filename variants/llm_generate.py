"""LLM-based variant code generation via OpenAI API."""
from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o"

_SYSTEM_PROMPT = """You are a chess variant code generator. You must produce exactly two Python functions that define a chess variant.

## Contract
You must define these two functions with EXACTLY these names:

```python
def apply_customvariant_move(board: Board, move: Move) -> Board:
    # Apply move under custom variant rules. Returns new Board (never mutate the input).

def generate_customvariant_moves(board: Board) -> list[Move]:
    # Return list of legal moves for board.side_to_move under custom variant rules.
```

## Available imports (use ONLY these)
```python
from core.board import Board
from core.move import Move
from core.apply_move import apply_move          # standard move application, returns new Board
from core.move_generation import generate_moves  # pseudo-legal moves (not filtered for check)
from core.move_generation import generate_legal_moves  # legal moves (filtered for check)
from core.move_generation import is_in_check     # is_in_check(board, color) -> bool
from core.move_generation import is_square_attacked  # is_square_attacked(board, square, by_color) -> bool
from core.types import piece_color, piece_type, opponent_color
from core.coordinates import algebraic_to_square, square_to_algebraic
```

## Board API
- board.copy() -> Board          # deep copy, ALWAYS copy before mutating
- board.get_piece((row, col)) -> str | None  # e.g. "P", "k", None
- board.set_piece((row, col), piece_or_none)
- board.find_king(color) -> (row, col) | None
- board.grid                     # 8x8 list[list[str|None]], row 0 = rank 1 (white's back rank)
- board.side_to_move             # "w" or "b"
- board.winner                   # set to "w" or "b" for terminal states, None otherwise
- board.castling_rights          # dict {"K": bool, "Q": bool, "k": bool, "q": bool}
- board.en_passant_square        # (row, col) | None
- board.move_count               # int, total plies played

## Move API
- Move(start=(row,col), end=(row,col), promotion=None)  # frozen dataclass
- move.start, move.end -> (row, col) tuples
- move.promotion -> str | None  # "Q","R","B","N" for white, "q","r","b","n" for black

## Types API
- piece_color(piece) -> "w" or "b"   # e.g. piece_color("P") -> "w", piece_color("n") -> "b"
- piece_type(piece) -> str            # uppercase: piece_type("p") -> "P"
- opponent_color("w") -> "b", opponent_color("b") -> "w"

## Coordinate system
- Row 0 = rank 1 (white's back rank), Row 7 = rank 8 (black's back rank)
- Col 0 = file a, Col 7 = file h

## CRITICAL rules for apply_customvariant_move:
1. ALWAYS call board.copy() first and work on the copy. Never mutate the input.
2. After applying the move, you MUST set:
   - new_board.side_to_move = opponent_color(board.side_to_move)
   - new_board.move_count = board.move_count + 1
3. Set new_board.winner = "w" or "b" if someone wins under your variant's rules.
4. You can delegate standard move mechanics to apply_move(board, move) which handles
   piece placement, castling, en passant, promotion, side toggle, and move_count for you.
   Then add your variant-specific logic on top of the returned board.

## CRITICAL rules for generate_customvariant_moves:
1. NEVER mutate the input board. If you need to modify the board, call board.copy() first.
2. Start from generate_legal_moves(board) for standard-legal moves, or generate_moves(board)
   for pseudo-legal moves if you need to add custom filtering.
3. Filter or augment as needed for your variant rules.
4. Return a list[Move]. Return empty list if no moves available.
5. If pieces change type (e.g. queens become knights), implement this in apply_customvariant_move
   by modifying the copied board AFTER the move, NOT in generate_customvariant_moves.

## Optional: setup_customvariant_board
If your variant changes the starting position (e.g. replacing pieces, removing pieces, adding pieces),
you MUST also define:

```python
def setup_customvariant_board(board: Board) -> Board:
    # Modify the starting position for your variant. Returns new Board (never mutate input).
```

This receives a standard starting position Board and returns the modified starting board.
For example, if queens become knights, this function should replace both queens with knights
on the starting board so the game begins with the correct pieces.
If your variant uses the standard starting position unchanged, you may omit this function.

## Complete example: Antichess (forced captures, lose all pieces to win)

```python
from core.board import Board
from core.move import Move
from core.apply_move import apply_move
from core.move_generation import generate_moves
from core.types import piece_color

def apply_customvariant_move(board: Board, move: Move) -> Board:
    new_board = apply_move(board, move)
    # Check if either side lost all pieces (= that side wins in antichess)
    for color in ("w", "b"):
        has_pieces = False
        for r in range(8):
            for c in range(8):
                p = new_board.get_piece((r, c))
                if p is not None and piece_color(p) == color:
                    has_pieces = True
                    break
            if has_pieces:
                break
        if not has_pieces:
            new_board.winner = color  # losing all pieces = winning
            break
    return new_board

def generate_customvariant_moves(board: Board) -> list[Move]:
    all_moves = generate_moves(board)
    captures = [m for m in all_moves if board.get_piece(m.end) is not None]
    return captures if captures else all_moves  # forced capture rule
```

## Output format
Return ONLY the Python code. No markdown fences, no explanations, no comments outside the code.
Start with the import statements, then the two functions.
"""


def generate_variant_code(
    description: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    timeout_seconds: int = 120,
) -> dict[str, str | None]:
    """Call OpenAI API to generate variant code from a natural language description.

    Requires OPENAI_API_KEY environment variable to be set.

    Returns:
        {"code": str, "error": str | None}
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"code": "", "error": "OPENAI_API_KEY environment variable is not set."}
    try:
        raw = _call_openai(
            prompt=description,
            system=_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
            timeout=timeout_seconds,
            api_key=api_key,
        )
        code = _extract_code(raw)
        return {"code": code, "error": None}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        return {"code": "", "error": f"OpenAI API error {exc.code}: {body[:200]}"}
    except urllib.error.URLError as exc:
        return {"code": "", "error": f"Cannot connect to OpenAI API: {exc.reason}"}
    except Exception as exc:
        return {"code": "", "error": str(exc)}


def _call_openai(
    prompt: str,
    system: str,
    model: str,
    temperature: float,
    timeout: int,
    api_key: str,
) -> str:
    """POST to OpenAI chat completions and return the assistant message."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }).encode()

    req = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode())
    return body["choices"][0]["message"]["content"]


def _extract_code(raw: str) -> str:
    """Strip markdown fences if present and return pure Python code."""
    # Remove ```python ... ``` wrappers
    cleaned = re.sub(r"^```(?:python)?\s*\n", "", raw.strip())
    cleaned = re.sub(r"\n```\s*$", "", cleaned)
    return cleaned.strip()
