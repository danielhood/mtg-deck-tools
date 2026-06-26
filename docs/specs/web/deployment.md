# Web deployment (local and self-host)

**Status:** UX7b — `mtg-deck-tools serve` with env defaults and optional static UI mount; **Docker** — `Dockerfile` + `docker-compose.yml`.

## Local development

| Mode | Command |
| --- | --- |
| API only | `mtg-deck-tools serve` |
| API + hot reload | `mtg-deck-tools serve --reload` |
| API + built SPA | `mtg-deck-tools serve --with-ui` (requires `packages/web/dist` after UX7c) |
| Frontend dev (UX7c+) | Vite dev server proxying `/api` to `serve` |

Default bind: `127.0.0.1:8000`. **v1 has no auth** — use the default host for local use.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `MTG_SERVE_HOST` | `127.0.0.1` | Bind address |
| `MTG_SERVE_PORT` | `8000` | Listen port |
| `MTG_DB_PATH` | `data/cards.db` | Default SQLite for API when `?db=` is omitted |
| `MTG_AUTO_DOWNLOAD` | `1` | When `MTG_DB_PATH` is missing at `serve` startup, download oracle bulk + import (`0` to skip and start without a DB — use web **Download card data** or CLI `import`) |
| `MTG_DECKS_PATH` | `data/decks.db` | Saved deck library SQLite (persist on same volume as `cards.db`) |
| `MTG_PROJECT_ROOT` | *(source layout)* | Repo root for `config/`, `resources/`, and `packages/web/dist` when the package is pip-installed outside a checkout |
| `MTG_SERVE_STATIC_DIR` | *(unset)* | SPA static root (set by `serve --with-ui` / `--ui-dir`) |

CLI flags override env for the current process (`--host`, `--port`, `--db`, `--ui-dir`).

## Self-hosted (single process)

1. Install with web extra: `pip install -e ".[web]"`.
2. Run `mtg-deck-tools serve --host 0.0.0.0 --port 8000` — on first start, missing `cards.db` triggers Scryfall download + import when `MTG_AUTO_DOWNLOAD=1` (default). With `MTG_AUTO_DOWNLOAD=0`, the API starts without a DB; use the SPA **Download card data** or CLI `import`. Or import/copy `cards.db` to a persistent volume beforehand.
3. Optionally mount the built UI:

```bash
export MTG_DB_PATH=/data/cards.db
export MTG_DECKS_PATH=/data/decks.db
mtg-deck-tools serve --host 0.0.0.0 --port 8000 --with-ui
```

**Constraints (v1):** one deployment = one user; single-writer SQLite; no built-in login. Operators exposing a public URL should add reverse-proxy auth (out of product scope).

## Docker

Production image: multi-stage build (pnpm → `packages/web/dist`, pip → `mtg-deck-tools serve --with-ui`). Runtime data lives on a volume at `/data`.

### Traefik (LAN reverse proxy)

`docker-compose.yml` joins the external Docker network `proxy` and registers Traefik labels (same pattern as [docker-reverse-proxy](https://github.com/danielhood/docker-reverse-proxy)). Traefik listens on host port **80**; this stack does not publish `8000` by default.

1. Start Traefik once on the Docker host (`docker-reverse-proxy`: `docker compose up -d`).
2. Ensure `mtg-deck-tools.deck-build.lan` resolves to that host (LAN DNS or `/etc/hosts`).
3. Start this stack:

```bash
docker compose up --build
```

Open `http://mtg-deck-tools.deck-build.lan`. Traefik forwards plain HTTP to container port `8000`.

Standalone (no Traefik): uncomment the `ports` mapping in `docker-compose.yml` and use `http://<host-ip>:8000`.

| Topic | Policy |
| --- | --- |
| **Routing** | Traefik `Host(`mtg-deck-tools.deck-build.lan`)` → container `:8000` on network `proxy` |
| **Volume** | `mtg-data:/data` — `cards.db`, `decks.db`, survives container recreate |
| **First boot** | Empty volume → Scryfall download + import (same as `MTG_AUTO_DOWNLOAD=1`) |
| **Health** | `GET /health` (Docker `HEALTHCHECK`; long `start-period` for first import) |
| **Scale** | One container instance — SQLite single-writer |

Air-gapped: set `MTG_AUTO_DOWNLOAD=0`, bind-mount a host directory with `cards.db` (and optional `decks.db`) to `/data`.

Files: [`Dockerfile`](../../../Dockerfile), [`docker-compose.yml`](../../../docker-compose.yml), [`.dockerignore`](../../../.dockerignore).

## Simple PaaS (Fly.io, Railway, Render)

- One web service running `mtg-deck-tools serve --host 0.0.0.0 --port $PORT --with-ui --db /data/cards.db`.
- Persistent disk/volume for `MTG_DB_PATH` and **`MTG_DECKS_PATH`** (import on deploy or bake a snapshot in the image; library survives redeploys).
- No secrets required for Scryfall (bulk JSON only).
- Same container image as Docker self-host; point the platform at the repo `Dockerfile`.

## References

- [architecture.md](architecture.md) — deployment modes and hosting policy
- [openapi.yaml](openapi.yaml) — API contract
- [README.md](../../../README.md) — install and quick checks
