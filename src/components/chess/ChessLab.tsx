import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { FEATURES, makeEvaluator } from "@/lib/chess/features";
import { pickBestMove, playGame } from "@/lib/chess/engine";
import { Crown, Cpu, Sparkles, RotateCcw, Play, Trophy } from "lucide-react";

type Phase = "configure" | "training" | "play";

interface AgentResult {
  id: string;
  name: string;
  weights: Record<string, number>;
  wins: number;
  draws: number;
  losses: number;
  score: number; // wins + 0.5 * draws
}

function makeAgents(baseWeights: Record<string, number>): AgentResult[] {
  // Generate 4 variant agents that perturb the user's weights
  const variants: { name: string; bias: Record<string, number> }[] = [
    { name: "Aggressor", bias: { king_danger: 1.6, capture_threats: 1.4, mobility: 1.2 } },
    { name: "Fortress", bias: { king_safety: 1.6, pawn_structure: 1.4, material: 1.2 } },
    { name: "Positional", bias: { piece_position: 1.5, center_control: 1.4, bishop_pair: 1.3 } },
    { name: "Tactician", bias: { capture_threats: 1.5, mobility: 1.4, rook_activity: 1.3 } },
  ];
  return variants.map((v, i) => {
    const w: Record<string, number> = {};
    for (const f of FEATURES) {
      const base = baseWeights[f.id] ?? 0;
      const mult = v.bias[f.id] ?? 1;
      w[f.id] = base * mult;
    }
    return {
      id: `agent-${i}`,
      name: v.name,
      weights: w,
      wins: 0,
      draws: 0,
      losses: 0,
      score: 0,
    };
  });
}

export default function ChessLab() {
  const [phase, setPhase] = useState<Phase>("configure");
  const [enabled, setEnabled] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(FEATURES.map((f) => [f.id, true])),
  );
  const [weights, setWeights] = useState<Record<string, number>>(() =>
    Object.fromEntries(FEATURES.map((f) => [f.id, f.defaultWeight])),
  );

  // Training state
  const [agents, setAgents] = useState<AgentResult[]>([]);
  const [trainingLog, setTrainingLog] = useState<string[]>([]);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingTotal, setTrainingTotal] = useState(0);
  const [champion, setChampion] = useState<AgentResult | null>(null);

  // Play state
  const [game, setGame] = useState(() => new Chess());
  const [fen, setFen] = useState(() => new Chess().fen());
  const [playerColor] = useState<"w" | "b">("w");
  const [thinking, setThinking] = useState(false);
  const [status, setStatus] = useState("Your move");
  const gameRef = useRef(game);
  gameRef.current = game;

  const activeWeights = useMemo(() => {
    const w: Record<string, number> = {};
    for (const f of FEATURES) w[f.id] = enabled[f.id] ? weights[f.id] : 0;
    return w;
  }, [enabled, weights]);

  const enabledCount = Object.values(enabled).filter(Boolean).length;

  // ---- Training ----
  const runTraining = useCallback(async () => {
    setPhase("training");
    setTrainingLog([]);
    setChampion(null);
    const fresh = makeAgents(activeWeights);
    setAgents(fresh);

    const pairs: [number, number][] = [];
    for (let i = 0; i < fresh.length; i++) {
      for (let j = 0; j < fresh.length; j++) {
        if (i !== j) pairs.push([i, j]);
      }
    }
    setTrainingTotal(pairs.length);
    setTrainingProgress(0);

    const results = fresh.map((a) => ({ ...a }));
    for (let p = 0; p < pairs.length; p++) {
      const [wi, bi] = pairs[p];
      // yield to UI
      await new Promise((r) => setTimeout(r, 30));
      const { result } = playGame(
        makeEvaluator(results[wi].weights),
        makeEvaluator(results[bi].weights),
        { maxPlies: 80, depth: 1, randomness: 40 },
      );
      const log =
        result === "w"
          ? `${results[wi].name} (W) defeated ${results[bi].name} (B)`
          : result === "b"
            ? `${results[bi].name} (B) defeated ${results[wi].name} (W)`
            : `${results[wi].name} (W) drew with ${results[bi].name} (B)`;
      if (result === "w") {
        results[wi].wins++;
        results[bi].losses++;
      } else if (result === "b") {
        results[bi].wins++;
        results[wi].losses++;
      } else {
        results[wi].draws++;
        results[bi].draws++;
      }
      results.forEach((r) => (r.score = r.wins + 0.5 * r.draws));
      setAgents([...results].sort((a, b) => b.score - a.score));
      setTrainingLog((l) => [log, ...l].slice(0, 20));
      setTrainingProgress(p + 1);
    }

    const sorted = [...results].sort((a, b) => b.score - a.score);
    setChampion(sorted[0]);
  }, [activeWeights]);

  const startPlaying = useCallback(() => {
    const fresh = new Chess();
    setGame(fresh);
    setFen(fresh.fen());
    setStatus("Your move");
    setPhase("play");
  }, []);

  // ---- AI move when it's not the player's turn ----
  useEffect(() => {
    if (phase !== "play" || !champion) return;
    if (game.isGameOver()) {
      if (game.isCheckmate()) setStatus(game.turn() === playerColor ? "Checkmate — you lost" : "Checkmate — you won!");
      else setStatus("Draw");
      return;
    }
    if (game.turn() !== playerColor) {
      setThinking(true);
      setStatus(`${champion.name} is thinking…`);
      const timer = setTimeout(() => {
        const evalFn = makeEvaluator(champion.weights);
        const move = pickBestMove(game, evalFn, 2, 10);
        if (move) {
          const next = new Chess(game.fen());
          next.move(move);
          setGame(next);
          setFen(next.fen());
        }
        setThinking(false);
        setStatus("Your move");
      }, 350);
      return () => clearTimeout(timer);
    }
  }, [phase, game, champion, playerColor]);

  const onPieceDrop = useCallback(
    ({ sourceSquare, targetSquare }: { sourceSquare: string; targetSquare: string | null }) => {
      if (phase !== "play" || thinking || !targetSquare) return false;
      if (game.turn() !== playerColor) return false;
      const next = new Chess(game.fen());
      try {
        const move = next.move({ from: sourceSquare, to: targetSquare, promotion: "q" });
        if (!move) return false;
        setGame(next);
        setFen(next.fen());
        return true;
      } catch {
        return false;
      }
    },
    [game, phase, playerColor, thinking],
  );

  const resetGame = () => {
    const fresh = new Chess();
    setGame(fresh);
    setFen(fresh.fen());
    setStatus("Your move");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/15 text-primary">
              <Crown className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">ChessLab</h1>
              <p className="text-xs text-muted-foreground">Train. Tournament. Play.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${phase === "configure" ? "bg-primary" : "bg-muted-foreground/40"}`} />
              Configure
            </span>
            <span className="text-border">/</span>
            <span className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${phase === "training" ? "bg-primary" : "bg-muted-foreground/40"}`} />
              Train
            </span>
            <span className="text-border">/</span>
            <span className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${phase === "play" ? "bg-primary" : "bg-muted-foreground/40"}`} />
              Play
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-6 py-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        {/* Left — Board area */}
        <section className="space-y-4">
          <Card className="overflow-hidden border-border bg-card p-4">
            <div className="mx-auto" style={{ maxWidth: 600 }}>
              <Chessboard
                options={{
                  position: fen,
                  onPieceDrop,
                  boardOrientation: playerColor === "w" ? "white" : "black",
                  boardStyle: { borderRadius: 6, overflow: "hidden" },
                  darkSquareStyle: { backgroundColor: "#b58863" },
                  lightSquareStyle: { backgroundColor: "#f0d9b5" },
                  allowDragging: phase === "play" && !thinking && !game.isGameOver(),
                }}
              />
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm">
                <span className="text-muted-foreground">Status: </span>
                <span className="font-medium">{phase === "play" ? status : phase === "training" ? "Training engines…" : "Configure your engine to begin"}</span>
              </div>
              {phase === "play" && (
                <Button variant="outline" size="sm" onClick={resetGame} className="gap-1.5">
                  <RotateCcw className="h-3.5 w-3.5" /> New game
                </Button>
              )}
            </div>
          </Card>

          {/* Training scoreboard */}
          {phase === "training" && (
            <Card className="border-border bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold">Tournament — Round Robin</h3>
                </div>
                <span className="text-xs text-muted-foreground">
                  {trainingProgress} / {trainingTotal} games
                </span>
              </div>
              <div className="mb-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${trainingTotal ? (trainingProgress / trainingTotal) * 100 : 0}%` }}
                />
              </div>
              <div className="space-y-1.5">
                {agents.map((a, i) => (
                  <div
                    key={a.id}
                    className="flex items-center justify-between rounded-md border border-border bg-background/50 px-3 py-2 text-sm transition-all"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 text-xs text-muted-foreground">#{i + 1}</span>
                      {i === 0 && trainingProgress === trainingTotal && trainingTotal > 0 && (
                        <Trophy className="h-3.5 w-3.5 text-primary" />
                      )}
                      <span className="font-medium">{a.name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{a.wins}W</span>
                      <span>{a.draws}D</span>
                      <span>{a.losses}L</span>
                      <span className="font-semibold text-foreground">{a.score.toFixed(1)} pts</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 max-h-32 overflow-y-auto rounded-md bg-background/50 p-2 font-mono text-[11px] text-muted-foreground">
                {trainingLog.length === 0 ? (
                  <div>Waiting for games…</div>
                ) : (
                  trainingLog.map((l, i) => <div key={i}>› {l}</div>)
                )}
              </div>
              {champion && trainingProgress === trainingTotal && (
                <div className="mt-3 flex items-center justify-between rounded-md border border-primary/30 bg-primary/10 p-3">
                  <div>
                    <div className="flex items-center gap-1.5 text-xs text-primary">
                      <Trophy className="h-3.5 w-3.5" /> Champion
                    </div>
                    <div className="text-sm font-semibold">{champion.name}</div>
                  </div>
                  <Button onClick={startPlaying} className="gap-1.5">
                    <Play className="h-3.5 w-3.5" /> Play it
                  </Button>
                </div>
              )}
            </Card>
          )}
        </section>

        {/* Right — Sidebar */}
        <aside className="space-y-4">
          <Card className="border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-primary" />
                <h2 className="text-sm font-semibold">Evaluation Features</h2>
              </div>
              <Badge variant="secondary" className="text-xs">
                {enabledCount} active
              </Badge>
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
              Toggle features and tune their weights. Agents will be generated from this baseline.
            </p>

            <div className="space-y-3">
              {FEATURES.map((f) => (
                <div key={f.id} className="rounded-md border border-border bg-background/40 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium">{f.name}</div>
                      <div className="text-xs text-muted-foreground">{f.description}</div>
                    </div>
                    <Switch
                      checked={enabled[f.id]}
                      onCheckedChange={(v) => setEnabled((e) => ({ ...e, [f.id]: v }))}
                    />
                  </div>
                  {enabled[f.id] && (
                    <div className="mt-3 flex items-center gap-3">
                      <Slider
                        value={[weights[f.id]]}
                        min={0.1}
                        max={3}
                        step={0.1}
                        onValueChange={(v) => setWeights((w) => ({ ...w, [f.id]: v[0] }))}
                        className="flex-1"
                      />
                      <span className="w-10 text-right font-mono text-xs text-muted-foreground">
                        {weights[f.id].toFixed(1)}×
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <Separator className="my-4" />

            <Button
              className="w-full gap-2"
              size="lg"
              disabled={enabledCount === 0 || phase === "training"}
              onClick={runTraining}
            >
              <Sparkles className="h-4 w-4" />
              {phase === "configure" ? "Run Training Tournament" : "Re-run Tournament"}
            </Button>
            {champion && phase !== "play" && (
              <Button variant="outline" className="mt-2 w-full gap-2" onClick={startPlaying}>
                <Play className="h-4 w-4" /> Play vs {champion.name}
              </Button>
            )}
          </Card>

          <Card className="border-border bg-card p-4 text-xs text-muted-foreground">
            <div className="mb-1.5 font-medium text-foreground">How it works</div>
            <ol className="list-inside list-decimal space-y-1">
              <li>Pick which evaluation features your engine cares about.</li>
              <li>Four variant agents play a round-robin tournament.</li>
              <li>The winning evaluator becomes your opponent.</li>
            </ol>
          </Card>
        </aside>
      </main>
    </div>
  );
}