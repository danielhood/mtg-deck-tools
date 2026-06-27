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
    "slot_template": { "ramp": 10, "draw": 8, "lands": 36 },
    "seed": 42
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
      "mechanic_tags": ["aristocrats", "sacrifice"],
      "color_identity": ["B"],
      "produced_mana": []
    }
  ],
  "stats": {
    "total_cards": 100,
    "estimated_price_usd": 142.30,
    "unpriced_card_count": 3,
    "unpriced_card_names": ["..."],
    "avg_cmc_nonland": 3.2,
    "avg_creature_cmc": 2.8,
    "land_count": 36,
    "ramp_count": 10,
    "cmc_histogram": {"0": 2, "1": 8, "2": 12, "3": 10, "4": 8, "5": 6, "6": 4, "7": 2, "7+": 1},
    "creature_cmc_histogram": {"1": 4, "2": 10, "3": 8, "4": 4, "5": 2},
    "type_counts": {"Creature": 28, "Instant": 8, "Land": 36, "Artifact": 6}
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
| `criteria.seed` | Reproducible regeneration — persisted when assigned (**UX7f** server library) |
| `slot` | Which template slot the card filled |
| `quantity` | 1 for singleton; >1 only for basic lands |
| `price_known` | Budget transparency when `prices.usd` was null |
| `schema_version` | Forward-compatible migrations |

### Web library persistence (UX7f)

**Status:** Planned — [library-api.md](../specs/web/library-api.md).

| Rule | Detail |
| --- | --- |
| Canonical payload | This `.deck.json` document — **sole** persisted record in the server library |
| Included | `criteria` (with `seed`), `dependency_report`, `commanders`, `cards`, `stats`, generator metadata |
| Excluded | `json_path`, `md_path`, markdown text — filesystem paths are not stored in library JSON |
| Markdown | Human-readable `.md` remains a **CLI/export derivative** generated from this JSON when needed |

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

### Deck composition metrics (UX10 — shipped)

**Status:** **Shipped (2026-06-26)** — **UX10a** CLI report + **UX10b** web charts + **UX10c** curve advisories. Lock/swap UI on deck view edit mode (**UX11** shipped). The builder uses **average nonland CMC** for land-count heuristics (`mana_base.py`) and **per-slot target CMC** while scoring picks (`scorer.py`). Post-build distribution metrics appear in Markdown, `.deck.json` `stats`, and the web deck view.

**Goal:** After a successful build, give the user **actionable composition metrics** — starting with **mana curve / CMC distribution** — in Markdown and `.deck.json`, and eventually in a richer UI (UX7). Metrics are **informational** by default; optional **advisory warnings** (e.g. “few cards at CMC 2–3”, “creature curve top-heavy”) are separate from legality and from dependency `fail` rules unless the user opts into strict curve hints later.

| Layer | Deliverable |
| --- | --- |
| **Report (UX10a)** | CMC histogram (0–7+ buckets), counts by primary type (creature, instant, …), `avg_cmc_nonland`, **creature-only** average and histogram, ramp count, land count (reuse build stats) |
| **Markdown** | Table and/or ASCII bar chart; short interpretation blurb |
| **JSON** | `deck_metrics` or extended `stats` with `cmc_histogram`, `creature_cmc_histogram`, `type_counts` |
| **Visualization (UX10b)** | Local web: bar chart on `/deck/:id`; All nonlands / Creatures only toggle; curve blurb — shipped |
| **Advisory rules (UX10c)** | Warn-only `CURVE_TOP_HEAVY` / `CURVE_MISSING_EARLY` — theme overrides in `config/curve-advisories.yaml`; surfaced in MD, `.deck.json` `stats.curve_advisories`, and web deck metrics panel |

**Relationship to existing behavior:**

| Today | UX10 adds |
| --- | --- |
| Slot fill prefers CMC near `SLOT_TARGET_CMC` | Post-build **whole-deck** view the user can sanity-check |
| `REANIMATION_SUPPORT` checks creature count / avg creature CMC when reanimation present | General curve metrics for any deck |
| `mana_base` uses `avg_cmc_nonland` | Same stat, plus **distribution** so average alone is not misleading |

**Non-goals for first ship:** Enforcing a universal “correct” Commander curve; simulating goldfish turns; sideboard metrics.

Spec and UX phasing: [user-experience.md](../specs/dependency-engine/user-experience.md) § UX10. Shipped: [changelog.md](../history/changelog.md).

### GUI deck editor (shipped — UX11)

**Status:** **Shipped (2026-06-26)** — field spec in [user-experience.md](../specs/dependency-engine/user-experience.md) § UX11.

| Feature | Behavior |
| --- | --- |
| **Lock** | Per maindeck card `"locked": true` in `cards[]` — default `false` or omitted; commanders treated as locked (no field required on commander rows) |
| **Swap** | User selects maindeck card(s) → replacements via generate pick pipeline (criteria, CI, budget, tags, strict dependencies, slot guards) |
| **Slot regen** | Refill one slot; locked cards in that slot are never replaced |

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

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `locked` | boolean | no | Default `false`. When `true`, slot regen and swap vacated positions skip this row. Commander rows: implicit locked — field optional and ignored for swap selection. |

CLI today: `--refill-slot` replaces unlocked cards in that slot when deck JSON includes `locked` flags (**UX11a**). Stretch: `--keep-locked` CLI flag. Full spec: [user-experience.md](../specs/dependency-engine/user-experience.md) § UX11.

### Future utility operations on `.deck.json`

- **Load & modify** — swap a card, re-validate color identity and budget (GUI **Swap** — UX11)
- **Re-generate slot** — keep commanders + criteria, refill one slot (respect **locked** cards — UX11)
- **Image gallery** — fetch or cache images from `image_uri`
- **Diff two decks** — compare oracle_id sets
- **Export to Moxfield/Archidekt** — translation layer in v2

### File location

Default: `./output/<deck-slug>/` or user-specified path via CLI `--out`.

Both files share the same slug: `golgari-aristocrats-20260528.md` and `golgari-aristocrats-20260528.deck.json`.
