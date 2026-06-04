# Deck Output Format

Every successful deck build produces **two files** with a shared basename (e.g. `golgari-aristocrats-20260528`).

## 1. Human-readable — Markdown (`.md`)

For review, sharing, and printing. Example structure:

```markdown
# Golgari Aristocrats

**Commanders:** Meren of Clan Nel Toth  
**Color identity:** B,G  
**Budget cap:** $150 · **Estimated total:** $142.30 (3 cards unpriced — see notes)  
**Generated:** 2026-05-28T21:06:54

## Summary
| Slot | Count |
| --- | ---: |
| Lands | 36 |
| Ramp | 10 |
| ... | |

## Commander
- Meren of Clan Nel Toth

## Deck (99)
### Creatures (28)
- ...

### Lands (36)
- 14x Swamp
- 13x Forest
- ...

## Criteria
- **Themes:** aristocrats, sacrifice
- **Include mechanics:** scry, deathtouch
- **Avoid mechanics:** flying

## Notes
- 3 cards had no Scryfall USD price; excluded from budget total.
```

Card names link to `scryfall_uri` when rendered in tools that support it; plain Markdown uses bare URLs or name-only for simplicity.

## 2. Machine-readable — Deck file (`.deck.json`)

For reload, modification, image lookup, and future UI versions. Versioned schema.

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-05-28T21:06:54Z",
  "generator": {
    "name": "mtg-deck-tools",
    "version": "0.1.0"
  },
  "criteria": {
    "themes": ["aristocrats", "sacrifice"],
    "colors": ["B", "G"],
    "include_mechanics": ["scry", "deathtouch"],
    "avoid_mechanics": ["flying"],
    "budget_usd": 150,
    "slot_template": { "ramp": 10, "draw": 8, "lands": 36 }
  },
  "commanders": [
    {
      "oracle_id": "...",
      "name": "Meren of Clan Nel Toth",
      "scryfall_uri": "https://scryfall.com/card/...",
      "image_uri": "https://cards.scryfall.io/normal/front/...jpg"
    }
  ],
  "cards": [
    {
      "oracle_id": "...",
      "name": "Grave Pact",
      "slot": "synergy",
      "quantity": 1,
      "cmc": 3,
      "mana_cost": "{1}{B}{B}",
      "type_line": "Enchantment",
      "price_usd": 12.50,
      "price_known": true,
      "scryfall_uri": "https://scryfall.com/card/...",
      "image_uri": "https://cards.scryfall.io/normal/front/...jpg",
      "mechanic_tags": ["aristocrats", "sacrifice"]
    }
  ],
  "stats": {
    "total_cards": 100,
    "estimated_price_usd": 142.30,
    "unpriced_card_count": 3,
    "unpriced_card_names": ["..."],
    "avg_cmc_nonland": 3.2
  }
}
```

Unpriced cards use `price_known: false`. See [card-availability.md](card-availability.md) for budget policy and future obscure-vs-new classification.

### `dependency_report` (schema 1.0, optional)

Populated after a successful build when `card_effects` data exists in the database (post–D2). Warn-only by default.

```json
{
  "dependency_report": {
    "passed": false,
    "issues": [
      {
        "rule_id": "ENERGY_BALANCE",
        "status": "warn",
        "message": "Deck has 2 energy producer(s) (Aether Hub, …) but no cards that pay {E}.",
        "card_name": null,
        "card_oracle_id": null,
        "profile_id": "energy",
        "detail": { "producers": ["Aether Hub"], "consumers": [] }
      }
    ],
    "profiles": [
      {
        "profile_id": "energy",
        "counts": { "producer": 2, "consumer": 0 },
        "status": "warn",
        "messages": []
      }
    ]
  }
}
```

Markdown output includes a **Deck dependencies** section (and dependency lines under **Notes** when folded into `warnings`).

### Design choices

| Field | Purpose |
| --- | --- |
| `oracle_id` | Stable identity across printings; DB joins |
| `scryfall_uri` / `image_uri` | Online image lookup without re-querying API |
| `criteria` | Re-run generator with tweaks; audit why card was picked |
| `slot` | Which template slot the card filled |
| `quantity` | 1 for singleton; >1 only for basic lands |
| `price_known` | Budget transparency when `prices.usd` was null |
| `schema_version` | Forward-compatible migrations |

### Related token cards (planned — acquisition companion list)

**Status:** Not implemented. Token layout objects exist in Scryfall oracle bulk (~1k entries) but are **excluded** from `cards.db` import (not Commander-deckable). See [oracle-bulk-contract.md](../specs/data/oracle-bulk-contract.md) and [data-sources.md](../architecture/data-sources.md).

**Goal:** After a successful build, append a **companion list** of token cards that the 99 (plus commander) is likely to create or reference, so a player can buy or sleeve the right tokens. This list is **not** part of the Commander deck, does **not** count toward the 100-card requirement, and must **not** affect legality validation, singleton checks, color identity, or budget totals for the main deck.

| Property | Rule |
| --- | --- |
| Deck size / `stats.total_cards` | Unchanged — still 100 (commander + 99) |
| Budget | Token companion prices optional; separate subtotal if shown |
| Validation (903 / 702.124) | Main `cards` only |
| Reload / `--refill-slot` | Companion list regenerated or preserved per CLI policy (TBD) |

**Data sources (v1 proposal):**

1. **`all_parts` on oracle bulk** — For each card in the built deck, follow Scryfall `all_parts` entries whose related object has `component: "token"` (or `layout` `token` / `double_faced_token`). Resolve to `oracle_id`, name, type line, `scryfall_uri`, `image_uri`.
2. **Oracle-text heuristics (stretch)** — “Create a … token” without `all_parts` (older cards, generic tokens) — defer or warn-only; see [resources/dependency/hard-cases.yaml](../resources/dependency/hard-cases.yaml) `defer_tokens` stance.
3. **Import option (stretch)** — Secondary `tokens` table or read-through cache keyed by `oracle_id`, populated at import from bulk token layouts, without adding tokens to the playable pool.

**Aggregation:** Deduplicate by token `oracle_id`; optional `quantity` when multiple main-deck cards produce the same token (default 1 per distinct token unless rules text implies multiples — product decision). Group under producing card names in Markdown for clarity.

**Markdown (illustrative):**

```markdown
## Related tokens (not in deck)
Companion list for acquisition — not counted in the 100-card Commander deck.

| Token | Type | Produced by |
| --- | --- | --- |
| Clue Token | Artifact — Clue | … |
| Treasure Token | Artifact — Treasure | …, … |
```

**`.deck.json` (illustrative — schema bump likely `1.1`):**

```json
{
  "related_tokens": [
    {
      "oracle_id": "...",
      "name": "Clue Token",
      "type_line": "Artifact — Clue",
      "quantity": 1,
      "scryfall_uri": "https://scryfall.com/card/...",
      "image_uri": "https://cards.scryfall.io/...",
      "sources": [{ "oracle_id": "...", "name": "Trail of Evidence" }]
    }
  ],
  "stats": {
    "total_cards": 100,
    "related_token_count": 4
  }
}
```

**CLI / UX (TBD):** e.g. `--include-related-tokens` / `--no-related-tokens`; wizard toggle default on. Omit section when no tokens resolved.

**Non-goals for first ship:** Emblems, planes, scheme cards; meld back faces; choosing a specific printing art for tokens (any English token printing is enough for acquisition).

Tracked in backlog: [active.md](../roadmap/active.md).

### Deck composition metrics (planned — UX10)

**Status:** Not implemented. Today the builder only uses **average nonland CMC** for land-count heuristics (`mana_base.py`) and **per-slot target CMC** while scoring picks (`scorer.py`); output may show `avg_cmc_nonland` in stats. There is **no** deck-wide check or report for a healthy mix of low- and high-CMC cards (especially creatures).

**Goal:** After a successful build, give the user **actionable composition metrics** — starting with **mana curve / CMC distribution** — in Markdown and `.deck.json`, and eventually in a richer UI (UX7). Metrics are **informational** by default; optional **advisory warnings** (e.g. “few cards at CMC 2–3”, “creature curve top-heavy”) are separate from legality and from dependency `fail` rules unless the user opts into strict curve hints later.

| Layer | Deliverable |
| --- | --- |
| **Report (UX10a)** | CMC histogram (0–7+ buckets), counts by primary type (creature, instant, …), `avg_cmc_nonland`, **creature-only** average and histogram, ramp count, land count (reuse build stats) |
| **Markdown** | Table and/or ASCII bar chart; short interpretation blurb |
| **JSON** | `deck_metrics` or extended `stats` with `cmc_histogram`, `creature_cmc_histogram`, `type_counts` |
| **Visualization (UX10b)** | Local web or desktop: bar chart, pip color breakdown (stretch) — depends on UX7 shell |
| **Advisory rules (stretch)** | Warn-only `CURVE_TOP_HEAVY` / `CURVE_MISSING_EARLY` — profile- or archetype-specific thresholds; not v1 gate |

**Relationship to existing behavior:**

| Today | UX10 adds |
| --- | --- |
| Slot fill prefers CMC near `SLOT_TARGET_CMC` | Post-build **whole-deck** view the user can sanity-check |
| `REANIMATION_SUPPORT` checks creature count / avg creature CMC when reanimation present | General curve metrics for any deck |
| `mana_base` uses `avg_cmc_nonland` | Same stat, plus **distribution** so average alone is not misleading |

**Non-goals for first ship:** Enforcing a universal “correct” Commander curve; simulating goldfish turns; sideboard metrics.

Spec and UX phasing: [user-experience.md](../specs/dependency-engine/user-experience.md) § UX10. Backlog: [active.md](../roadmap/active.md).

### GUI deck editor (parked — UX11)

**Status:** Not implemented. Planned for **UX7** GUI; schema and core should allow it without a breaking migration.

| Feature | Behavior |
| --- | --- |
| **Lock** | Per-card `"locked": true` in `cards[]` — excluded from slot refill and from automatic package/repair swaps unless user overrides |
| **Swap** | User selects card(s) → replacements chosen with the same rules as `generate` (criteria, CI, budget, tags, strict dependencies, slot guards) |

Illustrative card entry:

```json
{
  "oracle_id": "...",
  "name": "Grave Pact",
  "slot": "synergy",
  "quantity": 1,
  "locked": false
}
```

CLI today: `--refill-slot` replaces **all** cards in that slot; no `locked` field. Stretch: `--keep-locked` on refill. Full spec: [user-experience.md](../specs/dependency-engine/user-experience.md) § UX11.

### Future utility operations on `.deck.json`

- **Load & modify** — swap a card, re-validate color identity and budget (GUI **Swap** — UX11)
- **Re-generate slot** — keep commanders + criteria, refill one slot (respect **locked** cards — UX11)
- **Image gallery** — fetch or cache images from `image_uri`
- **Diff two decks** — compare oracle_id sets
- **Export to Moxfield/Archidekt** — translation layer in v2

### File location

Default: `./output/<deck-slug>/` or user-specified path via CLI `--out`.

Both files share the same slug: `golgari-aristocrats-20260528.md` and `golgari-aristocrats-20260528.deck.json`.
