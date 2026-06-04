---
name: ship-dependency-feature
description: Implement or ship a dependency expansion feature with code, tests, dogfood, and all docs updates per DOC-MAP. Use when changing effect-patterns, dependency-profiles, mechanic_packages, dependencies validation, or dogfood-matrix for dependency rules.
paths: config/dependency-profiles.yaml,config/effect-patterns.yaml,config/dogfood-matrix.yaml,src/mtg_deck_tools/builder/mechanic_packages.py,src/mtg_deck_tools/rules/dependencies.py,src/mtg_deck_tools/effects/**,tests/test_mechanic_packages.py,tests/test_dependencies_validate.py
---

# Ship dependency feature

End-to-end workflow for dependency expansion PRs. Combines implementation, verification, and **mandatory** doc updates.

## Phase A — Implementation

Follow checklist in [docs/DOC-MAP.md](../../docs/DOC-MAP.md) and [docs/roadmap/dependency-expansion.md](../../docs/roadmap/dependency-expansion.md):

1. Patterns → `config/effect-patterns.yaml` + `tests/fixtures/effect_golden.yaml`
2. Profile → `config/dependency-profiles.yaml`; scope in `dependency_scope.py` if needed
3. Validate → `rules/dependencies.py` (new or extended `rule_id`)
4. Build → `dependency_profiles.py`, `dependency_scoring.py`, `mechanic_packages.py`, `dependency_repair.py`
5. Dogfood → `config/dogfood-matrix.yaml`; rubric in `analysis/rubric.py` if needed
6. Tests → unit tests; `pytest`; after import, `mtg-deck-tools analyze run --fail-on-expect`

## Phase B — Ship documentation (same PR)

When the feature is **complete** (roadmap row done):

| File | Action |
| --- | --- |
| `docs/roadmap/dependency-expansion.md` | `~~**Work item**~~` in Priority grid; **Shipped YYYY-MM** in Notes |
| `docs/roadmap/dependency-expansion.md` | Remove from Suggested sequence; append to **Shipped** line |
| `docs/roadmap/dependency-expansion.md` | Update Shipped inventory tables if new kinds/rules/packages |
| `docs/history/changelog.md` | Append one dated bullet |
| `docs/roadmap/active.md` | Remove from open tables if listed; update **Suggested next task** |
| `README.md` | User-facing mechanic/flag if applicable |

## Phase C — Finish

1. Run **`/sync-documentation`** as a final pass.
2. PR body: list all docs touched + verification commands run.
3. Do not open PR until Phase B is complete for shipped work.

## Partial work (not shipping yet)

If the PR is incremental (WIP, no roadmap row closed):

- Update dependency-expansion **only** if inventory tables or checklist semantics change
- Do **not** strike through roadmap rows until the feature is fully shipped
- Still run `/sync-documentation` for any behavior README users would see
