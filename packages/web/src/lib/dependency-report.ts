/** Dependency rule labels — keep in sync with `shipped-inventory.md` validation rules table. */
export const RULE_LABELS: Record<string, string> = {
  TUTOR_TARGET_EXISTS: "Tutor target",
  ENERGY_BALANCE: "Energy balance",
  EXPERIENCE_BALANCE: "Experience balance",
  BLOOD_BALANCE: "Blood balance",
  RAD_BALANCE: "Rad balance",
  OIL_BALANCE: "Oil balance",
  CHARGE_BALANCE: "Charge balance",
  PLUS_ONE_BALANCE: "+1/+1 balance",
  SACRIFICE_BALANCE: "Sacrifice balance",
  TOKEN_BALANCE: "Token balance",
  TOKEN_SUBTYPE_BUFF_SUPPORT: "Token subtype buff",
  VEHICLE_BALANCE: "Vehicle balance",
  EQUIPMENT_BALANCE: "Equipment balance",
  TYPE_SYNERGY_MIN: "Subtype synergy",
  AURA_SUPPORT_MIN: "Aura support",
  ENCHANTMENT_SUPPORT_MIN: "Enchantment support",
  REANIMATION_SUPPORT: "Reanimation support",
  GRAVEYARD_COST_SUPPORT: "Graveyard cost support",
  SELF_MILL_BALANCE: "Self-mill balance",
  LANDFALL_BALANCE: "Landfall balance",
};

/** Wizard step-3 profile labels — keep in sync with `WIZARD_FOCUS_PROMPT_LABELS` (Python). */
export const PROFILE_PROMPT_LABELS: Record<string, string> = {
  energy: "Energy focus",
  aura_support: "Aura support",
  rad: "Rad counter focus",
  oil: "Oil counter focus",
  charge: "Charge counter focus",
  experience: "Experience focus",
  blood: "Blood counter focus",
  plus_one: "+1/+1 counter focus",
  vehicles: "Vehicle focus",
  equipment: "Equipment focus",
  tokens: "Token focus",
  sacrifice: "Sacrifice package focus",
  enchantments: "Enchantment focus",
  graveyard: "Graveyard focus",
  landfall: "Landfall focus",
};

export type DependencyStatus = "pass" | "warn" | "fail";

export interface DependencyProfileRow {
  profile_id: string;
  label: string;
  status: DependencyStatus;
  counts: Record<string, number>;
  messages: string[];
}

export interface DependencyIssueRow {
  rule_id: string;
  rule_label: string;
  status: DependencyStatus;
  message: string;
  card_name: string | null;
  card_oracle_id: string | null;
  profile_id: string | null;
  profile_label: string | null;
  detail: Record<string, unknown>;
}

export interface DetailBlock {
  kind: "list" | "scalar" | "json";
  label: string;
  items?: string[];
  text?: string;
  json?: string;
}

export interface ParsedDependencyReport {
  hasReport: boolean;
  passed: boolean;
  reviewCount: number;
  hasFail: boolean;
  defaultOpen: boolean;
  summaryHint: string;
  summaryTone: "pass" | "warn" | "neutral";
  profiles: DependencyProfileRow[];
  issues: DependencyIssueRow[];
}

const STATUS_RANK: Record<DependencyStatus, number> = {
  fail: 0,
  warn: 1,
  pass: 2,
};

const DETAIL_LIST_KEYS = new Set([
  "producers",
  "consumers",
  "outlets",
  "payoffs",
  "mill_enabler",
  "graveyard_payoff",
  "equipment_cards",
  "equip_payoffs",
]);

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
  return value.filter((entry): entry is string => typeof entry === "string" && entry.length > 0);
}

function parseStatus(value: unknown): DependencyStatus {
  if (value === "fail" || value === "warn" || value === "pass") return value;
  return "warn";
}

export function profileLabel(profileId: string): string {
  if (!profileId) return "Unknown profile";
  return (
    PROFILE_PROMPT_LABELS[profileId] ??
    profileId
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ")
  );
}

export function ruleLabel(ruleId: string): string {
  if (!ruleId) return "Unknown rule";
  return (
    RULE_LABELS[ruleId] ??
    ruleId
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
      .join(" ")
  );
}

function formatDetailLabel(key: string): string {
  if (DETAIL_LIST_KEYS.has(key)) {
    return key
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }
  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatReviewSummary(count: number): string {
  if (count === 0) return "Looks good";
  return `${count} area${count === 1 ? "" : "s"} to review`;
}

export function issueSwapOracleIds(
  issue: DependencyIssueRow,
  cards: IssueSwapCard[],
  strategyId?: string | null,
): string[] {
  const nameListKeys = [
    ...DETAIL_LIST_KEYS,
    "equip_payoffs",
    "equipment_cards",
    "tutor",
  ] as const;

  if (issue.card_oracle_id) {
    const card = cards.find((row) => row.oracle_id === issue.card_oracle_id);
    if (card && !card.locked) return [issue.card_oracle_id];
  }

  const names = new Set<string>();
  if (issue.card_name?.trim()) names.add(issue.card_name.trim());

  for (const key of nameListKeys) {
    const value = issue.detail[key];
    if (!Array.isArray(value)) continue;
    for (const item of value) {
      if (typeof item === "string" && item.trim()) names.add(item.trim());
    }
  }

  const ids: string[] = [];
  for (const name of names) {
    const card = cards.find((row) => row.name === name);
    if (card && !card.locked) ids.push(card.oracle_id);
  }
  const unique = [...new Set(ids)];
  if (unique.length) return unique;

  return issueSwapFallbackTargets(issue, cards, strategyId);
}

const ISSUE_SWAP_FLEX_SLOTS = new Set(["flex", "synergy"]);
const ISSUE_SWAP_FALLBACK_LIMIT = 3;

function unlockedIssueCards(cards: IssueSwapCard[]): IssueSwapCard[] {
  return cards.filter((card) => !card.locked);
}

function flexSlotTargets(cards: IssueSwapCard[], limit = ISSUE_SWAP_FALLBACK_LIMIT): string[] {
  return unlockedIssueCards(cards)
    .filter((card) => card.slot != null && ISSUE_SWAP_FLEX_SLOTS.has(card.slot))
    .slice(0, limit)
    .map((card) => card.oracle_id);
}

function equipmentTypeTargets(cards: IssueSwapCard[]): string[] {
  return unlockedIssueCards(cards)
    .filter((card) => (card.type_line ?? "").includes("Equipment"))
    .map((card) => card.oracle_id);
}

function vehicleTypeTargets(cards: IssueSwapCard[]): string[] {
  return unlockedIssueCards(cards)
    .filter((card) => (card.type_line ?? "").includes("Vehicle"))
    .map((card) => card.oracle_id);
}

/** Heuristic vacate targets when the issue detail has counts but no card names. */
export function issueSwapFallbackTargets(
  issue: DependencyIssueRow,
  cards: IssueSwapCard[],
  strategyId?: string | null,
): string[] {
  const deficit = issueDeficit(issue);

  if (issue.rule_id === "EQUIPMENT_BALANCE") {
    if (strategyId === "trim_equipment") {
      const equipment = equipmentTypeTargets(cards);
      if (equipment.length) return equipment;
    }
    return flexSlotTargets(cards);
  }

  if (issue.rule_id === "VEHICLE_BALANCE") {
    if (strategyId === "add_pilots" || deficit === "creatures") {
      const vehicles = vehicleTypeTargets(cards);
      if (vehicles.length) return vehicles.slice(0, ISSUE_SWAP_FALLBACK_LIMIT);
    }
    return flexSlotTargets(cards);
  }

  if (issue.rule_id === "TOKEN_BALANCE" || issue.rule_id === "ENERGY_BALANCE") {
    return flexSlotTargets(cards);
  }

  return [];
}

/** UX12 playbook-backed dependency rules. */
export const SWAP_PLAYBOOK_RULES = new Set([
  "EQUIPMENT_BALANCE",
  "VEHICLE_BALANCE",
  "TOKEN_BALANCE",
  "ENERGY_BALANCE",
]);

export function issueDeficit(issue: DependencyIssueRow): string | null {
  const deficit = issue.detail.deficit;
  return typeof deficit === "string" && deficit.trim() ? deficit.trim() : null;
}

/** UX12 playbook-backed dependency rules. */
export const SWAP_PLAYBOOK_RULES = new Set([
  "EQUIPMENT_BALANCE",
  "VEHICLE_BALANCE",
  "TOKEN_BALANCE",
  "ENERGY_BALANCE",
]);

export function issueDeficit(issue: DependencyIssueRow): string | null {
  const deficit = issue.detail.deficit;
  return typeof deficit === "string" && deficit.trim() ? deficit.trim() : null;
}

export interface IssueSwapCard {
  oracle_id: string;
  name: string;
  locked: boolean;
  slot?: string;
  type_line?: string;
}

export function buildDetailBlocks(detail: Record<string, unknown>): DetailBlock[] {
  const blocks: DetailBlock[] = [];
  const consumed = new Set<string>();

  for (const key of DETAIL_LIST_KEYS) {
    if (!(key in detail)) continue;
    const items = asStringArray(detail[key]);
    consumed.add(key);
    if (!items.length) continue;
    blocks.push({ kind: "list", label: formatDetailLabel(key), items });
  }

  for (const [key, value] of Object.entries(detail)) {
    if (consumed.has(key)) continue;
    if (Array.isArray(value)) {
      const items = asStringArray(value);
      if (items.length) {
        blocks.push({ kind: "list", label: formatDetailLabel(key), items });
      } else {
        blocks.push({
          kind: "json",
          label: formatDetailLabel(key),
          json: JSON.stringify(value, null, 2),
        });
      }
      consumed.add(key);
      continue;
    }
    if (value !== null && typeof value === "object") {
      blocks.push({
        kind: "json",
        label: formatDetailLabel(key),
        json: JSON.stringify(value, null, 2),
      });
      consumed.add(key);
      continue;
    }
    if (value === null || value === undefined) continue;
    blocks.push({
      kind: "scalar",
      label: formatDetailLabel(key),
      text: String(value),
    });
    consumed.add(key);
  }

  return blocks;
}

function sortProfiles(profiles: DependencyProfileRow[]): DependencyProfileRow[] {
  return [...profiles].sort((a, b) => {
    const rank = STATUS_RANK[a.status] - STATUS_RANK[b.status];
    if (rank !== 0) return rank;
    return a.label.localeCompare(b.label);
  });
}

function sortIssues(issues: DependencyIssueRow[]): DependencyIssueRow[] {
  return [...issues].sort((a, b) => {
    const rank = STATUS_RANK[a.status] - STATUS_RANK[b.status];
    if (rank !== 0) return rank;
    return a.rule_id.localeCompare(b.rule_id);
  });
}

function profileCardTotal(counts: Record<string, number>): number {
  return Object.values(counts).reduce((sum, count) => sum + count, 0);
}

/**
 * Count keys that indicate a profile is materially present in the deck.
 * Ancillary stats (e.g. carrier_creature on equipment, land_ramp without landfall payoffs)
 * must not keep an otherwise inactive profile visible.
 */
const PROFILE_RELEVANCE_KEYS: Record<string, readonly string[]> = {
  energy: ["producer", "consumer"],
  sacrifice: ["outlet", "payoff", "opponent_sacrifice", "death_recursion"],
  tokens: ["producer", "payoff"],
  tokens_subtype: ["produce_subtypes", "buff_subtypes"],
  vehicles: ["vehicle"],
  equipment: ["equipment", "equip_payoff"],
  aura_support: ["aura_spell"],
  enchantments: ["enchantment_spell"],
  graveyard_reanimation: ["reanimate"],
  graveyard_cost: ["graveyard_cost"],
  graveyard_self_mill: ["mill_enabler", "graveyard_payoff"],
  landfall: ["landfall_payoff"],
  experience: ["producer", "consumer"],
  blood: ["producer", "consumer"],
  plus_one: ["producer", "consumer"],
  rad: ["producer", "consumer"],
  oil: ["producer", "consumer"],
  charge: ["producer", "consumer"],
};

function profileHasRelevantCounts(profile: DependencyProfileRow): boolean {
  const keys = PROFILE_RELEVANCE_KEYS[profile.profile_id];
  if (keys?.length) {
    return keys.some((key) => (profile.counts[key] ?? 0) > 0);
  }
  return profileCardTotal(profile.counts) > 0;
}

/** Hide pass profiles with no relevant cards — inactive criteria are noise in the dashboard. */
export function shouldDisplayProfile(profile: DependencyProfileRow): boolean {
  if (profile.status !== "pass") return true;
  return profileHasRelevantCounts(profile);
}

function parseIssue(entry: unknown): DependencyIssueRow | null {
  const row = asRecord(entry);
  if (!row) return null;
  const status = parseStatus(row.status);
  if (status === "pass") return null;
  const ruleId = asString(row.rule_id);
  const message = asString(row.message);
  if (!ruleId || !message) return null;
  const profileId = asString(row.profile_id) || null;
  return {
    rule_id: ruleId,
    rule_label: ruleLabel(ruleId),
    status,
    message,
    card_name: asString(row.card_name) || null,
    card_oracle_id: asString(row.card_oracle_id) || null,
    profile_id: profileId,
    profile_label: profileId ? profileLabel(profileId) : null,
    detail: asRecord(row.detail) ?? {},
  };
}

export function parseDependencyReport(deck: Record<string, unknown>): ParsedDependencyReport {
  const report = asRecord(deck.dependency_report);
  if (!report) {
    return {
      hasReport: false,
      passed: true,
      reviewCount: 0,
      hasFail: false,
      defaultOpen: false,
      summaryHint: "",
      summaryTone: "neutral",
      profiles: [],
      issues: [],
    };
  }

  const profiles = (Array.isArray(report.profiles) ? report.profiles : [])
    .map((entry) => {
      const row = asRecord(entry);
      if (!row) return null;
      const profileId = asString(row.profile_id);
      if (!profileId) return null;
      const counts: Record<string, number> = {};
      const countsRow = asRecord(row.counts);
      if (countsRow) {
        for (const [key, value] of Object.entries(countsRow)) {
          const num = asNumber(value);
          if (num != null) counts[key] = num;
        }
      }
      return {
        profile_id: profileId,
        label: profileLabel(profileId),
        status: parseStatus(row.status),
        counts,
        messages: asStringArray(row.messages),
      };
    })
    .filter((row): row is DependencyProfileRow => row != null);

  const issues = (Array.isArray(report.issues) ? report.issues : [])
    .map(parseIssue)
    .filter((row): row is DependencyIssueRow => row != null);

  const reviewCount = issues.length;
  const hasFail = issues.some((issue) => issue.status === "fail");
  const passed = report.passed === true;
  const looksGood = passed || reviewCount === 0;

  return {
    hasReport: true,
    passed,
    reviewCount,
    hasFail,
    defaultOpen: reviewCount > 0,
    summaryHint: looksGood ? "Looks good" : formatReviewSummary(reviewCount),
    summaryTone: looksGood ? "pass" : "warn",
    profiles: sortProfiles(profiles.filter(shouldDisplayProfile)),
    issues: sortIssues(issues),
  };
}
