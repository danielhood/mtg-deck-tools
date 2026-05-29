# Card availability and pricing

## v1 — Budget null prices

**Policy:** **Allow with warning** (decided).

- Cards with `prices.usd == null` may be selected.
- They count as **$0** toward the user's budget cap.
- Markdown and `.deck.json` flag each with `price_known: false` and summarize count in notes.
- Optional CLI: `--strict-budget` → treat null as ineligible (exclude from pool).

## Future — Obscure vs newly unpriced

Scryfall null USD price mixes two different situations:

| Situation | Typical signals | Deck-builder intent |
| --- | --- | --- |
| **Older / obscure** | Old `released_at`, low `edhrec_rank` or missing, no recent reprint, niche set | **Deprioritize or exclude** — hard to find, weak for "buildable" lists |
| **Newly added** | Recent `released_at`, Commander-legal rare/mythic, active set | May be **available soon** — warn but don't treat as obscure |

### Proposed availability heuristic (v2+)

Compute `availability_score` at import:

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

- v1: soft bias via `edhrec_rank` in scoring (already planned)
- v2: explicit availability score + optional hard filter on obscure null-price cards

No LGS inventory integration in scope; heuristics only.

## Related fields

See [oracle-card-fields.md](../resources/scryfall/oracle-card-fields.md): `prices.usd`, `released_at`, `edhrec_rank`, `reprint`, `set_type`.
