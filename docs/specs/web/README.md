# Web UI specification (planned)

**Status:** **UX7a shipped** (service layer + OpenAPI) — **UX7** remains active for UX7b–UX7d.

## Code location

| Artifact | Path |
| --- | --- |
| Frontend app | [`packages/web/`](../../../packages/web/) (`.gitkeep` until implementation) |
| Service + API | `src/mtg_deck_tools/service/`, `src/mtg_deck_tools/api/` |
| Package index | [packages/web/README.md](../../packages/web/README.md) |

## Architecture (read first)

**[architecture.md](architecture.md)** — cross-platform + mobile-first direction, shared Python `service/` layer, FastAPI for web, **no engine port**, CLI/API coexistence, local and simple hosting modes.

Summary:

- **Engine:** Keep Python (`src/mtg_deck_tools/`) — single source of truth for rules and dogfood.
- **Common layer:** New `service/` module with pydantic DTOs; CLI and HTTP API both call it.
- **Web:** Mobile-first SPA in `packages/web/`; talks REST/OpenAPI only — no duplicated validation in TypeScript.
- **CLI:** In-process `service/` by default; optional `--api-url` for remote/hosted parity later.
- **Run locally:** `mtg-deck-tools serve` (+ optional bundled static UI).
- **Host simply:** Single process + persistent volume for `cards.db`.

## Spec index (fill as UX7 progresses)

| Doc | Status |
| --- | --- |
| [architecture.md](architecture.md) | **Draft** — stack and layering |
| [openapi.yaml](openapi.yaml) | **UX7a** — health, stats, import, generate |
| `routes.md` | Not started — wizard screens, dashboard, editor |
| `deployment.md` | Not started — Docker, env vars, PaaS notes |

## Shared contracts

Reuse existing product specs — do not fork schemas in the frontend:

- [deck-output-format.md](../../product/deck-output-format.md) — `.deck.json`, metrics, lock/swap fields (UX11)
- [user-experience.md](../dependency-engine/user-experience.md) — wizard flow, dependency UX, UX7–UX11 roadmap

## Locked v1 decisions

| Topic | Decision |
| --- | --- |
| Auth | **None** — product does not implement login or API keys |
| Multi-tenant | **Out of scope** — one deployment, one user, single-writer SQLite |
| Engine language | **Python** — no port |
| Frontend framework | **Svelte 5 + Vite** SPA — [architecture.md § Frontend framework](architecture.md#frontend-framework-svelte-locked) |

## Out of scope for v1 web MVP

- Duplicating dependency rules or validation in TypeScript
- Live Scryfall sync (same static snapshot policy as CLI)
- User accounts, sessions, or per-user databases
- Porting the engine to another language

## References

- [active.md](../../roadmap/active.md) — UX7 is the primary product thread
- [backlog/web-ui.md](../../roadmap/backlog/web-ui.md) — UX10, UX11 after shell
- [pipeline-and-components.md](../../architecture/pipeline-and-components.md) — unified service option
