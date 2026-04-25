"""
Chess board rendering utilities for the EngineLab Streamlit UI.

Public functions:
  chess_game_viewer — interactive game replay (chessboard.js, server-side FEN)
  chess_play_dnd   — drag-and-drop play board (chessboard.js, server-side logic)
  chess_play_board — static SVG position viewer (python-chess)
"""
from __future__ import annotations

import html as _html_mod
import json

import streamlit as st
import streamlit.components.v1 as components

# Piece images — chessboard.js Wikipedia set from the library's own CDN.
# The {piece} literal stays in the JS string; __PIECE_THEME__ is the Python placeholder.
_PIECE_THEME_URL = "https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png"

# ---------------------------------------------------------------------------
# Game Viewer (replay)
# ---------------------------------------------------------------------------

_VIEWER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script src="https://code.jquery.com/jquery-3.7.1.min.js" crossorigin="anonymous"></script>
<link  rel="stylesheet"
       href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css"
       crossorigin="anonymous">
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"
        crossorigin="anonymous"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #161512;
    color: #bababa;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 6px 4px 4px;
  }

  .board-wrap { width: 460px; }

  #board { width: 460px; }

  .player-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 2px;
    font-weight: 600;
    width: 460px;
  }
  .pip {
    width: 13px; height: 13px; border-radius: 50%; flex-shrink: 0;
  }
  .pip-white { background: #f0d9b5; border: 1px solid #aaa; }
  .pip-black { background: #272727; border: 1px solid #555; }
  .player-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .board-b72b1 {
    border: 2px solid #3a3a38 !important;
    border-radius: 3px;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 0 6px;
    width: 460px;
  }
  .ctrl-btn {
    background: #272522;
    border: 1px solid #3a3a38;
    color: #bababa;
    width: 32px; height: 32px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.12s;
    flex-shrink: 0;
  }
  .ctrl-btn:hover { background: #3a3a38; }
  .ctrl-btn:disabled { opacity: 0.35; cursor: default; }
  .move-indicator {
    flex: 1; text-align: center;
    color: #8b8580; font-size: 12px;
  }

  .movelist-card {
    background: #272522;
    border: 1px solid #3a3a38;
    border-radius: 6px;
    padding: 8px 12px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 12.5px;
    line-height: 1.9;
    max-height: 110px;
    width: 460px;
  }

  .move-pair { display: flex; align-items: baseline; gap: 2px; }
  .move-num  { color: #6a7068; min-width: 26px; flex-shrink: 0; }
  .mv {
    background: none; border: none;
    color: #bababa; cursor: pointer;
    padding: 1px 5px; border-radius: 3px;
    font-family: inherit; font-size: inherit;
    min-width: 52px;
  }
  .mv:hover  { background: #3a3a38; }
  .mv.active { background: #629924; color: #fff; font-weight: 700; }

  .result-badge {
    display: inline-block;
    background: #272522;
    border: 1px solid #3a3a38;
    border-radius: 4px;
    padding: 1px 7px;
    font-size: 12px;
    margin-top: 4px;
    color: #bababa;
  }
</style>
</head>
<body>

  <div class="player-row">
    <span class="pip pip-black"></span>
    <span class="player-name" id="black-name">Black</span>
  </div>

  <div class="board-wrap">
    <div id="board"></div>
  </div>

  <div class="player-row">
    <span class="pip pip-white"></span>
    <span class="player-name" id="white-name">White</span>
  </div>

  <div class="controls">
    <button class="ctrl-btn" id="btn-first" title="First"    onclick="goFirst()">&#9664;&#9664;</button>
    <button class="ctrl-btn" id="btn-prev"  title="Previous" onclick="goPrev()">&#9664;</button>
    <span   class="move-indicator" id="indicator">Start</span>
    <button class="ctrl-btn" id="btn-next"  title="Next"     onclick="goNext()">&#9654;</button>
    <button class="ctrl-btn" id="btn-last"  title="Last"     onclick="goLast()">&#9654;&#9654;</button>
  </div>

  <div class="movelist-card" id="movelist"></div>
</div>

<script>
// ── Data injected by Python ──────────────────────────────────────────────────
var UCI_MOVES  = __UCI_MOVES__;
var WHITE_NAME = "__WHITE_NAME__";
var BLACK_NAME = "__BLACK_NAME__";
var RESULT     = "__RESULT__";
var FENS       = __FENS__;       // Pre-computed by Python (variant-aware)
var SAN_MOVES  = __SAN_MOVES__;  // Pre-computed by Python

// ── Init ─────────────────────────────────────────────────────────────────────
document.getElementById('white-name').textContent = WHITE_NAME;
document.getElementById('black-name').textContent = BLACK_NAME;

var fens     = FENS;
var sanMoves = SAN_MOVES;

var cursor = 0;

// ── Board ────────────────────────────────────────────────────────────────────
var board = Chessboard('board', {
  position: 'start',
  pieceTheme: '__PIECE_THEME__',
  boardWidth: 460,
  showNotation: true,
  draggable: false,
});

// ── Move list HTML ───────────────────────────────────────────────────────────
(function buildMoveList() {
  var html = '';
  for (var i = 0; i < sanMoves.length; i++) {
    if (i % 2 === 0) {
      if (i) html += '</div>';
      html += '<div class="move-pair"><span class="move-num">' + (i/2+1|0) + '.</span>';
    }
    html += '<button class="mv" data-idx="'+(i+1)+'" onclick="jumpTo('+(i+1)+')">'
          + sanMoves[i] + '</button>';
  }
  if (sanMoves.length) { html += '</div>'; }
  if (RESULT) html += '<div><span class="result-badge">' + RESULT + '</span></div>';
  document.getElementById('movelist').innerHTML = html ||
    '<span style="color:#6a7068">No moves recorded</span>';
})();

// ── Navigation ───────────────────────────────────────────────────────────────
function updateUI() {
  board.position(fens[cursor], true);

  var ind = document.getElementById('indicator');
  if      (cursor === 0)             ind.textContent = 'Start';
  else if (cursor === fens.length-1) ind.textContent = 'End · move ' + cursor;
  else {
    var n    = Math.ceil(cursor / 2);
    var side = cursor % 2 === 1 ? 'White' : 'Black';
    ind.textContent = 'Move ' + n + ' · ' + side;
  }


  document.querySelectorAll('.mv').forEach(function(b) {
    b.classList.toggle('active', parseInt(b.dataset.idx) === cursor);
  });
  var active = document.querySelector('.mv.active');
  if (active) active.scrollIntoView({ block: 'nearest', behavior: 'smooth' });

  document.getElementById('btn-first').disabled = cursor === 0;
  document.getElementById('btn-prev').disabled  = cursor === 0;
  document.getElementById('btn-next').disabled  = cursor >= fens.length-1;
  document.getElementById('btn-last').disabled  = cursor >= fens.length-1;
}

function goFirst()  { cursor = 0;             updateUI(); }
function goLast()   { cursor = fens.length-1; updateUI(); }
function goNext()   { if (cursor < fens.length-1) { cursor++; updateUI(); } }
function goPrev()   { if (cursor > 0)             { cursor--; updateUI(); } }
function jumpTo(i)  { cursor = i;             updateUI(); }

document.addEventListener('keydown', function(e) {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown')  { goNext();  e.preventDefault(); }
  if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')    { goPrev();  e.preventDefault(); }
  if (e.key === 'Home')                                  { goFirst(); e.preventDefault(); }
  if (e.key === 'End')                                   { goLast();  e.preventDefault(); }
});

$(window).resize(function() { board.resize(); });

updateUI();
</script>
</body>
</html>
"""


def chess_game_viewer(
    moves: list[str],
    white_name: str = "White",
    black_name: str = "Black",
    result: str = "",
    board_size: int = 380,
    height: int = 560,
    variant: str = "standard",
) -> None:
    """Render an interactive chess game replay viewer inside a Streamlit app.

    Pre-computes FEN positions using the real variant engine so that
    atomic explosions, antichess captures, etc. are displayed correctly.

    Args:
        moves:       List of UCI move strings, e.g. ["e2e4", "e7e5", ...].
        white_name:  Display name for the white player.
        black_name:  Display name for the black player.
        result:      Short result string shown at the end of the move list, e.g. "1-0".
        board_size:  Unused (board is now responsive); kept for API compatibility.
        height:      Component iframe height in pixels.
        variant:     Chess variant for correct move application.
    """
    fens, san_moves = _precompute_replay_positions(moves, variant)

    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    html = (
        _VIEWER_TEMPLATE
        .replace("__UCI_MOVES__",   json.dumps(moves))
        .replace("__FENS__",        json.dumps(fens))
        .replace("__SAN_MOVES__",   json.dumps(san_moves))
        .replace("__WHITE_NAME__",  _esc(white_name))
        .replace("__BLACK_NAME__",  _esc(black_name))
        .replace("__RESULT__",      _esc(result))
        .replace("__PIECE_THEME__", _PIECE_THEME_URL)
    )
    components.html(html, height=height, scrolling=False)


def _precompute_replay_positions(
    uci_moves: list[str], variant: str,
) -> tuple[list[str], list[str]]:
    """Compute FEN positions and SAN labels for each move using the real engine.

    Returns (fens, san_labels) where fens[0] is the starting position and
    fens[i+1] is the position after uci_moves[i].
    """
    from core.board import Board
    from core.move import Move
    from core.coordinates import algebraic_to_square
    from variants.base import get_apply_move, get_generate_legal_moves

    board = Board.starting_position()
    apply_fn = get_apply_move(variant)
    gen_legal_fn = get_generate_legal_moves(variant)

    fens = [board.to_fen()]
    san_labels = []

    for uci in uci_moves:
        # Parse UCI
        start = algebraic_to_square(uci[0:2])
        end = algebraic_to_square(uci[2:4])
        promo = None
        if len(uci) > 4:
            promo = uci[4].upper() if board.side_to_move == "w" else uci[4].lower()
        candidate = Move(start=start, end=end, promotion=promo)

        # Find matching legal move
        legal = gen_legal_fn(board)
        matched = None
        for m in legal:
            if m.start == candidate.start and m.end == candidate.end:
                if candidate.promotion is None or m.promotion == candidate.promotion:
                    matched = m
                    break

        if matched is None:
            # Move not legal in this variant — stop replay here
            break

        # Build a simple SAN-like label: piece + target (good enough for display)
        san = _build_move_label(board, matched, uci)
        san_labels.append(san)

        board = apply_fn(board, matched)
        fens.append(board.to_fen())

        if board.is_terminal():
            break

    return fens, san_labels


def _build_move_label(board, move, uci: str) -> str:
    """Build a human-readable move label from a Move object.

    Not full SAN, but good enough for the replay move list.
    """
    from core.coordinates import square_to_algebraic

    piece = board.get_piece(move.start)
    target_sq = square_to_algebraic(move.end[0], move.end[1])
    is_capture = board.get_piece(move.end) is not None

    if piece and piece.upper() == "K":
        # Detect castling
        if abs(move.start[1] - move.end[1]) == 2:
            return "O-O" if move.end[1] > move.start[1] else "O-O-O"

    piece_letter = ""
    if piece and piece.upper() != "P":
        piece_letter = piece.upper()

    source_file = chr(ord("a") + move.start[1])
    cap = "x" if is_capture else ""

    # For pawn captures, include source file
    if not piece_letter and is_capture:
        piece_letter = source_file
        label = f"{piece_letter}{cap}{target_sq}"
    else:
        label = f"{piece_letter}{cap}{target_sq}"

    if move.promotion:
        label += f"={move.promotion.upper()}"

    return label


# ---------------------------------------------------------------------------
# Drag-and-drop play board (components.html + query param communication)
# ---------------------------------------------------------------------------

_DND_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script src="https://code.jquery.com/jquery-3.7.1.min.js" crossorigin="anonymous"></script>
<link rel="stylesheet"
      href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css"
      crossorigin="anonymous">
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"
        crossorigin="anonymous"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #161512;
  display: flex; flex-direction: column; align-items: center;
  padding: 4px 0 0;
}
#board { width: 460px; cursor: pointer; }
.board-b72b1 { border: 2px solid #2c2b29 !important; border-radius: 2px; }

/* Legal move dots */
.highlight-legal {
  background: radial-gradient(circle, rgba(98,153,36,0.45) 24%, transparent 25%) !important;
}
.highlight-capture {
  background: radial-gradient(circle, transparent 50%, rgba(98,153,36,0.45) 51%) !important;
}
/* Last move highlight */
.highlight-lastmove {
  background-color: rgba(155, 199, 0, 0.35) !important;
}
/* Selected piece */
.highlight-selected {
  background-color: rgba(98, 153, 36, 0.55) !important;
}
/* Atomic explosion highlight */
.highlight-explosion {
  background-color: rgba(255, 107, 53, 0.45) !important;
}

/* Promotion modal */
#promo-modal {
  display:none; position:fixed; inset:0;
  background:rgba(0,0,0,0.7); z-index:999;
  justify-content:center; align-items:center;
}
#promo-modal.show { display:flex; }
.promo-opts {
  background:#272522; border:1px solid #3a3a38;
  border-radius:8px; padding:16px 20px; display:flex; gap:10px;
}
.promo-btn {
  width:56px; height:56px; background:#1f1e1c;
  border:1px solid #3a3a38; border-radius:5px;
  cursor:pointer; font-size:32px;
  display:flex; align-items:center; justify-content:center; color:#d0cfc8;
}
.promo-btn:hover { background:#3a3a38; }
</style>
</head>
<body>

<div id="promo-modal">
  <div class="promo-opts">
    <button class="promo-btn" onclick="doPromotion('q')">&#9819;</button>
    <button class="promo-btn" onclick="doPromotion('r')">&#9820;</button>
    <button class="promo-btn" onclick="doPromotion('b')">&#9821;</button>
    <button class="promo-btn" onclick="doPromotion('n')">&#9822;</button>
  </div>
</div>

<div id="board"></div>

<script>
var LEGAL_MOVES = __LEGAL_MOVES__;
var GAME_STATUS = "__STATUS__";
var LAST_MOVE_SQUARES = __LAST_MOVE_SQUARES__;
var EXPLODED_SQUARES = __EXPLODED_SQUARES__;
var pendingPromotion = null;
var selectedSquare = null;

// Build lookup: source -> [target, ...]
var legalTargets = {};
LEGAL_MOVES.forEach(function(uci) {
  var from = uci.substring(0,2), to = uci.substring(2,4);
  if (!legalTargets[from]) legalTargets[from] = [];
  legalTargets[from].push(to);
});

// Board — display only, no drag (drag doesn't work in Streamlit iframes)
var board = Chessboard('board', {
  position: '__FEN__',
  pieceTheme: '__PIECE_THEME__',
  draggable: false,
  onMouseoverSquare: function(sq) { if (!selectedSquare) onMouseover(sq); },
  onMouseoutSquare: function() { if (!selectedSquare) onMouseout(); },
});

// ── Click-to-move ───────────────────────────────────────────────────────────
document.getElementById('board').addEventListener('click', function(e) {
  if (GAME_STATUS !== 'ongoing') return;
  // Walk up from click target to find the square element
  var el = e.target;
  var square = null;
  while (el && el.id !== 'board') {
    if (el.className && typeof el.className === 'string') {
      var m = el.className.match(/square-([a-h][1-8])/);
      if (m) { square = m[1]; break; }
    }
    el = el.parentElement;
  }
  if (!square) return;

  var pos = board.position();
  var piece = pos[square];

  if (selectedSquare) {
    // ── A piece is already selected ──
    if (square === selectedSquare) {
      deselect(); return;                          // click same piece → deselect
    }
    if (legalTargets[selectedSquare] && legalTargets[selectedSquare].indexOf(square) !== -1) {
      // Legal target → make the move
      var srcPiece = pos[selectedSquare];
      if (srcPiece === 'wP' && square[1] === '8') {
        pendingPromotion = { from: selectedSquare, to: square };
        deselect();
        document.getElementById('promo-modal').classList.add('show');
        return;
      }
      var uci = selectedSquare + square;
      deselect();
      sendMove(uci);
      return;
    }
    // Click another own piece with moves → switch selection
    if (piece && piece[0] === 'w' && legalTargets[square] && legalTargets[square].length > 0) {
      deselect(); selectPiece(square); return;
    }
    deselect(); return;                            // click elsewhere → deselect
  }

  // ── No piece selected ──
  if (piece && piece[0] === 'w' && legalTargets[square] && legalTargets[square].length > 0) {
    selectPiece(square);
  }
});

function selectPiece(square) {
  selectedSquare = square;
  onMouseout(); // clear hover hints
  var el = document.querySelector('.square-' + square);
  if (el) el.classList.add('highlight-selected');
  var pos = board.position();
  (legalTargets[square] || []).forEach(function(t) {
    var e = document.querySelector('.square-' + t);
    if (e) e.classList.add(pos[t] ? 'highlight-capture' : 'highlight-legal');
  });
}

function deselect() {
  selectedSquare = null;
  document.querySelectorAll('.highlight-selected,.highlight-legal,.highlight-capture').forEach(function(e) {
    e.classList.remove('highlight-selected', 'highlight-legal', 'highlight-capture');
  });
}

// ── Promotion ───────────────────────────────────────────────────────────────
function doPromotion(p) {
  document.getElementById('promo-modal').classList.remove('show');
  if (!pendingPromotion) return;
  sendMove(pendingPromotion.from + pendingPromotion.to + p);
  pendingPromotion = null;
}

// ── Send move to Python via query params ────────────────────────────────────
function sendMove(uci) {
  try {
    var url = new URL(window.parent.location.href);
    url.searchParams.set('chess_move', uci);
    window.parent.location.href = url.toString();
  } catch(e) {
    window.top.location.search = '?chess_move=' + uci;
  }
}

// ── Hover hints (only when no piece is selected) ────────────────────────────
function onMouseover(square) {
  if (GAME_STATUS !== 'ongoing') return;
  var targets = legalTargets[square];
  if (!targets) return;
  var el = document.querySelector('.square-' + square);
  if (el) el.classList.add('highlight-legal');
  var pos = board.position();
  targets.forEach(function(t) {
    var e = document.querySelector('.square-' + t);
    if (!e) return;
    e.classList.add(pos[t] ? 'highlight-capture' : 'highlight-legal');
  });
}

function onMouseout() {
  document.querySelectorAll('.highlight-legal,.highlight-capture').forEach(function(e) {
    e.classList.remove('highlight-legal','highlight-capture');
  });
}

// ── Last-move and explosion highlights ──────────────────────────────────────
(function() {
  LAST_MOVE_SQUARES.forEach(function(sq) {
    var el = document.querySelector('.square-' + sq);
    if (el) el.classList.add('highlight-lastmove');
  });
  EXPLODED_SQUARES.forEach(function(sq) {
    var el = document.querySelector('.square-' + sq);
    if (el) el.classList.add('highlight-explosion');
  });
})();

$(window).resize(function() { board.resize(); });
</script>
</body>
</html>
"""


def chess_play_dnd(
    fen: str,
    legal_moves: list[str],
    status: str = "ongoing",
    last_move_uci: str | None = None,
    exploded_squares: list[str] | None = None,
    height: int = 520,
) -> None:
    """Render a drag-and-drop chess board for interactive play.

    Moves are communicated back to Streamlit via query params.
    All game logic stays server-side.
    """
    # Build last-move square pair from UCI (e.g. "e2e4" → ["e2","e4"])
    if last_move_uci and len(last_move_uci) >= 4:
        lm_squares = [last_move_uci[:2], last_move_uci[2:4]]
    else:
        lm_squares = []

    html = (
        _DND_TEMPLATE
        .replace("__FEN__", fen)
        .replace("__LEGAL_MOVES__", json.dumps(legal_moves))
        .replace("__STATUS__", status)
        .replace("__LAST_MOVE_SQUARES__", json.dumps(lm_squares))
        .replace("__EXPLODED_SQUARES__", json.dumps(exploded_squares or []))
        .replace("__PIECE_THEME__", _PIECE_THEME_URL)
    )
    components.html(html, height=height, scrolling=False)


# ---------------------------------------------------------------------------
# Static board (SVG via python-chess)
# ---------------------------------------------------------------------------

def chess_play_board(
    fen: str,
    last_move_uci: str | None = None,
    flipped: bool = False,
    size: int = 480,
) -> None:
    """Render current board position as SVG via st.image.

    Args:
        fen:           FEN string of the position to display.
        last_move_uci: Optional UCI string of the last move to highlight, e.g. "e2e4".
        flipped:       If True, render board from Black's perspective.
        size:          Square size in pixels passed to python-chess svg renderer.
    """
    from ui.board import render_board

    svg = render_board(fen, last_move_uci=last_move_uci, size=size, flipped=flipped)
    st.image(svg, use_container_width=True)
