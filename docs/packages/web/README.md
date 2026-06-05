# Web UI package (planned)

**Status:** **UX7a–UX7b shipped** (backend + `mtg-deck-tools serve`) — SPA (**UX7c**) not started.

## Stack (locked)

| Piece | Choice |
| --- | --- |
| Framework | **Svelte 5** |
| Build | **Vite** SPA (`@sveltejs/vite-plugin-svelte`) |
| API client | OpenAPI-generated TypeScript |
| Hosting | Built `dist/` served by `mtg-deck-tools serve` (FastAPI static mount) |

Not **SvelteKit** — Python owns HTTP; frontend is a client-only bundle.

## Intended layout

```
packages/web/
  src/                   # Svelte components, routes (client-side)
  static/                # Public assets
  package.json
  vite.config.ts
  svelte.config.js
docs/packages/web/       # this file
docs/specs/web/        # architecture, OpenAPI, routes, deployment
src/mtg_deck_tools/
  service/               # Shared facades (CLI + API) — UX7a
  api/                   # FastAPI app — UX7a
```

## Principles

- **Cross-platform:** Browser UI on Windows, Linux, macOS, and mobile without native builds.
- **Mobile-first:** Single-column UX; phone-width layouts are the design baseline.
- **One engine:** Python core via `service/` + HTTP — no duplicate rules in Svelte.
- **CLI coexistence:** Terminal wizard remains; web is the rich shell for dashboards, charts, swap/lock.
- **Local-first:** Default launch is `mtg-deck-tools serve` on localhost; simple self-hosting supported.

Architecture: [specs/web/architecture.md](../../specs/web/architecture.md).

## When implementation begins

Add `package.json` scripts (`dev`, `build`, `check`), document Vite proxy to local API in dev, and how `serve` mounts `dist/`. Add OpenAPI and route docs under `docs/specs/web/`.
