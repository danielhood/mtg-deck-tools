# Documentation map — agent SDLC

**Canonical guide** for which docs to update when code or product status changes. Cursor agents must follow this map on **every pull request**; there are no CI doc gates or human review checkpoints in the prototype SDLC.

Related: [AGENTS.md](../AGENTS.md) · [docs/README.md](README.md) · Cursor rules (`.cursor/rules/`) · skills (`/sync-documentation`, `/ship-dependency-feature`).

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
| **User-facing generate / analyze behavior** | [README.md](../README.md); [specs/dependency-engine/user-experience.md](specs/dependency-engine/user-experience.md) if dependency UX |
| **Shipped feature or backlog priority shift** | [roadmap/active.md](roadmap/active.md) (suggested next / open rows only); [history/changelog.md](history/changelog.md) (one dated line); [roadmap/dependency-expansion.md](roadmap/dependency-expansion.md) if dependency-related |
| **New / changed dependency profile, rule, package, pattern** | Dependency checklist (below); dependency-expansion shipped grid; [README.md](../README.md) if user selects new mechanic |
| **Dogfood matrix or analyze expectations** | [specs/deck-analysis.md](specs/deck-analysis.md) if semantics change; [config/dogfood-matrix.yaml](../config/dogfood-matrix.yaml) |
| **Effect extraction contract** | [specs/dependency-engine/overview.md](specs/dependency-engine/overview.md); [specs/dependency-engine/effect-extraction-policy.md](specs/dependency-engine/effect-extraction-policy.md); golden fixtures |
| **Architecture / data layout** | Relevant doc under `docs/architecture/` or `docs/product/`; [specs/data/oracle-bulk-contract.md](specs/data/oracle-bulk-contract.md) if import fields change; [README.md](../README.md) project layout if paths move |
| **Locked v1 dependency decisions** | [specs/dependency-engine/decisions.md](specs/dependency-engine/decisions.md) — only when scope/decisions change |
| **Major milestone completed (rare)** | [history/milestones.md](history/milestones.md) — phase-level ship only |

**Do not** duplicate maintenance tables in [README.md](README.md). That file indexes the tree; **this file** owns the update map.

---

## Shipping a dependency expansion feature

When a row in [dependency-expansion.md](roadmap/dependency-expansion.md) Priority 1–8 is **completed**, update in the **same PR**:

| Step | File | Action |
| --- | --- | --- |
| 1 | `docs/roadmap/dependency-expansion.md` | Strike through the work item in the Priority grid (`~~**Name**~~`, **Shipped YYYY-MM** in Notes) |
| 2 | `docs/roadmap/dependency-expansion.md` | Remove from **Suggested sequence**; add to **Shipped (YYYY-MM)** line |
| 3 | `docs/history/changelog.md` | Append one dated bullet (title + optional PR) |
| 4 | `docs/roadmap/active.md` | Remove from open tables if listed; update **Suggested next task** if this was the top item |
| 5 | `README.md` | Update dependency expansion blurb if users can select the new mechanic |
| 6 | `docs/roadmap/dependency-expansion.md` | Confirm **Shipped inventory** tables list new `effect_kind` / `rule_id` / package if applicable |

Use skill **`/ship-dependency-feature`** for the full implementation + doc checklist.

---

## Dependency feature implementation checklist

From [dependency-expansion.md](roadmap/dependency-expansion.md) — code **and** docs in one PR:

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
| `dependency-documentation` | `config/dependency-*.yaml`, `config/effect-patterns.yaml`, `config/dogfood-matrix.yaml`, dependency engine `src/` | Require dependency-expansion / active / README updates |
| `cli-documentation` | `src/mtg_deck_tools/cli/**`, `src/mtg_deck_tools/wizard/**` | Require README (+ UX spec if UX) |

---

## PR description template (agents)

```markdown
## Documentation
- [ ] Updated per [docs/DOC-MAP.md](DOC-MAP.md)
- Docs touched: _list paths or "none — reason"_

## Verification
- _pytest / analyze run / other commands run_
```

---

## References

| Doc | Role |
| --- | --- |
| [roadmap/active.md](roadmap/active.md) | Active work and suggested next task |
| [roadmap/dependency-expansion.md](roadmap/dependency-expansion.md) | Dependency inventory + expansion backlog |
| [history/changelog.md](history/changelog.md) | Recent ships (append-only) |
| [specs/deck-analysis.md](specs/deck-analysis.md) | Dogfood matrix runner |
| [specs/dependency-engine/user-experience.md](specs/dependency-engine/user-experience.md) | Wizard / CLI dependency UX |
