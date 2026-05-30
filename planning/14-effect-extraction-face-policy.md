# Effect extraction — face policy (D0)

How oracle text from multi-face cards maps to `card_effects` rows.

## v1 policy (D0–D1)

| Aspect | Policy |
| --- | --- |
| **Input text** | Same as import: merged `oracle_text` and `type_line` with `//` between faces ([`normalize.py`](../src/mtg_deck_tools/import_/normalize.py)) |
| **`face_index`** | Always **0** on extracted atoms |
| **Per-face extraction** | **Deferred** — modal DFC, Adventure, split cards may miss face-specific effects until D1.1 |
| **Modal “Choose one”** | Single merged string; multiple modes may each match patterns (acceptable duplicate atoms in v1) |

## Rationale

- Matches current wizard/builder behavior (one row per `oracle_id`).
- Simplifies golden tests and D0.5 audit (one pass per card).
- Commander decks rarely need opposite-face tutor targets in isolation.

## Future (post–D1)

| Change | When |
| --- | --- |
| Extract per `card_faces[]` with `face_index` 0..n | If audit shows high miss rate on DFC/adventure |
| Link adventure spell ↔ creature half | Named-card dependency class |

## Pattern registry

Pattern `id` → `effect_kind` mapping lives in [`config/effect-patterns.yaml`](../config/effect-patterns.yaml) (`schema_version`, `extraction_version`).
