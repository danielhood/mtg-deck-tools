# Web deployment (local and self-host)

**Status:** UX7b — `mtg-deck-tools serve` with env defaults and optional static UI mount.

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
| `MTG_SERVE_STATIC_DIR` | *(unset)* | SPA static root (set by `serve --with-ui` / `--ui-dir`) |

CLI flags override env for the current process (`--host`, `--port`, `--db`, `--ui-dir`).

## Self-hosted (single process)

1. Install with web extra: `pip install -e ".[web]"`.
2. Import or copy `cards.db` to a persistent volume.
3. Run:

```bash
export MTG_DB_PATH=/data/cards.db
mtg-deck-tools serve --host 0.0.0.0 --port 8000
```

4. Optionally mount the built UI: `mtg-deck-tools serve --host 0.0.0.0 --with-ui`.

**Constraints (v1):** one deployment = one user; single-writer SQLite; no built-in login. Operators exposing a public URL should add reverse-proxy auth (out of product scope).

## Simple PaaS (Fly.io, Railway, Render)

- One web service running `mtg-deck-tools serve --host 0.0.0.0 --port $PORT`.
- Persistent disk/volume for `MTG_DB_PATH` (import on deploy or bake a snapshot in the image).
- No secrets required for Scryfall (bulk JSON only).

Docker is not shipped in-repo; wrap the same command in your own image if needed.

## References

- [architecture.md](architecture.md) — deployment modes and hosting policy
- [openapi.yaml](openapi.yaml) — API contract
- [README.md](../../../README.md) — install and quick checks
