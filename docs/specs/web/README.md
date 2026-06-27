# Web UI specification

**Status:** **UX7 MVP shipped** (UX7a–UX7d) — build wizard, enhanced deck view, saved deck library, and dependency dashboard. **UX10** deck metrics (UX10a–c) and **UX11** editor shipped. Post-MVP backlog: [backlog/web-ui.md](../../roadmap/backlog/web-ui.md).

## Code location

| Artifact | Path |
| --- | --- |
| Frontend app | [`packages/web/`](../../../packages/web/) (Svelte 5 + Vite — UX7c-a) |
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

## Spec index

| Doc | Role |
| --- | --- |
| [architecture.md](architecture.md) | Stack, layering, product modes, DB gate, phased delivery |
| [routes.md](routes.md) | **Client routes only** |
| [screens.md](screens.md) | Screen behavior per route; **API consumed per screen** |
| [navigation.md](navigation.md) | Next/Back, review, home flows |
| [wizard-api.md](wizard-api.md) | Wizard HTTP endpoints; screen → API index |
| [library-api.md](library-api.md) | **UX7f shipped** — saved deck library HTTP API |
| [iterate-api.md](iterate-api.md) | **UX11 shipped** — deck editor iterate API |
| [design.md](design.md) | Visual design tokens |
| [wireframes/README.md](wireframes/README.md) | Layout mock and review process (HTML wireframes) |
| [openapi.yaml](openapi.yaml) | **Shipped** — health, stats, import, generate, library |
| [deployment.md](deployment.md) | **UX7b** — env vars, self-host, PaaS notes |

## Shared contracts

Reuse existing product specs — do not fork schemas in the frontend:

- [deck-output-format.md](../../product/deck-output-format.md) — `.deck.json`, metrics (UX10a–c), lock/swap fields (UX11)
- [user-experience.md](../dependency-engine/user-experience.md) — wizard flow, UX7c scope, UX roadmap
- [backlog/web-ui.md](../../roadmap/backlog/web-ui.md) — post-MVP web backlog (UX10/UX11 shipped)

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
