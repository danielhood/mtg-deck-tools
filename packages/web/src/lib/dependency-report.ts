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

/** Hide pass profiles with no counted cards — inactive criteria are noise in the dashboard. */
export function shouldDisplayProfile(profile: DependencyProfileRow): boolean {
  if (profile.status !== "pass") return true;
  return profileCardTotal(profile.counts) > 0;
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
