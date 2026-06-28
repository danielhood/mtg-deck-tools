# Web UI package

**Status:** **UX7 MVP shipped** (UX7c + UX7e + UX7f + UX7d) — build wizard, enhanced deck view, saved deck library, and dependency dashboard (`DependenciesPanel`, `/library`, library API client, JSON-first deck view). **UX13b** — plain-text deck import on `/library` (template download + file upload).

## Stack (locked)

| Piece | Choice |
| --- | --- |
| Framework | **Svelte 5** (runes) |
| Build | **Vite** SPA (`@sveltejs/vite-plugin-svelte`) |
| Package manager | **pnpm** (`packageManager` in `package.json`) |
| API client | Hand-written `fetch` wrappers (`src/lib/api.ts`) — OpenAPI types later |
| Hosting | Built `dist/` served by `mtg-deck-tools serve --with-ui` |

Not **SvelteKit** — Python owns HTTP; frontend is a client-only bundle.

## Layout

```
packages/web/
  src/
    App.svelte              # Route switcher
    app.css                 # Design tokens (wireframe parity)
    components/             # AppShell, WizardChrome, DbBanner, DependenciesPanel, LoadingState, ErrorState, CardLightbox
    lib/                    # api, criteria draft, router, format
    pages/                  # Home, build steps 1–7, review, deck view
  index.html
  package.json
  pnpm-lock.yaml            # commit after pnpm install
  vite.config.ts            # Dev proxy → localhost:8000
docs/packages/web/          # this file
docs/specs/web/             # architecture, OpenAPI, routes, wireframes
```

## One-time: enable pnpm

Node 20+ ships [Corepack](https://nodejs.org/api/corepack.html), which reads `packageManager` from `package.json`:

```bash
corepack enable
cd packages/web
pnpm install   # creates pnpm-lock.yaml — commit with dependency changes
```

Without Corepack, install pnpm globally: `npm install -g pnpm` (or see [pnpm.io/installation](https://pnpm.io/installation)).

## Scripts

| Command | Purpose |
| --- | --- |
| `pnpm dev` | Vite on port 5173; proxies `/api` and `/health` to `mtg-deck-tools serve` |
| `pnpm build` | Output to `packages/web/dist` |
| `pnpm check` | `svelte-check` type pass |

## Dev workflow

1. `mtg-deck-tools serve` — with default `MTG_AUTO_DOWNLOAD=1`, missing `cards.db` is built at startup (no separate `import` step). Set `MTG_AUTO_DOWNLOAD=0` only when using a pre-built DB.
2. Confirm `GET /api/v1/wizard/meta` reports `db_ready: true`.
3. `cd packages/web && pnpm install && pnpm dev` in another terminal.
4. Walk `/` → `/build/1` … `/build/7` → `/build/review` → Generate → `/deck/:id`.

Wizard draft persists in `sessionStorage` (`mtg-wizard-draft`). Loaded decks cache in `sessionStorage` as `mtg-deck-cache-{uuid}` (includes `returnTo` for delete redirect). Canonical deck store is the server library API.

## Principles

- **Cross-platform:** Browser UI on Windows, Linux, macOS, and mobile without native builds.
- **Mobile-first:** Single-column UX; 375px baseline per [design.md](../../specs/web/design.md).
- **One engine:** Python core via wizard HTTP API — no duplicate rules in Svelte.
- **Local-first:** Default launch is `mtg-deck-tools serve` on localhost.

Architecture: [specs/web/architecture.md](../../specs/web/architecture.md). Routes: [routes.md](../../specs/web/routes.md). Wireframes: [wireframes/index.md](../../specs/web/wireframes/index.md).
