# Scryfall oracle bulk snapshot

The deck builder uses a **static** oracle-cards JSON file (not live API calls). See [planning/02-data-sources.md](../../planning/02-data-sources.md).

## Expected filename

```
oracle-cards-YYYYMMDDhhmmss.json
```

Place the newest file in this directory. `mtg-deck-tools import` picks the lexicographically latest `oracle-cards-*.json` match.

## Download (maintainer refresh)

```bash
curl -s https://api.scryfall.com/bulk-data/oracle-cards \
  | jq -r '.download_uri' \
  | xargs curl -o "resources/scryfall/oracle-cards-$(date -u +%Y%m%d%H%M%S).json"
```

Then from repo root:

```bash
source .venv/bin/activate
mtg-deck-tools import
mtg-deck-tools stats
```

Record the bulk date in import metadata and release notes when refreshing companion data (`card_mechanic_tags`, future `card_effects`, dependency audit).

## CI / agents

Automated tests do **not** require this file. Full import tests and D0.5 inventory audit run locally or in maintainer workflows after download.
