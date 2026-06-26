# Web UI — deck iterate HTTP API

**Status:** **UX11 shipped (2026-06-26).** Implementation: [user-experience.md](../dependency-engine/user-experience.md) § UX11.

Server-side iterate operations for saved library decks. The SPA does **not** call subprocess CLI; all paths use `service/` facades (same rule as generate).

Contract: [openapi.yaml](openapi.yaml).

---

## Design principle

- **Canonical store:** server library (`GET/PATCH /api/v1/decks/{id}`) — see [library-api.md](library-api.md).
- **Persisted payload:** `.deck.json` document — `locked` on `cards[]` per [deck-output-format.md](../../product/deck-output-format.md).
- **Iterate responses:** same shape as generate where possible — `{ id, deck }` (`GenerateResponse`); optional `swaps[]` diff on swap.
- **No new analyze endpoints** — `dependency_report` and validation messages are embedded in returned `deck` JSON after engine runs.

---

## Screen → API map (UX11)

| Route / action | Endpoints |
| --- | --- |
| `/deck/:id` — toggle lock | `PATCH /api/v1/decks/{id}` with updated `deck` body (lock flags only; client merges into cached deck) |
| `/deck/:id` — slot regen | `POST /api/v1/decks/{id}/refill-slot` |
| `/deck/:id` — swap selected | `POST /api/v1/decks/{id}/swap` |
| `/deck/:id` — load | `GET /api/v1/decks/{id}` on cache miss (unchanged **UX7f**) |

**DB gate:** Same as library — blocked when `db_ready` is false.

---

## Planned endpoints

### `PATCH /api/v1/decks/{id}` (extend **UX7f**)

| Behavior | Rule |
| --- | --- |
| Rename (shipped) | `{ "name": "…" }` |
| Lock toggle (**UX11c**) | `{ "deck": { …full .deck.json… } }` — client sends deck with updated `cards[].locked`; server validates schema and persists |
| No engine call | Lock-only PATCH does not re-run generate or dependency validation |

### `POST /api/v1/decks/{id}/refill-slot`

Refill one slot on a library deck, respecting **locked** cards in that slot.

**Request body:**

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `slot` | string | yes | Slot name from deck template (e.g. `synergy`, `lands`) |
| `seed` | integer | no | Reproducibility; server randomizes when absent |

**Behavior:**

1. Load deck from library by `id`.
2. Run `refill_deck_slot` pipeline (same as CLI `generate --from … --refill-slot`) with **keep-locked** semantics.
3. Re-run validation + `dependency_report` on result.
4. Auto-save to library; return `{ id, deck }`.

**Errors:**

| Code | When |
| --- | --- |
| 400 | Unknown slot; locked cards exceed slot target size; engine/validation failure |
| 404 | Deck id unknown |

### `POST /api/v1/decks/{id}/swap`

Replace one or more **maindeck** cards with new picks under current `DeckCriteria`.

**Request body:**

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `oracle_ids` | string[] | yes | Cards to replace (maindeck only; duplicates allowed for basics quantity) |
| `seed` | integer | no | Reproducibility |

**Behavior:**

1. Load deck from library.
2. Remove requested `oracle_id` rows (respect quantity for basics).
3. For each vacated slot position, run generate pick pipeline — exclude deck cards + **locked** cards.
4. Process slots in deterministic order: slot name A→Z, then vacated row order within slot.
5. Re-run validation + `dependency_report`.
6. Auto-save; return `{ id, deck, swaps }`.

**`swaps` entry (planned):**

```json
{ "slot": "synergy", "from_oracle_id": "…", "from_name": "…", "to_oracle_id": "…", "to_name": "…" }
```

**Errors:**

| Code | When |
| --- | --- |
| 400 | Commander oracle_id in request; empty selection; engine cannot find replacement; validation failure |
| 404 | Deck id unknown |

### Existing: `POST /api/v1/generate/from-deck`

**UX11:** Remains for CLI and automation. Web iterate uses **`/decks/{id}/…`** so the server loads the canonical library record (no client path or inline deck path). `refill_slot` on this endpoint is **not** wired from the SPA.

---

## Explicit non-goals (UX11 API)

| Topic | Phase |
| --- | --- |
| Profile package swap | UX8 / future |
| `repair_dependencies` trigger from web | Deferred — not UX11 |
| Full-deck regen button | **UX11b** uses slot refill only; full `from-deck` regen without slot stays CLI |
| JSON download / import | Post-UX7f |
| Batch iterate across multiple library decks | Out of scope |

---

## References

- [user-experience.md](../dependency-engine/user-experience.md) § UX11 — product decisions and slices
- [screens.md](screens.md) § Deck editor
- [library-api.md](library-api.md) — library persistence
- [deck-output-format.md](../../product/deck-output-format.md) — `locked` field
