const DECK_PREFIX = "mtg-deck-cache-";

export interface DeckCacheState {
  id: string;
  name: string;
  deck: Record<string, unknown>;
  returnTo: string;
}

function deckStorageKey(id: string): string {
  return `${DECK_PREFIX}${id}`;
}

export function cacheDeck(state: Omit<DeckCacheState, "returnTo"> & { returnTo?: string }): void {
  const payload: DeckCacheState = {
    id: state.id,
    name: state.name,
    deck: state.deck,
    returnTo: state.returnTo ?? "/library",
  };
  sessionStorage.setItem(deckStorageKey(state.id), JSON.stringify(payload));
}

export function loadCachedDeck(id: string): DeckCacheState | null {
  try {
    const raw = sessionStorage.getItem(deckStorageKey(id));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<DeckCacheState>;
    if (!parsed.id || !parsed.name || !parsed.deck) return null;
    return {
      id: parsed.id,
      name: parsed.name,
      deck: parsed.deck,
      returnTo: parsed.returnTo ?? "/library",
    };
  } catch {
    return null;
  }
}

export function updateCachedDeckName(id: string, name: string): void {
  const cached = loadCachedDeck(id);
  if (!cached) return;
  cacheDeck({ ...cached, name });
}

export function updateCachedDeck(id: string, deck: Record<string, unknown>): void {
  const cached = loadCachedDeck(id);
  if (!cached) return;
  cacheDeck({ ...cached, deck });
}

export function removeCachedDeck(id: string): void {
  sessionStorage.removeItem(deckStorageKey(id));
}

export function clearDeckCache(): void {
  const keys: string[] = [];
  for (let i = 0; i < sessionStorage.length; i += 1) {
    const key = sessionStorage.key(i);
    if (key?.startsWith(DECK_PREFIX)) keys.push(key);
  }
  for (const key of keys) sessionStorage.removeItem(key);
}
