import { Chess, type Move } from "chess.js";

export type Evaluator = (game: Chess) => number;

// Negamax with alpha-beta pruning. Returns score from side-to-move perspective.
function negamax(
  game: Chess,
  depth: number,
  alpha: number,
  beta: number,
  evaluator: Evaluator,
): number {
  if (depth === 0 || game.isGameOver()) {
    const v = evaluator(game);
    return game.turn() === "w" ? v : -v;
  }
  const moves = game.moves({ verbose: true }) as Move[];
  // Simple move ordering: captures first
  moves.sort((a, b) => (b.captured ? 1 : 0) - (a.captured ? 1 : 0));
  let best = -Infinity;
  for (const m of moves) {
    game.move(m);
    const score = -negamax(game, depth - 1, -beta, -alpha, evaluator);
    game.undo();
    if (score > best) best = score;
    if (best > alpha) alpha = best;
    if (alpha >= beta) break;
  }
  return best;
}

export function pickBestMove(
  game: Chess,
  evaluator: Evaluator,
  depth = 2,
  randomness = 0,
): Move | null {
  const moves = game.moves({ verbose: true }) as Move[];
  if (moves.length === 0) return null;
  const scored: { move: Move; score: number }[] = [];
  for (const m of moves) {
    game.move(m);
    const score =
      -negamax(game, depth - 1, -Infinity, Infinity, evaluator) +
      (randomness > 0 ? (Math.random() - 0.5) * randomness : 0);
    game.undo();
    scored.push({ move: m, score });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored[0].move;
}

// Play a full game between two engines. Returns winner: "w" | "b" | "d".
export function playGame(
  whiteEval: Evaluator,
  blackEval: Evaluator,
  options: { maxPlies?: number; depth?: number; randomness?: number } = {},
): { result: "w" | "b" | "d"; plies: number; pgn: string } {
  const { maxPlies = 120, depth = 1, randomness = 30 } = options;
  const game = new Chess();
  let plies = 0;
  while (!game.isGameOver() && plies < maxPlies) {
    const evalFn = game.turn() === "w" ? whiteEval : blackEval;
    const move = pickBestMove(game, evalFn, depth, randomness);
    if (!move) break;
    game.move(move);
    plies++;
  }
  let result: "w" | "b" | "d" = "d";
  if (game.isCheckmate()) {
    result = game.turn() === "w" ? "b" : "w";
  }
  return { result, plies, pgn: game.pgn() };
}