# CLI package

Entry point: `mtg-deck-tools` after `pip install -e ".[dev]"`. Commands call `service/` facades in-process (same layer as the HTTP API). User-facing commands: root [README.md](../../../README.md).

## Specs

| Topic | Doc |
| --- | --- |
| Wizard / dependency UX | [user-experience.md](../../specs/dependency-engine/user-experience.md) |
| Dogfood / analyze | [deck-analysis.md](../../specs/deck-analysis.md) |
| Deck output | [deck-output-format.md](../../product/deck-output-format.md) |
| Dependency engine | [overview.md](../../specs/dependency-engine/overview.md) |

## Active work

[active.md](../../roadmap/active.md) — **UX7a shipped** (`service/`, `api/`, OpenAPI). **UX7b–UX7c** add `serve` and the web SPA without forking business logic.
