const COLOR_ORDER = ["W", "U", "B", "R", "G"] as const;

const COLOR_NAMES: Record<string, string> = {
  W: "White",
  U: "Blue",
  B: "Black",
  R: "Red",
  G: "Green",
};

/** Display label for taxonomy tag ids (matches CLI `format_tag_label` without description). */
export const RARITY_HINTS: Record<string, string> = {
  common: "All rarities allowed",
  uncommon: "Exclude commons",
  rare: "Rare and mythic only",
  mythic: "Mythic only",
};

export function chunk<T>(items: T[], size: number): T[][] {
  const rows: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    rows.push(items.slice(i, i + size));
  }
  return rows;
}

export function formatSlotLabel(slotId: string, labels: Record<string, string>): string {
  return labels[slotId] ?? formatTagLabel(slotId);
}

export function formatTagLabel(id: string): string {
  return id
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatPrice(value: number | null | undefined): string {
  if (value == null) return "—";
  const rounded = Math.round(value * 100) / 100;
  if (Number.isInteger(rounded)) return `$${rounded}`;
  return `$${rounded.toFixed(2)}`;
}

export function sortColors(colors: string[]): string[] {
  return colors
    .slice()
    .sort(
      (a, b) =>
        COLOR_ORDER.indexOf(a as (typeof COLOR_ORDER)[number]) -
        COLOR_ORDER.indexOf(b as (typeof COLOR_ORDER)[number]),
    );
}

export function formatColors(colors: string[]): string {
  if (!colors.length) return "Any";
  return sortColors(colors)
    .map((c) => COLOR_NAMES[c] ?? c)
    .join(", ");
}

/** Wireframe step 6 label — e.g. "Blue & Green". */
export function formatColorListLabel(colors: string[]): string {
  const names = sortColors(colors).map((c) => COLOR_NAMES[c] ?? c);
  if (!names.length) return "Any";
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} & ${names[1]}`;
  return `${names.slice(0, -1).join(", ")} & ${names[names.length - 1]}`;
}

export function pipMiniClass(color: string): string {
  return `pip-${color.toLowerCase()}`;
}

export function parseMoneyInput(raw: string): number | null {
  const trimmed = raw.trim().replace(/^\$/, "");
  if (!trimmed) return null;
  const value = Number.parseFloat(trimmed);
  return Number.isFinite(value) ? value : null;
}

export function formatMoneyInput(value: number | null): string {
  if (value == null) return "";
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(2);
}
