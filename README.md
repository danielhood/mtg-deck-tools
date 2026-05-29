# MTG Deck Tools

Local utility for building **Commander** (EDH) decks: a terminal wizard walks through themes, colors, mechanics, and budget, then generates a legal 100-card list with Markdown and machine-readable output.

Planning docs: [`planning/README.md`](planning/README.md).

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

```powershell
cd mtg-deck-tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Ensure oracle cards JSON and Comprehensive Rules are in place (see above).

## Usage

```powershell
# Import oracle cards into local SQLite (one-time or after bulk refresh)
mtg-deck-tools import

# Database summary
mtg-deck-tools stats

# Phase 1 stub: seeded sample commander + synergy cards → output/
mtg-deck-tools generate --seed 42 --colors B,G --themes aristocrats
```

Options:

| Command | Description |
| --- | --- |
| `import` | Load `resources/scryfall/oracle-cards-*.json` → `data/cards.db`, apply mechanic tags |
| `stats` | Row counts, import metadata, top tags |
| `generate` | Stub deck preview (Phase 2 adds full wizard + 100-card build) |

## Status

**Phase 1** complete: Python package, SQLite import, mechanic taxonomy v0, CLI (`import`, `stats`, `generate` stub).

**Phase 2** (next): interactive wizard, slot filling, full Markdown + `.deck.json` deck output.

## License

Project code: see repository license when added.  
Magic: The Gathering and card data are © Wizards of the Coast.  
Card data via [Scryfall](https://scryfall.com) is unofficial Fan Content permitted under the Wizards Fan Content Policy.
