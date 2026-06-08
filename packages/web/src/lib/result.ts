const ACTIVE_ID_KEY = "mtg-active-deck-id";
const DECK_PREFIX = "mtg-deck-";
const LEGACY_KEY = "mtg-wizard-result";

export interface GenerateResultState {
  id: string;
  markdown: string;
  json_path: string;
  md_path: string;
  deck: Record<string, unknown> | null;
}

export function createDeckId(): string {
  return crypto.randomUUID();
}

function deckStorageKey(id: string): string {
  return `${DECK_PREFIX}${id}`;
}

export function saveResult(
  result: Omit<GenerateResultState, "id"> & { id?: string },
): string {
  const id = result.id ?? createDeckId();
  const state: GenerateResultState = { ...result, id };
  sessionStorage.setItem(deckStorageKey(id), JSON.stringify(state));
  sessionStorage.setItem(ACTIVE_ID_KEY, id);
  sessionStorage.removeItem(LEGACY_KEY);
  return id;
}

export function loadResult(id: string): GenerateResultState | null {
  try {
    const raw = sessionStorage.getItem(deckStorageKey(id));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<GenerateResultState>;
    if (!parsed.markdown || !parsed.id) return null;
    return {
      id: parsed.id,
      markdown: parsed.markdown,
      json_path: parsed.json_path ?? "",
      md_path: parsed.md_path ?? "",
      deck: parsed.deck ?? null,
    };
  } catch {
    return null;
  }
}

export function getActiveDeckId(): string | null {
  const id = sessionStorage.getItem(ACTIVE_ID_KEY);
  if (id) return id;
  return migrateLegacyResult()?.id ?? null;
}

export function loadActiveResult(): GenerateResultState | null {
  const id = getActiveDeckId();
  if (!id) return migrateLegacyResult();
  return loadResult(id);
}

function migrateLegacyResult(): GenerateResultState | null {
  try {
    const raw = sessionStorage.getItem(LEGACY_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<GenerateResultState>;
    if (!parsed.markdown) return null;
    const id = saveResult({
      markdown: parsed.markdown,
      json_path: parsed.json_path ?? "",
      md_path: parsed.md_path ?? "",
      deck: parsed.deck ?? null,
    });
    return loadResult(id);
  } catch {
    return null;
  }
}

export function clearResult(): void {
  const id = getActiveDeckId();
  if (id) sessionStorage.removeItem(deckStorageKey(id));
  sessionStorage.removeItem(ACTIVE_ID_KEY);
  sessionStorage.removeItem(LEGACY_KEY);
}
