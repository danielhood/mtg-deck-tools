# AGENTS.md

## Cursor-driven SDLC

Documentation is **agent-enforced**, not CI-gated.

### Planning vs implementation

| Phase | Guide | When |
| --- | --- | --- |
| **Planning** | [docs/sdlc/agent-phases.md](docs/sdlc/agent-phases.md) § Phase 1 | Promote backlog → active, design specs/UX, docs-only PRs |
| **Implementation** | [docs/DOC-MAP.md](docs/DOC-MAP.md) + agent-phases § Phase 2–3 | Code/config/tests; update docs in the **same PR** |
| **Ship** | Remove row from [roadmap/active.md](docs/roadmap/active.md); append [changelog](docs/history/changelog.md) | Feature complete |

**Do not** update changelog or shipped-inventory for planning-only work.

### Every task

1. Read [docs/sdlc/agent-phases.md](docs/sdlc/agent-phases.md) and classify phase.
2. Follow [docs/DOC-MAP.md](docs/DOC-MAP.md) for file targets.
3. Obey `.cursor/rules/` (`sdlc-documentation` always applies).
4. Before PR: **`/sync-documentation`**; dependency expansion: **`/ship-dependency-feature`**.

PRs must include **Phase** (planning | implementation) and a **Documentation** section.

## Cursor Cloud specific instructions

### Product

**MTG Deck Tools** is a Python package: **CLI** (default) plus optional **HTTP API** (UX7a). No Docker. Entry point: `mtg-deck-tools` after `pip install -e ".[dev]"`; API after `pip install -e ".[web]"` or `".[dev,web]"`. See [README.md](README.md) for CLI, import, and API launch (`uvicorn`).

### One-time VM prerequisites

Ubuntu images may ship without `ensurepip`. If `python3 -m venv .venv` fails, install once (not in the update script):

```bash
sudo apt-get update && sudo apt-get install -y python3.12-venv
```

### Python environment

From repo root:

```bash
source .venv/bin/activate   # after update script creates .venv
pytest                      # uses in-memory SQLite, no Scryfall file
mtg-deck-tools analyze run --fail-on-expect  # after import; see docs/specs/deck-analysis.md
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

**CLI-only:** nothing listens on a port. **With `[web]`:** run `mtg-deck-tools serve` locally (see README → HTTP API). No `docker compose` or background daemons required for dogfood or pytest.
