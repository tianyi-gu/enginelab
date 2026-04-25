"""
Chess board rendering utilities for the EngineLab Streamlit UI.

Public functions:
  chess_game_viewer — interactive game replay (chessboard.js, server-side FEN)
  chess_play_dnd   — drag-and-drop play board (pointer events, server-side logic)
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
# Drag-and-drop play board — custom pointer-event implementation
#
# Uses setPointerCapture so drag works correctly inside Streamlit iframes.
# The browser delivers pointermove/pointerup to the capturing element even
# when the pointer exits the iframe boundary — this is how Lichess's
# chessground library implements drag.  No jQuery / chessboard.js needed.
# ---------------------------------------------------------------------------

_DND_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  background:#161512;
  display:flex;flex-direction:column;align-items:center;
  padding:4px 0 0;
  -webkit-user-select:none;user-select:none;
  overflow:hidden;
}
#wrap{position:relative}
/* squares */
.sq{position:absolute}
.sq-l{background:#f0d9b5}
.sq-d{background:#b58863}
/* pieces */
.piece{position:absolute;touch-action:none;cursor:grab;z-index:2}
.piece.no-moves{cursor:default}
/* persistent highlights sit below pieces */
.hl{position:absolute;pointer-events:none;z-index:1}
.hl-lm {background:rgba(155,199,0,.41)}
.hl-sel{background:rgba(20,85,30,.5)}
.hl-exp{background:rgba(255,107,53,.5)}
/* legal-move dots sit above pieces */
.dot{position:absolute;pointer-events:none;z-index:4}
/* ghost follows cursor at viewport coords so it escapes the iframe clip */
#ghost{position:fixed;pointer-events:none;z-index:9999;display:none}
/* coordinate labels */
.lbl{position:absolute;font-size:10px;font-weight:700;pointer-events:none;z-index:5;line-height:1}
/* promotion modal */
#promo{
  display:none;position:fixed;inset:0;
  background:rgba(0,0,0,.78);z-index:10000;
  justify-content:center;align-items:center;
}
#promo.on{display:flex}
.pb{
  width:60px;height:60px;background:#1f1e1c;
  border:1px solid #3a3a38;border-radius:6px;
  cursor:pointer;font-size:34px;
  display:flex;align-items:center;justify-content:center;color:#d0cfc8;padding:0;
}
.pb:hover{background:#3a3a38}
</style>
</head>
<body>

<div id="promo">
  <div style="background:#272522;border:1px solid #3a3a38;border-radius:8px;padding:16px;display:flex;gap:12px">
    <button class="pb" onclick="doPromo('q')">&#9813;</button>
    <button class="pb" onclick="doPromo('r')">&#9814;</button>
    <button class="pb" onclick="doPromo('b')">&#9815;</button>
    <button class="pb" onclick="doPromo('n')">&#9816;</button>
  </div>
</div>

<div id="wrap"></div>
<img id="ghost" alt="">

<script>
// ── Injected by Python ────────────────────────────────────────────────────────
var FEN    = '__FEN__';
var LEGAL  = __LEGAL_MOVES__;
var STATUS = '__STATUS__';
var LM     = __LAST_MOVE_SQUARES__;
var EXP    = __EXPLODED_SQUARES__;
var PT     = '__PIECE_THEME__';
var BS     = __BOARD_SIZE__;

var SQ    = BS / 8;
var wrap  = document.getElementById('wrap');
var ghost = document.getElementById('ghost');

wrap.style.cssText  = 'position:relative;width:'+BS+'px;height:'+BS+'px;border:2px solid #2c2b29;border-radius:2px';
ghost.style.cssText = 'width:'+SQ+'px;height:'+SQ+'px';

// ── FEN parser ────────────────────────────────────────────────────────────────
function parseFEN(fen) {
  var ranks = fen.split(' ')[0].split('/'), pos = {};
  for (var r = 0; r < 8; r++) {
    var col = 0;
    for (var i = 0; i < ranks[r].length; i++) {
      var ch = ranks[r][i];
      if (ch >= '1' && ch <= '8') { col += +ch; }
      else {
        pos[String.fromCharCode(97+col)+(8-r)] =
          (ch === ch.toUpperCase() ? 'w' : 'b') + ch.toUpperCase();
        col++;
      }
    }
  }
  return pos;
}

// ── Coordinate helpers ────────────────────────────────────────────────────────
function sqXY(sq) {
  return { x: (sq.charCodeAt(0)-97)*SQ, y: (8-+sq[1])*SQ };
}
function xySq(x, y) {
  var c = Math.floor(x/SQ), r = Math.floor(y/SQ);
  return (c>=0&&c<8&&r>=0&&r<8) ? String.fromCharCode(97+c)+(8-r) : null;
}
function pimg(code) { return PT.replace('{piece}', code); }

// ── Legal-move map ────────────────────────────────────────────────────────────
var lmap = {};
LEGAL.forEach(function(u) {
  var f = u.slice(0,2), t = u.slice(2,4);
  if (!lmap[f]) lmap[f] = [];
  lmap[f].push(t);
});

// ── Build 64 squares ──────────────────────────────────────────────────────────
for (var r = 0; r < 8; r++) {
  for (var c = 0; c < 8; c++) {
    var sq = String.fromCharCode(97+c)+(8-r);
    var d  = document.createElement('div');
    d.className    = 'sq ' + ((r+c)%2 ? 'sq-d' : 'sq-l');
    d.style.cssText = 'left:'+c*SQ+'px;top:'+r*SQ+'px;width:'+SQ+'px;height:'+SQ+'px';
    d.dataset.sq   = sq;
    if (r === 7) {
      var fl = document.createElement('span');
      fl.className='lbl'; fl.textContent=sq[0];
      fl.style.cssText='bottom:2px;right:3px;color:'+((r+c)%2?'#f0d9b5':'#b58863');
      d.appendChild(fl);
    }
    if (c === 0) {
      var rl = document.createElement('span');
      rl.className='lbl'; rl.textContent=8-r;
      rl.style.cssText='top:2px;left:3px;color:'+((r+c)%2?'#f0d9b5':'#b58863');
      d.appendChild(rl);
    }
    wrap.appendChild(d);
  }
}

// ── Render pieces ─────────────────────────────────────────────────────────────
var pos = parseFEN(FEN), pels = {};
function renderPieces() {
  Object.values(pels).forEach(function(e){ e.remove(); }); pels = {};
  Object.keys(pos).forEach(function(sq) {
    var code = pos[sq], xy = sqXY(sq);
    var p = document.createElement('img');
    p.src = pimg(code); p.alt = code; p.draggable = false;
    p.dataset.sq = sq; p.dataset.code = code;
    var canMove = STATUS==='ongoing' && code[0]==='w' && lmap[sq] && lmap[sq].length;
    p.className = 'piece' + (canMove ? '' : ' no-moves');
    p.style.cssText = 'left:'+xy.x+'px;top:'+xy.y+'px;width:'+SQ+'px;height:'+SQ+'px';
    wrap.appendChild(p); pels[sq] = p;
  });
}
renderPieces();

// ── Persistent highlights ────────────────────────────────────────────────────
function addHL(sq, cls) {
  var xy = sqXY(sq), e = document.createElement('div');
  e.className = 'hl ' + cls;
  e.style.cssText = 'left:'+xy.x+'px;top:'+xy.y+'px;width:'+SQ+'px;height:'+SQ+'px';
  wrap.appendChild(e); return e;
}
LM.forEach(function(s)  { addHL(s, 'hl-lm');  });
EXP.forEach(function(s) { addHL(s, 'hl-exp'); });

// ── Selection + legal-move dots ───────────────────────────────────────────────
var dotEls = [], selEl = null;
function showDots(from) {
  clearSel();
  selEl = addHL(from, 'hl-sel');
  (lmap[from]||[]).forEach(function(to) {
    var xy  = sqXY(to);
    var dot = document.createElement('div');
    dot.className = 'dot';
    dot.style.cssText = 'left:'+xy.x+'px;top:'+xy.y+'px;width:'+SQ+'px;height:'+SQ+'px';
    var t = Math.round(SQ*.09);
    if (pos[to]) {
      // ring around occupied square
      dot.innerHTML = '<div style="width:100%;height:100%;border-radius:50%;border:'+t+'px solid rgba(20,85,30,.5);box-sizing:border-box"></div>';
    } else {
      // filled circle on empty square
      var ds = Math.round(SQ*.28), off = Math.round((SQ-ds)/2);
      dot.innerHTML = '<div style="position:absolute;width:'+ds+'px;height:'+ds+'px;top:'+off+'px;left:'+off+'px;background:rgba(20,85,30,.5);border-radius:50%"></div>';
    }
    wrap.appendChild(dot); dotEls.push(dot);
  });
}
function clearSel() {
  dotEls.forEach(function(d){ d.remove(); }); dotEls = [];
  if (selEl) { selEl.remove(); selEl = null; }
}

// ── Promotion ─────────────────────────────────────────────────────────────────
var pendingPromo = null;
function tryMove(from, to, code) {
  if (code === 'wP' && to[1] === '8') {
    pendingPromo = {from:from, to:to};
    document.getElementById('promo').classList.add('on');
    return;
  }
  sendMove(from+to);
}
function doPromo(p) {
  document.getElementById('promo').classList.remove('on');
  if (pendingPromo) { sendMove(pendingPromo.from+pendingPromo.to+p); pendingPromo = null; }
}

// ── Move → Streamlit via URL query param ──────────────────────────────────────
function sendMove(uci) {
  try {
    var url = new URL(window.parent.location.href);
    url.searchParams.set('chess_move', uci);
    window.parent.location.href = url.toString();
  } catch(e) {
    window.top.location.search = '?chess_move=' + uci;
  }
}

// ── DRAG — threshold-based, does NOT prevent click on tap ────────────────────
//
// Key insight: e.preventDefault() on pointerdown kills the subsequent click
// event.  We defer preventDefault until the pointer has actually moved (drag
// threshold), so a simple tap always falls through to the click handler below.
//
var drag = null;          // set only after threshold crossed
var dragCandidate = null; // set on pointerdown, cleared on pointerup/cancel
var dragDone = false;     // flag: suppress click after a completed drag-move

wrap.addEventListener('pointerdown', function(e) {
  if (STATUS !== 'ongoing') return;
  var el = e.target;
  while (el && el !== wrap && !(el.tagName === 'IMG' && el.dataset.sq))
    el = el.parentElement;
  if (!el || el === wrap) return;
  var sq = el.dataset.sq, code = el.dataset.code;
  if (!code || code[0] !== 'w' || !lmap[sq] || !lmap[sq].length) return;

  // NO e.preventDefault() here — click must be allowed to fire on a tap
  el.setPointerCapture(e.pointerId);
  dragCandidate = {sq:sq, code:code, el:el, x0:e.clientX, y0:e.clientY};
  ghost.src = pimg(code);  // pre-load image
});

wrap.addEventListener('pointermove', function(e) {
  if (!dragCandidate) return;
  var dx = e.clientX - dragCandidate.x0, dy = e.clientY - dragCandidate.y0;
  if (!drag && dx*dx + dy*dy > 64) {   // 8 px threshold
    // Threshold crossed — promote candidate to active drag
    drag = dragCandidate;
    e.preventDefault();                // NOW prevent scroll / click
    clearSel(); selected = null;
    showDots(drag.sq);
    drag.el.style.opacity = '.25';
    ghost.style.cssText = (
      'position:fixed;pointer-events:none;z-index:9999;display:block;' +
      'width:'+SQ+'px;height:'+SQ+'px;' +
      'left:'+(e.clientX-SQ/2)+'px;top:'+(e.clientY-SQ/2)+'px'
    );
  }
  if (drag) {
    ghost.style.left = (e.clientX-SQ/2)+'px';
    ghost.style.top  = (e.clientY-SQ/2)+'px';
  }
}, {passive:false});

wrap.addEventListener('pointerup', function(e) {
  if (!dragCandidate) return;
  var cand = dragCandidate;
  dragCandidate = null;
  if (!drag) return;   // was just a tap — let click handler deal with it

  ghost.style.display = 'none';
  drag.el.style.opacity = '';
  var rect = wrap.getBoundingClientRect();
  var to   = xySq(e.clientX-rect.left, e.clientY-rect.top);
  var from = drag.sq, code = drag.code;
  clearSel(); drag = null;
  if (to && lmap[from] && lmap[from].indexOf(to) !== -1) {
    dragDone = true;    // tell click handler to skip this event
    tryMove(from, to, code);
  }
});

wrap.addEventListener('pointercancel', function() {
  dragCandidate = null;
  if (!drag) return;
  ghost.style.display = 'none';
  drag.el.style.opacity = '';
  clearSel(); drag = null;
});

// ── CLICK-TO-MOVE ─────────────────────────────────────────────────────────────
var selected = null;

wrap.addEventListener('click', function(e) {
  if (STATUS !== 'ongoing') return;
  if (dragDone) { dragDone = false; return; }  // was a drag, not a click
  var rect = wrap.getBoundingClientRect();
  var sq   = xySq(e.clientX-rect.left, e.clientY-rect.top);
  if (!sq) return;

  if (selected) {
    var prev = selected;
    if (prev === sq) { clearSel(); selected = null; return; }
    if (lmap[prev] && lmap[prev].indexOf(sq) !== -1) {
      var code = pos[prev]; clearSel(); selected = null;
      tryMove(prev, sq, code); return;
    }
    clearSel(); selected = null;
    // fall through — maybe selecting a different own piece
  }
  var code2 = pos[sq];
  if (code2 && code2[0] === 'w' && lmap[sq] && lmap[sq].length) {
    selected = sq; showDots(sq);
  }
});
</script>
</body>
</html>
"""


import os as _os
_CHESS_DND_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                "components", "chess_dnd")
_chess_dnd_component = components.declare_component("chess_dnd", path=_CHESS_DND_DIR)


def chess_play_dnd(
    fen: str,
    legal_moves: list[str],
    status: str = "ongoing",
    last_move_uci: str | None = None,
    exploded_squares: list[str] | None = None,
    board_size: int = 460,
    height: int = 520,
    key: str = "chess_dnd",
) -> dict | None:
    """Render an interactive drag-and-drop chess board.

    Returns the value the component last set, or None if no move has been
    made yet.  When the user makes a move, the component returns
    {"uci": "<uci>", "id": <unique>}; the caller should compare `id`
    against the previously-seen value to know whether this is a new move.
    """
    lm_squares = (
        [last_move_uci[:2], last_move_uci[2:4]]
        if last_move_uci and len(last_move_uci) >= 4 else []
    )
    return _chess_dnd_component(
        fen=fen,
        legal_moves=legal_moves,
        status=status,
        last_move_squares=lm_squares,
        exploded_squares=exploded_squares or [],
        piece_theme=_PIECE_THEME_URL,
        board_size=board_size,
        key=key,
        default=None,
    )


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
