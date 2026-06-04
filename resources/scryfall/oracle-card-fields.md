# Oracle card object fields

Reference for card objects in the Scryfall **oracle-cards** bulk file (e.g. `oracle-cards-*.json`). One object per unique oracle card.

**Relevance key**

| Flag | Meaning |
| --- | --- |
| **gameplay** | Used for deck construction, filtering, or tagging |
| **secondary** | Useful for ranking, budget, or display |
| **metadata** | Ignored by deck builder logic in v1 |

## Core identity

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `object` | String | metadata | Always `"card"`. |
| `id` | UUID | metadata | Scryfall card id for this oracle entry. |
| `oracle_id` | UUID | **gameplay** | Stable id across printings; primary DB key. |
| `name` | String | **gameplay** | English name; singleton uniqueness (903.5b). |
| `lang` | String | **gameplay** | Filter to `"en"` for Commander deck lists. |
| `layout` | String | **gameplay** | Filter out `token`, `emblem`, `art_series`, `planar`, `scheme`, `vanguard`, etc. |

## Rules text and types

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `type_line` | String | **gameplay** | Card types; commander eligibility; land detection. |
| `oracle_text` | String | **gameplay** | Mechanics, synergy tagging, include/avoid rules. |
| `mana_cost` | String | **gameplay** | Pip analysis, color on card (not identity). |
| `cmc` | Number | **gameplay** | Curve filters and slot targets. |
| `colors` | Array | **gameplay** | Card colors; may differ from identity. |
| `color_identity` | Array | **gameplay** | Commander legality subset check (903.5c). |
| `color_indicator` | Array | **gameplay** | For cards without mana cost. |
| `keywords` | Array | **gameplay** | Structured mechanics (Trample, Landfall, …). |
| `power` | String | secondary | Creatures; commander selection. |
| `toughness` | String | secondary | Creatures. |
| `loyalty` | String | secondary | Planeswalkers. |
| `defense` | String | secondary | Battles (if present). |
| `hand_modifier` | String | metadata | Vanguard layouts only. |
| `life_modifier` | String | metadata | Vanguard layouts only. |

## Mana and lands

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `produced_mana` | Array | **gameplay** | Mana produced (lands and some rocks). |
| `card_faces` | Array | **gameplay** | DFC/modal: combined `oracle_text`, `mana_cost`, `colors`, `type_line`. |

## Commander and legality

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `legalities` | Object | **gameplay** | Use `legalities.commander === "legal"`. |
| `legalities.commander` | String | **gameplay** | `legal`, `not_legal`, `banned`, `restricted`. |
| `all_parts` | Array | secondary | Meld, related tokens; partner validation edge cases. |

## Related / combo

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `printed_text` | String | metadata | Non-English or special printings. |
| `printed_type_line` | String | metadata | |

## Availability and commerce

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `prices` | Object | **gameplay** | Budget filtering. |
| `prices.usd` | String | **gameplay** | Nullable; see budget policy in [docs/product/card-availability.md](../../docs/product/card-availability.md). |
| `released_at` | Date | secondary | Distinguish new vs old when price is null (future). |
| `edhrec_rank` | Integer | secondary | Popularity prior for slot ranking. |
| `rarity` | String | secondary | Budget heuristics. |
| `reserved` | Boolean | secondary | Optional exclusion. |

## Set and printing (mostly metadata)

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `set` | String | metadata | Set code for oracle entry. |
| `set_name` | String | metadata | |
| `set_type` | String | secondary | e.g. `commander`, `core`; acorn/silver-border hints. |
| `set_id` | UUID | metadata | |
| `collector_number` | String | metadata | |
| `reprint` | Boolean | secondary | Availability proxy (future). |
| `digital` | Boolean | secondary | |
| `games` | Array | metadata | `paper`, `mtgo`, `arena`. |

## Images and URIs (export / display)

| Field | Type | Relevance | Details |
| --- | --- | --- | --- |
| `scryfall_uri` | URI | secondary | Written to `.deck.json` for links. |
| `uri` | URI | metadata | API URI. |
| `image_uris` | Object | secondary | `normal`, `small`, `png` for Markdown/tools. |
| `image_status` | String | metadata | |
| `highres_image` | Boolean | metadata | |

## Fields present on some cards only

| Field | Relevance | Notes |
| --- | --- | --- |
| `attraction_lights` | metadata | Attraction cards |
| `variation_of` | metadata | |
| `flavor_name` | metadata | |
| `flavor_text` | metadata | |
| `watermark` | metadata | |
| `preview` | metadata | |
| `promo_types` | secondary | |
| `content_warning` | metadata | |
| `game_changer` | secondary | |
| `penny_rank` | metadata | |

## Derived at import (not in JSON)

| Column | Purpose |
| --- | --- |
| `commander_eligible` | Legendary creature/vehicle/spacecraft or "can be your commander" |
| `partner_kind` | `partner`, `partner_with`, `background`, etc. |
| `is_basic_land` | Unlimited copies in deck |
| `availability_score` | Future: likely purchasable vs obscure |
| `mechanic_tags` | From taxonomy (themes + keywords) |

## Layout values in current bulk (reference)

Common: `normal`, `transform`, `modal_dfc`, `adventure`, `split`, `saga`, `class`, `mutate`, …  
Non-deckable (exclude): `token`, `double_faced_token`, `emblem`, `art_series`, `planar`, `scheme`, `vanguard`.
