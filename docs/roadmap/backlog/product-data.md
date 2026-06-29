# Backlog — Product & data

Cross-cutting product features: deck file format, export, import pipeline. Not tied to a single package directory.

Promote to [active.md](../active.md) before starting. **Index:** [backlog/README.md](README.md).

---

## Deck input (import existing lists)

Users need ways to load an **existing deck** into the builder — not Scryfall oracle bulk (`import`), but **deck list** intake.

**Shipped:** **UX13-MVP** (CLI/API/parser), **UX13b** (home paste/file/template), **UX13c** (preview), **resolver v2**.

| ID | Topic | Notes | Spec |
| --- | --- | --- | --- |
| IN-DECK-SHEET | Spreadsheet CSV / XLSX | Web **UX13d**; UTF-8 CSV first | [deck-input.md](../../specs/product/deck-input.md) § Spreadsheet |
| IN-DECK-JSON | Upload `.deck.json` | Validates schema; library entry; re-resolve stale `oracle_id` after bulk refresh | [deck-input.md](../../specs/product/deck-input.md) · [library-api.md](../../specs/web/library-api.md) |
| IN-DECK-EXT | Third-party deck exports | Moxfield/Archidekt plaintext P1; MTGO `.dek`, Arena P2+ | [deck-input.md](../../specs/product/deck-input.md) § Third-party |

**Depends on:** **UX13-MVP** ships before CSV/JSON upload UI. **Parallel OK with:** web **UX13a** search-by-name once resolver exists.

---

## Export & deck output

| ID | Topic | Doc |
| --- | --- | --- |
| EXP-MOX | Moxfield / Archidekt export | [deck-output-format.md](../../product/deck-output-format.md) |
| EXP-TOKENS | Related token companion list | [deck-output-format.md](../../product/deck-output-format.md) § Related token cards |
| EXP-GALLERY | Image gallery / diff on `.deck.json` | [deck-output-format.md](../../product/deck-output-format.md) |

---

## Data pipeline & product

| ID | Topic | Doc |
| --- | --- | --- |
| DATA-PARQUET | Parquet / faster import | [technology-stack.md](../../architecture/technology-stack.md) |
| DATA-DFC | DFC / adventure normalization | [problem-decomposition.md](../../architecture/problem-decomposition.md) |
| PROD-POWER | Power level / salt | [open-questions.md](../../product/open-questions.md) |
| LEG-REPAIR | Post-validation CR repair | Deferred — fill-time filters sufficient |

**Parallel:** Most rows **parallel with web-ui work** if they do not change shared API contracts. **EXP-*** may **depend on** web preview UI.
