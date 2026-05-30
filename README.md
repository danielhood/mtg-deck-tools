# MTG Deck Tools

Local utility for building **Commander** (EDH) decks: a terminal wizard walks through themes, colors, mechanics, and budget, then generates a legal 100-card list with Markdown and machine-readable output.

Planning docs: [`planning/README.md`](planning/README.md) · next steps: [`planning/09-next-steps.md`](planning/09-next-steps.md).

## Prerequisites

- Python 3.12+ (for Phase 1+)
- Git

## External data (not in this repository)

These files are **copyrighted by their respective owners** and are **not** committed. Download them into the paths below before running import/build steps.

### Scryfall oracle cards

| | |
| --- | --- |
| **Source** | [Scryfall Bulk Data — Oracle Cards](https://scryfall.com/docs/api/bulk-data) |
| **Download** | Use the **Oracle Cards** row → Download, or fetch the current `download_uri` from `GET https://api.scryfall.com/bulk-data/oracle-cards` |
| **Place in repo** | `resources/scryfall/oracle-cards-<timestamp>.json` |

Example (filename will match the bulk export date):

```
resources/scryfall/oracle-cards-20260528210654.json
```

Scryfall provides gameplay and price data under their [API terms](https://scryfall.com/docs/api). Prices are stale after ~24 hours; gameplay fields change less often (weekly refresh is usually enough).

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
  planning/                 # Architecture and product decisions
  resources/
    scryfall/               # Oracle bulk JSON (local download) + field docs
    mtg/                    # Comprehensive Rules (local download)
  data/                     # Generated SQLite (gitignored)
  output/                   # Generated decks (gitignored)
```

## Setup (development)

**Windows (PowerShell)**

```powershell
cd mtg-deck-tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

**Linux / macOS (bash)**

```bash
cd mtg-deck-tools
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Ensure oracle cards JSON and Comprehensive Rules are in place (see above).

## Usage

```powershell
# Import oracle cards into local SQLite (one-time or after bulk refresh)
mtg-deck-tools import

# Database summary
mtg-deck-tools stats

# Full deck: slot-filled 99-card maindeck → output/
mtg-deck-tools generate --seed 42 --colors G --themes tokens

# Full wizard: themes, mechanics, colors, commander, budget
mtg-deck-tools wizard

# Wizard then generate
mtg-deck-tools generate --wizard --seed 42

# Regenerate from a saved deck (edit criteria in the .deck.json first)
mtg-deck-tools generate --from output/my-deck-20260530.deck.json --seed 42
mtg-deck-tools generate --from output/my-deck-20260530.deck.json --refill-slot synergy --seed 42

# Phase 1 stub preview only (sample synergy cards)
mtg-deck-tools generate --stub --seed 42 --colors B,G --themes aristocrats
```

### Commands

| Command | Description |
| --- | --- |
| `import` | Load `resources/scryfall/oracle-cards-*.json` → `data/cards.db`, apply mechanic tags |
| `stats` | Row counts, import metadata, top tags |
| `wizard` | Interactive wizard: themes, mechanics, colors, commander, budget (criteria only; does not write a deck) |
| `generate` | Build a 99-card maindeck plus commander metadata → `output/*.deck.json` and `output/*.md` |

### `generate` — how it works

The builder fills a **99-card maindeck** (commander is separate) using **slots**: fixed-size buckets such as ramp, draw, removal, synergy, lands, and so on. Default counts live in [`config/slot-templates.yaml`](config/slot-templates.yaml) (e.g. 30 synergy, 31 lands); the wizard can change them within bounds, and the saved `.deck.json` stores the template under `criteria.slot_template`.

Each slot is filled from `data/cards.db` using color identity, theme tags, mechanic tags, budget, and scoring. After nonland slots are filled, **lands** are chosen to match the mana base plan. Outputs include validation notes, budget totals, and per-card detail in Markdown.

#### Fresh generate (no `--from`)

| Flag | Effect |
| --- | --- |
| `--wizard` | Run the full wizard first, then generate using its criteria (ignores `--from`, `--colors`, `--themes`). |
| `--colors` | Comma-separated color letters for commander identity filter, e.g. `B,G`. |
| `--themes` | Comma-separated archetype tags, e.g. `tokens,aristocrats`. |
| `--seed` | RNG seed for reproducible picks (also stored in criteria). |
| `--strict-budget` | Exclude cards with no Scryfall price and enforce the budget cap during fill. |
| `--prefer-available` | Exclude cards below the import-time availability score (25th percentile). Re-run `import` after updating the card DB. |
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
| `--prefer-available` | Applied unless already set in the file’s criteria. |
| `--wizard` | **Ignored** — wizard is not run; criteria come from the file. |
| `--colors` / `--themes` | Ignored (identity and themes come from loaded criteria + commanders). |

## Status

**Phase 1** complete: Python package, SQLite import, mechanic taxonomy v0, CLI (`import`, `stats`, `generate` stub).

**Phase 2** complete: wizard, slot filling, dynamic mana base, and Commander rule validation.

**v1 polish:** budget enforcement during fill, post-fill budget trim pass, `--strict-budget`, tighter slot tags (`board_wipe`, `wincon`), and land price bias when a budget cap is set.

**Phase 3 (v1):** build-time legality filters, slot pool quality, `.deck.json` reload, availability scoring (`--prefer-available`, unpriced classification in Notes), and v1 success criteria closure — **complete** as of 2026-05-30.

## License

Project code: see repository license when added.  
Magic: The Gathering and card data are © Wizards of the Coast.  
Card data via [Scryfall](https://scryfall.com) is unofficial Fan Content permitted under the Wizards Fan Content Policy.
