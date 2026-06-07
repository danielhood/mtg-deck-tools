export interface DeckCardPreview {
  name: string;
  type_line?: string | null;
  image_uri?: string | null;
  scryfall_uri?: string | null;
}

function normalizeScryfallHref(href: string): string {
  try {
    const url = new URL(href);
    url.hash = "";
    return url.href.replace(/\/$/, "");
  } catch {
    return href.replace(/\/$/, "");
  }
}

function addCard(map: Map<string, DeckCardPreview>, card: DeckCardPreview): void {
  if (!card.scryfall_uri) return;
  map.set(normalizeScryfallHref(card.scryfall_uri), card);
}

export function buildCardIndex(deck: Record<string, unknown> | null): Map<string, DeckCardPreview> {
  const map = new Map<string, DeckCardPreview>();
  if (!deck) return map;

  const commanders = deck.commanders;
  if (Array.isArray(commanders)) {
    for (const entry of commanders) {
      if (entry && typeof entry === "object") {
        addCard(map, entry as DeckCardPreview);
      }
    }
  }

  const cards = deck.cards;
  if (Array.isArray(cards)) {
    for (const entry of cards) {
      if (entry && typeof entry === "object") {
        addCard(map, entry as DeckCardPreview);
      }
    }
  }

  return map;
}

export function lookupCard(
  index: Map<string, DeckCardPreview>,
  href: string,
): DeckCardPreview | null {
  return index.get(normalizeScryfallHref(href)) ?? null;
}
