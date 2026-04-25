import type { Chess, Square, PieceSymbol, Color } from "chess.js";

// ============================================================================
// Feature Registry — each feature returns a score from White's perspective
// (positive = good for White). Mirrors the python feature/ folder layout.
// ============================================================================

export type FeatureFn = (game: Chess) => number;

export interface FeatureDef {
  id: string;
  name: string;
  description: string;
  defaultWeight: number;
  fn: FeatureFn;
}

const PIECE_VALUES: Record<PieceSymbol, number> = {
  p: 100,
  n: 320,
  b: 330,
  r: 500,
  q: 900,
  k: 0,
};

// Piece-square tables (from White's perspective, a8 = index 0)
const PST: Record<PieceSymbol, number[]> = {
  p: [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
  ],
  n: [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
  ],
  b: [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
  ],
  r: [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
  ],
  q: [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
  ],
  k: [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
  ],
};

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"] as const;

function squareToIndex(sq: Square, color: Color): number {
  const file = FILES.indexOf(sq[0] as typeof FILES[number]);
  const rank = parseInt(sq[1], 10);
  // PST is from white's perspective (a8 = index 0)
  const row = color === "w" ? 8 - rank : rank - 1;
  const col = color === "w" ? file : 7 - file;
  return row * 8 + col;
}

function allPieces(game: Chess) {
  const board = game.board();
  const out: { square: Square; type: PieceSymbol; color: Color }[] = [];
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const p = board[r][c];
      if (p) {
        const sq = (FILES[c] + (8 - r)) as Square;
        out.push({ square: sq, type: p.type, color: p.color });
      }
    }
  }
  return out;
}

// --- material ---
const material: FeatureFn = (game) => {
  let s = 0;
  for (const p of allPieces(game)) {
    s += (p.color === "w" ? 1 : -1) * PIECE_VALUES[p.type];
  }
  return s;
};

// --- piece_position ---
const piecePosition: FeatureFn = (game) => {
  let s = 0;
  for (const p of allPieces(game)) {
    const idx = squareToIndex(p.square, p.color);
    const v = PST[p.type][idx];
    s += (p.color === "w" ? 1 : -1) * v;
  }
  return s;
};

// --- center_control ---
const CENTER: Square[] = ["d4", "e4", "d5", "e5"];
const centerControl: FeatureFn = (game) => {
  let s = 0;
  for (const sq of CENTER) {
    const piece = game.get(sq);
    if (piece) s += (piece.color === "w" ? 1 : -1) * 30;
    // attack control
    const wAtt = game.attackers(sq, "w").length;
    const bAtt = game.attackers(sq, "b").length;
    s += (wAtt - bAtt) * 10;
  }
  return s;
};

function findKing(game: Chess, color: Color): Square | null {
  for (const p of allPieces(game)) {
    if (p.type === "k" && p.color === color) return p.square;
  }
  return null;
}

function adjacentSquares(sq: Square): Square[] {
  const file = FILES.indexOf(sq[0] as typeof FILES[number]);
  const rank = parseInt(sq[1], 10);
  const out: Square[] = [];
  for (let df = -1; df <= 1; df++) {
    for (let dr = -1; dr <= 1; dr++) {
      if (df === 0 && dr === 0) continue;
      const f = file + df;
      const r = rank + dr;
      if (f >= 0 && f < 8 && r >= 1 && r <= 8) {
        out.push((FILES[f] + r) as Square);
      }
    }
  }
  return out;
}

// --- king_safety: count own pieces around king ---
const kingSafety: FeatureFn = (game) => {
  let s = 0;
  for (const color of ["w", "b"] as Color[]) {
    const k = findKing(game, color);
    if (!k) continue;
    let defenders = 0;
    for (const sq of adjacentSquares(k)) {
      const p = game.get(sq);
      if (p && p.color === color) defenders++;
    }
    s += (color === "w" ? 1 : -1) * defenders * 15;
  }
  return s;
};

// --- king_danger: attackers near opponent king ---
const kingDanger: FeatureFn = (game) => {
  let s = 0;
  for (const color of ["w", "b"] as Color[]) {
    const opp: Color = color === "w" ? "b" : "w";
    const k = findKing(game, opp);
    if (!k) continue;
    let attackers = 0;
    for (const sq of adjacentSquares(k)) {
      attackers += game.attackers(sq, color).length;
    }
    attackers += game.attackers(k, color).length * 2;
    s += (color === "w" ? 1 : -1) * attackers * 12;
  }
  return s;
};

// --- mobility ---
const mobility: FeatureFn = (game) => {
  // count moves for the side to move and approximate other
  const turn = game.turn();
  const myMoves = game.moves().length;
  // swap turn temporarily via FEN
  const fen = game.fen().split(" ");
  fen[1] = turn === "w" ? "b" : "w";
  let oppMoves = 0;
  try {
    const tmp = new (game.constructor as typeof Chess)();
    tmp.load(fen.join(" "));
    oppMoves = tmp.moves().length;
  } catch {
    oppMoves = 0;
  }
  const wMob = turn === "w" ? myMoves : oppMoves;
  const bMob = turn === "w" ? oppMoves : myMoves;
  return (wMob - bMob) * 4;
};

// --- pawn_structure: doubled / isolated penalties ---
const pawnStructure: FeatureFn = (game) => {
  let s = 0;
  const pawnsByFile: Record<Color, number[]> = {
    w: Array(8).fill(0),
    b: Array(8).fill(0),
  };
  for (const p of allPieces(game)) {
    if (p.type === "p") {
      const f = FILES.indexOf(p.square[0] as typeof FILES[number]);
      pawnsByFile[p.color][f]++;
    }
  }
  for (const color of ["w", "b"] as Color[]) {
    const sign = color === "w" ? 1 : -1;
    for (let f = 0; f < 8; f++) {
      const c = pawnsByFile[color][f];
      if (c > 1) s -= sign * 15 * (c - 1); // doubled
      if (c > 0) {
        const left = f > 0 ? pawnsByFile[color][f - 1] : 0;
        const right = f < 7 ? pawnsByFile[color][f + 1] : 0;
        if (left === 0 && right === 0) s -= sign * 20; // isolated
      }
    }
  }
  return s;
};

// --- bishop_pair ---
const bishopPair: FeatureFn = (game) => {
  let w = 0,
    b = 0;
  for (const p of allPieces(game)) {
    if (p.type === "b") {
      if (p.color === "w") w++;
      else b++;
    }
  }
  return (w >= 2 ? 50 : 0) - (b >= 2 ? 50 : 0);
};

// --- rook_activity: open files / 7th rank ---
const rookActivity: FeatureFn = (game) => {
  let s = 0;
  // collect pawn files
  const pawnFiles: Record<Color, Set<number>> = { w: new Set(), b: new Set() };
  for (const p of allPieces(game)) {
    if (p.type === "p") {
      pawnFiles[p.color].add(FILES.indexOf(p.square[0] as typeof FILES[number]));
    }
  }
  for (const p of allPieces(game)) {
    if (p.type !== "r") continue;
    const sign = p.color === "w" ? 1 : -1;
    const f = FILES.indexOf(p.square[0] as typeof FILES[number]);
    const rank = parseInt(p.square[1], 10);
    if (!pawnFiles.w.has(f) && !pawnFiles.b.has(f)) s += sign * 25; // open
    else if (!pawnFiles[p.color].has(f)) s += sign * 12; // semi-open
    if ((p.color === "w" && rank === 7) || (p.color === "b" && rank === 2)) {
      s += sign * 30; // 7th rank
    }
  }
  return s;
};

// --- capture_threats: hanging pieces / capture potential ---
const captureThreats: FeatureFn = (game) => {
  let s = 0;
  const turn = game.turn();
  const captures = game.moves({ verbose: true }).filter((m) => m.captured);
  for (const c of captures) {
    const v = PIECE_VALUES[c.captured!];
    s += (turn === "w" ? 1 : -1) * v * 0.05;
  }
  return s;
};

export const FEATURES: FeatureDef[] = [
  {
    id: "material",
    name: "Material",
    description: "Standard piece values balance.",
    defaultWeight: 1.0,
    fn: material,
  },
  {
    id: "piece_position",
    name: "Piece Position",
    description: "Piece-square table bonuses for good squares.",
    defaultWeight: 1.0,
    fn: piecePosition,
  },
  {
    id: "center_control",
    name: "Center Control",
    description: "Occupation and attack on d4/e4/d5/e5.",
    defaultWeight: 1.0,
    fn: centerControl,
  },
  {
    id: "king_safety",
    name: "King Safety",
    description: "Defenders surrounding own king.",
    defaultWeight: 1.0,
    fn: kingSafety,
  },
  {
    id: "king_danger",
    name: "King Danger",
    description: "Attackers pressuring opponent king.",
    defaultWeight: 1.0,
    fn: kingDanger,
  },
  {
    id: "mobility",
    name: "Mobility",
    description: "Difference in legal move counts.",
    defaultWeight: 1.0,
    fn: mobility,
  },
  {
    id: "pawn_structure",
    name: "Pawn Structure",
    description: "Penalties for doubled/isolated pawns.",
    defaultWeight: 1.0,
    fn: pawnStructure,
  },
  {
    id: "bishop_pair",
    name: "Bishop Pair",
    description: "Bonus for keeping both bishops.",
    defaultWeight: 1.0,
    fn: bishopPair,
  },
  {
    id: "rook_activity",
    name: "Rook Activity",
    description: "Open files and 7th rank rooks.",
    defaultWeight: 1.0,
    fn: rookActivity,
  },
  {
    id: "capture_threats",
    name: "Capture Threats",
    description: "Tactical capture potential.",
    defaultWeight: 1.0,
    fn: captureThreats,
  },
];

export function getFeature(id: string): FeatureDef | undefined {
  return FEATURES.find((f) => f.id === id);
}

// Combined evaluator from selected features + weights (white perspective, cp).
export function makeEvaluator(weights: Record<string, number>) {
  const active = FEATURES.filter((f) => (weights[f.id] ?? 0) > 0);
  return (game: Chess): number => {
    if (game.isCheckmate()) return game.turn() === "w" ? -100000 : 100000;
    if (game.isDraw() || game.isStalemate()) return 0;
    let total = 0;
    for (const f of active) {
      total += f.fn(game) * weights[f.id];
    }
    return total;
  };
}