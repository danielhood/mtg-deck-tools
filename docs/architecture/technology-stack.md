# Technology Options

Target environment: **Windows 10/11**, local database, offline-capable after import.

## Language / runtime

| Option | Pros | Cons | Fit |
| --- | --- | --- | --- |
| **Python 3.12+** | Fast JSON/SQLite work, rich text/regex for tagging, `questionary` for CLI wizard | Packaging for non-dev users needs PyInstaller/uv | **Strong** — best for data pipeline + CLI v1 |
| **C# / .NET 8** | Native Windows, WPF/WinUI, excellent SQLite | Slower iteration on text tagging rules | **Strong** if native GUI is v1 |
| **TypeScript (Node)** | Good if web UI is primary | Weaker for offline CLI-first workflow | Moderate |
| **Rust** | Performance | Overkill for ~31k cards | Low priority |

### Recommendation

**Python core + SQLite** for phases 1–2, with UI added as either:

- **CLI:** `questionary` / `typer` / `rich` (minimal deps, good UX for power users)
- **Local web:** FastAPI + HTMX or small React SPA (best wizard UX / card preview)
- **Later:** Thin WPF app calling Python via subprocess, or port core to C#

Since UI preference is **undecided**, Python keeps options open without committing to a GUI framework yet.

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

## UI options (since undecided)

| UI | Effort | UX quality | Notes |
| --- | ---: | ---: | --- |
| **Typer + questionary CLI** | Low | Medium | Good for v1 proof; scriptable |
| **FastAPI + HTMX** | Medium | High | Localhost wizard, show Scryfall images |
| **Streamlit** | Low–Medium | Medium | Rapid prototype; less customizable |
| **WPF (.NET)** | High | High | Best native Windows feel |
| **Tauri + web frontend** | High | High | Cross-platform packaging |

**Pragmatic path:** Start CLI → if wizard feels cramped, add FastAPI layer reusing same Python modules.

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
