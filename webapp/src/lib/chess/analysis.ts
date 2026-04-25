import type { FeatureDef } from "./features";

export interface AgentResult {
  id: string;
  name: string;
  features: string[];
  weights: Record<string, number>;
  wins: number;
  draws: number;
  losses: number;
  score: number; // wins + 0.5 * draws
}

export interface FeatureMarginal {
  feature: string;
  name: string;
  marginal: number; // avg score-rate with feature minus avg score-rate without
  avgWith: number;
  avgWithout: number;
}

export interface SynergyPair {
  featureA: string;
  featureB: string;
  nameA: string;
  nameB: string;
  synergy: number; // avg_both - (avg_a_only + avg_b_only) / 2
}

function scoreRate(a: AgentResult): number {
  const games = a.wins + a.draws + a.losses;
  return games > 0 ? a.score / games : 0;
}

function avg(xs: number[]): number {
  return xs.length > 0 ? xs.reduce((s, x) => s + x, 0) / xs.length : 0;
}

export function computeMarginals(
  results: AgentResult[],
  features: FeatureDef[],
): FeatureMarginal[] {
  return features.map((f) => {
    const withF = results.filter((a) => a.features.includes(f.id));
    const withoutF = results.filter((a) => !a.features.includes(f.id));
    const avgWith = avg(withF.map(scoreRate));
    const avgWithout = avg(withoutF.map(scoreRate));
    return {
      feature: f.id,
      name: f.name,
      marginal: avgWith - avgWithout,
      avgWith,
      avgWithout,
    };
  });
}

export function computeSynergies(
  results: AgentResult[],
  features: FeatureDef[],
): SynergyPair[] {
  const pairs: SynergyPair[] = [];
  for (let i = 0; i < features.length; i++) {
    for (let j = i + 1; j < features.length; j++) {
      const fi = features[i];
      const fj = features[j];
      const both = results.filter(
        (a) => a.features.includes(fi.id) && a.features.includes(fj.id),
      );
      const iOnly = results.filter(
        (a) => a.features.includes(fi.id) && !a.features.includes(fj.id),
      );
      const jOnly = results.filter(
        (a) => !a.features.includes(fi.id) && a.features.includes(fj.id),
      );
      if (both.length === 0) continue;
      const avgBoth = avg(both.map(scoreRate));
      const avgIOny = avg(iOnly.map(scoreRate));
      const avgJOnly = avg(jOnly.map(scoreRate));
      pairs.push({
        featureA: fi.id,
        featureB: fj.id,
        nameA: fi.name,
        nameB: fj.name,
        synergy: avgBoth - (avgIOny + avgJOnly) / 2,
      });
    }
  }
  return pairs.sort((a, b) => b.synergy - a.synergy);
}

/** Generate agent definitions: singletons + full + leave-one-out */
export function generateAgentDefs(
  selectedFeatures: string[],
  weights: Record<string, number>,
  featureNames: Record<string, string>,
): Omit<AgentResult, "wins" | "draws" | "losses" | "score">[] {
  const makeW = (feats: string[]) =>
    Object.fromEntries(feats.map((f) => [f, weights[f] ?? 1.0]));

  const defs: Omit<AgentResult, "wins" | "draws" | "losses" | "score">[] = [];

  // Singletons: each feature alone
  for (const f of selectedFeatures) {
    defs.push({
      id: `s-${f}`,
      name: featureNames[f] ?? f,
      features: [f],
      weights: makeW([f]),
    });
  }

  // Full: all selected features together
  defs.push({
    id: "full",
    name: "All Features",
    features: [...selectedFeatures],
    weights: makeW(selectedFeatures),
  });

  // Leave-one-out: each feature removed from the full set
  if (selectedFeatures.length >= 3) {
    for (const f of selectedFeatures) {
      const sub = selectedFeatures.filter((x) => x !== f);
      defs.push({
        id: `loo-${f}`,
        name: `No ${featureNames[f] ?? f}`,
        features: sub,
        weights: makeW(sub),
      });
    }
  }

  return defs;
}
