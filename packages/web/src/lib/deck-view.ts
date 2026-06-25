import { VOID_COLOR_ID } from "./color-pips";
import { parseDependencyReport, type ParsedDependencyReport } from "./dependency-report";
import { formatPrice, formatTagLabel, sortColors } from "./format";

const MANA_COLORS = ["W", "U", "B", "R", "G"] as const;
const TYPE_ORDER = [
  "Creature",
  "Instant",
  "Sorcery",
  "Enchantment",
  "Artifact",
  "Planeswalker",
  "Battle",
  "Land",
  "Other",
] as const;

export interface DeckCommander {
  oracle_id: string;
  name: string;
  type_line: string;
  color_identity: string[];
  image_uri: string | null;
  scryfall_uri: string | null;
}

export interface DeckCardRow {
  oracle_id: string;
  name: string;
  slot: string;
  quantity: number;
  cmc: number;
  mana_cost: string;
  type_line: string;
  primary_type: string;
  colors: string[];
  price_usd: number | null;
  price_known: boolean;
  image_uri: string | null;
  scryfall_uri: string | null;
}

export interface DeckStats {
  estimated_price_usd: number | null;
  unpriced_card_count: number;
  avg_cmc_nonland: number | null;
}

export interface DeckFilters {
  slots: Set<string>;
  types: Set<string>;
  colors: Set<string>;
}

export interface SlotGroup {
  slot: string;
  label: string;
  cards: DeckCardRow[];
}

export interface ParsedDeck {
  commanders: DeckCommander[];
  cards: DeckCardRow[];
  slotOrder: string[];
  slotCounts: Record<string, number>;
  stats: DeckStats;
  typeCounts: Record<string, number>;
  dependencyReport: ParsedDependencyReport;
  filterOptions: {
    slots: string[];
    types: string[];
    colors: string[];
  };
}

const DEFAULT_SLOT_ORDER = [
  "ramp",
  "draw",
  "removal",
  "protection",
  "synergy",
  "finisher",
  "lands",
];

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((entry): entry is string => typeof entry === "string");
}

export function primaryCardType(typeLine: string): string {
  const beforeDash = typeLine.split("—")[0]?.trim() ?? typeLine.trim();
  const parts = beforeDash.split(/\s+/);
  for (let i = parts.length - 1; i >= 0; i -= 1) {
    if ((TYPE_ORDER as readonly string[]).includes(parts[i])) return parts[i];
  }
  return parts.at(-1) ?? "Other";
}

function colorsFromTypeLine(typeLine: string): string[] {
  const lower = typeLine.toLowerCase();
  const found = new Set<string>();
  if (lower.includes("plains")) found.add("W");
  if (lower.includes("island")) found.add("U");
  if (lower.includes("swamp")) found.add("B");
  if (lower.includes("mountain")) found.add("R");
  if (lower.includes("forest")) found.add("G");
  return sortColors([...found]);
}

function isLandCard(typeLine: string, primaryType: string): boolean {
  return primaryType === "Land" || typeLine.toLowerCase().includes("land");
}

function filterWubrg(colors: string[]): string[] {
  return sortColors(colors.filter((color) => (MANA_COLORS as readonly string[]).includes(color)));
}

/** Colored pips in casting cost — hybrid ({W/U}) and phyrexian ({W/P}); void when none. */
export function parseManaColors(manaCost: string): string[] {
  const found = new Set<string>();
  const tokens = manaCost.match(/\{[^}]+\}/g) ?? [];

  for (const token of tokens) {
    const inner = token.slice(1, -1);
    if (inner.includes("/")) {
      for (const part of inner.split("/")) {
        if ((MANA_COLORS as readonly string[]).includes(part)) found.add(part);
      }
      continue;
    }
    if ((MANA_COLORS as readonly string[]).includes(inner)) found.add(inner);
  }

  if (found.size) return sortColors([...found]);
  return [VOID_COLOR_ID];
}

/**
 * Colors used for deck-view filters: casting pips on nonlands; produced mana (then
 * basic land type names) on lands. Lands are never tagged void — only true colorless
 * spells/artifacts use void.
 */
export function cardFilterColors(
  manaCost: string,
  typeLine: string,
  producedMana: string[] = [],
  colorIdentity: string[] = [],
): string[] {
  const primaryType = primaryCardType(typeLine);
  if (isLandCard(typeLine, primaryType)) {
    const produced = filterWubrg(producedMana);
    if (produced.length) return produced;
    const fromType = colorsFromTypeLine(typeLine);
    if (fromType.length) return fromType;
    const identity = filterWubrg(colorIdentity);
    if (identity.length) return identity;
    return [];
  }
  return parseManaColors(manaCost);
}

function parseCommander(entry: unknown): DeckCommander | null {
  const row = asRecord(entry);
  if (!row) return null;
  const oracleId = asString(row.oracle_id);
  const name = asString(row.name);
  if (!oracleId || !name) return null;
  return {
    oracle_id: oracleId,
    name,
    type_line: asString(row.type_line),
    color_identity: sortColors(asStringArray(row.color_identity)),
    image_uri: asString(row.image_uri) || null,
    scryfall_uri: asString(row.scryfall_uri) || null,
  };
}

function parseCard(entry: unknown): DeckCardRow | null {
  const row = asRecord(entry);
  if (!row) return null;
  const oracleId = asString(row.oracle_id);
  const name = asString(row.name);
  const slot = asString(row.slot);
  if (!oracleId || !name || !slot) return null;
  const typeLine = asString(row.type_line);
  const manaCost = asString(row.mana_cost);
  return {
    oracle_id: oracleId,
    name,
    slot,
    quantity: Math.max(1, asNumber(row.quantity) ?? 1),
    cmc: asNumber(row.cmc) ?? 0,
    mana_cost: manaCost,
    type_line: typeLine,
    primary_type: primaryCardType(typeLine),
    colors: cardFilterColors(
      manaCost,
      typeLine,
      asStringArray(row.produced_mana),
      asStringArray(row.color_identity),
    ),
    price_usd: asNumber(row.price_usd),
    price_known: row.price_known !== false,
    image_uri: asString(row.image_uri) || null,
    scryfall_uri: asString(row.scryfall_uri) || null,
  };
}

function slotOrderFromDeck(deck: Record<string, unknown>): string[] {
  const criteria = asRecord(deck.criteria);
  const template = criteria ? asRecord(criteria.slot_template) : null;
  if (template) {
    const keys = Object.keys(template);
    const ordered = DEFAULT_SLOT_ORDER.filter((slot) => keys.includes(slot));
    for (const key of keys) {
      if (!ordered.includes(key)) ordered.push(key);
    }
    return ordered;
  }
  return DEFAULT_SLOT_ORDER;
}

function parseStats(deck: Record<string, unknown>): DeckStats {
  const stats = asRecord(deck.stats);
  return {
    estimated_price_usd: stats ? asNumber(stats.estimated_price_usd) : null,
    unpriced_card_count: stats ? Math.max(0, asNumber(stats.unpriced_card_count) ?? 0) : 0,
    avg_cmc_nonland: stats ? asNumber(stats.avg_cmc_nonland) : null,
  };
}

export function defaultDeckName(deck: Record<string, unknown>): string {
  const commanders = Array.isArray(deck.commanders) ? deck.commanders : [];
  const names = commanders
    .map((entry) =>
      entry && typeof entry === "object" && typeof (entry as { name?: unknown }).name === "string"
        ? (entry as { name: string }).name.trim()
        : "",
    )
    .filter(Boolean);
  return names.length ? names.join(" / ") : "Untitled deck";
}

export function parseDeck(deck: Record<string, unknown> | null): ParsedDeck | null {
  if (!deck) return null;

  const commanders = (Array.isArray(deck.commanders) ? deck.commanders : [])
    .map(parseCommander)
    .filter((row): row is DeckCommander => row != null);

  const cards = (Array.isArray(deck.cards) ? deck.cards : [])
    .map(parseCard)
    .filter((row): row is DeckCardRow => row != null)
    .sort((a, b) => a.name.localeCompare(b.name));

  const slotOrder = slotOrderFromDeck(deck);
  const slotCounts: Record<string, number> = {};
  const typeCounts: Record<string, number> = {};
  for (const card of cards) {
    slotCounts[card.slot] = (slotCounts[card.slot] ?? 0) + card.quantity;
    typeCounts[card.primary_type] = (typeCounts[card.primary_type] ?? 0) + card.quantity;
  }

  const slots = [...new Set([...slotOrder, ...cards.map((card) => card.slot)])];
  const types = [...new Set(cards.map((card) => card.primary_type))].sort(
    (a, b) =>
      TYPE_ORDER.indexOf(a as (typeof TYPE_ORDER)[number]) -
        TYPE_ORDER.indexOf(b as (typeof TYPE_ORDER)[number]) || a.localeCompare(b),
  );
  const colors = [...new Set(cards.flatMap((card) => card.colors))].sort(
    (a, b) =>
      (a === VOID_COLOR_ID
        ? 99
        : MANA_COLORS.indexOf(a as (typeof MANA_COLORS)[number])) -
      (b === VOID_COLOR_ID
        ? 99
        : MANA_COLORS.indexOf(b as (typeof MANA_COLORS)[number])),
  );

  return {
    commanders,
    cards,
    slotOrder: slots,
    slotCounts,
    stats: parseStats(deck),
    typeCounts,
    dependencyReport: parseDependencyReport(deck),
    filterOptions: { slots, types, colors },
  };
}

export function emptyFilters(): DeckFilters {
  return { slots: new Set(), types: new Set(), colors: new Set() };
}

export function toggleFilterValue<T extends string>(set: Set<T>, value: T): Set<T> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

export function cardMatchesFilters(card: DeckCardRow, filters: DeckFilters): boolean {
  if (filters.slots.size && !filters.slots.has(card.slot)) return false;
  if (filters.types.size && !filters.types.has(card.primary_type)) return false;
  if (filters.colors.size) {
    if (!card.colors.length) return false;
    if (!card.colors.some((color) => filters.colors.has(color))) return false;
  }
  return true;
}

export function filteredCards(cards: DeckCardRow[], filters: DeckFilters): DeckCardRow[] {
  return cards.filter((card) => cardMatchesFilters(card, filters));
}

export function groupCardsBySlot(
  cards: DeckCardRow[],
  slotOrder: string[],
  slotLabels: Record<string, string> = {},
): SlotGroup[] {
  const bySlot = new Map<string, DeckCardRow[]>();
  for (const card of cards) {
    const rows = bySlot.get(card.slot) ?? [];
    rows.push(card);
    bySlot.set(card.slot, rows);
  }

  const groups: SlotGroup[] = [];
  for (const slot of slotOrder) {
    const slotCards = bySlot.get(slot);
    if (!slotCards?.length) continue;
    groups.push({
      slot,
      label: slotLabels[slot] ?? formatTagLabel(slot),
      cards: slotCards.sort((a, b) => a.name.localeCompare(b.name)),
    });
  }
  return groups;
}

export function formatSummaryLine(stats: DeckStats): string {
  const parts: string[] = [];
  if (stats.estimated_price_usd != null) {
    parts.push(`Estimated ${formatPrice(stats.estimated_price_usd)}`);
  }
  if (stats.unpriced_card_count > 0) {
    parts.push(
      `${stats.unpriced_card_count} unpriced card${stats.unpriced_card_count === 1 ? "" : "s"}`,
    );
  }
  if (stats.avg_cmc_nonland != null) {
    parts.push(`avg CMC ${stats.avg_cmc_nonland.toFixed(1)} (nonlands)`);
  }
  return parts.join(" · ") || "No summary stats available.";
}

export function formatSlotCountLine(
  slotCounts: Record<string, number>,
  slotOrder: string[],
  slotLabels: Record<string, string> = {},
): string {
  const parts = slotOrder
    .filter((slot) => (slotCounts[slot] ?? 0) > 0)
    .map((slot) => `${slotLabels[slot] ?? formatTagLabel(slot)} ${slotCounts[slot]}`);
  return parts.join(" · ");
}

export function formatTypeCountLine(typeCounts: Record<string, number>): string {
  return Object.entries(typeCounts)
    .sort(
      ([a], [b]) =>
        TYPE_ORDER.indexOf(a as (typeof TYPE_ORDER)[number]) -
          TYPE_ORDER.indexOf(b as (typeof TYPE_ORDER)[number]) || a.localeCompare(b),
    )
    .map(([type, count]) => `${type} ${count}`)
    .join(" · ");
}

export function formatCardPrice(card: DeckCardRow): string {
  if (!card.price_known || card.price_usd == null) return "—";
  return formatPrice(card.price_usd);
}

export function formatCardMana(card: DeckCardRow): string {
  return card.mana_cost || "—";
}

export function displayCardName(card: DeckCardRow): string {
  return card.quantity > 1 ? `${card.quantity}x ${card.name}` : card.name;
}
