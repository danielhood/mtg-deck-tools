# Technology stack

Target environment: **cross-platform** (Windows, Linux, macOS) CLI; **web UI** for interactive use on desktop and **mobile browsers**. Local SQLite database, offline-capable after import.

## Language / runtime

| Option | Pros | Cons | Fit |
| --- | --- | --- | --- |
| **Python 3.12+** | Fast JSON/SQLite work, rich text/regex for tagging, `questionary` for CLI wizard | Packaging for non-dev users needs PyInstaller/uv | **Strong** — best for data pipeline + CLI v1 |
| **TypeScript (frontend only)** | Mobile-first SPA, OpenAPI client | Must not host engine rules | **Web UI client** |
| **C# / .NET 8** | Native Windows shell | Duplicate engine; abandoned for v1 GUI | **Deferred** |
| **Rust** | Performance | Overkill for ~31k cards; rewrite cost | **Not planned** |

### Recommendation

**Python engine + SQLite** remains the single source of truth. UI layers:

- **CLI (shipped):** `typer` / `questionary` / `rich` — scripting, dogfood, power users
- **Service layer (planned UX7):** `service/` facades shared by CLI and HTTP API
- **Web API (planned UX7):** FastAPI + OpenAPI — local `serve` and simple self-hosting
- **Web SPA (planned UX7):** Mobile-first app in `packages/web/` — no engine port

See [specs/web/architecture.md](../specs/web/architecture.md) for layering and deployment.

## Database

| Option | Pros | Cons |
| --- | --- | --- |
| **SQLite** | Zero config, single file, great Windows support, FTS5 | Single-writer (fine for local tool) |
| **DuckDB** | Excellent analytics on JSON/Parquet | Heavier; less natural for app state |
| **PostgreSQL** | Overpowered | Requires service install |

**Recommendation:** **SQLite** (`cards.db` in project or `%APPDATA%/mtg-deck-tools/`).

Suggested schema sketch:

```sql
CREATE TABLE cards (
  oracle_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type_line TEXT,
  oracle_text TEXT,
  mana_cost TEXT,
  cmc REAL,
  colors TEXT,           -- JSON array
  color_identity TEXT,   -- JSON array
  keywords TEXT,
  produced_mana TEXT,
  commander_legal INTEGER,
  commander_eligible INTEGER,
  edhrec_rank INTEGER,
  price_usd REAL,
  layout TEXT
);

CREATE TABLE card_mechanic_tags (
  oracle_id TEXT,
  tag TEXT,
  source TEXT,           -- 'rule:aristocrats_sacrifice'
  PRIMARY KEY (oracle_id, tag)
);

CREATE INDEX idx_cards_cmc ON cards(cmc);
CREATE INDEX idx_cards_commander_legal ON cards(commander_legal);
```

## Preprocessing tooling

| Task | Tool |
| --- | --- |
| JSON load | Python `json` or `orjson` (faster for 173MB) |
| Regex tagging | Python `re` + versioned YAML taxonomy |
| Pip parsing | Custom parser or adapt existing MTG mana parsers |
| CLI | `typer` |
| Config | `pydantic` models for DeckCriteria |

Optional: store raw JSON as **Parquet** for faster reloads — only worth it if import time becomes painful (currently ~4–5s load in Python).

## UI options

| UI | Status | Notes |
| --- | --- | --- |
| **Typer + questionary CLI** | **Shipped** | Scriptable; calls engine directly (→ `service/` over time) |
| **FastAPI + mobile-first SPA** | **Planned UX7** | Cross-platform + mobile; `mtg-deck-tools serve` |
| **WPF / native desktop** | Deferred | Superseded by web for cross-platform reach |
| **Tauri installable shell** | Optional later | Only if offline installable `.app` / `.exe` is required beyond browser |

**Path:** CLI proved the engine → **UX7** adds `service/` + API + `packages/web` without forking rules.

## Testing

| Layer | Approach |
| --- | --- |
| Color identity subset | Unit tests with known commanders |
| Tagging rules | Golden-file tests: sample oracle_text → expected tags |
| Slot filler | Integration test: fixed criteria → deterministic deck (seeded RNG) |
| Commander validation | Rule cases from CR 903 |

## Project layout (proposed)

```
mtg-deck-tools/
  docs/                  # product, architecture, specs, roadmap, history, SDLC
  resources/
    scryfall/
    mtg/
  src/
    mtg_deck_tools/
      import/
      tags/
      rules/
      builder/
      cli/
  data/
    cards.db             # generated, gitignored
  config/
    mechanic-taxonomy.yaml
    slot-templates.yaml
  tests/
  pyproject.toml
```

## Dependencies (Python starter set)

- `typer` — CLI
- `questionary` — interactive prompts
- `pydantic` — criteria models
- `pyyaml` — taxonomy config
- `rich` — formatted deck output

No ORM required initially; `sqlite3` stdlib is sufficient.

## Performance expectations

| Operation | Expected time |
| --- | --- |
| Full JSON import + tag | 30–90 seconds (one-time) |
| Single deck generation | < 2 seconds |
| DB size | ~50–100 MB |

## What we are not recommending for v1

- **LLM at runtime** — adds cost, latency, non-determinism; curated tags align with your preference
- **Full rules engine** — Commander construction rules are enough; don't parse entire CR
- **Live Scryfall API** — bulk JSON + optional manual refresh is simpler offline
