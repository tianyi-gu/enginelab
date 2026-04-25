"""EngineLab animated landing page.

Renders a full-width hero over the static Wisp Three.js shader background,
with glassmorphic agent cards and typewriter text via st.components.v1.html().
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

#wisp-bg {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  border: none;
  z-index: 0;
  pointer-events: none;
  transform: scale(1.08);
  filter: brightness(0.65) contrast(1.25) saturate(1.2);
}

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

<iframe
  id="wisp-bg"
  src="/app/static/wisp/index.html"
  frameborder="0"
></iframe>

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
