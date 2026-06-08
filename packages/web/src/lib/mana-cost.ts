/** Parsed mana symbol from a Scryfall-style cost string, e.g. `{W/U}` → key `WU`. */
export interface ManaCostSymbol {
  /** Scryfall card-symbol slug (slashes removed), e.g. `WU`, `WP`, `2W`, `3`. */
  key: string;
  /** Original token including braces, e.g. `{W/U}`. */
  raw: string;
}

const SCRYFALL_SYMBOL_BASE = "https://svgs.scryfall.io/card-symbols";

/** Split `{3}{U}{U}` / `{W/U}{W/P}` into symbol tokens for rendering. */
export function parseManaCostSymbols(manaCost: string): ManaCostSymbol[] {
  const trimmed = manaCost.trim();
  if (!trimmed) return [];

  const tokens = trimmed.match(/\{[^}]+\}/g) ?? [];
  return tokens.map((raw) => ({
    raw,
    key: raw.slice(1, -1).replace(/\//g, ""),
  }));
}

export function symbolSvgUrl(key: string): string {
  return `${SCRYFALL_SYMBOL_BASE}/${encodeURIComponent(key)}.svg`;
}
