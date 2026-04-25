"""EngineLab animated landing page.

Renders a full-width hero with Canvas 2D particle effects, glassmorphic
agent cards with typewriter text, decorative mini chess boards, and a
dither overlay — all via st.components.v1.html().
"""
from __future__ import annotations

import streamlit.components.v1 as components

_HOME_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #161512;
  color: #bababa;
  font-family: 'Inter', system-ui, sans-serif;
  overflow: hidden;
  width: 100%;
  height: 100%;
  position: relative;
}

/* ── Particle canvas ───────────────────────────────────────── */
#particles {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

/* ── Dither overlay ────────────────────────────────────────── */
#dither {
  position: absolute;
  inset: 0;
  z-index: 1;
  opacity: 0.035;
  background-image: radial-gradient(circle, #bababa 1px, transparent 1px);
  background-size: 4px 4px;
  pointer-events: none;
}

/* ── Mini chess boards ─────────────────────────────────────── */
.mini-boards {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
}
.mini-board {
  position: absolute;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  grid-template-rows: repeat(6, 1fr);
  width: 140px;
  height: 140px;
  opacity: 0.10;
  border: 1px solid rgba(98, 153, 36, 0.15);
  border-radius: 4px;
  overflow: hidden;
}
.mini-board .sq {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
  user-select: none;
}
.sq-l { background: #2c2b29; }
.sq-d { background: #1f1e1c; }

/* ── Content layer ─────────────────────────────────────────── */
.content {
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 24px;
  text-align: center;
}

/* Title */
.title {
  font-size: 4.2rem;
  font-weight: 800;
  color: #e8e6e3;
  letter-spacing: 0.18em;
  -webkit-text-stroke: 1px rgba(98, 153, 36, 0.35);
  text-shadow:
    0 0 20px rgba(98,153,36,0.5),
    0 0 40px rgba(98,153,36,0.25),
    0 0 80px rgba(98,153,36,0.1);
  animation: pulseGlow 4s ease-in-out infinite;
  margin-bottom: 6px;
}
.subtitle {
  font-size: 0.95rem;
  color: #629924;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 12px;
}
.tagline {
  font-size: 0.82rem;
  color: #7a7775;
  max-width: 520px;
  line-height: 1.6;
  margin-bottom: 36px;
}

@keyframes pulseGlow {
  0%, 100% {
    text-shadow:
      0 0 20px rgba(98,153,36,0.5),
      0 0 40px rgba(98,153,36,0.25),
      0 0 80px rgba(98,153,36,0.1);
  }
  50% {
    text-shadow:
      0 0 30px rgba(98,153,36,0.7),
      0 0 60px rgba(98,153,36,0.4),
      0 0 100px rgba(98,153,36,0.15);
  }
}

/* ── Agent cards ───────────────────────────────────────────── */
.agent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  max-width: 640px;
  width: 100%;
  margin-bottom: 32px;
}
.agent-card {
  background: rgba(31, 30, 28, 0.55);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(98, 153, 36, 0.18);
  border-radius: 12px;
  padding: 16px 18px;
  text-align: left;
  transition: border-color 0.3s, transform 0.3s;
}
.agent-card:hover {
  border-color: rgba(98, 153, 36, 0.5);
  transform: translateY(-2px);
}
.agent-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}
.agent-icon {
  font-size: 1.6rem;
  line-height: 1;
  filter: drop-shadow(0 0 6px rgba(98,153,36,0.4));
}
.agent-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: #d0cfc8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.agent-traits {
  font-size: 0.68rem;
  color: #629924;
  margin-bottom: 10px;
  font-style: italic;
}
.agent-terminal {
  background: rgba(22, 21, 18, 0.7);
  border: 1px solid #2c2b29;
  border-radius: 6px;
  padding: 10px 12px;
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
  color: #7a7775;
  height: 72px;
  overflow: hidden;
  line-height: 1.65;
}
.agent-terminal .line {
  white-space: nowrap;
  overflow: hidden;
}
.cursor {
  color: #629924;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}

/* ── Bottom info ───────────────────────────────────────────── */
.bottom-info {
  font-size: 0.72rem;
  color: #4a4845;
  letter-spacing: 0.06em;
}
.bottom-info span {
  color: #629924;
}

/* ── Fade-in ───────────────────────────────────────────────── */
.fade-in {
  animation: fadeIn 1.2s ease-out both;
}
.fade-in-d1 { animation-delay: 0.2s; }
.fade-in-d2 { animation-delay: 0.5s; }
.fade-in-d3 { animation-delay: 0.8s; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
</head>
<body>

<canvas id="particles"></canvas>
<div id="dither"></div>

<!-- Mini chess boards (decorative) -->
<div class="mini-boards">
  <div class="mini-board" id="mb0" style="top:4%; left:3%;  transform:rotate(-6deg);"></div>
  <div class="mini-board" id="mb1" style="top:58%;left:5%;  transform:rotate(4deg);"></div>
  <div class="mini-board" id="mb2" style="top:6%; right:4%; transform:rotate(5deg);"></div>
  <div class="mini-board" id="mb3" style="top:55%;right:3%; transform:rotate(-3deg);"></div>
  <div class="mini-board" id="mb4" style="top:30%;left:1%;  transform:rotate(2deg);"></div>
  <div class="mini-board" id="mb5" style="top:32%;right:1%; transform:rotate(-4deg);"></div>
</div>

<!-- Main content -->
<div class="content">
  <div class="title fade-in">ENGINELAB</div>
  <div class="subtitle fade-in fade-in-d1">feature-subset engine discovery</div>
  <div class="tagline fade-in fade-in-d1">
    Build chess engines by selecting evaluation features, run round-robin
    tournaments across variants, and discover which strategic concepts
    actually win.
  </div>

  <div class="agent-grid fade-in fade-in-d2">
    <!-- Card 1: Standard -->
    <div class="agent-card" id="card0">
      <div class="agent-header">
        <div class="agent-icon">&#9812;</div>
        <div class="agent-name">Standard Strategist</div>
      </div>
      <div class="agent-traits">methodical, positional, material-driven</div>
      <div class="agent-terminal" id="term0"></div>
    </div>

    <!-- Card 2: Atomic -->
    <div class="agent-card" id="card1">
      <div class="agent-header">
        <div class="agent-icon">&#9818;</div>
        <div class="agent-name">Atomic Tactician</div>
      </div>
      <div class="agent-traits">explosive, aggressive, king-danger-aware</div>
      <div class="agent-terminal" id="term1"></div>
    </div>

    <!-- Card 3: Antichess -->
    <div class="agent-card" id="card2">
      <div class="agent-header">
        <div class="agent-icon">&#9822;</div>
        <div class="agent-name">Antichess Rebel</div>
      </div>
      <div class="agent-traits">sacrificial, contrarian, loss-seeking</div>
      <div class="agent-terminal" id="term2"></div>
    </div>

    <!-- Card 4: Analyst -->
    <div class="agent-card" id="card3">
      <div class="agent-header">
        <div class="agent-icon">&#9823;</div>
        <div class="agent-name">Feature Analyst</div>
      </div>
      <div class="agent-traits">data-driven, systematic, pattern-seeking</div>
      <div class="agent-terminal" id="term3"></div>
    </div>
  </div>

  <div class="bottom-info fade-in fade-in-d3">
    <span>10</span> features &middot;
    <span>3</span> variants &middot;
    <span>1023</span> possible engines &middot;
    alpha-beta search
  </div>
</div>

<script>
/* ================================================================
   PARTICLE SYSTEM
   ================================================================ */
(function() {
  var canvas = document.getElementById('particles');
  var ctx = canvas.getContext('2d');
  var W, H;

  function resize() {
    W = canvas.width  = canvas.parentElement.clientWidth  || window.innerWidth;
    H = canvas.height = canvas.parentElement.clientHeight || window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  var COLORS = ['#629924','#2d8a6e','#4a7a2a','#7ab648','#3d7a1a','#8fce3a','#5aad2b'];
  var N = 200;
  var particles = [];

  function spawn(p) {
    p.x = Math.random() * W;
    p.y = Math.random() * H;
    p.vx = (Math.random() - 0.5) * 0.5;
    p.vy = (Math.random() - 0.5) * 0.5;
    p.r  = Math.random() * 3.0 + 1.0;
    p.color = COLORS[Math.floor(Math.random() * COLORS.length)];
    p.life = 0;
    p.maxLife = 100 + Math.random() * 120;
  }

  for (var i = 0; i < N; i++) {
    var p = {};
    spawn(p);
    p.life = Math.random() * p.maxLife;
    particles.push(p);
  }

  function hexToRgb(hex) {
    var r = parseInt(hex.slice(1,3), 16);
    var g = parseInt(hex.slice(3,5), 16);
    var b = parseInt(hex.slice(5,7), 16);
    return r + ',' + g + ',' + b;
  }

  var time = 0;

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter';
    time += 0.008;

    for (var i = 0; i < N; i++) {
      var p = particles[i];
      // Add sine-wave drift for organic flowing motion
      var wave = Math.sin(time + p.x * 0.003 + i * 0.1) * 0.3;
      var wave2 = Math.cos(time * 0.7 + p.y * 0.004 + i * 0.05) * 0.25;
      p.x += p.vx + wave;
      p.y += p.vy + wave2;
      p.life++;

      if (p.x < -10) p.x = W + 10;
      if (p.x > W + 10) p.x = -10;
      if (p.y < -10) p.y = H + 10;
      if (p.y > H + 10) p.y = -10;

      if (p.life > p.maxLife) spawn(p);

      var fade = 1.0;
      if (p.life < 30) fade = p.life / 30;
      else if (p.life > p.maxLife - 30) fade = (p.maxLife - p.life) / 30;

      var rgb = hexToRgb(p.color);

      // Outer glow — large soft halo
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 8, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(' + rgb + ',' + (0.15 * fade) + ')';
      ctx.fill();

      // Middle glow
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(' + rgb + ',' + (0.35 * fade) + ')';
      ctx.fill();

      // Core — bright center
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(' + rgb + ',' + (0.7 * fade) + ')';
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }
  draw();
})();

/* ================================================================
   MINI CHESS BOARDS
   ================================================================ */
(function() {
  var WP = ['\u2654','\u2655','\u2656','\u2657','\u2658','\u2659'];
  var BP = ['\u265A','\u265B','\u265C','\u265D','\u265E','\u265F'];

  function initBoard(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    var cells = [];
    var grid = [];
    for (var r = 0; r < 6; r++) {
      var row = [];
      for (var c = 0; c < 6; c++) {
        var sq = document.createElement('div');
        sq.className = 'sq ' + ((r + c) % 2 === 0 ? 'sq-l' : 'sq-d');
        el.appendChild(sq);
        cells.push(sq);
        row.push(null);
      }
      grid.push(row);
    }

    // Place some pieces randomly
    var pieces = [];
    for (var k = 0; k < 5; k++) pieces.push(WP[Math.floor(Math.random()*WP.length)]);
    for (var k = 0; k < 5; k++) pieces.push(BP[Math.floor(Math.random()*BP.length)]);

    var placed = {};
    for (var k = 0; k < pieces.length; k++) {
      var tries = 0;
      while (tries < 50) {
        var rr = Math.floor(Math.random()*6);
        var cc = Math.floor(Math.random()*6);
        var key = rr*6+cc;
        if (!placed[key]) {
          placed[key] = true;
          grid[rr][cc] = pieces[k];
          cells[rr*6+cc].textContent = pieces[k];
          break;
        }
        tries++;
      }
    }

    return { cells: cells, grid: grid };
  }

  function animateBoard(board) {
    if (!board) return;
    var g = board.grid;
    var c = board.cells;

    // Find occupied and empty squares
    var occ = [], emp = [];
    for (var r = 0; r < 6; r++) {
      for (var col = 0; col < 6; col++) {
        if (g[r][col]) occ.push([r, col]);
        else emp.push([r, col]);
      }
    }
    if (occ.length === 0 || emp.length === 0) return;

    var from = occ[Math.floor(Math.random() * occ.length)];
    var to   = emp[Math.floor(Math.random() * emp.length)];
    var piece = g[from[0]][from[1]];

    g[from[0]][from[1]] = null;
    c[from[0]*6+from[1]].textContent = '';
    g[to[0]][to[1]] = piece;
    c[to[0]*6+to[1]].textContent = piece;
  }

  var boards = [];
  for (var i = 0; i < 6; i++) {
    boards.push(initBoard('mb' + i));
  }

  // Stagger animations so boards move at different times
  boards.forEach(function(b, idx) {
    setInterval(function() { animateBoard(b); }, 1800 + idx * 400);
  });
})();

/* ================================================================
   TYPEWRITER TERMINALS
   ================================================================ */
(function() {
  var PHRASES = [
    [
      "evaluating material balance... +2.3",
      "mobility score for Nf3: 0.85",
      "pawn_structure: isolated d-pawn detected",
      "center_control weight adjusted to 0.61",
      "bishop_pair bonus applied: +0.18",
      "rook_activity on open file: significant",
    ],
    [
      "explosion radius check on e4... 5 pieces",
      "king_danger threshold exceeded at g8",
      "capture_threats near enemy king: critical",
      "simulating atomic chain reaction d5-e4...",
      "enemy_king_danger score: 0.94",
      "avoiding self-explosion on f7... filtered",
    ],
    [
      "minimizing material... sacrifice Qd1",
      "forcing capture sequence: Bxf7+ Kxf7",
      "piece_position inverted: corners preferred",
      "material is a liability: shedding pieces",
      "pawn advance to force opponent captures",
      "target: 0 remaining pieces = victory",
    ],
    [
      "pairwise synergy: material + mobility = 0.82",
      "running round-robin: game 147/210...",
      "top agent: king_safety + capture_threats",
      "feature marginal: center_control +0.034",
      "computing leaderboard... 31 agents ranked",
      "bishop_pair + rook_activity: synergy 0.41",
    ],
  ];

  function Typewriter(termId, phrases) {
    this.el = document.getElementById(termId);
    this.phrases = phrases;
    this.pIdx = 0;
    this.lines = [];
    this.typing = false;
    this.el.innerHTML = '';
  }

  Typewriter.prototype.start = function() {
    var self = this;
    self._next();
  };

  Typewriter.prototype._next = function() {
    var self = this;
    var phrase = self.phrases[self.pIdx % self.phrases.length];
    self.pIdx++;

    // Add a new line element
    var lineEl = document.createElement('div');
    lineEl.className = 'line';
    self.el.appendChild(lineEl);
    self.lines.push(lineEl);

    // Keep only last 3 lines
    while (self.lines.length > 3) {
      var old = self.lines.shift();
      if (old.parentNode) old.parentNode.removeChild(old);
    }

    // Type character by character
    var charIdx = 0;
    var cursor = document.createElement('span');
    cursor.className = 'cursor';
    cursor.textContent = '_';

    function typeChar() {
      if (charIdx < phrase.length) {
        lineEl.textContent = phrase.slice(0, charIdx + 1);
        lineEl.appendChild(cursor);
        charIdx++;
        setTimeout(typeChar, 30 + Math.random() * 25);
      } else {
        // Done typing this line — pause, then next
        if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
        setTimeout(function() { self._next(); }, 1800 + Math.random() * 1200);
      }
    }
    typeChar();
  };

  // Start each terminal with a staggered delay
  for (var i = 0; i < 4; i++) {
    (function(idx) {
      setTimeout(function() {
        var tw = new Typewriter('term' + idx, PHRASES[idx]);
        tw.start();
      }, idx * 600 + 800);
    })(i);
  }
})();
</script>

</body>
</html>"""


def render_home_page() -> None:
    """Render the full-width animated landing page."""
    components.html(_HOME_TEMPLATE, height=900, scrolling=False)
