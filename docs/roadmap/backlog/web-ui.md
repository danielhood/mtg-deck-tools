# Backlog — Web UI

Planned app: `packages/web/`. **Active:** **UX7d** (dashboard) in [active.md](../active.md).

Spec: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package: [packages/web/README.md](../../packages/web/README.md).

---

## UX7 MVP status

Sub-phases **UX7a–UX7c**, **UX7e**, and **UX7f** are **shipped**. **UX7d** is active (not backlog).

| Sub-phase | Deliverable | Status |
| --- | --- | --- |
| UX7a | `service/` + OpenAPI | Shipped — [changelog](../../history/changelog.md) |
| UX7b | `mtg-deck-tools serve` | Shipped |
| UX7c | Build wizard + result | Shipped |
| UX7e | Enhanced deck view | Shipped |
| UX7f | Saved deck library | Shipped — [library-api.md](../../specs/web/library-api.md) |
| **UX7d** | Dependency dashboard | **Active** — [active.md](../active.md) |

Ship dates and PR notes: [changelog.md](../../history/changelog.md).

---

## Up next (after UX7d)

Promote to [active.md](../active.md) before implementation.

| Order | ID | Topic | Notes | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **UX10** | Deck composition metrics UI | CMC charts; may overlap enhanced deck view | UX7e+ (shipped), [deck-output-format.md](../../product/deck-output-format.md) |
| 2 | **UX11** | GUI deck editor / iterate | Swap, lock, slot regen, regen without wizard | UX7e (shipped), [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX11 |

**Parallel:** UX10 and UX11 can run **in parallel with each other** once UX7d closes the MVP; both need enhanced deck view (shipped).

---

## Infrastructure backlog

| ID | Topic | Notes | Depends on |
| --- | --- | --- | --- |
| **UX7g** | Web DB init / refresh | Import or auto-download Scryfall bulk when online; replaces CLI-only first-time setup gate | UX7b (shipped) |

---

## Platform notes (reference)

- **Platform:** Windows, Linux, macOS browsers + mobile layouts.
- **Engine:** Python only — no port.
- **Frontend:** Svelte 5 + Vite SPA.
- **CLI:** Automation and dogfood; interactive users target web.
- **Hosting:** Local-first `serve`; self-host / PaaS in [deployment.md](../../specs/web/deployment.md).
