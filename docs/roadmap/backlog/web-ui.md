# Backlog — Web UI

Planned app: `packages/web/`. **UX7 MVP shipped** — promote next row to [active.md](../active.md) before implementation.

Spec: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package: [packages/web/README.md](../../packages/web/README.md).

---

## UX7 MVP status

All sub-phases **UX7a–UX7d** are **shipped**.

| Sub-phase | Deliverable | Status |
| --- | --- | --- |
| UX7a | `service/` + OpenAPI | Shipped — [changelog](../../history/changelog.md) |
| UX7b | `mtg-deck-tools serve` | Shipped |
| UX7c | Build wizard + result | Shipped |
| UX7e | Enhanced deck view | Shipped |
| UX7f | Saved deck library | Shipped — [library-api.md](../../specs/web/library-api.md) |
| UX7d | Dependency dashboard | Shipped — [screens.md](../../specs/web/screens.md) § Dependency dashboard |

Ship dates and PR notes: [changelog.md](../../history/changelog.md).

---

## Up next

Promote to [active.md](../active.md) before implementation.

| Order | ID | Topic | Notes | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **UX10** | Deck composition metrics UI | CMC charts; may overlap enhanced deck view | UX7e+ (shipped), [deck-output-format.md](../../product/deck-output-format.md) |
| 2 | **UX11** | GUI deck editor / iterate | Swap, lock, slot regen, regen without wizard | UX7e (shipped), [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX11 |

**Parallel:** UX10 and UX11 can run **in parallel with each other**; both need enhanced deck view (shipped).

---

## Infrastructure backlog

### UX7g — Database init / refresh

**Status:** **Partially shipped** — server bootstrap done; web-initiated flow backlog.

| Slice | Deliverable | Status |
| --- | --- | --- |
| **UX7g-a** | Scryfall bulk auto-download (`scryfall_bulk.py`, `MTG_AUTO_DOWNLOAD`) | Shipped |
| **UX7g-a** | `mtg-deck-tools serve` startup bootstrap via `ensure_cards_database` | Shipped |
| **UX7g-a** | `POST /api/v1/import` (same pipeline; unused by SPA) | Shipped |
| **UX7g-a** | Docker first-boot download + import | Shipped |
| **UX7g-b** | Home **Download card data** → `POST /api/v1/import` with progress UI | Backlog |
| **UX7g-b** | Poll `GET /api/v1/wizard/meta` until `db_ready`; enable wizard without CLI | Backlog |
| **UX7g-b** | Optional web **refresh** (re-import bulk) | Backlog |

**Today:** With default `MTG_AUTO_DOWNLOAD=1`, `serve` (and Docker) often builds `cards.db` **before** the SPA loads — many users never see the DB-missing banner. When `MTG_AUTO_DOWNLOAD=0`, the API is already running without a DB, or a browser-only user needs refresh, the SPA still shows a **CLI/server** banner (`DbBanner`) — not UX7g-b.

Spec: [architecture.md](../../specs/web/architecture.md) § Database gate · [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX7g.

---

## Platform notes (reference)

- **Platform:** Windows, Linux, macOS browsers + mobile layouts.
- **Engine:** Python only — no port.
- **Frontend:** Svelte 5 + Vite SPA.
- **CLI:** Automation and dogfood; interactive users target web.
- **Hosting:** Local-first `serve`; self-host / PaaS in [deployment.md](../../specs/web/deployment.md).
