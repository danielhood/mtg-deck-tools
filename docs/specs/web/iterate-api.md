# Web UI — deck iterate HTTP API

**Status:** **UX11 shipped (2026-06-26).** **UX12** advanced swap in progress — [advanced-swap-ux.md](advanced-swap-ux.md).

Server-side iterate operations for saved library decks. The SPA does **not** call subprocess CLI; all paths use `service/` facades (same rule as generate).

Contract: [openapi.yaml](openapi.yaml).

---

## Design principle

- **Canonical store:** server library (`GET/PATCH /api/v1/decks/{id}`) — see [library-api.md](library-api.md).
- **Persisted payload:** `.deck.json` document — `locked` on `cards[]` per [deck-output-format.md](../../product/deck-output-format.md).
- **Iterate responses:** same shape as generate where possible — `{ id, deck }` (`GenerateResponse`); optional `swaps[]` diff on swap.
- **No new analyze endpoints** — `dependency_report` and validation messages are embedded in returned `deck` JSON after engine runs.

---

## Screen → API map

| Route / action | Endpoints |
| --- | --- |
| `/deck/:id` — toggle lock | `PATCH /api/v1/decks/{id}` with updated `deck` body (lock flags only; client merges into cached deck) |
| `/deck/:id` — slot regen | `POST /api/v1/decks/{id}/refill-slot` |
| `/deck/:id` — swap selected | `POST /api/v1/decks/{id}/swap` |
| `/deck/:id` — advanced swap / preview | `POST /api/v1/decks/{id}/swap` · `POST /api/v1/decks/{id}/swap/preview` |
| `/deck/:id` — issue playbooks | `GET /api/v1/decks/swap-playbooks/{rule_id}` |
| `/deck/:id` — named card search | `GET /api/v1/wizard/cards/search` |
| `/deck/:id` — load | `GET /api/v1/decks/{id}` on cache miss (unchanged **UX7f**) |

**DB gate:** Same as library — blocked when `db_ready` is false.

---

## Endpoints

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
| `constraints` | `SwapConstraints` | no | **UX12** — type, color, rarity, price, role, named card, slot policy |
| `strategy_id` | string | no | **UX12** — playbook preset (used when `constraints` omitted) |
| `force_validation_override` | boolean | no | **UX12** — when `true`, save deck even if post-swap validation fails; default `false` |

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
| 400 | Commander oracle_id in request; empty selection; engine cannot find replacement; validation failure (unless `force_validation_override`) — structured `validation_errors[]` when validation fails |
| 404 | Deck id unknown |

### `POST /api/v1/decks/{id}/swap/preview` (**UX12**)

Same request body as swap (including `constraints`, `strategy_id`, `preview_limit`). Returns top candidates per vacated position **without persisting**:

```json
{
  "candidates_by_position": [
    {
      "from_oracle_id": "…",
      "from_name": "…",
      "slot": "synergy",
      "candidates": [
        { "oracle_id": "…", "name": "…", "mana_cost": "{2}", "price_usd": 1.5, "rarity": "uncommon" }
      ]
    }
  ]
}
```

### `GET /api/v1/decks/swap-playbooks/{rule_id}` (**UX12**)

Query `deficit` optional — filters strategies by `when_deficit` in `config/swap-playbooks.yaml`.

Returns `{ rule_id, strategies: [{ id, label, default }] }`.

### `GET /api/v1/wizard/cards/search` (**UX12**)

Named-card replacement search. Query: `q`, `colors[]`, `limit`. Commander-legal cards only.

### Existing: `POST /api/v1/generate/from-deck`

**UX11:** Remains for CLI and automation. Web iterate uses **`/decks/{id}/…`** so the server loads the canonical library record (no client path or inline deck path). `refill_slot` on this endpoint is **not** wired from the SPA.

---

## Explicit non-goals

| Topic | Phase |
| --- | --- |
| Profile package swap | UX8 / future |
| `repair_dependencies` trigger from web | Deferred |
| Full-deck regen button | Slot refill only from web |
| JSON download / import | Post-UX7f |
| Batch iterate across multiple library decks | Out of scope |
| Curve advisory iterate (`CURVE_*`) | **UX12f** — deferred post-v1 |

---

## References

- [user-experience.md](../dependency-engine/user-experience.md) § UX11 / UX12
- [advanced-swap-ux.md](advanced-swap-ux.md) — UX12 product spec
- [screens.md](screens.md) § Deck editor
- [library-api.md](library-api.md) — library persistence
- [deck-output-format.md](../../product/deck-output-format.md) — `locked` field
