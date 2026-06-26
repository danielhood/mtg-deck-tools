export type ColorFilter = "any" | "colorless" | "selected";
export type ColorMatchMode = "includes" | "exact";

export interface CommanderSnapshot {
  oracle_id: string;
  name: string;
  type_line: string;
  color_identity: string[];
  partner_kind: string | null;
  edhrec_rank: number | null;
  price_usd: number | null;
  price_known: boolean;
  released_at: string | null;
  image_uri: string | null;
}

export interface WizardDraft {
  themes: string[];
  include_mechanics: string[];
  avoid_mechanics: string[];
  colors: string[];
  colorFilter: ColorFilter;
  colorMatch: ColorMatchMode;
  commander_oracle_ids: string[];
  commander_label: string | null;
  commander_search_query: string;
  commander_snapshot: CommanderSnapshot | null;
  /** Commander search price bounds (step 6); default from budget per-card min/max once. */
  commander_price_min_usd: number | null;
  commander_price_max_usd: number | null;
  commanderPriceInitialized: boolean;
  budget_usd: number | null;
  card_price_min_usd: number | null;
  card_price_max_usd: number | null;
  strict_budget: boolean;
  strict_dependencies: boolean;
  repair_dependencies: boolean;
  mechanic_focus: Record<string, string>;
  prefer_available: boolean;
  min_rarity: string;
  slot_template: Record<string, number>;
  seed: number | null;
  budgetEnabled: boolean;
  cardPriceRangeEnabled: boolean;
}

const STORAGE_KEY = "mtg-wizard-draft";

export function emptyDraft(): WizardDraft {
  return {
    themes: [],
    include_mechanics: [],
    avoid_mechanics: [],
    colors: [],
    colorFilter: "any",
    colorMatch: "exact",
    commander_oracle_ids: [],
    commander_label: null,
    commander_search_query: "",
    commander_snapshot: null,
    commander_price_min_usd: null,
    commander_price_max_usd: null,
    commanderPriceInitialized: false,
    budget_usd: null,
    card_price_min_usd: null,
    card_price_max_usd: null,
    strict_budget: false,
    strict_dependencies: true,
    repair_dependencies: true,
    mechanic_focus: {},
    prefer_available: false,
    min_rarity: "common",
    slot_template: {},
    seed: null,
    budgetEnabled: false,
    cardPriceRangeEnabled: false,
  };
}

export function loadDraft(): WizardDraft {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyDraft();
    return { ...emptyDraft(), ...JSON.parse(raw) };
  } catch {
    return emptyDraft();
  }
}

export function saveDraft(draft: WizardDraft): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
}

export function clearDraft(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}

/** Clear wizard draft — use when starting a new build from home, not when stepping back. */
export function resetDraft(): void {
  clearDraft();
}

/** Stable key for synergy profile activation (themes + include mechanics only). */
export function synergyActivationKey(draft: WizardDraft): string {
  return JSON.stringify({
    themes: draft.themes,
    include_mechanics: draft.include_mechanics,
  });
}

/** Partial criteria for synergy profile activation (themes + include mechanics only). */
export function toSynergyContextCriteria(draft: WizardDraft): Record<string, unknown> {
  return {
    themes: draft.themes,
    include_mechanics: draft.include_mechanics,
  };
}

export function toDeckCriteria(draft: WizardDraft): Record<string, unknown> {
  const colors =
    draft.colorFilter === "selected" ? [...draft.colors].sort() : [];

  return {
    themes: draft.themes,
    include_mechanics: draft.include_mechanics,
    avoid_mechanics: draft.avoid_mechanics,
    colors,
    commander_oracle_ids: draft.commander_oracle_ids,
    budget_usd: draft.budgetEnabled ? draft.budget_usd : null,
    card_price_min_usd: draft.cardPriceRangeEnabled ? draft.card_price_min_usd : null,
    card_price_max_usd: draft.cardPriceRangeEnabled ? draft.card_price_max_usd : null,
    strict_budget: draft.budgetEnabled ? draft.strict_budget : false,
    strict_dependencies: draft.strict_dependencies,
    repair_dependencies: draft.repair_dependencies,
    mechanic_focus: draft.mechanic_focus,
    prefer_available: draft.budgetEnabled ? draft.prefer_available : false,
    min_rarity: draft.min_rarity,
    slot_template: draft.slot_template,
    seed: draft.seed,
  };
}

export function commanderSearchColors(draft: WizardDraft): { colors: string[]; color_match: ColorMatchMode } {
  if (draft.colorFilter === "colorless") {
    return { colors: [], color_match: "exact" };
  }
  if (draft.colorFilter === "selected" && draft.colors.length > 0) {
    return { colors: [...draft.colors], color_match: draft.colorMatch };
  }
  return { colors: [], color_match: "includes" };
}

/** Seed commander search price bounds from budget step per-card range (once). */
export function seedCommanderPricesIfNeeded(draft: WizardDraft): WizardDraft {
  if (draft.commanderPriceInitialized) return draft;
  return {
    ...draft,
    commander_price_min_usd: draft.cardPriceRangeEnabled ? draft.card_price_min_usd : null,
    commander_price_max_usd: draft.cardPriceRangeEnabled ? draft.card_price_max_usd : null,
    commanderPriceInitialized: true,
  };
}

export function commanderSearchPriceBounds(draft: WizardDraft): {
  card_price_min_usd: number | null;
  card_price_max_usd: number | null;
} {
  return {
    card_price_min_usd: draft.commander_price_min_usd,
    card_price_max_usd: draft.commander_price_max_usd,
  };
}
