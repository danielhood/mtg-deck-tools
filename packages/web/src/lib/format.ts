const COLOR_ORDER = ["W", "U", "B", "R", "G"] as const;

const COLOR_NAMES: Record<string, string> = {
  W: "White",
  U: "Blue",
  B: "Black",
  R: "Red",
  G: "Green",
};

export function formatPrice(value: number | null | undefined): string {
  if (value == null) return "—";
  const rounded = Math.round(value * 100) / 100;
  if (Number.isInteger(rounded)) return `$${rounded}`;
  return `$${rounded.toFixed(2)}`;
}

export function formatColors(colors: string[]): string {
  if (!colors.length) return "Any";
  return colors
    .slice()
    .sort((a, b) => COLOR_ORDER.indexOf(a as (typeof COLOR_ORDER)[number]) - COLOR_ORDER.indexOf(b as (typeof COLOR_ORDER)[number]))
    .map((c) => COLOR_NAMES[c] ?? c)
    .join(", ");
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
