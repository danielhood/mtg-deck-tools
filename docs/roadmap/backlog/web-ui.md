# Backlog — Web UI

Planned app: `packages/web/`. Promote the next row to [active.md](../active.md) before implementation.

Specs: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package: [packages/web/README.md](../../packages/web/README.md). Shipped work: [changelog.md](../../history/changelog.md).

---

## Up next

*No promoted rows — see [deck-input.md](../../specs/product/deck-input.md) for next deck-input priorities (resolver v2).*

---

## Deck input — existing lists (UX13)

Cross-format parsers: [deck-input.md](../../specs/product/deck-input.md).

**Shipped:** **UX13-MVP** (CLI/API/parser), **UX13b** (home paste/file/template), **UX13c** (preview + gated import).

| ID | Topic | Notes | Spec |
| --- | --- | --- | --- |
| **UX13** | Deck input (umbrella) | See roadmap analysis in deck-input.md | [deck-input.md](../../specs/product/deck-input.md) |
| UX13a | Search by name | Typeahead add-card; after resolver v2 | [deck-input.md](../../specs/product/deck-input.md) § Search |
| UX13d | Spreadsheet upload UI | CSV (XLSX later); was UX13c before preview promotion | [deck-input.md](../../specs/product/deck-input.md) § Spreadsheet |
| UX13e | Voice input (mobile) | Web Speech API; experimental | [deck-input.md](../../specs/product/deck-input.md) § Voice |
| UX13f | Camera scan (mobile) | Per-card recognition spike | [deck-input.md](../../specs/product/deck-input.md) § Camera |

**Depends on:** resolver v2 before **UX13a** search-by-name. Spreadsheet (**UX13d**) after resolver UX solid.

**Deferred wireframes:** import preview panel, disambiguation list, mobile capture bar — [wireframes/README.md](../../specs/web/wireframes/README.md) when promoted.

---

## Platform notes (reference)

- **Platform:** Windows, Linux, macOS browsers + mobile layouts.
- **Engine:** Python only — no port.
- **Frontend:** Svelte 5 + Vite SPA.
- **CLI:** Automation and dogfood; interactive users target web.
- **Hosting:** Local-first `serve`; self-host / PaaS in [deployment.md](../../specs/web/deployment.md).
