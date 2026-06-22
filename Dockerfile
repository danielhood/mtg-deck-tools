# syntax=docker/dockerfile:1

# --- Stage 1: build web UI ---
FROM node:20-bookworm-slim AS web

WORKDIR /build

RUN corepack enable

COPY packages/web/package.json packages/web/pnpm-lock.yaml packages/web/.npmrc ./
RUN pnpm install --frozen-lockfile

COPY packages/web/ ./
RUN pnpm build

# --- Stage 2: runtime (API + static UI) ---
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    MTG_SERVE_HOST=0.0.0.0 \
    MTG_SERVE_PORT=8000 \
    MTG_DB_PATH=/data/cards.db \
    MTG_DECKS_PATH=/data/decks.db \
    MTG_AUTO_DOWNLOAD=1

COPY LICENSE pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/
COPY resources/ resources/

RUN pip install --no-cache-dir ".[web]"

COPY --from=web /build/dist /app/packages/web/dist

RUN mkdir -p /data

VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=600s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"

CMD [
    "mtg-deck-tools",
    "serve",
    "--with-ui",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--db",
    "/data/cards.db",
]
