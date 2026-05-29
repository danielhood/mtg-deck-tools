# Planning decisions

All v1 planning questions are resolved. Revisit only when scope changes.

## Decided

| Question | Answer |
| --- | --- |
| Format | Commander (100-card singleton) |
| Deck generation style | Guided slot template |
| Mechanic matching | Curated taxonomy + rule-based tagging on `oracle_text` |
| v1 constraints | Commander rules, budget, commander synergy, include/avoid mechanics |
| Runtime | Local Windows, local DB OK |
| Preprocessing | Acceptable and recommended |
| UI (v1) | Terminal wizard (CLI) — Python + `typer` / `questionary` / `rich` |
| Include / avoid mechanics | Keyword-level want / avoid lists — see [03-problem-decomposition.md](03-problem-decomposition.md) |
| Wizard flow | Theme → include/avoid mechanics → colors → commander |
| Partner commanders | In v1 |
| Export format | Markdown + `.deck.json` — [07-deck-output-format.md](07-deck-output-format.md) |
| Budget null price | **Allow with warning**; optional `--strict-budget` — [08-card-availability.md](08-card-availability.md) |
| Field reference | Split: `bulk-data-metadata-fields.md` + `oracle-card-fields.md` |
| Deck variety | **Seeded random** slot selection (`--seed` for reproducibility) |
| Power level dial | **Deferred** — needs richer model than a simple dial |
| Card availability | v1: EDHREC bias; v2: obscure vs new-unpriced analysis — [08-card-availability.md](08-card-availability.md) |

## Deferred (post-v1)

See [09-next-steps.md](09-next-steps.md) for the active Phase 3 roadmap and priority order.

| Topic | Notes |
| --- | --- |
| Power level / salt | Complicated, context-dependent; not a single dial |
| Obscure vs new null-price classification | Heuristic spec in [08-card-availability.md](08-card-availability.md) |
| Moxfield / Archidekt export | Translate from `.deck.json` |
| Local web / desktop UI | Reuse Python core |

## Implementation start

**Phase 1:** import script + mechanic taxonomy v0 + SQLite schema + CLI stub.
