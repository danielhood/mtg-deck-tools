---
name: ship-dependency-feature
description: Implement or ship a dependency expansion feature with code, tests, dogfood, and all docs updates per DOC-MAP. Use when changing effect-patterns, dependency-profiles, mechanic_packages, dependencies validation, or dogfood-matrix for dependency rules.
paths: config/dependency-profiles.yaml,config/effect-patterns.yaml,config/dogfood-matrix.yaml,src/mtg_deck_tools/builder/mechanic_packages.py,src/mtg_deck_tools/rules/dependencies.py,src/mtg_deck_tools/effects/**,tests/test_mechanic_packages.py,tests/test_dependencies_validate.py
---

# Ship dependency feature

Follow [docs/DOC-MAP.md](../../docs/DOC-MAP.md) and [docs/sdlc/dependency-validation.md](../../docs/sdlc/dependency-validation.md).

## Before coding

Promote task from [docs/roadmap/backlog/cli-engine.md](../../docs/roadmap/backlog/cli-engine.md) into [docs/roadmap/active.md](../../docs/roadmap/active.md) (cli-engine row with Depends on / Parallel columns).

## Phase A — Implementation

Patterns → profile → validate → build → dogfood → tests → `analyze run --fail-on-expect`.

## Phase B — Ship documentation (same PR)

| File | Action |
| --- | --- |
| `docs/specs/dependency-engine/shipped-inventory.md` | Inventory tables |
| `docs/history/changelog.md` | Dated bullet |
| `docs/roadmap/active.md` | Remove shipped task row |
| `README.md` | User-facing blurb if applicable |

## Phase C

Run **`/sync-documentation`**. PR lists docs + verification commands.
