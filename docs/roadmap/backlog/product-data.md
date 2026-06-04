# Backlog — Product & data

Cross-cutting product features: deck file format, export, import pipeline. Not tied to a single package directory.

Promote to [active.md](../active.md) before starting.

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

**Parallel:** Most rows **parallel with UX7** if they do not change shared API contracts. **EXP-*** may **depend on** UX7 for preview UI.
