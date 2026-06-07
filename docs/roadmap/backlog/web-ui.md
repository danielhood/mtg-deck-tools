# Backlog — Web UI

Planned app: `packages/web/`. Active work: **UX7c** (wizard) under **UX7** in [active.md](../active.md).

Spec: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package index: [packages/web/README.md](../../packages/web/README.md).

---

## Delivery sequence (after UX7b)

| Order | ID | Topic | Notes | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **UX7c** | Build wizard + MD result | 7 steps, linear nav, preflight, generate — [screens.md](../../specs/web/screens.md), [routes.md](../../specs/web/routes.md) | UX7b |
| 2 | **UX7e** | Enhanced deck view | Filters, summaries, Scryfall art; entry to edit/analysis | UX7c |
| 3 | **UX7f** | Saved deck library | Save, load, organize `.deck.json` (single-user); JSON download | UX7e |
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
| **UX7c** | Build wizard + result | Wireframes **approved** — implementation slices c-a / c-b / c-c; [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX7c |
| **UX7e** | Enhanced deck view | Filters (slot, type, color); summaries (balance, distribution, cost); analysis hooks; Scryfall art; route `/deck/:id` — [screens.md](../../specs/web/screens.md) | UX7c |
| **UX7f** | Saved deck library | Save/load/organize `.deck.json` (single-user, not multi-tenant); JSON download; load → deck view → iterate/regen without wizard; slot/full regen preserving locks ties to **UX11**; route `/library` | UX7e |
| **UX7d** | Dependency dashboard | Drill-down on `dependency_report` (D5); after library so persisted decks can be inspected | UX7f, D5 |

**Platform:** Windows, Linux, macOS browsers + mobile layouts. **Engine:** Python only. **Frontend:** Svelte 5 + Vite SPA.

**CLI:** Automation and dogfood; interactive users target web. In-process `service/` by default.

**Hosting:** Local-first `serve`; self-host / PaaS documented in [deployment.md](../../specs/web/deployment.md).
