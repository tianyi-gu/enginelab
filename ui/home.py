"""EngineLab animated landing page.

Renders a full-width hero with WebGL neuronal shader background (ported
from Darwin project), Canvas 2D particle bloom overlay, glassmorphic agent
cards with typewriter text, and decorative mini chess boards — all via
st.components.v1.html().
"""
from __future__ import annotations

import streamlit.components.v1 as components

_HOME_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100;200;300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=BBH+Sans+Bartle&display=swap');

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #161512;
  color: #bababa;
  font-family: 'Geist Mono', monospace;
  text-transform: lowercase;
  overflow: hidden;
  width: 100%;
  height: 100%;
  position: relative;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── WebGL shader background (Darwin NeuroShaderCanvas) ──── */
#neuro-canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

/* ── Particle overlay (Darwin SideParticles) ─────────────── */
#particles {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* ── Dither overlay ────────────────────────────────────────── */
#dither {
  position: absolute;
  inset: 0;
  z-index: 2;
  opacity: 0.035;
  background-image: radial-gradient(circle, #bababa 1px, transparent 1px);
  background-size: 4px 4px;
  pointer-events: none;
}

/* ── Mini chess boards ─────────────────────────────────────── */
.mini-boards {
  position: absolute;
  inset: 0;
  z-index: 3;
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
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 24px;
  text-align: center;
}

/* Title — matches Darwin's .title styling */
.title {
  font-size: 3rem;
  color: transparent;
  text-align: center;
  margin: 0 0 6px;
  line-height: 1;
  font-weight: 400;
  -webkit-text-stroke: 1.5px rgba(255, 255, 255, 0.9);
  text-stroke: 1.5px rgba(255, 255, 255, 0.9);
  text-shadow:
    0 0 15px rgba(255, 255, 255, 0.15),
    0 0 30px rgba(98, 153, 36, 0.2);
  font-family: "BBH Sans Bartle", sans-serif;
  text-transform: lowercase;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  letter-spacing: 0.2em;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  animation: pulseGlow 4s ease-in-out infinite;
}
.subtitle {
  font-family: 'Geist Mono', monospace;
  font-size: 0.9rem;
  color: white;
  text-align: center;
  margin: 0.75rem 0 0 0;
  font-weight: 400;
  letter-spacing: 0.02em;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
  margin-bottom: 12px;
}
.tagline {
  font-family: 'Geist Mono', monospace;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  max-width: 520px;
  line-height: 1.6;
  margin-bottom: 36px;
  font-weight: 200;
  letter-spacing: 0.02em;
}

@keyframes pulseGlow {
  0%, 100% {
    text-shadow:
      0 0 15px rgba(255, 255, 255, 0.15),
      0 0 30px rgba(98,153,36,0.2);
  }
  50% {
    text-shadow:
      0 0 20px rgba(255, 255, 255, 0.25),
      0 0 40px rgba(98,153,36,0.35),
      0 0 60px rgba(98,153,36,0.15);
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
  color: rgba(255, 255, 255, 0.9);
  font-family: 'BBH Sans Bartle', sans-serif;
  font-size: 0.85rem;
  text-transform: lowercase;
  letter-spacing: 0.1em;
  font-weight: 400;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
.agent-traits {
  color: rgba(255, 255, 255, 0.7);
  font-family: 'Geist Mono', monospace;
  font-size: 0.65rem;
  margin-bottom: 10px;
  font-weight: 400;
  letter-spacing: 0.02em;
}
.agent-terminal {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 10px 12px;
  font-family: 'Geist Mono', monospace;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.7);
  height: 72px;
  overflow: hidden;
  line-height: 1.5;
}
.agent-terminal .line {
  white-space: nowrap;
  overflow: hidden;
}
.cursor {
  color: #629924;
  font-weight: bold;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* ── Bottom info ───────────────────────────────────────────── */
.bottom-info {
  font-family: 'Geist Mono', monospace;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 0.04em;
  font-weight: 200;
}
.bottom-info span {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 400;
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

<!-- WebGL neuronal shader background (from Darwin NeuroShaderCanvas) -->
<canvas id="neuro-canvas"></canvas>

<!-- Canvas 2D particle bloom overlay (from Darwin SideParticles) -->
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
   NEURO SHADER BACKGROUND
   Ported directly from Darwin's NeuroShaderCanvas.jsx
   https://github.com/qtzx06/darwin/blob/main/src/components/NeuroShaderCanvas.jsx
   ================================================================ */
(function() {
  var canvas = document.getElementById('neuro-canvas');
  if (!canvas) return;
  var parent = canvas.parentElement;
  if (!parent) return;

  var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) return;

  // Vertex shader — identical to Darwin
  var vertexShaderSource =
    'precision mediump float;\n' +
    'attribute vec2 a_position;\n' +
    'varying vec2 vUv;\n' +
    'void main() {\n' +
    '  vUv = 0.5 * (a_position + 1.0);\n' +
    '  gl_Position = vec4(a_position, 0.0, 1.0);\n' +
    '}\n';

  // Fragment shader — Darwin's neuro_shape with green tint
  var fragmentShaderSource =
    'precision mediump float;\n' +
    'varying vec2 vUv;\n' +
    'uniform float u_time;\n' +
    'uniform float u_ratio;\n' +
    'uniform vec2 u_pointer_position;\n' +
    '\n' +
    'vec2 rotate(vec2 uv, float th) {\n' +
    '  return mat2(cos(th), sin(th), -sin(th), cos(th)) * uv;\n' +
    '}\n' +
    '\n' +
    'float neuro_shape(vec2 uv, float t, float p) {\n' +
    '  vec2 sine_acc = vec2(0.0);\n' +
    '  vec2 res = vec2(0.0);\n' +
    '  float scale = 8.0;\n' +
    '  for (int j = 0; j < 15; j++) {\n' +
    '    uv = rotate(uv, 1.0);\n' +
    '    sine_acc = rotate(sine_acc, 1.0);\n' +
    '    vec2 layer = uv * scale + float(j) + sine_acc - t;\n' +
    '    sine_acc += sin(layer);\n' +
    '    res += (0.5 + 0.5 * cos(layer)) / scale;\n' +
    '    scale *= (1.2 - 0.07 * p);\n' +
    '  }\n' +
    '  return res.x + res.y;\n' +
    '}\n' +
    '\n' +
    'void main() {\n' +
    '  vec2 uv = 0.5 * vUv;\n' +
    '  uv.x *= u_ratio;\n' +
    '  vec2 pointer = vUv - u_pointer_position;\n' +
    '  pointer.x *= u_ratio;\n' +
    '  float p = clamp(length(pointer), 0.0, 1.0);\n' +
    '  p = 0.5 * pow(1.0 - p, 2.0);\n' +
    '  float t = 0.001 * u_time;\n' +
    '  float noise = neuro_shape(uv, t, p);\n' +
    '  noise = 1.2 * pow(noise, 3.0);\n' +
    '  noise += pow(noise, 10.0);\n' +
    '  noise = max(0.0, noise - 0.5);\n' +
    '  noise *= (1.0 - length(vUv - 0.5));\n' +
    // Tint green instead of white: multiply by EngineLab green
    '  vec3 color = noise * vec3(0.38, 0.60, 0.14);\n' +
    '  gl_FragColor = vec4(color, noise);\n' +
    '}\n';

  function compileShader(source, type) {
    var shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('Shader compile error:', gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  }

  var vertexShader = compileShader(vertexShaderSource, gl.VERTEX_SHADER);
  var fragmentShader = compileShader(fragmentShaderSource, gl.FRAGMENT_SHADER);
  if (!vertexShader || !fragmentShader) return;

  var program = gl.createProgram();
  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('Program link error:', gl.getProgramInfoLog(program));
    return;
  }
  gl.useProgram(program);

  // Full-screen quad
  var vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
  var buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

  var positionLocation = gl.getAttribLocation(program, 'a_position');
  gl.enableVertexAttribArray(positionLocation);
  gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

  var timeLocation = gl.getUniformLocation(program, 'u_time');
  var ratioLocation = gl.getUniformLocation(program, 'u_ratio');
  var pointerLocation = gl.getUniformLocation(program, 'u_pointer_position');

  // Mouse tracking with smoothing (same as Darwin)
  var pointer = { x: 0.5, y: 0.5, tX: 0.5, tY: 0.5 };
  canvas.addEventListener('pointermove', function(e) {
    var rect = canvas.getBoundingClientRect();
    pointer.tX = (e.clientX - rect.left) / rect.width;
    pointer.tY = 1.0 - (e.clientY - rect.top) / rect.height;
  });

  // Enable blending for transparent background
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

  function resize() {
    var dpr = Math.min(window.devicePixelRatio, 2);
    canvas.width = parent.clientWidth * dpr;
    canvas.height = parent.clientHeight * dpr;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform1f(ratioLocation, canvas.width / canvas.height);
  }
  window.addEventListener('resize', resize);
  resize();

  function render() {
    pointer.x += (pointer.tX - pointer.x) * 0.5;
    pointer.y += (pointer.tY - pointer.y) * 0.5;

    gl.uniform1f(timeLocation, performance.now());
    gl.uniform2f(pointerLocation, pointer.x, pointer.y);

    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(render);
  }
  render();
})();

/* ================================================================
   PARTICLE BLOOM OVERLAY
   Ported directly from Darwin's SideParticles.jsx
   https://github.com/qtzx06/darwin/blob/main/src/components/SideParticles.jsx
   Colors adapted from purple/pink to green/teal.
   ================================================================ */
(function() {
  var canvas = document.getElementById('particles');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var particleCount = 200;
  var particles = [];

  // Match Darwin's particle colors but in green/teal palette
  var colors = [
    'rgba(98, 153, 36, 0.4)',
    'rgba(122, 182, 72, 0.35)',
    'rgba(45, 138, 110, 0.3)',
    'rgba(74, 122, 42, 0.25)',
    'rgba(143, 206, 58, 0.3)'
  ];

  function resize() {
    canvas.width = canvas.offsetWidth || canvas.parentElement.clientWidth;
    canvas.height = canvas.offsetHeight || canvas.parentElement.clientHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function Particle() {
    this.reset();
  }

  Particle.prototype.reset = function() {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.vx = (Math.random() - 0.5) * 0.5;
    this.vy = (Math.random() - 0.5) * 0.5;
    this.radius = Math.random() * 2 + 1;
    this.color = colors[Math.floor(Math.random() * colors.length)];
    this.life = Math.random() * 100 + 100;
    this.maxLife = this.life;
  };

  Particle.prototype.update = function() {
    this.x += this.vx;
    this.y += this.vy;
    this.life--;
    if (this.life <= 0) this.reset();
    if (this.x < 0) this.x = canvas.width;
    if (this.x > canvas.width) this.x = 0;
    if (this.y < 0) this.y = canvas.height;
    if (this.y > canvas.height) this.y = 0;
  };

  Particle.prototype.draw = function() {
    var opacity = this.life / this.maxLife;
    var match = this.color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!match) return;
    var r = match[1], g = match[2], b = match[3];

    // Outer glow — identical to Darwin
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius * 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (opacity * 0.15) + ')';
    ctx.fill();

    // Middle glow
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius * 2, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (opacity * 0.4) + ')';
    ctx.fill();

    // Core
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (opacity * 0.7) + ')';
    ctx.fill();
  };

  for (var i = 0; i < particleCount; i++) {
    particles.push(new Particle());
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var i = 0; i < particles.length; i++) {
      particles[i].update();
      particles[i].draw();
    }
    requestAnimationFrame(animate);
  }
  animate();
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
    this.el.innerHTML = '';
  }

  Typewriter.prototype.start = function() {
    this._next();
  };

  Typewriter.prototype._next = function() {
    var self = this;
    var phrase = self.phrases[self.pIdx % self.phrases.length];
    self.pIdx++;

    var lineEl = document.createElement('div');
    lineEl.className = 'line';
    self.el.appendChild(lineEl);
    self.lines.push(lineEl);

    while (self.lines.length > 3) {
      var old = self.lines.shift();
      if (old.parentNode) old.parentNode.removeChild(old);
    }

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
        if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
        setTimeout(function() { self._next(); }, 1800 + Math.random() * 1200);
      }
    }
    typeChar();
  };

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
