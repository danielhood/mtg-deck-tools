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
}

export interface RarityChoice {
  id: string;
  label: string;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getWizardMeta(): Promise<WizardMeta> {
  return fetchJson<WizardMeta>("/api/v1/wizard/meta");
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
