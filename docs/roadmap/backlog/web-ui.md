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

**Shipped:** **UX11** GUI deck editor — spec [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX11 · API [iterate-api.md](../../specs/web/iterate-api.md).

**Parallel:** UX10 and UX11 may run in parallel; UX11 is the current primary thread.

---

## Infrastructure (shipped — UX7g)

### UX7g — Database init / refresh

**Status:** **Shipped** — server bootstrap (UX7g-a) and web-initiated import/refresh (UX7g-b).

| Slice | Deliverable | Status |
| --- | --- | --- |
| **UX7g-a** | Scryfall bulk auto-download (`scryfall_bulk.py`, `MTG_AUTO_DOWNLOAD`) | Shipped |
| **UX7g-a** | `mtg-deck-tools serve` startup bootstrap via `ensure_cards_database` | Shipped |
| **UX7g-a** | `POST /api/v1/import` (same pipeline; unused by SPA) | Shipped |
| **UX7g-a** | Docker first-boot download + import | Shipped |
| **UX7g-b** | Home **Download card data** → `POST /api/v1/import` with progress UI | Shipped |
| **UX7g-b** | Poll `GET /api/v1/wizard/meta` until `db_ready`; enable wizard without CLI | Shipped |
| **UX7g-b** | Optional web **refresh** (re-import bulk) | Shipped |

**Today:** With default `MTG_AUTO_DOWNLOAD=1`, `serve` (and Docker) often builds `cards.db` **before** the SPA loads. When the API is up without a DB (`MTG_AUTO_DOWNLOAD=0`), or a browser user wants a newer snapshot, the home screen offers **Download card data** / **Refresh card data** via `POST /api/v1/import` (`DbBanner`, `HomePage`).

Spec: [architecture.md](../../specs/web/architecture.md) § Database gate · [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX7g.

---

## Platform notes (reference)

- **Platform:** Windows, Linux, macOS browsers + mobile layouts.
- **Engine:** Python only — no port.
- **Frontend:** Svelte 5 + Vite SPA.
- **CLI:** Automation and dogfood; interactive users target web.
- **Hosting:** Local-first `serve`; self-host / PaaS in [deployment.md](../../specs/web/deployment.md).
