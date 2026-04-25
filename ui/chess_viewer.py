"""
Chess board rendering utilities for the EngineLab Streamlit UI.

Three public functions:
  chess_game_viewer      — interactive game replay (chessboard.js + chess.js)
  chess_play_interactive — drag-and-drop game vs random engine (self-contained HTML)
  chess_play_board       — static SVG position viewer (python-chess)
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
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"
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

// ── Init ─────────────────────────────────────────────────────────────────────
document.getElementById('white-name').textContent = WHITE_NAME;
document.getElementById('black-name').textContent = BLACK_NAME;

var game = new Chess();
var fens     = [game.fen()];
var sanMoves = [];

UCI_MOVES.forEach(function(uci) {
  var mv = game.move({ from: uci.slice(0,2), to: uci.slice(2,4),
                       promotion: uci[4] || 'q' });
  if (mv) { sanMoves.push(mv.san); fens.push(game.fen()); }
});

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
) -> None:
    """Render an interactive chess game replay viewer inside a Streamlit app.

    Args:
        moves:       List of UCI move strings, e.g. ["e2e4", "e7e5", ...].
        white_name:  Display name for the white player.
        black_name:  Display name for the black player.
        result:      Short result string shown at the end of the move list, e.g. "1-0".
        board_size:  Unused (board is now responsive); kept for API compatibility.
        height:      Component iframe height in pixels.
    """
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    html = (
        _VIEWER_TEMPLATE
        .replace("__UCI_MOVES__",   json.dumps(moves))
        .replace("__WHITE_NAME__",  _esc(white_name))
        .replace("__BLACK_NAME__",  _esc(black_name))
        .replace("__RESULT__",      _esc(result))
        .replace("__PIECE_THEME__", _PIECE_THEME_URL)
    )
    components.html(html, height=height, scrolling=False)


# ---------------------------------------------------------------------------
# Interactive play (drag-and-drop vs random engine)
# ---------------------------------------------------------------------------

_PLAY_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script src="https://code.jquery.com/jquery-3.7.1.min.js" crossorigin="anonymous"></script>
<link  rel="stylesheet"
       href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css"
       crossorigin="anonymous">
<script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"
        crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"
        crossorigin="anonymous"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #161512; color: #bababa; font-family: 'Inter', system-ui, sans-serif; display: flex; flex-direction: column; align-items: center; padding: 6px 4px 8px; }
.player-row { display: flex; align-items: center; gap: 7px; padding: 5px 0; font-size: 12.5px; font-weight: 600; color: #d0cfc8; width: 460px; }
.dot { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
.dot-black { background: #1a1a1a; border: 1px solid #555; }
.dot-white { background: #f0d9b5; border: 1px solid #aaa; }
#board { width: 460px; }
.board-b72b1 { border: 2px solid #2c2b29 !important; border-radius: 2px; }
.status-row { display: flex; align-items: center; justify-content: space-between; width: 460px; padding: 5px 0 3px; }
#status { font-size: 13px; font-weight: 600; }
.your-turn { color: #629924 !important; }
.thinking { color: #7a7775 !important; font-style: italic; }
.check { color: #e67e22 !important; }
.checkmate { color: #c84b4b !important; }
.draw { color: #7a7775 !important; }
.movelist { background: #1f1e1c; border: 1px solid #3a3a38; border-radius: 5px; padding: 6px 9px; overflow-y: auto; max-height: 90px; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.85; width: 460px; }
.mp { display: flex; gap: 2px; align-items: baseline; }
.mn { color: #6a7068; min-width: 20px; font-size: 11px; }
.mw, .mb { padding: 0 4px; border-radius: 2px; color: #c9d1d9; cursor: default; }
.cur { background: #629924 !important; color: #fff !important; font-weight: 700; }
.btn-new { margin-top: 6px; width: 460px; padding: 7px 0; border-radius: 4px; border: none; background: #629924; color: #fff; font-weight: 600; font-size: 13px; cursor: pointer; font-family: inherit; }
.btn-new:hover { background: #4e7a1b; }
#promo-modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 999; justify-content: center; align-items: center; }
#promo-modal.show { display: flex; }
.promo-opts { background: #272522; border: 1px solid #3a3a38; border-radius: 8px; padding: 16px 20px; display: flex; gap: 10px; }
.promo-btn { width: 56px; height: 56px; background: #1f1e1c; border: 1px solid #3a3a38; border-radius: 5px; cursor: pointer; font-size: 32px; display: flex; align-items: center; justify-content: center; }
.promo-btn:hover { background: #3a3a38; }
</style>
</head>
<body>

<!-- Promotion modal -->
<div id="promo-modal">
  <div class="promo-opts">
    <button class="promo-btn" onclick="doPromotion('q')" title="Queen">&#9819;</button>
    <button class="promo-btn" onclick="doPromotion('r')" title="Rook">&#9820;</button>
    <button class="promo-btn" onclick="doPromotion('b')" title="Bishop">&#9821;</button>
    <button class="promo-btn" onclick="doPromotion('n')" title="Knight">&#9822;</button>
  </div>
</div>

<div class="player-row">
  <span class="dot dot-black"></span>
  <span id="engine-name-top">__ENGINE_NAME__</span>
</div>

<div id="board"></div>

<div class="player-row">
  <span class="dot dot-white"></span>
  <span>You (White)</span>
</div>

<div class="status-row">
  <div id="status" class="your-turn">Your turn</div>
</div>

<div class="movelist" id="movelist">
  <span style="color:#6a7068;font-size:11px">No moves yet</span>
</div>

<button class="btn-new" onclick="newGame()">New Game</button>

<script>
var game = new Chess();
var pendingPromotion = null;

var board = Chessboard('board', {
  draggable: true,
  position: 'start',
  pieceTheme: '__PIECE_THEME__',
  boardWidth: 460,
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: function() { board.position(game.fen()); },
});

// ── Drag start guard ────────────────────────────────────────────────────────
function onDragStart(source, piece) {
  if (game.game_over()) return false;
  if (game.turn() !== 'w') return false;
  if (piece.search(/^b/) !== -1) return false;
}

// ── Drop handler ─────────────────────────────────────────────────────────────
function onDrop(source, target) {
  // Detect pawn promotion
  var isPawnPromo = (
    game.get(source) &&
    game.get(source).type === 'p' &&
    game.get(source).color === 'w' &&
    target[1] === '8'
  );

  if (isPawnPromo) {
    // Check if the move is at least pseudo-legal before showing modal
    var testMove = game.move({ from: source, to: target, promotion: 'q' });
    if (testMove === null) return 'snapback';
    game.undo();
    pendingPromotion = { from: source, to: target };
    document.getElementById('promo-modal').classList.add('show');
    return;
  }

  var move = game.move({ from: source, to: target, promotion: 'q' });
  if (move === null) return 'snapback';

  afterPlayerMove();
}

// ── Promotion modal callback ─────────────────────────────────────────────────
function doPromotion(piece) {
  document.getElementById('promo-modal').classList.remove('show');
  if (!pendingPromotion) return;
  var move = game.move({ from: pendingPromotion.from, to: pendingPromotion.to, promotion: piece });
  pendingPromotion = null;
  board.position(game.fen());
  if (move === null) return;
  afterPlayerMove();
}

// ── After player moves ────────────────────────────────────────────────────────
function afterPlayerMove() {
  updateMoveList();
  updateStatus();
  if (!game.game_over()) {
    setStatus('thinking', 'Thinking…');
    var delay = 400 + Math.random() * 300;
    setTimeout(engineMove, delay);
  }
}

// ── Engine move (random legal move) ──────────────────────────────────────────
function engineMove() {
  if (game.game_over()) return;
  var moves = game.moves();
  if (moves.length === 0) return;
  var chosen = moves[Math.floor(Math.random() * moves.length)];
  game.move(chosen);
  board.position(game.fen());
  updateMoveList();
  updateStatus();
}

// ── Move list ─────────────────────────────────────────────────────────────────
function updateMoveList() {
  var history = game.history();
  if (history.length === 0) {
    document.getElementById('movelist').innerHTML =
      '<span style="color:#6a7068;font-size:11px">No moves yet</span>';
    return;
  }

  var html = '';
  for (var i = 0; i < history.length; i++) {
    var isLast = (i === history.length - 1);
    if (i % 2 === 0) {
      if (i) html += '</div>';
      html += '<div class="mp"><span class="mn">' + (Math.floor(i / 2) + 1) + '.</span>';
      html += '<span class="mw' + (isLast ? ' cur' : '') + '">' + history[i] + '</span>';
    } else {
      html += '<span class="mb' + (isLast ? ' cur' : '') + '">' + history[i] + '</span></div>';
    }
  }
  // Close open pair if white just moved (odd total)
  if (history.length % 2 === 1) html += '</div>';

  var el = document.getElementById('movelist');
  el.innerHTML = html;
  el.scrollTop = el.scrollHeight;
}

// ── Status ────────────────────────────────────────────────────────────────────
function setStatus(cls, text) {
  var el = document.getElementById('status');
  el.className = cls;
  el.textContent = text;
}

function updateStatus() {
  if (game.in_checkmate()) {
    var winner = game.turn() === 'w' ? 'Engine wins' : 'You win';
    setStatus('checkmate', 'Checkmate – ' + winner + '!');
  } else if (game.in_stalemate()) {
    setStatus('draw', 'Stalemate – Draw');
  } else if (game.in_draw()) {
    setStatus('draw', 'Draw');
  } else if (game.in_check()) {
    if (game.turn() === 'w') {
      setStatus('check', 'You are in check!');
    } else {
      setStatus('check', 'Engine is in check');
    }
  } else if (game.turn() === 'w') {
    setStatus('your-turn', 'Your turn (White)');
  } else {
    setStatus('thinking', 'Engine is thinking…');
  }
}

// ── New game ──────────────────────────────────────────────────────────────────
function newGame() {
  game.reset();
  board.start(true);
  pendingPromotion = null;
  document.getElementById('promo-modal').classList.remove('show');
  updateMoveList();
  setStatus('your-turn', 'Your turn (White)');
}
</script>
</body>
</html>
"""


def chess_play_interactive(
    engine_name: str = "Best Engine",
    engine_features_html: str = "",
    height: int = 540,
) -> None:
    """Render a self-contained drag-and-drop chess game vs a random-move engine.

    All game state lives in JavaScript; no Python callbacks are needed.

    Args:
        engine_name:           Display name shown above the board for the engine.
        engine_features_html:  Pre-built HTML (e.g. feature pills) injected into the
                               features panel.  Pass an empty string to leave it blank.
        height:                Component iframe height in pixels.
    """
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    html = (
        _PLAY_TEMPLATE
        .replace("__ENGINE_NAME__",       _esc(engine_name))
        .replace("__FEATURE_PILLS_HTML__", engine_features_html)
        .replace("__PIECE_THEME__",        _PIECE_THEME_URL)
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
