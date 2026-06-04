# MTG Deck Tools — documentation

Single source of truth for the monorepo. Quick links:

| I need… | Start here |
| --- | --- |
| What to build **now** (all components) | [roadmap/active.md](roadmap/active.md) |
| Parked work by component | [roadmap/backlog/README.md](roadmap/backlog/README.md) |
| Dependency engine spec (shipped) | [specs/dependency-engine/shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) |
| Agent doc rules | [DOC-MAP.md](DOC-MAP.md) |

## Layout

```
docs/
  DOC-MAP.md
  product/ · architecture/ · specs/ · history/
  roadmap/
    active.md              # unified active register
    backlog/               # cli-engine, cli-ui, web-ui, product-data
  sdlc/
  packages/
```

## Roadmap

| Doc | Purpose |
| --- | --- |
| [active.md](roadmap/active.md) | **Active** — cross-component tasks, dependencies, parallel streams |
| [backlog/](roadmap/backlog/) | **Backlog** — one file per component |

## Specifications · history · SDLC

See prior index sections in git history; maintenance: [DOC-MAP.md](DOC-MAP.md).

**Components:** cli-engine (`src/mtg_deck_tools/`), cli-ui (`cli/`, `wizard/`), web-ui (`packages/web/`), product-data (formats, import, export).

Current focus: [roadmap/active.md](roadmap/active.md).
