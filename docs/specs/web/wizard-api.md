# Web UI — wizard HTTP API (planned)

**Status:** **UX7c-a shipped** — wizard catalog endpoints in [openapi.yaml](openapi.yaml). Review/generate UI (**UX7c-b**) uses `preflight` + existing `generate`.

Function-specific API for the build wizard. The SPA holds a `DeckCriteria` draft; **validation and wizard logic stay on the server**. Shipped endpoints (health, stats, import, generate) remain in OpenAPI.

---

## Design principle

Minimal logic in the web layer — backend owns catalogs, synergy context, preflight, commander search, and generate. Contract tested in Python; OpenAPI extended in the same PR as handlers.

---

## Screen → API map (UX7c)

Forward mapping (route → endpoints consumed). Screen behavior: [screens.md](screens.md).

| Route | Endpoints |
| --- | --- |
| `/` | `GET /health`, `GET /api/v1/wizard/meta` (or `GET /api/v1/stats`) |
| `/build/1` | `GET /api/v1/wizard/themes`, `GET /api/v1/wizard/slot-template/defaults` |
| `/build/2` | `GET /api/v1/wizard/mechanics` |
| `/build/3` | `POST /api/v1/wizard/synergy-context` |
| `/build/4` | — (client-only; preflight validates) |
| `/build/5` | — (client-only; preflight validates) |
| `/build/6` | `GET /api/v1/wizard/commanders/search` |
| `/build/7` | `GET /api/v1/wizard/rarities` (optional) |
| `/build/review` | `POST /api/v1/wizard/preflight`, `POST /api/v1/generate` |
| `/build/result` | Response from `POST /api/v1/generate` (display only) |

---

## Planned endpoints

| Method | Path | Purpose | Route |
| --- | --- | --- | --- |
| GET | `/api/v1/wizard/meta` | Step labels, `db_ready`, app version | `/` |
| GET | `/api/v1/wizard/themes` | Archetype choices | `/build/1` |
| GET | `/api/v1/wizard/slot-template/defaults` | Default slot template | `/build/1` |
| GET | `/api/v1/wizard/mechanics` | Include/avoid option lists | `/build/2` |
| POST | `/api/v1/wizard/synergy-context` | Activated profiles + focus chip options | `/build/3` |
| POST | `/api/v1/wizard/preflight` | `lint_criteria` warnings | `/build/review` |
| GET | `/api/v1/wizard/commanders/search` | Commander typeahead | `/build/6` |
| GET | `/api/v1/wizard/rarities` | Min rarity choices (optional static list) | `/build/7` |
| POST | `/api/v1/generate` | Build deck — **existing** | `/build/review` → `/build/result` |

### Request/response notes

- **`synergy-context`** — body: partial `DeckCriteria`; response: activated profiles and allowed focus levels.
- **`preflight`** — body: full `DeckCriteria`; response: `criteria_warnings[]` aligned with CLI preflight.
- **`commanders/search`** — query: `q`, `colors`, `color_match=includes|exact`, budget fields from criteria.
- **`generate`** — server assigns random `seed` when absent; stored in `.deck.json` when **UX7f** persists decks.

Implementation may extend `GenerateResponse` with inline markdown/HTML, or add a follow-up GET for MD content — decide in UX7c-b.

---

## Existing endpoints (UX7a)

Used by home and generate flow:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/api/v1/stats` | DB probe (`404` when missing) |
| POST | `/api/v1/import` | Not used in UX7c (CLI import until **UX7g**) |
| POST | `/api/v1/generate` | Deck build |

See [openapi.yaml](openapi.yaml) for current schemas.

---

## References

- [screens.md](screens.md) — which route calls which endpoint
- [openapi.yaml](openapi.yaml) — shipped contract
- [architecture.md](architecture.md) — service layer; no duplicated rules in TypeScript
