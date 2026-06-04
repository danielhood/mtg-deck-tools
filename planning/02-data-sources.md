# Data Sources

## Oracle cards bulk file

**File:** `resources/scryfall/oracle-cards-20260528210654.json`

| Stat | Value |
| --- | ---: |
| Total card objects | 37,474 |
| Unique top-level fields | 87 |
| Commander-legal + English | ~30,969 |
| Commander-eligible (legendary creature/vehicle/etc.) | ~2,993 |
| Cards with `oracle_text` | ~33,638 |

This is Scryfall's **oracle-cards** bulk type: one entry per unique oracle card (not every printing). Suitable as the canonical card library.

### Field reference gap

`resources/scryfall/bulk-data-metadata-fields.md` documents Scryfall bulk **download** metadata. Card object fields are in [`oracle-card-fields.md`](../resources/scryfall/oracle-card-fields.md).

### Field categories

#### Gameplay-relevant (primary for deck builder)

| Field | Presence | Deck-building use |
| --- | --- | --- |
| `oracle_id` | 100% | Stable card identity (dedupe key) |
| `name` | 100% | Display, singleton check |
| `layout` | 100% | Filter out tokens, emblems, art series |
| `type_line` | 100% | Types, commander eligibility, land detection |
| `oracle_text` | ~92% | Mechanic tagging, synergy heuristics |
| `mana_cost` | ~93% | Pip analysis, color requirements |
| `cmc` | ~93% | Curve filters, slot filling |
| `colors` | ~93% | Card color (not same as identity) |
| `color_identity` | 100% | Commander legality filter |
| `color_indicator` | rare | Cards without mana cost |
| `keywords` | partial | Structured mechanic hints |
| `produced_mana` | ~7% (lands) | Mana base / identity for lands |
| `power` / `toughness` | creatures | Commander selection, theme |
| `loyalty` | planeswalkers | |
| `legalities.commander` | 100% | Format filter |
| `card_faces` | ~8% | DFC color identity, combined text |
| `all_parts` | ~18% | Meld, tokens, related cards |

#### Useful secondary

| Field | Use |
| --- | --- |
| `edhrec_rank` | Popularity prior for ranking within slots |
| `prices.usd` | Budget filter |
| `rarity` | Budget / power heuristics |
| `set_type` | Optional: exclude unset / acorn / silver-border |

#### Exclude from v1 logic (metadata / commerce / images)

`image_uris`, `purchase_uris`, `related_uris`, `artist`, `collector_number`, `scryfall_uri`, `tcgplayer_id`, `preview`, `watermark`, `frame`, etc.

### Cards to exclude from the playable pool

Preprocessing should drop or flag:

| Condition | Reason |
| --- | --- |
| `legalities.commander != "legal"` | Not Commander legal |
| `layout` in token, emblem, art_series, planar, scheme, vanguard | Not deckable |
| `lang != "en"` | Singleton uses English names (903.5b) |
| Optional: acorn / un-set silver border | Table rule dependent |

**Note:** Only **6** distinct basic land oracle entries exist in this file (Plains, Island, Swamp, Mountain, Forest, Wastes). Basic lands can appear unlimited times in decks; the generator should treat them as a special pool.

### Token cards in bulk vs playable DB

Oracle bulk includes **~1,000** token-layout objects (`layout`: `token`, `double_faced_token`). Import **drops** them from `cards.db` (see `NON_DECKABLE_LAYOUTS` in code). Deck **themes: tokens** and `TOKEN_BALANCE` refer to **main-deck spells** that create or care about tokens, not token layout rows.

**Planned:** [07-deck-output-format.md](07-deck-output-format.md) — **Related token companion list** in generated Markdown/JSON: resolve tokens for the built deck (primarily parent card `all_parts`), listed for acquisition, **outside** the 100-card deck count.

## Comprehensive Rules

**File:** `resources/mtg/MagicCompRules 20260417.txt`

Use as authoritative reference for:

- Commander deck construction (903.5)
- Color identity (903.4)
- Partner (702.124)
- Keyword abilities (702) for tag definitions

**Preprocessing option:** Extract rules 903.* and 702.124 into a smaller `commander-rules.json` for programmatic checks — the full 9,000+ line file is not needed at runtime.

## Derived data (to build)

| Artifact | Purpose |
| --- | --- |
| `cards` table | Filtered playable oracle cards |
| `mechanic_tags` table | Curated taxonomy |
| `card_mechanic_tags` | Rule-based tag assignments |
| `commander_synergy` scores | Commander ↔ card relevance |
| `mana_pips` | Parsed from `mana_cost` ({W}, {U}, hybrid, etc.) |

## Static database policy

The card library is a **versioned snapshot**, not a live feed. This matches the product goal in [01-goals-and-scope.md](01-goals-and-scope.md): decks for **older used cards**, where same-day oracle or price accuracy is unnecessary.

| Aspect | Policy |
| --- | --- |
| **Bundled default** | Commit or ship a known `oracle-cards-<date>.json` (and derived `data/cards.db` optional) |
| **User expectation** | “Card pool as of May 2026” — sufficient for kitchen-table and LGS used inventory |
| **Prices** | Whatever Scryfall embedded at import time; no intraday refresh |
| **Gameplay text** | Oracle text from snapshot; errata lag until next manual refresh is acceptable |
| **Companion datasets** | `card_mechanic_tags`, future `card_effects`, dependency audit reports — rebuilt **with** the same import, not on their own schedule |

### Maintainer refresh workflow (explicit, infrequent)

When the team chooses to advance the snapshot (new sets, errata, dependency pattern work):

1. Download oracle-cards bulk from Scryfall (or replace file under `resources/scryfall/`).
2. `mtg-deck-tools import` → regenerate `data/cards.db`.
3. Re-run tagging (part of import) and any **dependency audit** / effect extraction (planned).
4. Update golden tests and `dependency-profiles.yaml` if inventory counts shift materially.
5. Record versions in `import_metadata` (bulk date, extractor version, audit version).

No requirement for users to refresh before every deck build. Document the snapshot date in `stats` / README.

### What we do not build

- Background Scryfall sync or “check for updates” on launch
- Per-deck API calls for oracle or price
- Penalizing decks for cards “too new” unless user opts in (availability heuristic already biases **toward** established cards)
