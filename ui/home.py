"""EngineLab animated landing page.

Renders a full-width hero with WebGL neuronal shader background, particle
bloom overlay, and a decorative 8x8 grid of mini chess boards each looping
through real precomputed tournament games (mix of atomic, horde, and
other variants).
"""
from __future__ import annotations

import streamlit.components.v1 as components

from ui.home_animation_data import bake_animation_payload

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

/* ── Content layer ─────────────────────────────────────────── */
.content {
  position: relative;
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px 24px;
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
  margin-bottom: 28px;
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

/* ── Chess animation grid (8x8 mini-boards each playing a real game) ── */
.chess-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
  width: 100%;
  max-width: 560px;
  margin: 4px auto 32px;
  opacity: 0.78;
  filter: drop-shadow(0 4px 18px rgba(0, 0, 0, 0.4));
}
.mini {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-rows: repeat(8, 1fr);
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 2px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.45);
  background: #b58863;
}
.cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cell.cl { background: #f0d9b5; }
.cell.cd { background: #b58863; }
.cell.exp { background: #ff1818 !important; }
.cell img {
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
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

<!-- Main content -->
<div class="content">
  <div class="title fade-in">ENGINELAB</div>
  <div class="subtitle fade-in fade-in-d1">feature-subset engine discovery</div>
  <div class="tagline fade-in fade-in-d1">
    Build chess engines by selecting evaluation features, run round-robin
    tournaments across variants, and discover which strategic concepts
    actually win.
  </div>

  <!-- 8x8 grid of mini-boards each looping a real game -->
  <div class="chess-grid fade-in fade-in-d2" id="chess-grid"></div>

  <div class="bottom-info fade-in fade-in-d3">
    <span>12</span> features &middot;
    <span>7</span> variants &middot;
    <span>4095</span> possible engines &middot;
    alpha-beta search
  </div>
</div>

<script>
/* ================================================================
   NEURO SHADER BACKGROUND
   Ported directly from Darwin's NeuroShaderCanvas.jsx
   ================================================================ */
(function() {
  var canvas = document.getElementById('neuro-canvas');
  if (!canvas) return;
  var parent = canvas.parentElement;
  if (!parent) return;

  var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) return;

  var vertexShaderSource =
    'precision mediump float;\n' +
    'attribute vec2 a_position;\n' +
    'varying vec2 vUv;\n' +
    'void main() {\n' +
    '  vUv = 0.5 * (a_position + 1.0);\n' +
    '  gl_Position = vec4(a_position, 0.0, 1.0);\n' +
    '}\n';

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

  var pointer = { x: 0.5, y: 0.5, tX: 0.5, tY: 0.5 };
  canvas.addEventListener('pointermove', function(e) {
    var rect = canvas.getBoundingClientRect();
    pointer.tX = (e.clientX - rect.left) / rect.width;
    pointer.tY = 1.0 - (e.clientY - rect.top) / rect.height;
  });

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
   ================================================================ */
(function() {
  var canvas = document.getElementById('particles');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var particleCount = 200;
  var particles = [];

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

  function Particle() { this.reset(); }
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
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius * 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (opacity * 0.15) + ')';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius * 2, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (opacity * 0.4) + ')';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (opacity * 0.7) + ')';
    ctx.fill();
  };
  for (var i = 0; i < particleCount; i++) particles.push(new Particle());
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var i = 0; i < particles.length; i++) { particles[i].update(); particles[i].draw(); }
    requestAnimationFrame(animate);
  }
  animate();
})();

/* ================================================================
   CHESS GRID ANIMATION
   8x8 grid of mini-boards each looping a real precomputed game.
   ================================================================ */
(function() {
  var ANIMATION_DATA = __ANIMATION_DATA__;
  var GRID = document.getElementById('chess-grid');
  if (!GRID || !ANIMATION_DATA || ANIMATION_DATA.length === 0) return;

  var PIECE_URL = 'https://chessboardjs.com/img/chesspieces/wikipedia/{p}.png';
  var TICK_MS = 130;        // each board advances one move every ~130ms
  var EXPLOSION_HOLD = 280; // hold an explosion frame so red flash registers

  function parseFEN(fen) {
    var ranks = fen.split(' ')[0].split('/');
    var grid = new Array(64).fill(null);
    for (var r = 0; r < 8; r++) {
      var col = 0;
      var rank = ranks[r];
      for (var i = 0; i < rank.length; i++) {
        var ch = rank[i];
        if (ch >= '1' && ch <= '8') {
          col += +ch;
        } else {
          var isW = (ch === ch.toUpperCase());
          var code = (isW ? 'w' : 'b') + ch.toUpperCase();
          grid[r * 8 + col] = code;
          col++;
        }
      }
    }
    return grid;
  }

  function buildBoard(idx) {
    var board = document.createElement('div');
    board.className = 'mini';
    var cells = [];
    for (var r = 0; r < 8; r++) {
      for (var c = 0; c < 8; c++) {
        var sq = document.createElement('div');
        sq.className = 'cell ' + (((r + c) % 2 === 0) ? 'cl' : 'cd');
        board.appendChild(sq);
        cells.push(sq);
      }
    }
    GRID.appendChild(board);
    return { el: board, cells: cells, lastGrid: new Array(64).fill(null) };
  }

  function renderBoard(b, fen, exploded) {
    var grid = parseFEN(fen);
    // Diff against last grid: only update changed cells
    for (var i = 0; i < 64; i++) {
      var prev = b.lastGrid[i];
      var curr = grid[i];
      if (prev !== curr) {
        var cell = b.cells[i];
        if (curr) {
          // Reuse existing img if present
          var img = cell.firstChild;
          if (img && img.tagName === 'IMG') {
            img.src = PIECE_URL.replace('{p}', curr);
          } else {
            cell.innerHTML = '';
            var ni = document.createElement('img');
            ni.src = PIECE_URL.replace('{p}', curr);
            cell.appendChild(ni);
          }
        } else {
          cell.innerHTML = '';
        }
      }
    }
    // Explosion highlight: clear all, then mark current
    for (var k = 0; k < 64; k++) {
      if (b.cells[k].classList.contains('exp')) b.cells[k].classList.remove('exp');
    }
    if (exploded && exploded.length) {
      for (var j = 0; j < exploded.length; j++) {
        var sq = exploded[j];
        if (!sq || sq.length < 2) continue;
        var file = sq.charCodeAt(0) - 97; // a-h
        var rank = parseInt(sq[1], 10) - 1; // 1-8
        if (file < 0 || file > 7 || rank < 0 || rank > 7) continue;
        var idx = (7 - rank) * 8 + file;
        b.cells[idx].classList.add('exp');
      }
    }
    b.lastGrid = grid;
  }

  // Build all 64 boards
  var boards = [];
  for (var i = 0; i < ANIMATION_DATA.length; i++) {
    var b = buildBoard(i);
    b.data = ANIMATION_DATA[i];
    b.frame = 0;
    // Random initial offset so boards aren't synchronized
    b.nextTick = performance.now() + Math.random() * 1500;
    renderBoard(b, b.data.fens[0], b.data.exploded[0]);
    boards.push(b);
  }

  function loop() {
    var now = performance.now();
    for (var i = 0; i < boards.length; i++) {
      var b = boards[i];
      if (now < b.nextTick) continue;
      b.frame++;
      if (b.frame >= b.data.fens.length) {
        b.frame = 0;
      }
      var fen = b.data.fens[b.frame];
      var exp = b.data.exploded[b.frame];
      renderBoard(b, fen, exp);
      var hold = (exp && exp.length) ? EXPLOSION_HOLD : TICK_MS;
      // ±15ms jitter so they stay desynchronized
      b.nextTick = now + hold + (Math.random() * 30 - 15);
    }
    requestAnimationFrame(loop);
  }
  loop();
})();
</script>

</body>
</html>"""


def render_home_page() -> None:
    """Render the full-width animated landing page."""
    payload = bake_animation_payload(64)
    html = _HOME_TEMPLATE.replace("__ANIMATION_DATA__", payload)
    components.html(html, height=900, scrolling=False)
