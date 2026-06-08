# Backlog — Web UI

Planned app: `packages/web/`. Active work: **UX7f** (library) under **UX7** in [active.md](../active.md). **UX7c** wizard and **UX7e** deck view shipped.

Spec: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package index: [packages/web/README.md](../../packages/web/README.md).

---

## Delivery sequence (after UX7b)

| Order | ID | Topic | Notes | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **UX7c** | Build wizard + MD result | 7 steps, linear nav, preflight, generate — [screens.md](../../specs/web/screens.md), [routes.md](../../specs/web/routes.md) | UX7b |
| 2 | **UX7e** | Enhanced deck view | Filters, summaries, Scryfall art; entry to edit/analysis | UX7c |
| 3 | **UX7f** | Saved deck library | Server persistence; auto-save on generate; card grid (search, sort, rename, delete) — [library-api.md](../../specs/web/library-api.md) | UX7e |
| 4 | **UX7d** | Dependency dashboard | D5 reporting; after library so decks persist | UX7f, D5 |
| 5 | **UX10** | Deck composition metrics UI | CMC charts; may overlap enhanced deck view | UX7e+, [deck-output-format.md](../../product/deck-output-format.md) |
| 6 | **UX11** | GUI deck editor / iterate | Swap, lock, slot regen, regen without wizard | UX7e, [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX11 |

**Parallel:** UX10 and UX11 can run **in parallel with each other** once **UX7e** exists; both need enhanced deck view, not raw UX7c result page.

---

## Infrastructure backlog

| ID | Topic | Notes | Depends on |
| --- | --- | --- | --- |
| **UX7g** | Web DB init / refresh | Import or auto-download Scryfall bulk when online; replaces CLI-only first-time setup gate | UX7b |

---

## UX7 scope (reference — active, not backlog)

MVP tracked as **UX7** in [active.md](../active.md).

| Sub-phase | Deliverable | Notes |
| --- | --- | --- |
| ~~**UX7a**~~ | ~~`service/` extraction + OpenAPI~~ | **Shipped** |
| ~~**UX7b**~~ | ~~`mtg-deck-tools serve`~~ | **Shipped** |
| ~~**UX7c**~~ | ~~Build wizard + result~~ | **Shipped** — [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX7c |
| ~~**UX7e**~~ | ~~Enhanced deck view~~ | **Shipped** — [screens.md](../../specs/web/screens.md) | UX7c |
| **UX7f** | Saved deck library | Server-side `.deck.json` store; auto-save on generate; card grid (search, sort, rename, delete); load → deck view — decisions locked — [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX7f | UX7e |
| **UX7d** | Dependency dashboard | Drill-down on `dependency_report` (D5); after library so persisted decks can be inspected | UX7f, D5 |

**Platform:** Windows, Linux, macOS browsers + mobile layouts. **Engine:** Python only. **Frontend:** Svelte 5 + Vite SPA.

**CLI:** Automation and dogfood; interactive users target web. In-process `service/` by default.

**Hosting:** Local-first `serve`; self-host / PaaS documented in [deployment.md](../../specs/web/deployment.md).
