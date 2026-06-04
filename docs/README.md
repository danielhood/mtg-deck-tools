# MTG Deck Tools — documentation

Single source of truth for product intent, architecture, technical specs, roadmap, shipped history, and agent SDLC. All packages in this monorepo (CLI today; `packages/web/` later) share this tree.

## Quick links

| I need… | Start here |
| --- | --- |
| What to build next | [roadmap/active.md](roadmap/active.md) |
| Dependency backlog + inventory | [roadmap/dependency-expansion.md](roadmap/dependency-expansion.md) |
| What already shipped | [history/milestones.md](history/milestones.md) · [history/changelog.md](history/changelog.md) |
| Agent doc update rules | [DOC-MAP.md](DOC-MAP.md) |
| CLI / wizard UX spec | [specs/dependency-engine/user-experience.md](specs/dependency-engine/user-experience.md) |
| Package-specific notes | [packages/](packages/) |

## Folder layout

```
docs/
  DOC-MAP.md           # Agent SDLC — which docs to update per change type
  product/             # Goals, scope, output formats, product decisions
  architecture/        # Problem decomposition, pipeline, stack, data sources (overview)
  specs/               # Technical specifications
    data/              # Import contracts (oracle bulk, …)
    dependency-engine/
  roadmap/             # Active work and domain backlogs
  history/             # Shipped milestones and changelog
  packages/            # Per-package indexes (cli, web, …)
```

## Product

| Doc | Purpose |
| --- | --- |
| [goals-and-scope.md](product/goals-and-scope.md) | Problem statement, v1 scope, success criteria |
| [open-questions.md](product/open-questions.md) | Resolved and open product decisions |
| [deck-output-format.md](product/deck-output-format.md) | Markdown + `.deck.json` schema |
| [card-availability.md](product/card-availability.md) | Budget null prices; availability heuristic |

## Architecture

| Doc | Purpose |
| --- | --- |
| [problem-decomposition.md](architecture/problem-decomposition.md) | Wizard, filtering, tagging, slots, mana base |
| [pipeline-and-components.md](architecture/pipeline-and-components.md) | End-to-end pipeline and component options |
| [technology-stack.md](architecture/technology-stack.md) | Stack comparison (local runtime + database) |
| [data-sources.md](architecture/data-sources.md) | External data overview and static snapshot policy |

## Specifications

| Doc | Purpose |
| --- | --- |
| [data/oracle-bulk-contract.md](specs/data/oracle-bulk-contract.md) | Scryfall oracle import fields and pool filters |
| [deck-analysis.md](specs/deck-analysis.md) | Dogfood matrix runner (`analyze run`) |
| [dependency-engine/overview.md](specs/dependency-engine/overview.md) | Cross-card synergy engine (D0–D5) |
| [dependency-engine/user-experience.md](specs/dependency-engine/user-experience.md) | Wizard / CLI dependency UX (UX2+) |
| [dependency-engine/decisions.md](specs/dependency-engine/decisions.md) | Locked v1 dependency decisions |
| [dependency-engine/implementation-checklist.md](specs/dependency-engine/implementation-checklist.md) | D0–D5 pre-ship gate |
| [dependency-engine/effect-extraction-policy.md](specs/dependency-engine/effect-extraction-policy.md) | Merged-face extraction policy |

## Roadmap

| Doc | Purpose |
| --- | --- |
| [active.md](roadmap/active.md) | **Active work** — suggested next task, open items, product backlog |
| [dependency-expansion.md](roadmap/dependency-expansion.md) | Dependency inventory, priority grid, expansion sequence |

Maintenance rules: [DOC-MAP.md](DOC-MAP.md). Do **not** duplicate ship lists across roadmap and history.

## History

| Doc | Purpose |
| --- | --- |
| [milestones.md](history/milestones.md) | Phase 1–3, v1 polish, D0–D5, major capabilities |
| [changelog.md](history/changelog.md) | Append-only **recent ships** (agents update on merge) |

## Packages (monorepo)

| Package | Index |
| --- | --- |
| CLI | [packages/cli/README.md](packages/cli/README.md) → `src/mtg_deck_tools/` |
| Web (planned) | [packages/web/README.md](packages/web/README.md) → `packages/web/` |

## Current preferences (summary)

- **Deck generation:** Guided slot template; seeded random picks (`--seed`)
- **Dependencies:** Warn by default; strict/repair on CLI and wizard step 3
- **Export:** Markdown + `.deck.json`
- **UI today:** Terminal CLI · **next:** UX7 web (`packages/web/`)

See [roadmap/active.md](roadmap/active.md) for open work.
