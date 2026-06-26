# Web UI — saved deck library HTTP API (planned)

**Status:** **UX7f shipped** — see [user-experience.md](../dependency-engine/user-experience.md) § UX7f.

Server-side persistence for saved decks. The SPA does **not** own the canonical store; it caches loaded decks in session for the active `/deck/:id` view only.

Contract: [openapi.yaml](openapi.yaml).

---

## Design principle

- **Persisted payload:** `.deck.json` document only — see [deck-output-format.md](../../product/deck-output-format.md).
- **No filesystem paths** in stored JSON or library API responses (`json_path`, `md_path` removed from the web persistence contract).
- **Markdown** is a CLI/export derivative; not stored or required for web rendering.
- **Single-user** per deployment; no auth in v1.

---

## Storage (implementation)

| Topic | Decision |
| --- | --- |
| Location | Server-side store colocated with deployment (SQLite table or JSON files under configurable data path — implementation detail) |
| Key | Client UUID (`id`) assigned at first save (new wizard generate) |
| Record | `id` + optional user `name` (rename) + `saved_at` + full deck JSON body |
| Volume | Self-host / PaaS: persist deck store on the same volume as `MTG_DB_PATH` (see [deployment.md](deployment.md)) |

Service facades live in `src/mtg_deck_tools/service/`; handlers in `src/mtg_deck_tools/api/`.

---

## Screen → API map (UX7f)

| Route | Endpoints |
| --- | --- |
| `/` | `GET /api/v1/decks?limit=1` (or dedicated “latest”) for **View last deck** |
| `/build/review` | `POST /api/v1/generate` — auto-persists new library entry |
| `/library` | `GET /api/v1/decks` (list, search, sort) |
| `/library` | `PATCH /api/v1/decks/{id}` (rename — invoked from deck view only) |
| `/library` | `DELETE /api/v1/decks/{id}` |
| `/deck/:id` | `DELETE /api/v1/decks/{id}` (delete from deck view footer only) |
| `/deck/:id` | `PATCH /api/v1/decks/{id}` (rename; **UX11** lock via deck body) |
| `/deck/:id` | `POST /api/v1/decks/{id}/refill-slot` (**UX11**) |
| `/deck/:id` | `POST /api/v1/decks/{id}/swap` (**UX11**) |
| `/deck/:id` | `GET /api/v1/decks/{id}` on cache miss; session cache on load |

Iterate detail: [iterate-api.md](iterate-api.md).

**DB gate:** All library and deck routes require `db_ready`; when the database is missing, library endpoints return `404` / blocked state consistent with wizard routes.

---

## Planned endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/decks` | List saved decks — summary rows for library grid |
| GET | `/api/v1/decks/{id}` | Fetch full persisted deck JSON by id |
| PATCH | `/api/v1/decks/{id}` | Update metadata (rename `name`); **UX11** — in-place `deck` body (lock toggles) |
| DELETE | `/api/v1/decks/{id}` | Remove from library |
| POST | `/api/v1/generate` | **Existing** — extended to auto-save new deck (new UUID) and return `id` + `deck` |

### `GET /api/v1/decks`

Query parameters (planned):

| Param | Purpose |
| --- | --- |
| `q` | Search — match user `name`, commander name(s), theme tags |
| `sort` | `saved_at` (default desc), `name`, commander |
| `limit` | Page size (library grid) |

Response: `DeckLibraryEntry[]` — summary fields only (not full card lists).

### `DeckLibraryEntry` (summary)

| Field | Source |
| --- | --- |
| `id` | UUID |
| `name` | User label (defaults to commander name on first save) |
| `saved_at` | Server timestamp |
| `commander_names` | From deck `commanders[].name` |
| `colors` | From deck `criteria.colors` or commander CI |
| `themes` | From deck `criteria.themes` |
| `estimated_price_usd` | From deck `stats` |

### `GET /api/v1/decks/{id}`

Response: `{ "id": "…", "name": "…", "saved_at": "…", "deck": { … } }` where `deck` is the `.deck.json` document.

404 when id unknown → client redirects `/deck/:id` → `/`.

### `POST /api/v1/generate` (UX7f changes)

| Behavior | Rule |
| --- | --- |
| New wizard build | Server assigns new `id` (UUID), builds deck, **auto-saves** to library, returns `{ id, deck }` |
| `criteria.seed` | Persisted inside `deck.criteria.seed` |
| `dependency_report` | Persisted inside deck JSON when present |
| `markdown` | Optional response field for CLI/export only — **not** persisted; web generate does not require it |
| `json_path` / `md_path` | **Removed** from web-facing response (CLI migration: use API ids, not paths) |

### Deferred endpoints

| Topic | Phase |
| --- | --- |
| JSON file download | Post-UX7f |
| Import uploaded `.deck.json` | Post-UX7f |
| Save-as / clone / duplicate | Post-UX7f |

Iterate endpoints (`refill-slot`, `swap`): [iterate-api.md](iterate-api.md) — **UX11**.

---

## CLI alignment (planned refactor)

Today the CLI writes `.deck.json` / `.md` to `output/` and returns filesystem paths. Target state:

- Interactive flows use the **same HTTP API** as the web (or in-process `service/` facades with identical DTOs).
- CLI does **not** depend on `json_path` / `md_path` inside persisted JSON.
- Markdown remains a **CLI export** (`--out` or explicit write); not part of the library record.

Dogfood (`analyze run --fail-on-expect`) may continue using filesystem fixtures until migrated separately.

---

## References

- [user-experience.md](../dependency-engine/user-experience.md) § UX7f — product decisions
- [screens.md](screens.md) — library and deck view behavior
- [routes.md](routes.md) — client routes and guards
- [deck-output-format.md](../../product/deck-output-format.md) — persisted JSON schema
- [openapi.yaml](openapi.yaml) — contract (updated at implementation)
