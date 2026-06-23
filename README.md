# MTG Deck Tools

Local utility for building **Commander** (EDH) decks: a terminal wizard walks through themes, mechanics, colors, budget, commander, and rarity, then generates a legal 100-card list with Markdown and machine-readable output.

Documentation: [`docs/README.md`](docs/README.md) · agent doc map: [`docs/DOC-MAP.md`](docs/DOC-MAP.md) · active roadmap: [`docs/roadmap/active.md`](docs/roadmap/active.md).

## Prerequisites

- Python 3.12+ on `PATH` as `python3` (interpreter only — see setup below for `pip` / `venv`)
- Git
- **Linux (optional):** [uv](https://docs.astral.sh/uv/) via `scripts/bootstrap-linux.sh` when the system Python lacks `pip`, `venv`, or `ensurepip` (no `sudo` required)

## External data (not in this repository)

These files are **copyrighted by their respective owners** and are **not** committed. Download them into the paths below before running import/build steps.

### Scryfall oracle cards

| | |
| --- | --- |
| **Source** | [Scryfall Bulk Data — Oracle Cards](https://scryfall.com/docs/api/bulk-data) |
| **Download** | Use the **Oracle Cards** row → Download, or fetch the current `download_uri` from `GET https://api.scryfall.com/bulk-data/oracle-cards` |
| **Place in repo** | `resources/scryfall/oracle-cards-<timestamp>.json` |
| **Automatic** | If no local JSON exists, `mtg-deck-tools import` and `mtg-deck-tools serve` download the latest oracle bulk from Scryfall (disable with `MTG_AUTO_DOWNLOAD=0` or `import --no-download`) |

Example (filename will match the bulk export date):

```
resources/scryfall/oracle-cards-20260528210654.json
```

Scryfall provides gameplay and price data under their [API terms](https://scryfall.com/docs/api). This project uses a **static oracle bulk snapshot** (see `resources/scryfall/`). Prices and oracle text reflect import time only — fine for building with **older used cards**; run `import` again when you intentionally update the snapshot.

Field reference for card objects: [`resources/scryfall/oracle-card-fields.md`](resources/scryfall/oracle-card-fields.md).

### Magic: The Gathering Comprehensive Rules

| | |
| --- | --- |
| **Source** | [Magic Rules](https://magic.wizards.com/en/rules) — **Comprehensive Rules** (TXT, PDF, or DOCX) |
| **Place in repo** | `resources/mtg/MagicCompRules YYYYMMDD.txt` |

Example:

```
resources/mtg/MagicCompRules 20260417.txt
```

Use the effective date in the filename so updates are obvious. Commander deck construction is defined in **rule 903** and partner rules in **702.124**.

## Generated data (local only)

| Artifact | Location | Notes |
| --- | --- | --- |
| SQLite card DB | `data/cards.db` | Built from oracle JSON; derivative of Scryfall — not committed |
| Deck outputs | `output/` | `.md` + `.deck.json` per build |

## Project layout

```
mtg-deck-tools/
  docs/                     # Product, architecture, specs, roadmap, history (see docs/README.md)
  src/mtg_deck_tools/       # CLI + engine; service/ + api/ (UX7a)
  packages/web/             # Web SPA (Svelte 5 + Vite — UX7c wizard + UX7e deck view)
  scripts/                  # bootstrap-linux.sh (uv-based env on Linux)
  Dockerfile                # Production image (API + built SPA)
  docker-compose.yml        # Single-service LAN/self-host stack
  resources/
    scryfall/               # Oracle bulk JSON (local download) + field docs
    mtg/                    # Comprehensive Rules (local download)
  data/                     # Generated SQLite (gitignored)
  output/                   # Generated decks (gitignored)
```

## Setup (development)

Pick one path. All options install editable package `mtg-deck-tools` with dev dependencies into `.venv/`. Add the **`[web]`** extra when you want the HTTP API (FastAPI + uvicorn):

```bash
pip install -e ".[dev,web]"
```

CLI-only installs can omit `[web]` until you run the API locally.

### Standard (Python `venv` + `pip`)

**Windows (PowerShell)**

```powershell
cd mtg-deck-tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,web]"   # omit ,web for CLI-only
```

**Linux / macOS (bash)**

```bash
cd mtg-deck-tools
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,web]"   # omit ,web for CLI-only
```

On Debian/Ubuntu, if `python3 -m venv` fails, install the matching `python3.*-venv` package once (e.g. `python3.12-venv`).

### Bootstrap with uv (Linux)

Use this when you have **Python 3.12+** but not a working `pip` or `venv` module (minimal cloud images, fresh Ubuntu without `python3-venv`). The script downloads a project-local [uv](https://docs.astral.sh/uv/) binary to `.tools/uv` (gitignored), creates `.venv`, and runs `uv pip install -e ".[dev,web]"` (CLI, pytest, FastAPI, uvicorn). It does **not** install Python itself.

```bash
cd mtg-deck-tools
chmod +x scripts/bootstrap-linux.sh   # first clone only
./scripts/bootstrap-linux.sh
source .venv/bin/activate
```

Recreate the virtual environment from scratch:

```bash
./scripts/bootstrap-linux.sh --clear
```

A PowerShell equivalent for Windows is not bundled yet; use the standard Windows steps above when `pip` and `venv` are available.

### Data and database

Ensure oracle cards JSON and Comprehensive Rules are in place (see [External data](#external-data-not-in-this-repository)), then:

```bash
mtg-deck-tools import
mtg-deck-tools stats
```

## HTTP API (local)

The same engine as the CLI is exposed over REST for web clients and integration tests. Contract: [`docs/specs/web/openapi.yaml`](docs/specs/web/openapi.yaml). Architecture: [`docs/specs/web/architecture.md`](docs/specs/web/architecture.md).

**Requires:** `pip install -e ".[web]"` (or `".[dev,web]"`) and a built `data/cards.db` (`mtg-deck-tools import`).

### Launch

From the repo root with `.venv` activated:

```bash
mtg-deck-tools serve
```

| Flag / env | Purpose |
| --- | --- |
| `--host` / `MTG_SERVE_HOST` | Bind address (default `127.0.0.1`) |
| `--port` / `MTG_SERVE_PORT` | Listen port (default `8000`) |
| `--db` / `MTG_DB_PATH` | Default SQLite path for API requests without `?db=` |
| `MTG_AUTO_DOWNLOAD` | When `cards.db` is missing at startup, download oracle bulk + import (default `1`; set `0` to skip) |
| `--with-ui` | Mount built SPA from `packages/web/dist` |
| `--ui-dir` | Override static UI directory |
| `--reload` | Auto-restart on code changes (development) |

API-only with hot reload (equivalent to `serve --reload`):

```bash
uvicorn mtg_deck_tools.api.serve:create_serve_app --factory --host 127.0.0.1 --port 8000 --reload
```

| URL | Purpose |
| --- | --- |
| http://127.0.0.1:8000/health | Liveness + package version |
| http://127.0.0.1:8000/docs | Swagger UI (interactive) |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | OpenAPI schema (for client codegen) |

Bind another host/port with `--host` / `--port` (e.g. `--host 0.0.0.0` only when you intend to expose the machine on the LAN). **v1 has no auth** — keep the default `127.0.0.1` for local use.

Self-hosting notes: [`docs/specs/web/deployment.md`](docs/specs/web/deployment.md).

### Docker (LAN / self-host)

**Requires:** Docker Engine with Compose v2. **Traefik:** external `proxy` network from [docker-reverse-proxy](https://github.com/danielhood/docker-reverse-proxy) (start Traefik first).

Build and run (API + web UI behind Traefik on port 80):

```bash
docker compose up --build
```

Open `http://mtg-deck-tools.deck-build.lan` when DNS points that hostname at the Traefik host. Without Traefik, uncomment `ports` in `docker-compose.yml` and use `http://<docker-host-ip>:8000`.

| Detail | Value |
| --- | --- |
| **Routing** | Traefik `Host(`mtg-deck-tools.deck-build.lan`)` → container `:8000` |
| **Persistent data** | Named volume `mtg-data` → `/data/cards.db` and `/data/decks.db` |
| **First start** | Downloads Scryfall oracle bulk and runs `import` when `/data/cards.db` is missing (may take several minutes) |
| **Disable auto-download** | Set `MTG_AUTO_DOWNLOAD=0` in `docker-compose.yml` and mount a pre-built `cards.db` |
| **Auth** | None in v1 — do not expose to the public internet without reverse-proxy auth |

Equivalent one-off:

```bash
docker build -t mtg-deck-tools .
docker run --rm -p 8000:8000 -v mtg-data:/data mtg-deck-tools
```

### Web UI (UX7c + UX7e)

**Requires:** Node.js 20+ with **pnpm** (via [Corepack](https://nodejs.org/api/corepack.html): `corepack enable`), `pip install -e ".[dev,web]"`, and `data/cards.db`.

Development (API + Vite dev server with `/api` proxy):

```bash
# Terminal 1 — API
mtg-deck-tools serve

# Terminal 2 — SPA (from repo root)
cd packages/web
pnpm install
pnpm dev
```

Open http://127.0.0.1:5173 — home → build wizard (steps 1–7) → review → generate → deck view (`/deck/:id`). Production bundle:

```bash
cd packages/web && pnpm build
mtg-deck-tools serve --with-ui
```

Package index: [`docs/packages/web/README.md`](docs/packages/web/README.md).

Regenerate the committed OpenAPI file after API changes:

```bash
python scripts/export_openapi.py
```

### Routes (v1)

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `GET` | `/api/v1/stats` | Database stats (`?db=` optional path to SQLite) |
| `POST` | `/api/v1/import` | Import oracle JSON → SQLite (body: optional `json_path`, `db_path`) |
| `POST` | `/api/v1/generate` | Build deck from `DeckCriteria` + flags; response includes `.deck.json` document |
| `POST` | `/api/v1/generate/from-deck` | Regenerate from `deck_path` or inline `deck` object |

### Quick checks

```bash
curl -s http://127.0.0.1:8000/health

curl -s "http://127.0.0.1:8000/api/v1/stats"

curl -s -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"stub": true, "seed": 42, "colors": ["G"], "themes": ["tokens"]}'
```

Full generate runs can take a few seconds; the API returns the same `.deck.json` shape as CLI `generate` (paths on disk plus optional `deck` body in the JSON response).

## Usage

```powershell
# Import oracle cards into local SQLite (one-time or after bulk refresh)
mtg-deck-tools import

# Database summary
mtg-deck-tools stats

# Dependency inventory audit (after import; writes resources/dependency/reports/)
mtg-deck-tools dependency-audit

# Repeatable validation + dependency dogfood (matrix in config/dogfood-matrix.yaml)
mtg-deck-tools analyze run --write-decks --fail-on-expect

# Full deck: slot-filled 99-card maindeck → output/
mtg-deck-tools generate --seed 42 --colors G --themes tokens

# Full wizard: themes, mechanics, synergy controls, colors, budget, commander, rarity
mtg-deck-tools wizard

# Wizard then generate
mtg-deck-tools generate --wizard --seed 42

# Regenerate from a saved deck (edit criteria in the .deck.json first)
mtg-deck-tools generate --from output/my-deck-20260530.deck.json --seed 42
mtg-deck-tools generate --from output/my-deck-20260530.deck.json --refill-slot synergy --seed 42

# Stricter synergy: filter dead tutors at pick time, or repair after fill
mtg-deck-tools generate --wizard --seed 42 --strict-dependencies
mtg-deck-tools generate --from output/my-deck.deck.json --repair-dependencies --seed 42

# Phase 1 stub preview only (sample synergy cards)
mtg-deck-tools generate --stub --seed 42 --colors B,G --themes aristocrats
```

### Commands

| Command | Description |
| --- | --- |
| `import` | Load `resources/scryfall/oracle-cards-*.json` → `data/cards.db`, mechanic tags, and `card_effects` atoms (downloads oracle bulk from Scryfall when no local JSON exists) |
| `stats` | Row counts, import metadata, top tags, effect counts |
| `serve` | Start HTTP API (`--with-ui` mounts built SPA); see [HTTP API (local)](#http-api-local) |
| `dependency-audit` | Scan DB → dependency reports (pattern hits, profiles, tutor predicates, review queue) |
| `wizard` | Interactive wizard (7 steps + criteria preflight): themes, mechanics, synergy/dependency controls, colors, budget & per-card prices, commander (color + price filters), rarity; after **step 2 onward** and at preflight you can **re-run** the step you just finished, **go back** to an earlier step (downstream steps re-run automatically), or at preflight **re-run criteria review**; step 1 advances directly to step 2; end-of-wizard **criteria linter** warns on conflicting include/avoid, focus vs avoid, heavy theme pairs, and over-constrained budget before showing the summary (criteria only; does not write a deck) |
| `generate` | Build a 99-card maindeck plus commander metadata → `output/*.deck.json` and `output/*.md` |

### `generate` — how it works

The builder fills a **99-card maindeck** (commander is separate) using **slots**: fixed-size buckets such as ramp, draw, removal, synergy, lands, and so on. Default counts live in [`config/slot-templates.yaml`](config/slot-templates.yaml) (e.g. 30 synergy, 31 lands); the wizard can change them within bounds, and the saved `.deck.json` stores the template under `criteria.slot_template`.

Each slot is filled from `data/cards.db` using color identity, theme tags, mechanic tags, budget, and scoring. After nonland slots are filled, **lands** are chosen to match the mana base plan. A **dependency pass** (when `card_effects` is populated after `import`) scores picks during fill, validates cross-card synergy after the build, and can optionally filter or repair gaps (tutor targets, energy/experience/blood/rad/oil/charge/+1/+1 counter balance, token/vehicle/equipment/artifact/type payoffs). Enable counter profiles with `include_mechanics` such as `energy`, `experience`, `blood`, `rad`, `oil`, `charge`, or `counters` (+1/+1). Outputs include validation notes, a **Deck dependencies** section, budget totals, and per-card detail in Markdown.

#### Fresh generate (no `--from`)

| Flag | Effect |
| --- | --- |
| `--wizard` | Run the full wizard first, then generate using its criteria (ignores `--from`, `--colors`, `--themes`). |
| `--colors` | Comma-separated color letters for commander identity filter, e.g. `B,G`. |
| `--themes` | Comma-separated archetype tags, e.g. `tokens,aristocrats`. |
| `--seed` | RNG seed for reproducible picks (also stored in criteria). |
| `--strict-budget` | Exclude cards with no Scryfall price and enforce the budget cap during fill. |
| `--strict-dependencies` | Exclude cards at pick time that would create unfulfillable tutors or one-sided resource loops (requires `card_effects` from `import`). |
| `--repair-dependencies` | After fill, swap cards to fix dependency warnings (tutor targets, resource counter balance, type support). |
| `--prefer-available` | Exclude cards below the import-time availability score (25th percentile). Uses scores from the current `cards.db` snapshot. |
| `--card-price-min` / `--card-price-max` | Per-card USD floor/ceiling when picking cards. |
| `--min-rarity` | Minimum rarity (`common`, `uncommon`, `rare`, `mythic`; default `common`). |
| `--db` | Path to SQLite DB (default `data/cards.db`). |
| `--out` | Output directory (default `output/`). |
| `--stub` | **Preview only:** old Phase 1 sample list, not a full slot fill. Cannot combine with `--from`. |

Without `--wizard` or `--from`, you must supply enough criteria via flags (or extend criteria in code); in practice **`generate --wizard`** is the usual path for a complete deck.

#### Reload from `.deck.json` (`--from`)

Point `--from` at a deck file produced by a previous run (or hand-edited). The tool:

1. Reads **`criteria`** (themes, budget, slot template, mechanics, price filters, seed, etc.) and **`commanders`** from the file.
2. Resolves commanders against the current database (re-import if oracle IDs are missing).
3. Builds a **new** timestamped `.deck.json` / `.md` in `output/` (the source file is not overwritten).

Edit the source file before reloading — for example change `criteria.budget_usd`, `criteria.themes`, or `criteria.slot_template` — then regenerate without rerunning the wizard.

**Full regen** (no `--refill-slot`): discards every maindeck card from the file and runs a complete slot fill from scratch, as if you had just run `generate --wizard` with the same criteria. Only criteria and commanders from the file matter; the old `cards` list is not kept.

#### Refill one slot (`--from` + `--refill-slot`)

Requires `--from`. Use this when you like most of a list but want to **re-roll a single bucket** without touching the rest.

**What happens to each slot**

| Slot in file | Behavior |
| --- | --- |
| **Target slot** (e.g. `synergy`) | All maindeck cards with `slot` equal to that name are **removed**. New cards are picked for that slot only, up to the count in `criteria.slot_template` for that slot (same rules as a normal fill: tags, budget, scoring). |
| **Every other slot** | Cards from the saved `cards` array are **kept as-is** (same names, quantities, and slot labels). |

So `--refill-slot synergy` replaces only the ~30 synergy cards (per default template); ramp, draw, lands, and the rest stay from the saved deck. `--refill-slot lands` replaces only the land package using the land filler for the template’s land count.

**After the refill**

- The deck is still trimmed to budget if a cap is set.
- A **mana base plan** is recomputed from the full 99-card list (including kept nonlands), so land-related warnings may change even when you did not refill `lands`.
- Commander(s) always come from the file / DB, not from the old maindeck list.

**Slot names** must match the template keys: `ramp`, `draw`, `removal`, `board_wipe`, `synergy`, `wincon`, `flex`, `lands`.

**Example:** keep a strong ramp/removal package, try a new synergy package:

```bash
mtg-deck-tools generate --from output/my-deck.deck.json --refill-slot synergy --seed 7
```

Use a different `--seed` to get another random synergy pool; omit `--seed` to use `criteria.seed` from the file.

#### Combining flags with `--from`

| Flag | With `--from` |
| --- | --- |
| `--seed` | Overrides `criteria.seed` for this run. |
| `--strict-budget` | Applied unless already set in the file’s criteria. |
| `--strict-dependencies` | Applied unless already set in the file’s criteria. |
| `--repair-dependencies` | Applied unless already set in the file’s criteria. |
| `--prefer-available` | Applied unless already set in the file’s criteria. |
| `--wizard` | **Ignored** — wizard is not run; criteria come from the file. |
| `--colors` / `--themes` | Ignored (identity and themes come from loaded criteria + commanders). |

## Status

**Phase 1** complete: Python package, SQLite import, mechanic taxonomy v0, CLI (`import`, `stats`, `generate` stub).

**Phase 2** complete: wizard, slot filling, dynamic mana base, and Commander rule validation.

**v1 polish:** budget enforcement during fill, post-fill budget trim pass, `--strict-budget`, tighter slot tags (`board_wipe`, `wincon`), and land price bias when a budget cap is set.

**Phase 3 (v1):** build-time legality filters, slot pool quality, `.deck.json` reload, availability scoring (`--prefer-available`, unpriced classification in Notes), and v1 success criteria closure — **complete** as of 2026-05-30.

**Dependency engine (D0–D5):** effect extraction at import (`card_effects`), post-build `dependency_report` in Markdown/JSON, pick-time scoring (D3), `--strict-dependencies` (D4), and `--repair-dependencies` (D5) — **complete** as of 2026-05-31.

**Dependency expansion:** **tutor payload matching** (CMC bands, colors, land subtypes, multi-type OR for `TUTOR_TARGET_EXISTS`), **enchantments** profile (`ENCHANTMENT_SUPPORT_MIN`, wizard `themes: [enchantress]`), **tokens** (`TOKEN_BALANCE`), **vehicles** (`VEHICLE_BALANCE`), **equipment depth** (`EQUIPMENT_BALANCE`, `include_mechanics: [equip]` or `themes: [voltron]`), **rad/oil/charge counters** (`RAD_BALANCE`, `OIL_BALANCE`, `CHARGE_BALANCE`; `include_mechanics: [rad, oil, charge]`), **subtype lords**, **sacrifice/token refinements** (aristocrats fodder includes token makers; Grave Pact-style `sacrifice_opponent`; persist/undying/escape `death_recursion`), **graveyard/landfall heuristics** (`REANIMATION_SUPPORT`, `GRAVEYARD_COST_SUPPORT`, `SELF_MILL_BALANCE`, `LANDFALL_BALANCE`; wizard `themes: [recursion, landfall]`), **graveyard filler atoms** (surveil, discover, looting discard; `include_mechanics: [surveil]`), and **token subtype buffs** (`TOKEN_SUBTYPE_BUFF_SUPPORT`, subtype capture on `token_produce`) — shipped as of 2026-06. **UX2** wizard step 3 sets `strict_dependencies`, `repair_dependencies`, and optional `mechanic_focus` presets for activated profiles. **UX3** end-of-wizard criteria linter warns on conflicting selections before generate. **UX4** wizard back-navigation. **UX5** `generate --wizard --from` and `wizard --from` pre-fill the wizard from saved criteria. **UX7a** shared `service/` layer + HTTP API (launch with `uvicorn`; see [HTTP API](#http-api-local)). Next: **UX7b** `serve`, **UX7c** web SPA — [`docs/roadmap/active.md`](docs/roadmap/active.md).

## License

Project code is licensed under the [MIT License](LICENSE).

Magic: The Gathering and card data are © Wizards of the Coast.  
Card data via [Scryfall](https://scryfall.com) is unofficial Fan Content permitted under the Wizards Fan Content Policy.
