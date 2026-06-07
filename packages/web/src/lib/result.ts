const STORAGE_KEY = "mtg-wizard-result";

export interface GenerateResultState {
  markdown: string;
  json_path: string;
  md_path: string;
  deck: Record<string, unknown> | null;
}

export function saveResult(result: GenerateResultState): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(result));
}

export function loadResult(): GenerateResultState | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<GenerateResultState>;
    if (!parsed.markdown) return null;
    return {
      markdown: parsed.markdown,
      json_path: parsed.json_path ?? "",
      md_path: parsed.md_path ?? "",
      deck: parsed.deck ?? null,
    };
  } catch {
    return null;
  }
}

export function clearResult(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
