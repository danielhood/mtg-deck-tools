# Backlog — Web UI

Planned app: `packages/web/`. Active work: **UX7** in [active.md](../active.md).

Spec placeholder: [specs/web/README.md](../../specs/web/README.md) · Package index: [packages/web/README.md](../../packages/web/README.md).

---

## After UX7 shell

| ID | Topic | Notes | Depends on |
| --- | --- | --- | --- |
| UX10 | Deck composition metrics UI | CMC charts; data from engine | **UX7**, [deck-output-format.md](../../product/deck-output-format.md) |
| UX11 | GUI deck editor | Swap / lock cards under build rules | **UX7**, [user-experience.md](../../specs/dependency-engine/user-experience.md) § UX11 |

**Parallel:** UX10 and UX11 can run **in parallel with each other** once UX7 shell lands; both **block on UX7**.

---

## UX7 scope (reference — active, not backlog)

MVP tracked as **UX7** in [active.md](../active.md). Architecture: [specs/web/architecture.md](../../specs/web/architecture.md).

| Sub-phase | Deliverable | Notes |
| --- | --- | --- |
| ~~**UX7a**~~ | ~~`service/` extraction + OpenAPI~~ | **Shipped** — `service/`, `api/`, [openapi.yaml](../../specs/web/openapi.yaml) |
| ~~**UX7b**~~ | ~~`mtg-deck-tools serve`~~ | **Shipped** — FastAPI, health/stats, optional static UI mount |
| **UX7c** | Web wizard shell | Mobile-first; theme → commander parity with CLI |
| **UX7d** | Dependency dashboard | D5 reporting; path to UX10 charts |

**Platform:** Windows, Linux, macOS browsers + mobile layouts. **Not** a native desktop port. **Engine:** Python only — no language port. **Frontend:** Svelte 5 + Vite SPA.

**CLI:** In-process `service/` by default; optional HTTP client (`--api-url`) deferred until API is stable.

**Hosting:** Local-first `serve`; document self-host / simple PaaS after UX7b.
