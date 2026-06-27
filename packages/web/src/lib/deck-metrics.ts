import type { DeckCardRow } from "./deck-view";
import { formatTagLabel } from "./format";

export const CMC_BUCKETS = ["0", "1", "2", "3", "4", "5", "6", "7", "7+"] as const;

export type CmcBucket = (typeof CMC_BUCKETS)[number];
export type CurveView = "nonlands" | "creatures";

export interface CmcHistogram {
  [bucket: string]: number;
}

export interface CurveAdvisory {
  rule: string;
  status: string;
  message: string;
  actual_share: number;
  threshold: number;
  histogram: string;
}

export interface DeckMetrics {
  cmc_histogram: CmcHistogram;
  creature_cmc_histogram: CmcHistogram;
  type_counts: Record<string, number>;
  avg_cmc_nonland: number | null;
  avg_creature_cmc: number | null;
  land_count: number;
  ramp_count: number;
  curve_advisories?: CurveAdvisory[];
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return null;
}

function emptyHistogram(): CmcHistogram {
  return Object.fromEntries(CMC_BUCKETS.map((bucket) => [bucket, 0]));
}

function isLand(typeLine: string): boolean {
  return typeLine.toLowerCase().includes("land");
}

function isCreature(typeLine: string): boolean {
  return typeLine.includes("Creature") && !typeLine.includes("Vehicle");
}

function cmcBucket(cmc: number): CmcBucket {
  if (cmc >= 7) return "7+";
  return String(Math.trunc(cmc)) as CmcBucket;
}

export function cmcHistogramFromCards(
  cards: DeckCardRow[],
  options: { creaturesOnly?: boolean; excludeLands?: boolean } = {},
): CmcHistogram {
  const { creaturesOnly = false, excludeLands = true } = options;
  const counts = emptyHistogram();
  for (const card of cards) {
    const typeLine = card.type_line ?? "";
    if (excludeLands && isLand(typeLine)) continue;
    if (creaturesOnly && !isCreature(typeLine)) continue;
    const bucket = cmcBucket(card.cmc);
    counts[bucket] = (counts[bucket] ?? 0) + card.quantity;
  }
  return counts;
}

function avgCmc(cards: DeckCardRow[], predicate: (typeLine: string) => boolean): number | null {
  let totalCmc = 0;
  let totalQty = 0;
  for (const card of cards) {
    if (!predicate(card.type_line ?? "")) continue;
    totalCmc += card.cmc * card.quantity;
    totalQty += card.quantity;
  }
  if (totalQty === 0) return null;
  return Math.round((totalCmc / totalQty) * 100) / 100;
}

export function computeDeckMetricsFromCards(cards: DeckCardRow[]): DeckMetrics {
  const typeCounts: Record<string, number> = {};
  let landCount = 0;
  let rampCount = 0;

  for (const card of cards) {
    typeCounts[card.primary_type] = (typeCounts[card.primary_type] ?? 0) + card.quantity;
    if (isLand(card.type_line ?? "")) landCount += card.quantity;
    if (card.slot === "ramp") rampCount += card.quantity;
  }

  return {
    cmc_histogram: cmcHistogramFromCards(cards),
    creature_cmc_histogram: cmcHistogramFromCards(cards, { creaturesOnly: true }),
    type_counts: typeCounts,
    avg_cmc_nonland: avgCmc(cards, (tl) => !isLand(tl)),
    avg_creature_cmc: avgCmc(cards, (tl) => isCreature(tl)),
    land_count: landCount,
    ramp_count: rampCount,
  };
}

function parseHistogram(value: unknown): CmcHistogram | null {
  const row = asRecord(value);
  if (!row) return null;
  const hist = emptyHistogram();
  let hasValue = false;
  for (const bucket of CMC_BUCKETS) {
    const count = asNumber(row[bucket]);
    if (count != null && count > 0) {
      hist[bucket] = Math.max(0, Math.trunc(count));
      hasValue = true;
    }
  }
  return hasValue ? hist : null;
}

function parseTypeCounts(value: unknown): Record<string, number> | null {
  const row = asRecord(value);
  if (!row) return null;
  const counts: Record<string, number> = {};
  for (const [key, raw] of Object.entries(row)) {
    const count = asNumber(raw);
    if (count != null && count > 0) counts[key] = Math.trunc(count);
  }
  return Object.keys(counts).length ? counts : null;
}

function parseCurveAdvisories(value: unknown): CurveAdvisory[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const advisories: CurveAdvisory[] = [];
  for (const item of value) {
    const row = asRecord(item);
    if (!row) continue;
    const rule = typeof row.rule === "string" ? row.rule : "";
    const message = typeof row.message === "string" ? row.message : "";
    const status = typeof row.status === "string" ? row.status : "warn";
    const histogram = typeof row.histogram === "string" ? row.histogram : "nonlands";
    const actualShare = asNumber(row.actual_share);
    const threshold = asNumber(row.threshold);
    if (!rule || !message || actualShare == null || threshold == null) continue;
    advisories.push({
      rule,
      status,
      message,
      actual_share: actualShare,
      threshold,
      histogram,
    });
  }
  return advisories.length ? advisories : undefined;
}

function statsHaveMetrics(stats: Record<string, unknown>): boolean {
  return parseHistogram(stats.cmc_histogram) != null;
}

export function parseDeckMetrics(
  stats: unknown,
  cards: DeckCardRow[],
): DeckMetrics | null {
  const fromCards = computeDeckMetricsFromCards(cards);
  const row = asRecord(stats);
  if (!row || !statsHaveMetrics(row)) {
    const total = sumHistogram(fromCards.cmc_histogram);
    return total > 0 ? fromCards : null;
  }

  return {
    cmc_histogram: parseHistogram(row.cmc_histogram) ?? fromCards.cmc_histogram,
    creature_cmc_histogram:
      parseHistogram(row.creature_cmc_histogram) ?? fromCards.creature_cmc_histogram,
    type_counts: parseTypeCounts(row.type_counts) ?? fromCards.type_counts,
    avg_cmc_nonland: asNumber(row.avg_cmc_nonland) ?? fromCards.avg_cmc_nonland,
    avg_creature_cmc: asNumber(row.avg_creature_cmc) ?? fromCards.avg_creature_cmc,
    land_count: Math.max(0, asNumber(row.land_count) ?? fromCards.land_count),
    ramp_count: Math.max(0, asNumber(row.ramp_count) ?? fromCards.ramp_count),
    curve_advisories: parseCurveAdvisories(row.curve_advisories),
  };
}

export function sumHistogram(histogram: CmcHistogram): number {
  return CMC_BUCKETS.reduce((sum, bucket) => sum + (histogram[bucket] ?? 0), 0);
}

export function maxHistogramCount(histogram: CmcHistogram): number {
  return Math.max(0, ...CMC_BUCKETS.map((bucket) => histogram[bucket] ?? 0));
}

export function histogramForView(metrics: DeckMetrics, view: CurveView): CmcHistogram {
  return view === "creatures" ? metrics.creature_cmc_histogram : metrics.cmc_histogram;
}

export function curveBlurb(histogram: CmcHistogram, advisories?: CurveAdvisory[]): string {
  const total = sumHistogram(histogram);
  if (total === 0) return "No cards to chart for this view.";
  const matching = (advisories ?? []).filter((item) => item.histogram === "nonlands");
  if (matching.length) return matching.map((item) => item.message).join(" ");
  const early =
    (histogram["0"] ?? 0) + (histogram["1"] ?? 0) + (histogram["2"] ?? 0);
  const top =
    (histogram["5"] ?? 0) +
    (histogram["6"] ?? 0) +
    (histogram["7"] ?? 0) +
    (histogram["7+"] ?? 0);
  const earlyShare = early / total;
  const topShare = top / total;
  if (earlyShare < 0.15) return "Light early game — few cards at 0–2 CMC.";
  if (topShare > 0.45) return "Top-heavy curve — many cards at 5+ CMC.";
  return "Mana curve is spread across several CMC bands.";
}

/** Human-readable title for a curve advisory rule id (e.g. CURVE_TOP_HEAVY). */
export function formatCurveAdvisoryTitle(rule: string): string {
  const withoutPrefix = rule.startsWith("CURVE_") ? rule.slice("CURVE_".length) : rule;
  return formatTagLabel(withoutPrefix);
}

export function formatMetricsSummary(metrics: DeckMetrics): string {
  const parts: string[] = [];
  if (metrics.avg_cmc_nonland != null) {
    parts.push(`Avg nonland CMC ${metrics.avg_cmc_nonland.toFixed(1)}`);
  }
  if (metrics.avg_creature_cmc != null) {
    parts.push(`Avg creature CMC ${metrics.avg_creature_cmc.toFixed(1)}`);
  }
  if (metrics.land_count > 0) parts.push(`${metrics.land_count} lands`);
  if (metrics.ramp_count > 0) parts.push(`${metrics.ramp_count} ramp`);
  return parts.join(" · ");
}
