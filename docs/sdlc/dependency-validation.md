# Dependency expansion — validation and ship workflow

SDLC for **shipping** new dependency profiles, rules, and patterns: implementation steps, dogfood regression, and doc updates. **Spec** of what is already shipped: [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md). **Runner semantics:** [deck-analysis.md](../specs/deck-analysis.md).

Canonical agent map: [DOC-MAP.md](../DOC-MAP.md) · skill **`/ship-dependency-feature`**.

---

## Dogfood regression gate

| Artifact | Purpose |
| --- | --- |
| [`config/dogfood-matrix.yaml`](../../config/dogfood-matrix.yaml) | Scenario matrix with `expect.validation` and `expect.dependency` |
| `mtg-deck-tools analyze run --fail-on-expect` | CI-style gate after import |
| `analysis/rubric.py` | Inappropriate vs appropriate warning metrics (target &lt; 5% inappropriate) |

**Current:** **30/30** scenarios pass (tokens, voltron, energy, experience, blood, +1/+1, rad, oil, charge, tribal, artifacts, aristocrats, landfall, enchantress, budget, strict/repair, surveil, treasure, …).

After Scryfall bulk refresh: `import` → optional `dependency-audit` → `analyze run --fail-on-expect`.

---

## Implementation checklist (per feature PR)

1. **Patterns** — `config/effect-patterns.yaml`; golden cases in `tests/fixtures/effect_golden.yaml`.
2. **Import** — Re-run `mtg-deck-tools import`; note new `effect_count` in PR.
3. **Audit** — Optional `dependency-audit` refresh for pool-size evidence.
4. **Profile** — `config/dependency-profiles.yaml`: `activation`, `defaults`, `roles`.
5. **Scope** — `rules/dependency_scope.py` if deck-level gating needed.
6. **Validate** — New or extended `rule_id` in `rules/dependencies.py`.
7. **Build** — Floors in `dependency_profiles.py`; `dependency_scoring.py`; `mechanic_packages.py`; `dependency_repair.py`.
8. **Rubric** — `analysis/rubric.py` if dogfood inappropriate-warning metrics change.
9. **Dogfood** — Scenario in `config/dogfood-matrix.yaml` with `expect.dependency`.
10. **Tests** — Unit tests + `analyze run --fail-on-expect`.
11. **Docs** — [DOC-MAP.md](../DOC-MAP.md) shipping table (inventory, changelog, roadmap active/backlog).

---

## Doc updates when a dependency feature ships

| Step | File | Action |
| --- | --- | --- |
| 1 | `docs/specs/dependency-engine/shipped-inventory.md` | Add/update `effect_kind`, `rule_id`, or package rows |
| 2 | `docs/history/changelog.md` | One dated bullet |
| 3 | `docs/roadmap/dependency/active.md` | Remove shipped row; clear from product `roadmap/active.md` if listed |
| 4 | `docs/history/dependency-priorities.md` | Strike through row **only** if it lives in the archived Priority 1–8 grid |
| 5 | `README.md` | User-facing mechanic blurb when users gain a new selector |

New expansion work should be **backlog → active** before implementation (see [dependency/README.md](../roadmap/dependency/README.md)).
