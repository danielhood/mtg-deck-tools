# Web UI package

**Status:** **UX7c + UX7e shipped**. **UX7f** (server saved deck library) — decisions locked; implementation will add `/library`, library API client, and JSON-first deck view — see [library-api.md](../specs/web/library-api.md).

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
    components/             # AppShell, WizardChrome, LoadingState, ErrorState, CardLightbox
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

1. `mtg-deck-tools import` (once) so `GET /api/v1/wizard/meta` reports `db_ready`.
2. `mtg-deck-tools serve` in one terminal.
3. `cd packages/web && pnpm install && pnpm dev` in another.
4. Walk `/` → `/build/1` … `/build/7` → `/build/review` → Generate → `/deck/:id`.

Wizard draft state persists in `sessionStorage` (`mtg-wizard-draft`). Last generate result: `mtg-active-deck-id` + `mtg-deck-{uuid}` (legacy `mtg-wizard-result` migrated on read).

## Principles

- **Cross-platform:** Browser UI on Windows, Linux, macOS, and mobile without native builds.
- **Mobile-first:** Single-column UX; 375px baseline per [design.md](../../specs/web/design.md).
- **One engine:** Python core via wizard HTTP API — no duplicate rules in Svelte.
- **Local-first:** Default launch is `mtg-deck-tools serve` on localhost.

Architecture: [specs/web/architecture.md](../../specs/web/architecture.md). Routes: [routes.md](../../specs/web/routes.md). Wireframes: [wireframes/index.md](../../specs/web/wireframes/index.md).
