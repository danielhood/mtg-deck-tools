export interface WizardBuildStep {
  number: number;
  route: string;
  label: string;
}

export interface WizardMeta {
  version: string;
  db_ready: boolean;
  db_path: string;
  total_cards: number | null;
  steps: WizardBuildStep[];
  review_route: string;
  result_route: string;
}

export interface ImportResponse {
  source_file: string;
  source_count: number;
  playable_count: number;
  tag_count: number;
  effect_count: number;
  db_path: string;
}

export interface ThemeChoice {
  id: string;
  description: string;
}

export interface MechanicChoice {
  id: string;
  description: string;
}

export interface SlotTemplateDefaults {
  default: Record<string, number>;
  bounds: Record<string, { min: number; max: number }>;
  order: string[];
  labels: Record<string, string>;
  maindeck_total: number;
  deck_total: number;
  commander_slots: number;
}

export interface FocusLevelOption {
  value: string | null;
  label: string;
  dots: number;
}

export interface ActivatedProfile {
  profile_id: string;
  prompt_label: string;
  current_level: string | null;
  focus_options: FocusLevelOption[];
}

export interface SynergyContext {
  activated_profiles: ActivatedProfile[];
  focus_levels: string[];
}

export interface CommanderResult {
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
  rarity: string | null;
}

export interface RarityChoice {
  id: string;
  label: string;
}

export interface CriteriaWarning {
  rule_id: string;
  message: string;
}

export interface PreflightResponse {
  warnings: CriteriaWarning[];
}

export interface GenerateResponse {
  id: string;
  deck: Record<string, unknown>;
  markdown?: string | null;
}

export interface DeckLibraryEntry {
  id: string;
  name: string;
  saved_at: string;
  commander_names: string[];
  commander_image_uri: string | null;
  colors: string[];
  themes: string[];
  estimated_price_usd: number | null;
}

export interface DeckLibraryDetail {
  id: string;
  name: string;
  saved_at: string;
  deck: Record<string, unknown>;
}

export interface SwapRecord {
  slot: string;
  from_oracle_id: string;
  from_name: string;
  to_oracle_id: string;
  to_name: string;
}

export interface SwapCardsResponse {
  id: string;
  deck: Record<string, unknown>;
  swaps: SwapRecord[];
}

export type LibrarySort = "saved_at" | "name" | "commander";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const raw = await response.text();
    let detail = raw;
    try {
      const parsed = JSON.parse(raw) as { detail?: string | { msg: string }[] };
      if (typeof parsed.detail === "string") detail = parsed.detail;
      else if (Array.isArray(parsed.detail) && parsed.detail[0]?.msg) {
        detail = parsed.detail.map((row) => row.msg).join("; ");
      }
    } catch {
      /* use raw body */
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getWizardMeta(): Promise<WizardMeta> {
  return fetchJson<WizardMeta>("/api/v1/wizard/meta");
}

export function postImport(): Promise<ImportResponse> {
  return fetchJson<ImportResponse>("/api/v1/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function pollWizardMetaUntilReady(options?: {
  intervalMs?: number;
  timeoutMs?: number;
}): Promise<WizardMeta> {
  const intervalMs = options?.intervalMs ?? 1000;
  const timeoutMs = options?.timeoutMs ?? 60_000;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const meta = await getWizardMeta();
    if (meta.db_ready) return meta;
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Card database is still not ready after import. Try refreshing the page.");
}

export function getThemes(): Promise<ThemeChoice[]> {
  return fetchJson<ThemeChoice[]>("/api/v1/wizard/themes");
}

export function getSlotTemplateDefaults(): Promise<SlotTemplateDefaults> {
  return fetchJson<SlotTemplateDefaults>("/api/v1/wizard/slot-template/defaults");
}

export function getMechanics(): Promise<MechanicChoice[]> {
  return fetchJson<MechanicChoice[]>("/api/v1/wizard/mechanics");
}

export function postSynergyContext(criteria: Record<string, unknown>): Promise<SynergyContext> {
  return fetchJson<SynergyContext>("/api/v1/wizard/synergy-context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(criteria),
  });
}

export function searchCommanders(params: URLSearchParams): Promise<CommanderResult[]> {
  return fetchJson<CommanderResult[]>(`/api/v1/wizard/commanders/search?${params}`);
}

export function getRarities(): Promise<RarityChoice[]> {
  return fetchJson<RarityChoice[]>("/api/v1/wizard/rarities");
}

export function postPreflight(criteria: Record<string, unknown>): Promise<PreflightResponse> {
  return fetchJson<PreflightResponse>("/api/v1/wizard/preflight", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(criteria),
  });
}

export function postGenerate(criteria: Record<string, unknown>): Promise<GenerateResponse> {
  return fetchJson<GenerateResponse>("/api/v1/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ criteria }),
  });
}

export function listDecks(params: {
  q?: string;
  sort?: LibrarySort;
  limit?: number;
}): Promise<DeckLibraryEntry[]> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.sort) search.set("sort", params.sort);
  if (params.limit != null) search.set("limit", String(params.limit));
  const query = search.toString();
  return fetchJson<DeckLibraryEntry[]>(`/api/v1/decks${query ? `?${query}` : ""}`);
}

export function getDeck(id: string): Promise<DeckLibraryDetail> {
  return fetchJson<DeckLibraryDetail>(`/api/v1/decks/${encodeURIComponent(id)}`);
}

export function patchDeck(
  id: string,
  body: { name?: string; deck?: Record<string, unknown> },
): Promise<DeckLibraryDetail> {
  return fetchJson<DeckLibraryDetail>(`/api/v1/decks/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function refillDeckSlot(
  id: string,
  slot: string,
  seed?: number,
): Promise<DeckLibraryDetail> {
  const body: { slot: string; seed?: number } = { slot };
  if (seed != null) body.seed = seed;
  return fetchJson<DeckLibraryDetail>(`/api/v1/decks/${encodeURIComponent(id)}/refill-slot`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function swapDeckCards(
  id: string,
  oracleIds: string[],
  seed?: number,
): Promise<SwapCardsResponse> {
  const body: { oracle_ids: string[]; seed?: number } = { oracle_ids: oracleIds };
  if (seed != null) body.seed = seed;
  return fetchJson<SwapCardsResponse>(`/api/v1/decks/${encodeURIComponent(id)}/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteDeck(id: string): Promise<void> {
  const response = await fetch(`/api/v1/decks/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const raw = await response.text();
    throw new Error(raw || `Request failed (${response.status})`);
  }
}
