import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Crown,
  Cpu,
  Sparkles,
  RotateCcw,
  Play,
  Trophy,
  Download,
  ChevronLeft,
  Zap,
} from "lucide-react";
import { FEATURES, makeEvaluator } from "@/lib/chess/features";
import { pickBestMove, playGame } from "@/lib/chess/engine";
import {
  generateAgentDefs,
  computeMarginals,
  computeSynergies,
  type AgentResult,
  type FeatureMarginal,
  type SynergyPair,
} from "@/lib/chess/analysis";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Phase = "configure" | "training" | "analysis" | "play";
type Depth = 1 | 2 | 3;

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MarginalBar({
  m,
  maxAbs,
}: {
  m: FeatureMarginal;
  maxAbs: number;
}) {
  const pct = maxAbs > 0 ? (Math.abs(m.marginal) / maxAbs) * 100 : 0;
  const pos = m.marginal >= 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-32 shrink-0 text-right text-muted-foreground truncate text-[11px]">
        {m.name}
      </span>
      <div className="relative flex-1 h-3.5 rounded-sm overflow-hidden bg-muted/25">
        <div
          className="absolute top-0 bottom-0 rounded-sm transition-all duration-500"
          style={{
            width: `${pct}%`,
            left: pos ? 0 : "auto",
            right: pos ? "auto" : 0,
            background: pos
              ? "oklch(0.68 0.17 130 / 0.75)"
              : "oklch(0.62 0.22 25 / 0.75)",
          }}
        />
      </div>
      <span
        className={`w-14 shrink-0 text-right font-mono text-[10px] ${
          pos ? "text-primary" : "text-destructive"
        }`}
      >
        {pos ? "+" : ""}
        {(m.marginal * 100).toFixed(1)}%
      </span>
    </div>
  );
}

function SynergyList({ pairs }: { pairs: SynergyPair[] }) {
  const top = pairs.slice(0, 4);
  const bot = [...pairs].reverse().slice(0, 4);
  const Row = ({
    p,
    pos,
  }: {
    p: SynergyPair;
    pos: boolean;
  }) => (
    <div
      key={`${p.featureA}-${p.featureB}`}
      className="flex justify-between items-center text-[11px] py-0.5"
    >
      <span className="text-muted-foreground truncate pr-2">
        {p.nameA} + {p.nameB}
      </span>
      <span
        className={`font-mono shrink-0 ${pos ? "text-primary" : "text-destructive"}`}
      >
        {pos ? "+" : ""}
        {(p.synergy * 100).toFixed(1)}%
      </span>
    </div>
  );
  return (
    <div className="space-y-3">
      {top.length > 0 && (
        <div>
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground mb-1">
            Best pairs
          </p>
          {top.map((p) => (
            <Row key={`t-${p.featureA}-${p.featureB}`} p={p} pos />
          ))}
        </div>
      )}
      {bot.length > 0 && (
        <div>
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground mb-1">
            Worst pairs
          </p>
          {bot.map((p) => (
            <Row key={`b-${p.featureA}-${p.featureB}`} p={p} pos={false} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ChessLab() {
  // ── Phase ────────────────────────────────────────────────────────────────
  const [phase, setPhase] = useState<Phase>("configure");

  // ── Configure state ──────────────────────────────────────────────────────
  const [enabled, setEnabled] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(FEATURES.map((f) => [f.id, true])),
  );
  const [weights, setWeights] = useState<Record<string, number>>(() =>
    Object.fromEntries(FEATURES.map((f) => [f.id, f.defaultWeight])),
  );
  const [depth, setDepth] = useState<Depth>(1);

  // ── Training state ───────────────────────────────────────────────────────
  const [agents, setAgents] = useState<AgentResult[]>([]);
  const [trainingLog, setTrainingLog] = useState<string[]>([]);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingTotal, setTrainingTotal] = useState(0);
  const [champion, setChampion] = useState<AgentResult | null>(null);

  // ── Analysis state ───────────────────────────────────────────────────────
  const [marginals, setMarginals] = useState<FeatureMarginal[]>([]);
  const [synergies, setSynergies] = useState<SynergyPair[]>([]);

  // ── Play state ───────────────────────────────────────────────────────────
  const [game, setGame] = useState(() => new Chess());
  const [fen, setFen] = useState(() => new Chess().fen());
  const [thinking, setThinking] = useState(false);
  const [playStatus, setPlayStatus] = useState("Your move");
  const gameRef = useRef(game);
  gameRef.current = game;

  // ── Derived ──────────────────────────────────────────────────────────────
  const enabledFeatures = useMemo(
    () => FEATURES.filter((f) => enabled[f.id]),
    [enabled],
  );
  const enabledCount = enabledFeatures.length;

  const featureNames = useMemo(
    () => Object.fromEntries(FEATURES.map((f) => [f.id, f.name])),
    [],
  );

  const agentCount = useMemo(() => {
    const n = enabledCount;
    if (n === 0) return 0;
    // singletons + full + leave-one-out (if n >= 3)
    return n >= 3 ? n + 1 + n : n + 1;
  }, [enabledCount]);

  const gameCount = agentCount * Math.max(agentCount - 1, 0);

  // ── Training ─────────────────────────────────────────────────────────────
  const runTraining = useCallback(async () => {
    setPhase("training");
    setTrainingLog([]);
    setChampion(null);

    const defs = generateAgentDefs(
      enabledFeatures.map((f) => f.id),
      weights,
      featureNames,
    );
    const results: AgentResult[] = defs.map((d) => ({
      ...d,
      wins: 0,
      draws: 0,
      losses: 0,
      score: 0,
    }));
    setAgents(results.map((r) => ({ ...r })));

    const pairs: [number, number][] = [];
    for (let i = 0; i < results.length; i++)
      for (let j = 0; j < results.length; j++)
        if (i !== j) pairs.push([i, j]);

    setTrainingTotal(pairs.length);
    setTrainingProgress(0);

    for (let p = 0; p < pairs.length; p++) {
      const [wi, bi] = pairs[p];
      await new Promise((r) => setTimeout(r, 8));
      const { result } = playGame(
        makeEvaluator(results[wi].weights),
        makeEvaluator(results[bi].weights),
        { maxPlies: 60, depth, randomness: 30 },
      );
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

      const log =
        result === "w"
          ? `${results[wi].name} beat ${results[bi].name}`
          : result === "b"
            ? `${results[bi].name} beat ${results[wi].name}`
            : `${results[wi].name} drew ${results[bi].name}`;

      setAgents([...results].sort((a, b) => b.score - a.score));
      setTrainingLog((l) => [log, ...l].slice(0, 30));
      setTrainingProgress(p + 1);
    }

    const sorted = [...results].sort((a, b) => b.score - a.score);
    const champ = sorted[0];
    setChampion(champ);
    setAgents(sorted);

    // Compute analysis
    const m = computeMarginals(sorted, enabledFeatures);
    const s = computeSynergies(sorted, enabledFeatures);
    setMarginals(m.sort((a, b) => b.marginal - a.marginal));
    setSynergies(s);

    setPhase("analysis");
  }, [enabledFeatures, weights, featureNames, depth]);

  // ── Start play ───────────────────────────────────────────────────────────
  const startPlaying = useCallback(() => {
    const fresh = new Chess();
    setGame(fresh);
    setFen(fresh.fen());
    setPlayStatus("Your move");
    setPhase("play");
  }, []);

  // ── AI engine reply ──────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== "play" || !champion) return;
    if (game.isGameOver()) {
      if (game.isCheckmate())
        setPlayStatus(
          game.turn() === "w" ? "Checkmate — you lost" : "You win! Checkmate",
        );
      else setPlayStatus("Draw");
      return;
    }
    if (game.turn() !== "w") {
      setThinking(true);
      setPlayStatus(`${champion.name} is thinking…`);
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
        setPlayStatus("Your move");
      }, 350);
      return () => clearTimeout(timer);
    }
  }, [phase, game, champion]);

  // ── Piece drop ───────────────────────────────────────────────────────────
  const onPieceDrop = useCallback(
    ({
      sourceSquare,
      targetSquare,
    }: {
      sourceSquare: string;
      targetSquare: string | null;
    }) => {
      if (phase !== "play" || thinking || !targetSquare) return false;
      if (game.turn() !== "w") return false;
      const next = new Chess(game.fen());
      try {
        const move = next.move({
          from: sourceSquare,
          to: targetSquare,
          promotion: "q",
        });
        if (!move) return false;
        setGame(next);
        setFen(next.fen());
        return true;
      } catch {
        return false;
      }
    },
    [game, phase, thinking],
  );

  // ── Reset game ───────────────────────────────────────────────────────────
  const resetGame = () => {
    const fresh = new Chess();
    setGame(fresh);
    setFen(fresh.fen());
    setPlayStatus("Your move");
  };

  // ── Download results ─────────────────────────────────────────────────────
  const downloadResults = () => {
    const data = {
      config: {
        depth,
        features: enabledFeatures.map((f) => ({
          id: f.id,
          name: f.name,
          weight: weights[f.id],
        })),
      },
      champion: champion
        ? {
            name: champion.name,
            score: champion.score,
            wins: champion.wins,
            draws: champion.draws,
            losses: champion.losses,
            features: champion.features,
          }
        : null,
      marginals,
      synergies: synergies.slice(0, 10),
      leaderboard: agents.map((a, i) => ({
        rank: i + 1,
        name: a.name,
        score: a.score,
        wins: a.wins,
        draws: a.draws,
        losses: a.losses,
        features: a.features,
      })),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "enginelab-results.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── Move history (play panel) ────────────────────────────────────────────
  const moveHistory = useMemo(() => {
    const hist = game.history();
    const pairs: string[] = [];
    for (let i = 0; i < hist.length; i += 2) {
      const n = Math.floor(i / 2) + 1;
      const white = hist[i];
      const black = hist[i + 1] ?? "";
      pairs.push(`${n}. ${white}${black ? " " + black : ""}`);
    }
    return pairs;
  }, [game]);

  // ── Breadcrumb steps ─────────────────────────────────────────────────────
  const steps: { key: Phase; label: string }[] = [
    { key: "configure", label: "Configure" },
    { key: "training", label: "Train" },
    { key: "analysis", label: "Analysis" },
    { key: "play", label: "Play" },
  ];

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Header ── */}
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/15 text-primary">
              <Crown className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">
                EngineLab
              </h1>
              <p className="text-xs text-muted-foreground">
                Feature-subset engine discovery
              </p>
            </div>
          </div>
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {steps.map((s, i) => (
              <span key={s.key} className="flex items-center gap-2">
                {i > 0 && <span className="text-border">/</span>}
                <span
                  className={`flex items-center gap-1.5 ${
                    phase === s.key
                      ? "text-primary font-medium"
                      : "text-muted-foreground/50"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      phase === s.key
                        ? "bg-primary"
                        : "bg-muted-foreground/25"
                    }`}
                  />
                  {s.label}
                </span>
              </span>
            ))}
          </div>
        </div>
      </header>

      {/* ── Main grid ── */}
      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-6 py-6 lg:grid-cols-[minmax(0,1fr)_400px]">
        {/* ── Left: Board ── */}
        <section className="space-y-4">
          <Card className="overflow-hidden border-border bg-card p-4">
            <div className="mx-auto" style={{ maxWidth: 560 }}>
              <Chessboard
                options={{
                  position: fen,
                  onPieceDrop,
                  boardOrientation: "white",
                  boardStyle: { borderRadius: 4, overflow: "hidden" },
                  darkSquareStyle: { backgroundColor: "#b58863" },
                  lightSquareStyle: { backgroundColor: "#f0d9b5" },
                  allowDragging:
                    phase === "play" && !thinking && !game.isGameOver(),
                }}
              />
            </div>
            <div className="mt-3 flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {phase === "play"
                  ? playStatus
                  : phase === "training"
                    ? "Tournament running…"
                    : phase === "analysis"
                      ? champion
                        ? `Champion: ${champion.name}`
                        : "Analysis complete"
                      : "Configure your engine below"}
              </span>
              {phase === "play" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetGame}
                  className="gap-1.5"
                >
                  <RotateCcw className="h-3.5 w-3.5" /> New game
                </Button>
              )}
            </div>
          </Card>

          {/* Live scoreboard — shown during training */}
          {phase === "training" && (
            <Card className="border-border bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold">
                    Tournament — Round Robin
                  </h3>
                </div>
                <span className="text-xs text-muted-foreground">
                  {trainingProgress} / {trainingTotal} games
                </span>
              </div>
              {/* Progress bar */}
              <div className="mb-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{
                    width: `${trainingTotal ? (trainingProgress / trainingTotal) * 100 : 0}%`,
                  }}
                />
              </div>
              {/* Leaderboard rows */}
              <div className="space-y-1.5">
                {agents.slice(0, 8).map((a, i) => (
                  <div
                    key={a.id}
                    className="flex items-center justify-between rounded-md border border-border bg-background/50 px-3 py-1.5 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 text-muted-foreground">
                        #{i + 1}
                      </span>
                      {i === 0 &&
                        trainingProgress === trainingTotal &&
                        trainingTotal > 0 && (
                          <Trophy className="h-3.5 w-3.5 text-primary" />
                        )}
                      <span className="font-medium truncate max-w-[120px]">
                        {a.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-muted-foreground">
                      <span>{a.wins}W</span>
                      <span>{a.draws}D</span>
                      <span>{a.losses}L</span>
                      <span className="font-semibold text-foreground w-10 text-right">
                        {a.score.toFixed(1)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {/* Game log */}
              <div className="mt-3 max-h-28 overflow-y-auto rounded-md bg-background/50 p-2 font-mono text-[11px] text-muted-foreground">
                {trainingLog.length === 0 ? (
                  <div>Starting games…</div>
                ) : (
                  trainingLog.map((l, i) => <div key={i}>› {l}</div>)
                )}
              </div>
            </Card>
          )}

          {/* Play move list — shown during play */}
          {phase === "play" && moveHistory.length > 0 && (
            <Card className="border-border bg-card p-4">
              <h3 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Move List
              </h3>
              <ScrollArea className="h-32">
                <div className="font-mono text-xs text-foreground space-y-0.5">
                  {moveHistory.map((line, i) => (
                    <div key={i} className="text-muted-foreground">
                      {line}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </Card>
          )}
        </section>

        {/* ── Right: Panel ── */}
        <aside className="space-y-4">
          {/* ── Configure panel ── */}
          {phase === "configure" && (
            <>
              <Card className="border-border bg-card p-4">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-primary" />
                    <h2 className="text-sm font-semibold">
                      Evaluation Features
                    </h2>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {enabledCount} active
                  </Badge>
                </div>
                <p className="mb-3 text-xs text-muted-foreground">
                  Toggle features and tune weights. Agents are generated as
                  subsets — enabling marginal contribution analysis.
                </p>

                {/* Depth selector */}
                <div className="mb-4 flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-12 shrink-0">
                    Depth
                  </span>
                  <div className="flex gap-1.5">
                    {([1, 2, 3] as Depth[]).map((d) => (
                      <button
                        key={d}
                        onClick={() => setDepth(d)}
                        className={`px-2.5 py-0.5 rounded text-xs font-medium border transition-colors ${
                          depth === d
                            ? "border-primary bg-primary/15 text-primary"
                            : "border-border text-muted-foreground hover:border-primary/50"
                        }`}
                      >
                        {d === 1 ? "Fast" : d === 2 ? "Normal" : "Deep"}
                      </button>
                    ))}
                  </div>
                  <span className="text-[10px] text-muted-foreground ml-auto">
                    {agentCount} agents · {gameCount.toLocaleString()} games
                  </span>
                </div>

                <Separator className="mb-3" />

                {/* Feature list */}
                <ScrollArea className="h-[420px] pr-1">
                  <div className="space-y-2.5">
                    {FEATURES.map((f) => (
                      <div
                        key={f.id}
                        className="rounded-md border border-border bg-background/40 p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="text-sm font-medium">{f.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {f.description}
                            </div>
                          </div>
                          <Switch
                            checked={enabled[f.id]}
                            onCheckedChange={(v) =>
                              setEnabled((e) => ({ ...e, [f.id]: v }))
                            }
                          />
                        </div>
                        {enabled[f.id] && (
                          <div className="mt-2.5 flex items-center gap-3">
                            <Slider
                              value={[weights[f.id]]}
                              min={0.1}
                              max={3}
                              step={0.1}
                              onValueChange={(v) =>
                                setWeights((w) => ({ ...w, [f.id]: v[0] }))
                              }
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
                </ScrollArea>

                <Separator className="my-3" />

                <Button
                  className="w-full gap-2"
                  size="lg"
                  disabled={enabledCount < 2}
                  onClick={runTraining}
                >
                  <Sparkles className="h-4 w-4" />
                  Run Training Tournament
                </Button>
                {enabledCount < 2 && (
                  <p className="mt-1.5 text-center text-xs text-muted-foreground">
                    Enable at least 2 features
                  </p>
                )}
              </Card>

              <Card className="border-border bg-card p-4 text-xs text-muted-foreground">
                <div className="mb-1.5 font-medium text-foreground">
                  How it works
                </div>
                <ol className="list-inside list-decimal space-y-1">
                  <li>Select which evaluation features matter to your engine.</li>
                  <li>
                    Agents are generated as feature subsets (singletons,
                    full set, leave-one-out) and play a round-robin
                    tournament.
                  </li>
                  <li>
                    Analysis reveals which features and pairs drive wins.
                  </li>
                  <li>Play the champion engine on the board.</li>
                </ol>
              </Card>
            </>
          )}

          {/* ── Training panel (minimal — action on left) ── */}
          {phase === "training" && (
            <Card className="border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="h-4 w-4 text-primary animate-pulse" />
                <h2 className="text-sm font-semibold">Training in progress</h2>
              </div>
              <div className="mb-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{
                    width: `${trainingTotal ? (trainingProgress / trainingTotal) * 100 : 0}%`,
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {trainingProgress} / {trainingTotal} games complete
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {agents.length} agents · depth {depth}
              </p>
              <Separator className="my-3" />
              <p className="text-xs text-muted-foreground">
                Live leaderboard and game log are shown below the board.
              </p>
            </Card>
          )}

          {/* ── Analysis panel ── */}
          {phase === "analysis" && champion && (
            <ScrollArea className="h-[calc(100vh-120px)]">
              <div className="space-y-4 pr-1">
                {/* Champion card */}
                <Card className="border-primary/30 bg-primary/8 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Trophy className="h-4 w-4 text-primary" />
                    <span className="text-xs uppercase tracking-wider text-primary font-medium">
                      Champion
                    </span>
                  </div>
                  <div className="text-base font-semibold mb-1">
                    {champion.name}
                  </div>
                  <div className="text-xs text-muted-foreground mb-2">
                    {champion.wins}W · {champion.draws}D · {champion.losses}L
                    &nbsp;·&nbsp;
                    <span className="text-primary font-medium">
                      {(
                        (champion.score /
                          Math.max(
                            champion.wins + champion.draws + champion.losses,
                            1,
                          )) *
                        100
                      ).toFixed(1)}
                      % score rate
                    </span>
                  </div>
                  {champion.features.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {champion.features.map((fid) => (
                        <span
                          key={fid}
                          className="rounded px-1.5 py-0.5 text-[10px] bg-muted text-muted-foreground border border-border"
                        >
                          {featureNames[fid] ?? fid}
                        </span>
                      ))}
                    </div>
                  )}
                  <Button onClick={startPlaying} className="w-full gap-2">
                    <Play className="h-4 w-4" /> Play vs {champion.name}
                  </Button>
                </Card>

                {/* Feature marginals */}
                <Card className="border-border bg-card p-4">
                  <h3 className="text-sm font-semibold mb-1">
                    Feature Contributions
                  </h3>
                  <p className="text-xs text-muted-foreground mb-3">
                    Win-rate impact of each feature (with vs without)
                  </p>
                  <div className="space-y-1.5">
                    {(() => {
                      const maxAbs = Math.max(
                        ...marginals.map((m) => Math.abs(m.marginal)),
                        0.001,
                      );
                      return marginals.map((m) => (
                        <MarginalBar key={m.feature} m={m} maxAbs={maxAbs} />
                      ));
                    })()}
                  </div>
                </Card>

                {/* Synergy */}
                {synergies.length > 0 && (
                  <Card className="border-border bg-card p-4">
                    <h3 className="text-sm font-semibold mb-1">
                      Feature Synergy
                    </h3>
                    <p className="text-xs text-muted-foreground mb-3">
                      Pairs that are stronger together or redundant
                    </p>
                    <SynergyList pairs={synergies} />
                  </Card>
                )}

                {/* Full leaderboard */}
                <Card className="border-border bg-card p-4">
                  <h3 className="text-sm font-semibold mb-3">Leaderboard</h3>
                  <div className="space-y-1">
                    {agents.map((a, i) => (
                      <div
                        key={a.id}
                        className={`flex items-center justify-between rounded px-2 py-1.5 text-xs ${
                          i === 0
                            ? "bg-primary/10 border border-primary/20"
                            : "bg-background/30"
                        }`}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="w-5 shrink-0 text-muted-foreground">
                            #{i + 1}
                          </span>
                          <span className="truncate font-medium max-w-[130px]">
                            {a.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground shrink-0">
                          <span className="font-mono text-foreground">
                            {(
                              (a.score /
                                Math.max(
                                  a.wins + a.draws + a.losses,
                                  1,
                                )) *
                              100
                            ).toFixed(0)}
                            %
                          </span>
                          <span>
                            {a.wins}W/{a.draws}D/{a.losses}L
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Actions */}
                <div className="flex gap-2 pb-4">
                  <Button
                    variant="outline"
                    className="flex-1 gap-1.5"
                    onClick={downloadResults}
                  >
                    <Download className="h-3.5 w-3.5" /> Export JSON
                  </Button>
                  <Button
                    variant="ghost"
                    className="flex-1 gap-1.5 text-muted-foreground"
                    onClick={() => setPhase("configure")}
                  >
                    <ChevronLeft className="h-3.5 w-3.5" /> Reconfigure
                  </Button>
                </div>
              </div>
            </ScrollArea>
          )}

          {/* ── Play panel ── */}
          {phase === "play" && champion && (
            <Card className="border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="h-3 w-3 rounded-full bg-foreground/20 border border-muted-foreground/50" />
                <span className="text-sm font-semibold">{champion.name}</span>
                <Badge variant="secondary" className="ml-auto text-[10px]">
                  Engine
                </Badge>
              </div>
              <Separator className="my-2" />
              <div className="flex items-center gap-2 mb-3">
                <div className="h-3 w-3 rounded-full bg-[#f0d9b5] border border-[#b58863]" />
                <span className="text-sm font-medium">You (White)</span>
              </div>

              {/* Status */}
              <div className="rounded-md border border-border bg-background/50 px-3 py-2 mb-3">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
                  Status
                </p>
                <p
                  className={`text-sm font-semibold ${
                    thinking
                      ? "text-muted-foreground italic"
                      : game.isGameOver()
                        ? "text-primary"
                        : "text-foreground"
                  }`}
                >
                  {playStatus}
                </p>
              </div>

              {/* Engine features */}
              <div className="mb-3">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                  Engine features
                </p>
                <div className="flex flex-wrap gap-1">
                  {champion.features.map((fid) => (
                    <span
                      key={fid}
                      className="rounded px-1.5 py-0.5 text-[10px] bg-muted text-muted-foreground border border-border"
                    >
                      {featureNames[fid] ?? fid}
                    </span>
                  ))}
                </div>
              </div>

              <Separator className="mb-3" />

              <Button
                variant="outline"
                className="w-full gap-1.5 mb-2"
                onClick={resetGame}
              >
                <RotateCcw className="h-3.5 w-3.5" /> New Game
              </Button>
              <Button
                variant="ghost"
                className="w-full gap-1.5 text-muted-foreground"
                onClick={() => setPhase("analysis")}
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Back to Analysis
              </Button>
            </Card>
          )}
        </aside>
      </main>
    </div>
  );
}
