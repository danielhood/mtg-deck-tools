---
name: ship-dependency-feature
description: Implement and ship a dependency expansion feature — implementation + ship docs. Use for effect-patterns, dependency-profiles, mechanic_packages, dependencies validation, dogfood-matrix. Includes planning step (promote to active) when starting new work.
paths: config/dependency-profiles.yaml,config/effect-patterns.yaml,config/dogfood-matrix.yaml,src/mtg_deck_tools/builder/mechanic_packages.py,src/mtg_deck_tools/rules/dependencies.py,src/mtg_deck_tools/effects/**,tests/test_mechanic_packages.py,tests/test_dependencies_validate.py
---

# Ship dependency feature

**Phase:** implementation + ship. Read [docs/sdlc/agent-phases.md](../../docs/sdlc/agent-phases.md) and [docs/sdlc/dependency-validation.md](../../docs/sdlc/dependency-validation.md).

---

## Phase 0 — Planning (if not already active)

1. Read [roadmap/active.md](../../docs/roadmap/active.md) for parallel constraints.
2. Promote task from [backlog/cli-engine.md](../../docs/roadmap/backlog/cli-engine.md) → **active** (ID, Depends on, Parallel OK with).
3. Update specs if behavior is new (patterns contract in `effect-patterns.yaml` is code; design notes in specs optional).

---

## Phase A — Implementation

1. Patterns → `config/effect-patterns.yaml` + golden fixtures
2. Profile → `config/dependency-profiles.yaml`
3. Validate / build / rubric / dogfood matrix
4. Tests + `mtg-deck-tools analyze run --fail-on-expect`

---

## Phase B — Ship documentation (same PR)

| File | Action |
| --- | --- |
| `docs/specs/dependency-engine/shipped-inventory.md` | Inventory tables |
| `docs/history/changelog.md` | Dated bullet |
| `docs/roadmap/active.md` | Remove shipped task row |
| `README.md` | User-facing blurb if applicable |

---

## Phase C — Finish

Run **`/sync-documentation`**. PR: **Phase: implementation** + Documentation section + verification commands.
