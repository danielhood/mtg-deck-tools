# Documentation map — agent SDLC

**Canonical guide** for which docs to update when code or product status changes. Cursor agents must follow this map on **every pull request**; there are no CI doc gates or human review checkpoints in the prototype SDLC.

Related: [AGENTS.md](../AGENTS.md) · Cursor rules (`.cursor/rules/`) · skills (`/sync-documentation`, `/ship-dependency-feature`).

---

## Agent responsibilities (every PR)

Before commit, push, or opening/updating a PR:

1. **Classify** the change using the table below.
2. **Update** every listed doc in the same PR as the code (same branch, same commit series).
3. **Run** `/sync-documentation` (all PRs) or `/ship-dependency-feature` (dependency expansion).
4. **Verify** the PR description states which docs changed and why.

If no doc updates apply, state **explicitly** in the PR body: *No doc changes — [reason]* (e.g. test-only refactor with no behavior change).

---

## Change type → documentation

| If you changed… | Update these docs |
| --- | --- |
| **CLI commands, flags, wizard steps, setup** | [README.md](../README.md) |
| **User-facing generate / analyze behavior** | [README.md](../README.md); [planning/11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) if dependency UX |
| **Shipped feature or backlog priority shift** | [planning/09-next-steps.md](09-next-steps.md); [planning/15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) |
| **New / changed dependency profile, rule, package, pattern** | Doc 15 checklist (below); doc 09 + doc 15 shipped grid; [README.md](../README.md) if user selects new mechanic |
| **Dogfood matrix or analyze expectations** | [planning/14-deck-analysis.md](14-deck-analysis.md) if semantics change; [config/dogfood-matrix.yaml](../config/dogfood-matrix.yaml) |
| **Effect extraction contract** | [planning/10-card-dependency-engine.md](10-card-dependency-engine.md); [planning/14-effect-extraction-face-policy.md](14-effect-extraction-face-policy.md); golden fixtures |
| **Architecture / data layout** | Relevant planning doc (03–05); [README.md](../README.md) project layout if paths move |
| **Locked v1 dependency decisions** | [planning/13-dependency-engine-decisions.md](13-dependency-engine-decisions.md) — only when scope/decisions change |

**Do not** duplicate maintenance tables in [planning/README.md](README.md). That file indexes planning docs; **this file** owns the update map.

---

## Shipping a dependency expansion feature

When a row in doc 15 Priority 1–6 is **completed**, update in the **same PR**:

| Step | File | Action |
| --- | --- | --- |
| 1 | `planning/15-dependency-expansion-roadmap.md` | Strike through the work item in the Priority grid (`~~**Name**~~`, **Shipped YYYY-MM** in Notes) |
| 2 | `planning/15-dependency-expansion-roadmap.md` | Remove from **Suggested sequence**; add to **Shipped (YYYY-MM)** line |
| 3 | `planning/09-next-steps.md` | Remove from active priority table; add to **Recently shipped** |
| 4 | `planning/09-next-steps.md` | Update **Suggested next task** if this was the top item |
| 5 | `README.md` | Update dependency expansion blurb if users can select the new mechanic |
| 6 | `planning/15-dependency-expansion-roadmap.md` | Confirm **Shipped inventory** tables list new `effect_kind` / `rule_id` / package if applicable |

Use skill **`/ship-dependency-feature`** for the full implementation + doc checklist.

---

## Dependency feature implementation checklist

From [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) — code **and** docs in one PR:

1. **Patterns** — `config/effect-patterns.yaml`; golden cases in `tests/fixtures/effect_golden.yaml`
2. **Import** — Re-run `mtg-deck-tools import`; note new `effect_count` in PR
3. **Audit** — Optional `dependency-audit` refresh
4. **Profile** — `config/dependency-profiles.yaml`
5. **Scope** — `rules/dependency_scope.py` if needed
6. **Validate** — `rules/dependencies.py`
7. **Build** — profiles, scoring, `mechanic_packages.py`, `dependency_repair.py`
8. **Rubric** — `analysis/rubric.py` if dogfood metrics change
9. **Dogfood** — `config/dogfood-matrix.yaml`
10. **Tests** — Unit tests + `analyze run --fail-on-expect`
11. **Doc map** — Steps in [Shipping a dependency expansion feature](#shipping-a-dependency-expansion-feature) above

---

## Path triggers (Cursor rules)

Rules under `.cursor/rules/` auto-attach when matching paths are edited:

| Rule | Paths | Purpose |
| --- | --- | --- |
| `sdlc-documentation` | always | Every agent turn: doc map + pre-PR sync |
| `dependency-documentation` | `config/dependency-*.yaml`, `config/effect-patterns.yaml`, `config/dogfood-matrix.yaml`, dependency engine `src/` | Require doc 15 / doc 09 / README updates |
| `cli-documentation` | `src/mtg_deck_tools/cli/**`, `src/mtg_deck_tools/wizard/**` | Require README (+ doc 11 if UX) |

---

## PR description template (agents)

```markdown
## Documentation
- [ ] Updated per [planning/DOC-MAP.md](planning/DOC-MAP.md)
- Docs touched: _list paths or "none — reason"_

## Verification
- _pytest / analyze run / other commands run_
```

---

## References

| Doc | Role |
| --- | --- |
| [09-next-steps.md](09-next-steps.md) | Active roadmap and recently shipped |
| [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) | Shipped inventory + expansion backlog |
| [14-deck-analysis.md](14-deck-analysis.md) | Dogfood matrix runner |
| [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) | Wizard / CLI dependency UX (UX2+) |
