# Backlog — Web UI

Planned app: `packages/web/`. Promote the next row to [active.md](../active.md) before implementation.

Specs: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package: [packages/web/README.md](../../packages/web/README.md). Shipped work: [changelog.md](../../history/changelog.md).

---

## Up next

*No promoted rows — **UX13-MVP** text import shipped; web paste (**UX13b**) in backlog below.*

---

## Deck input — existing lists (UX13)

Load a deck the user already has (file, paste, or interactive capture) into the library and editor. Cross-format parsers: [deck-input.md](../../specs/product/deck-input.md).

**Active:** text file import (**UX13-MVP**) — CLI first; web paste/upload below follows API.

| ID | Topic | Notes | Spec |
| --- | --- | --- | --- |
| **UX13** | Deck input (umbrella) | Library **Import** entry when **UX13b** promotes | [deck-input.md](../../specs/product/deck-input.md) |
| UX13a | Search by name | Typeahead add-card; disambiguation when fuzzy ships | [deck-input.md](../../specs/product/deck-input.md) § Search |
| UX13b | Bulk paste + file upload | **Shipped** — library template download + `.txt` upload | [deck-input.md](../../specs/product/deck-input.md) |
| UX13c | Spreadsheet upload UI | CSV (XLSX later); column mapping step | [deck-input.md](../../specs/product/deck-input.md) § Spreadsheet |
| UX13e | Voice input (mobile) | Web Speech API → confirm matches; experimental | [deck-input.md](../../specs/product/deck-input.md) § Voice |
| UX13f | Camera scan (mobile) | Per-card recognition spike; on-device preferred | [deck-input.md](../../specs/product/deck-input.md) § Camera |

**Depends on:** **UX13-MVP** service + API. **After:** **UX13a** before voice/camera (**UX13e/f**).

**Deferred wireframes:** import hub, paste preview, disambiguation list, mobile capture bar — add under [wireframes/README.md](../../specs/web/wireframes/README.md) when promoted.

---

## Platform notes (reference)

- **Platform:** Windows, Linux, macOS browsers + mobile layouts.
- **Engine:** Python only — no port.
- **Frontend:** Svelte 5 + Vite SPA.
- **CLI:** Automation and dogfood; interactive users target web.
- **Hosting:** Local-first `serve`; self-host / PaaS in [deployment.md](../../specs/web/deployment.md).
