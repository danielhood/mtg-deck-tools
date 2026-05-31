# AGENTS.md

## Cursor Cloud specific instructions

### Product

**MTG Deck Tools** is a single Python CLI package (no web server, no Docker). Entry point: `mtg-deck-tools` after `pip install -e ".[dev]"`. See [README.md](README.md) for commands and data layout.

### One-time VM prerequisites

Ubuntu images may ship without `ensurepip`. If `python3 -m venv .venv` fails, install once (not in the update script):

```bash
sudo apt-get update && sudo apt-get install -y python3.12-venv
```

### Python environment

From repo root:

```bash
source .venv/bin/activate   # after update script creates .venv
pytest                      # 142 tests; uses in-memory SQLite, no Scryfall file
ruff check src tests        # configured in pyproject.toml; ruff is not a declared dev dep — pip install ruff if needed
```

### External data (full CLI E2E)

Tests do **not** need Scryfall bulk JSON. Manual `import` / `generate` do:

1. Use the bundled snapshot under `resources/scryfall/oracle-cards-*.json`, or download [Scryfall Oracle Cards bulk](https://scryfall.com/docs/api/bulk-data) when intentionally refreshing (see README).
2. `mtg-deck-tools import` → `data/cards.db` (gitignored).
3. Example full flow: `mtg-deck-tools stats` then `mtg-deck-tools generate --seed 42 --colors G --themes tokens`.

**Data freshness:** Static DB is intentional — target users build with older used cards; no live Scryfall sync. Companion datasets (tags, `card_effects`, audit reports) update when maintainers re-run `import` and `dependency-audit`.

`generate --stub` exercises the CLI without a database but only produces the Phase 1 preview, not a slot-filled deck.

### Services

Nothing listens on a port. No `docker compose` or background daemons are required.
