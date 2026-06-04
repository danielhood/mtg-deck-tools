# Data sources (architecture)

How external data enters the MTG Deck Tools monorepo. Field-level import contract: [oracle-bulk-contract.md](../specs/data/oracle-bulk-contract.md).

## Oracle cards (Scryfall bulk)

- **Location:** `resources/scryfall/oracle-cards-<date>.json` (user or maintainer download; see root [README.md](../../README.md))
- **Role:** Canonical playable card library for import → `data/cards.db`
- **Contract:** [oracle-bulk-contract.md](../specs/data/oracle-bulk-contract.md)

## Comprehensive Rules

- **Location:** `resources/mtg/MagicCompRules YYYYMMDD.txt`
- **Role:** Authoritative reference for Commander construction (903.*), color identity (903.4), partners (702.124), keyword definitions (702)
- **Runtime:** Full file not required at runtime; optional future `commander-rules.json` excerpt

## Static database policy

The card library is a **versioned snapshot**, not a live feed. Aligns with [goals-and-scope.md](../product/goals-and-scope.md): decks for **older used cards**, not day-one meta.

| Aspect | Policy |
| --- | --- |
| **Bundled default** | Known `oracle-cards-<date>.json` (optional committed `data/cards.db`) |
| **User expectation** | “Card pool as of &lt;snapshot date&gt;” |
| **Prices** | Embedded at import time only |
| **Companion datasets** | Tags, `card_effects`, audit reports — rebuilt **with** the same import |

### Maintainer refresh workflow

1. Replace oracle bulk under `resources/scryfall/`.
2. `mtg-deck-tools import` → `data/cards.db`.
3. Re-run dependency audit / effect extraction as needed.
4. Update golden tests and profiles if inventory shifts materially.
5. Record versions in `import_metadata`.

### Out of scope

- Background Scryfall sync or launch-time update checks
- Per-deck API calls for oracle or price

## Related product docs

- Budget / availability heuristics: [card-availability.md](../product/card-availability.md)
- Deck file schema: [deck-output-format.md](../product/deck-output-format.md)
