---
name: ship-dependency-feature
description: Implement or ship a dependency expansion feature with code, tests, dogfood, and all docs updates per DOC-MAP. Use when changing effect-patterns, dependency-profiles, mechanic_packages, dependencies validation, or dogfood-matrix for dependency rules.
paths: config/dependency-profiles.yaml,config/effect-patterns.yaml,config/dogfood-matrix.yaml,src/mtg_deck_tools/builder/mechanic_packages.py,src/mtg_deck_tools/rules/dependencies.py,src/mtg_deck_tools/effects/**,tests/test_mechanic_packages.py,tests/test_dependencies_validate.py
---

# Ship dependency feature

End-to-end workflow for dependency expansion PRs. Combines implementation, verification, and **mandatory** doc updates.

## Phase A — Implementation

Follow [docs/DOC-MAP.md](../../docs/DOC-MAP.md) and [docs/sdlc/dependency-validation.md](../../docs/sdlc/dependency-validation.md):

1. Patterns → `config/effect-patterns.yaml` + `tests/fixtures/effect_golden.yaml`
2. Profile → `config/dependency-profiles.yaml`; scope in `dependency_scope.py` if needed
3. Validate → `rules/dependencies.py` (new or extended `rule_id`)
4. Build → `dependency_profiles.py`, `dependency_scoring.py`, `mechanic_packages.py`, `dependency_repair.py`
5. Dogfood → `config/dogfood-matrix.yaml`; rubric in `analysis/rubric.py` if needed
6. Tests → unit tests; `pytest`; after import, `mtg-deck-tools analyze run --fail-on-expect`

## Phase B — Ship documentation (same PR)

When the feature is **complete** (row in `docs/roadmap/dependency/active.md` done):

| File | Action |
| --- | --- |
| `docs/specs/dependency-engine/shipped-inventory.md` | Update inventory tables |
| `docs/history/changelog.md` | Append one dated bullet |
| `docs/roadmap/dependency/active.md` | Remove shipped row |
| `docs/history/dependency-priorities.md` | Strike through **only** if item is in archived Priority grid |
| `README.md` | User-facing mechanic/flag if applicable |

## Phase C — Finish

1. Run **`/sync-documentation`** as a final pass.
2. PR body: list all docs touched + verification commands run.
3. Do not open PR until Phase B is complete for shipped work.

## Partial work (not shipping yet)

- Update `shipped-inventory.md` **only** if inventory semantics change before ship
- Do **not** remove backlog rows until the feature is fully shipped
- Promote work: `dependency/backlog.md` → `dependency/active.md` before starting
