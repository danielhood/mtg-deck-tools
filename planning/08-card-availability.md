# Card availability and pricing

**Audience context:** Users typically build from **used inventory** (cards that have been on the market for months or years). The tool should bias toward cards that are **findable and familiar**, not toward the newest releases. A **static** card DB is acceptable — see [01-goals-and-scope.md](01-goals-and-scope.md) and [02-data-sources.md](02-data-sources.md).

## v1 — Budget null prices

**Policy:** **Allow with warning** (decided).

- Cards with `prices.usd == null` may be selected.
- They count as **$0** toward the user's budget cap.
- Markdown and `.deck.json` flag each with `price_known: false` and summarize count in notes.
- Optional CLI: `--strict-budget` → treat null as ineligible (exclude from pool).

## Obscure vs newly unpriced (low priority)

Scryfall null USD price mixes two different situations. For this product, **older/obscure** matters more than **newly added**:

| Situation | Typical signals | Deck-builder intent |
| --- | --- | --- |
| **Older / obscure** | Old `released_at`, low `edhrec_rank` or missing, no recent reprint, niche set | **Deprioritize or exclude** — aligns with used-card audience |
| **Newly added** | Recent `released_at`, Commander-legal rare/mythic, active set | **Low priority** — audience rarely needs day-one cards; `price_pending` warning is enough |

Fine-grained “new vs obscure” classification remains optional polish, not a blocker for static DB releases.

### Availability heuristic (shipped)

Compute `availability_score` at import (schema v2):

```
signals:
  - has prices.usd → strong positive
  - released_at within last N months → neutral (new, price pending)
  - edhrec_rank below threshold → positive (played, likely stocked)
  - set_type in (core, commander, masters) → positive
  - reprint == true → positive
  - very old released_at + null price + low edhrec → negative (obscure)
```

Use score as:

- **Filter:** `--prefer-available` excludes bottom quartile
- **Ranking:** tie-breaker within slot filling (prefer stocked cards)
- **Warning:** classify null-price cards in output as `likely_obscure` vs `price_pending`

### Default deck-building bias (product goal)

The utility should **target cards likely to be available** for purchase or trade:

- v1: soft bias via `edhrec_rank` in scoring
- shipped: `availability_score` at import, `--prefer-available` filter (p25 threshold), wizard strict/prefer defaults when budget is set, `likely_obscure` / `price_pending` in deck Notes

No LGS inventory integration in scope; heuristics only.

## Related fields

See [oracle-card-fields.md](../resources/scryfall/oracle-card-fields.md): `prices.usd`, `released_at`, `edhrec_rank`, `reprint`, `set_type`.
