# MTG Deck Tools — documentation

Single source of truth for product intent, architecture, technical specs, roadmap, shipped history, and agent SDLC. All packages in this monorepo (CLI today; `packages/web/` later) share this tree.

## Quick links

| I need… | Start here |
| --- | --- |
| What to build **now** | [roadmap/active.md](roadmap/active.md) |
| What is **parked** | [roadmap/backlog.md](roadmap/backlog.md) |
| Dependency spec (shipped today) | [specs/dependency-engine/shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) |
| Dependency active / backlog | [roadmap/dependency/active.md](roadmap/dependency/active.md) · [backlog](roadmap/dependency/backlog.md) |
| What already shipped | [history/milestones.md](history/milestones.md) · [history/changelog.md](history/changelog.md) |
| Agent doc update rules | [DOC-MAP.md](DOC-MAP.md) |

## Folder layout

```
docs/
  DOC-MAP.md
  product/
  architecture/
  specs/
    data/
    dependency-engine/
    web/
  roadmap/
    active.md          # selected immediate work
    backlog.md         # parked product work
    dependency/        # dependency active / backlog
  history/             # milestones, changelog, priority archive
  sdlc/                # dependency-validation.md
  packages/
```

## Roadmap

| Doc | Purpose |
| --- | --- |
| [roadmap/README.md](roadmap/README.md) | Active vs backlog index |
| [roadmap/active.md](roadmap/active.md) | **Selected** immediate work (e.g. UX7) |
| [roadmap/backlog.md](roadmap/backlog.md) | **Parked** product / UX ideas |
| [roadmap/dependency/](roadmap/dependency/) | Dependency active, backlog, index |
| [roadmap/dependency-expansion.md](roadmap/dependency-expansion.md) | Redirect stub (split doc) |

## Specifications (dependency)

| Doc | Purpose |
| --- | --- |
| [shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) | Pipeline, effect kinds, rules, packages, non-goals |
| [overview.md](specs/dependency-engine/overview.md) | D0–D5 engine architecture |
| [user-experience.md](specs/dependency-engine/user-experience.md) | Wizard / CLI UX |
| [deck-analysis.md](specs/deck-analysis.md) | `analyze run` runner |

## SDLC

| Doc | Purpose |
| --- | --- |
| [DOC-MAP.md](DOC-MAP.md) | Change type → docs |
| [dependency-validation.md](sdlc/dependency-validation.md) | Dependency ship checklist + dogfood gate |

## History

| Doc | Purpose |
| --- | --- |
| [milestones.md](history/milestones.md) | Major phases |
| [changelog.md](history/changelog.md) | Recent ships |
| [dependency-priorities.md](history/dependency-priorities.md) | Archived Priority 1–8 grid |

See [roadmap/active.md](roadmap/active.md) for current focus.
