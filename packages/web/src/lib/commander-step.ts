import type { CommanderResult } from "./api";
import type { CommanderSnapshot, WizardDraft } from "./criteria";

export function snapshotToResult(snapshot: CommanderSnapshot): CommanderResult {
  return {
    oracle_id: snapshot.oracle_id,
    name: snapshot.name,
    type_line: snapshot.type_line,
    color_identity: snapshot.color_identity,
    partner_kind: snapshot.partner_kind,
    edhrec_rank: snapshot.edhrec_rank,
    price_usd: snapshot.price_usd,
    price_known: snapshot.price_known,
    released_at: snapshot.released_at,
    image_uri: snapshot.image_uri,
    rarity: snapshot.rarity,
  };
}

export function resultToSnapshot(row: CommanderResult): CommanderSnapshot {
  return {
    oracle_id: row.oracle_id,
    name: row.name,
    type_line: row.type_line,
    color_identity: [...row.color_identity],
    partner_kind: row.partner_kind,
    edhrec_rank: row.edhrec_rank,
    price_usd: row.price_usd,
    price_known: row.price_known,
    released_at: row.released_at,
    image_uri: row.image_uri,
    rarity: row.rarity,
  };
}

/** Restore the search box when returning to step 6. */
export function restoreCommanderQuery(draft: WizardDraft): string {
  if (draft.commander_search_query) return draft.commander_search_query;
  if (draft.commander_oracle_ids[0] && draft.commander_label) return draft.commander_label;
  return "";
}

/** Restore commander preview/selection when returning to step 6. */
export function restoreCommanderSelection(draft: WizardDraft): CommanderResult | null {
  if (draft.commander_snapshot) return snapshotToResult(draft.commander_snapshot);
  const oracleId = draft.commander_oracle_ids[0];
  if (!oracleId || !draft.commander_label) return null;
  return {
    oracle_id: oracleId,
    name: draft.commander_label,
    type_line: "",
    color_identity: [],
    partner_kind: null,
    edhrec_rank: null,
    price_usd: null,
    price_known: false,
    released_at: null,
    image_uri: null,
    rarity: null,
  };
}

export function mergeCommanderSearchResults(
  rows: CommanderResult[],
  oracleId: string | undefined,
  fallback: CommanderResult | null,
): { results: CommanderResult[]; selected: CommanderResult | null } {
  if (!oracleId) {
    return { results: rows, selected: null };
  }

  const match = rows.find((row) => row.oracle_id === oracleId);
  if (match) {
    return { results: rows, selected: match };
  }

  if (fallback?.oracle_id === oracleId) {
    return { results: [fallback, ...rows], selected: fallback };
  }

  return { results: rows, selected: null };
}
