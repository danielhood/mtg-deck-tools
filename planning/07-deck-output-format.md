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

Unpriced cards use `price_known: false`. See [08-card-availability.md](../planning/08-card-availability.md) for budget policy and future obscure-vs-new classification.

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

### Future utility operations on `.deck.json`

- **Load & modify** — swap a card, re-validate color identity and budget
- **Re-generate slot** — keep commanders + criteria, refill one slot
- **Image gallery** — fetch or cache images from `image_uri`
- **Diff two decks** — compare oracle_id sets
- **Export to Moxfield/Archidekt** — translation layer in v2

### File location

Default: `./output/<deck-slug>/` or user-specified path via CLI `--out`.

Both files share the same slug: `golgari-aristocrats-20260528.md` and `golgari-aristocrats-20260528.deck.json`.
