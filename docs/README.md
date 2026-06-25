# MTG Deck Tools — documentation

Single source of truth for the monorepo.

## For agents

| Phase | Guide |
| --- | --- |
| **Planning** (scope, promote tasks, spec design) | [sdlc/agent-phases.md](sdlc/agent-phases.md) § Phase 1 |
| **Implementation** (code + docs in one PR) | [sdlc/agent-phases.md](sdlc/agent-phases.md) § Phase 2–3 |
| **Which file to edit** | [DOC-MAP.md](DOC-MAP.md) |

Before every PR: skill **`/sync-documentation`**. Dependency engine ship: **`/ship-dependency-feature`**.

## Quick links

| I need… | Start here |
| --- | --- |
| Roadmap overview + **current snapshot** | [roadmap/README.md](roadmap/README.md) |
| What to build **now** (full register) | [roadmap/active.md](roadmap/active.md) |
| Parked work by component | [roadmap/backlog/README.md](roadmap/backlog/README.md) |
| Shipped dependency behavior | [specs/dependency-engine/shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) |
| Recent ships | [history/changelog.md](history/changelog.md) |

## Layout

```
docs/
  DOC-MAP.md              # change type → doc updates (implementation)
  product/                # goals, scope, formats (plan + ship)
  architecture/           # pipeline, stack, data policy (mostly plan)
  specs/                  # contracts; shipped-inventory = dependency truth
  roadmap/
    active.md             # unified active register
    backlog/              # cli-engine, cli-ui, web-ui, product-data
  history/                # changelog, milestones, archives (ship only)
  sdlc/                   # agent-phases, dependency-validation
  packages/               # per-package indexes
```

## Product

| Doc | Purpose |
| --- | --- |
| [goals-and-scope.md](product/goals-and-scope.md) | v1 scope, success criteria |
| [open-questions.md](product/open-questions.md) | Product decisions |
| [deck-output-format.md](product/deck-output-format.md) | `.deck.json` + Markdown |
| [card-availability.md](product/card-availability.md) | Budget / availability |

## Architecture

| Doc | Purpose |
| --- | --- |
| [problem-decomposition.md](architecture/problem-decomposition.md) | Sub-problems |
| [pipeline-and-components.md](architecture/pipeline-and-components.md) | Pipeline |
| [technology-stack.md](architecture/technology-stack.md) | Stack choices |
| [data-sources.md](architecture/data-sources.md) | Static data policy |

## Specifications

| Doc | Purpose |
| --- | --- |
| [data/oracle-bulk-contract.md](specs/data/oracle-bulk-contract.md) | Import field contract |
| [deck-analysis.md](specs/deck-analysis.md) | Dogfood runner |
| [dependency-engine/overview.md](specs/dependency-engine/overview.md) | Engine D0–D5 |
| [dependency-engine/shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) | **Shipped** atoms, rules, packages |
| [dependency-engine/user-experience.md](specs/dependency-engine/user-experience.md) | Wizard / CLI UX |
| [dependency-engine/decisions.md](specs/dependency-engine/decisions.md) | Locked v1 decisions |
| [web/README.md](specs/web/README.md) | Web UI spec index (UX7a shipped); UX7c design under `specs/web/` |

## Roadmap · history · SDLC

Work flows **backlog → active → history**. Start at [roadmap/README.md](roadmap/README.md) for the current snapshot.

| Layer | Doc | Purpose |
| --- | --- | --- |
| Index | [roadmap/README.md](roadmap/README.md) | Snapshot, components, agent workflow |
| Active | [roadmap/active.md](roadmap/active.md) | Selected tasks (all components) |
| Backlog | [roadmap/backlog/](roadmap/backlog/) | Parked work by component |
| History | [history/changelog.md](history/changelog.md) | Recent ships |
| History | [history/milestones.md](history/milestones.md) | Major phases |
| SDLC | [sdlc/agent-phases.md](sdlc/agent-phases.md) | Agent planning vs implementation |

**Components:** cli-engine · cli-ui · web-ui · product-data — see [roadmap/README.md](roadmap/README.md).
