# Oracle bulk data contract

Technical contract for Scryfall **oracle-cards** bulk import into `cards.db`. Architecture and refresh policy: [data-sources.md](../../architecture/data-sources.md).

**Bundled file:** `resources/scryfall/oracle-cards-20260528210654.json`

| Stat | Value |
| --- | ---: |
| Total card objects | 37,474 |
| Unique top-level fields | 87 |
| Commander-legal + English | ~30,969 |
| Commander-eligible (legendary creature/vehicle/etc.) | ~2,993 |
| Cards with `oracle_text` | ~33,638 |

One entry per unique oracle card (not every printing). Field reference: [`oracle-card-fields.md`](../../../resources/scryfall/oracle-card-fields.md). Bulk download metadata: `resources/scryfall/bulk-data-metadata-fields.md`.

## Gameplay-relevant fields

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

## Secondary fields

| Field | Use |
| --- | --- |
| `edhrec_rank` | Popularity prior for ranking within slots |
| `prices.usd` | Budget filter |
| `rarity` | Budget / power heuristics |
| `set_type` | Optional: exclude unset / acorn / silver-border |

## Exclude from import logic (v1)

Metadata / commerce / images — not used in deck logic: `image_uris`, `purchase_uris`, `related_uris`, `artist`, `collector_number`, `scryfall_uri`, `tcgplayer_id`, `preview`, `watermark`, `frame`, etc.

## Playable pool filters

Preprocessing drops or flags:

| Condition | Reason |
| --- | --- |
| `legalities.commander != "legal"` | Not Commander legal |
| `layout` in token, emblem, art_series, planar, scheme, vanguard | Not deckable |
| `lang != "en"` | Singleton uses English names (903.5b) |
| Optional: acorn / un-set silver border | Table rule dependent |

**Basic lands:** Six distinct basic oracle entries; generator treats them as a special unlimited pool.

## Token layout rows vs deck “tokens” theme

Oracle bulk includes **~1,000** token-layout objects. Import **drops** them (`NON_DECKABLE_LAYOUTS`). Deck `themes: [tokens]` and `TOKEN_BALANCE` refer to **main-deck spells** that create or care about tokens.

**Planned output:** [deck-output-format.md](../../product/deck-output-format.md) — related token companion list via parent `all_parts`, outside the 100-card count.

## Derived tables (import output)

| Artifact | Purpose |
| --- | --- |
| `cards` | Filtered playable oracle cards |
| `mechanic_tags` / `card_mechanic_tags` | Taxonomy assignments |
| `card_effects` | Dependency extraction (D1+) |
| `mana_pips` | Parsed from `mana_cost` |
