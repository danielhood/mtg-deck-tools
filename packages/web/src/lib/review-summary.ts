import type { ActivatedProfile } from "./api";
import type { WizardDraft } from "./criteria";
import { formatColors, formatPrice, formatSlotLabel, formatTagLabel } from "./format";

export interface SummaryRow {
  label: string;
  lines: string[];
  muted?: boolean;
}

function labelList(ids: string[], labels: Record<string, string>): string[] {
  if (!ids.length) return [];
  return ids.map((id) => labels[id] ?? formatTagLabel(id));
}

function noneLine(): string[] {
  return ["(none)"];
}

export function buildSummaryRows(
  draft: WizardDraft,
  catalogs: {
    themeLabels: Record<string, string>;
    mechanicLabels: Record<string, string>;
    slotLabels: Record<string, string>;
    slotOrder: string[];
    profiles: ActivatedProfile[];
    rarityLabels: Record<string, string>;
  },
): SummaryRow[] {
  const rows: SummaryRow[] = [];

  const themes = labelList(draft.themes, catalogs.themeLabels);
  rows.push({
    label: "Themes",
    lines: themes.length ? themes : noneLine(),
    muted: !themes.length,
  });

  const include = labelList(draft.include_mechanics, catalogs.mechanicLabels);
  rows.push({
    label: "Include",
    lines: include.length ? include : noneLine(),
    muted: !include.length,
  });

  const avoid = labelList(draft.avoid_mechanics, catalogs.mechanicLabels);
  rows.push({
    label: "Avoid",
    lines: avoid.length ? avoid : noneLine(),
    muted: !avoid.length,
  });

  let colorLine = "Any (no color filter)";
  if (draft.colorFilter === "colorless") colorLine = "Colorless only";
  else if (draft.colorFilter === "selected" && draft.colors.length) {
    const match = draft.colorMatch === "exact" ? "exact" : "includes";
    colorLine = `${formatColors(draft.colors)} (${match})`;
  }
  rows.push({ label: "Colors", lines: [colorLine] });

  const commander =
    draft.commander_label ??
    (draft.commander_oracle_ids.length ? "Selected commander" : null);
  rows.push({
    label: "Commander",
    lines: commander ? [commander] : noneLine(),
    muted: !commander,
  });

  if (draft.budgetEnabled && draft.budget_usd != null) {
    const budgetLines = [`${formatPrice(draft.budget_usd)} deck budget`];
    if (draft.strict_budget) budgetLines.push("Excluded unpriced cards");
    if (draft.prefer_available) budgetLines.push("Prefer readily available");
    rows.push({ label: "Budget", lines: budgetLines });
  } else {
    rows.push({ label: "Budget", lines: noneLine(), muted: true });
  }

  if (draft.cardPriceRangeEnabled) {
    const min = draft.card_price_min_usd;
    const max = draft.card_price_max_usd;
    const parts: string[] = [];
    if (min != null) parts.push(`min ${formatPrice(min)}`);
    if (max != null) parts.push(`max ${formatPrice(max)}`);
    rows.push({
      label: "Card prices",
      lines: parts.length ? [parts.join(" · ")] : noneLine(),
      muted: !parts.length,
    });
  } else {
    rows.push({ label: "Card prices", lines: noneLine(), muted: true });
  }

  const rarity = catalogs.rarityLabels[draft.min_rarity] ?? formatTagLabel(draft.min_rarity);
  rows.push({ label: "Min rarity", lines: [rarity] });

  rows.push({
    label: "Synergy",
    lines: [
      `Strict dependencies: ${draft.strict_dependencies ? "yes" : "no"}`,
      `Repair dependencies: ${draft.repair_dependencies ? "yes" : "no"}`,
    ],
  });

  const focusLines = catalogs.profiles
    .map((profile) => {
      const level = draft.mechanic_focus[profile.profile_id];
      if (!level) return null;
      return `${profile.prompt_label} (${level})`;
    })
    .filter((line): line is string => line != null);
  rows.push({
    label: "Focus",
    lines: focusLines.length ? focusLines : noneLine(),
    muted: !focusLines.length,
  });

  return rows;
}

export function slotTemplateEntries(
  draft: WizardDraft,
  slotLabels: Record<string, string>,
  slotOrder: string[],
): { label: string; count: number }[] {
  return slotOrder
    .map((slotId) => ({
      label: formatSlotLabel(slotId, slotLabels),
      count: draft.slot_template[slotId] ?? 0,
    }))
    .filter((row) => row.count > 0);
}
