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
| **Shipped feature or backlog priority shift** | [roadmap/active.md](roadmap/active.md) / [roadmap/backlog.md](roadmap/backlog.md); [history/changelog.md](history/changelog.md) (one line) |
| **New / changed dependency profile, rule, package, pattern** | [dependency-validation.md](sdlc/dependency-validation.md); [shipped-inventory.md](specs/dependency-engine/shipped-inventory.md); [README.md](../README.md) if user selects new mechanic |
| **Dogfood matrix or analyze expectations** | [specs/deck-analysis.md](specs/deck-analysis.md) if semantics change; [config/dogfood-matrix.yaml](../config/dogfood-matrix.yaml) |
| **Effect extraction contract** | [specs/dependency-engine/overview.md](specs/dependency-engine/overview.md); [specs/dependency-engine/effect-extraction-policy.md](specs/dependency-engine/effect-extraction-policy.md); golden fixtures |
| **Architecture / data layout** | Relevant doc under `docs/architecture/` or `docs/product/`; [specs/data/oracle-bulk-contract.md](specs/data/oracle-bulk-contract.md) if import fields change; [README.md](../README.md) project layout if paths move |
| **Locked v1 dependency decisions** | [specs/dependency-engine/decisions.md](specs/dependency-engine/decisions.md) — only when scope/decisions change |
| **Major milestone completed (rare)** | [history/milestones.md](history/milestones.md) — phase-level ship only |

**Do not** duplicate maintenance tables in [README.md](README.md). That file indexes the tree; **this file** owns the update map.

**Roadmap rule:** [roadmap/active.md](roadmap/active.md) = selected immediate work only. Parked items stay in [roadmap/backlog.md](roadmap/backlog.md) or [roadmap/dependency/backlog.md](roadmap/dependency/backlog.md).

---

## Shipping a dependency expansion feature

When dependency work listed in [roadmap/dependency/active.md](roadmap/dependency/active.md) is **completed**, update in the **same PR**:

| Step | File | Action |
| --- | --- | --- |
| 1 | `docs/specs/dependency-engine/shipped-inventory.md` | Add/update inventory tables (`effect_kind`, `rule_id`, package) |
| 2 | `docs/history/changelog.md` | Append one dated bullet |
| 3 | `docs/roadmap/dependency/active.md` | Remove shipped row |
| 4 | `docs/history/dependency-priorities.md` | Strike through **only** if the item is in the archived Priority 1–8 grid |
| 5 | `README.md` | User-facing mechanic blurb if applicable |
| 6 | `docs/roadmap/active.md` | Update **Suggested next task** if this was the top product item |

Use skill **`/ship-dependency-feature`**. Full checklist: [dependency-validation.md](sdlc/dependency-validation.md).

---

## Dependency feature implementation checklist

From [dependency-validation.md](sdlc/dependency-validation.md) — code **and** docs in one PR (summary):

1. Patterns → import → profile → scope → validate → build → rubric → dogfood → tests
2. Doc map steps in [Shipping a dependency expansion feature](#shipping-a-dependency-expansion-feature) above

---

## Path triggers (Cursor rules)

| Rule | Paths | Purpose |
| --- | --- | --- |
| `sdlc-documentation` | always | Every agent turn: doc map + pre-PR sync |
| `dependency-documentation` | `config/dependency-*.yaml`, `config/effect-patterns.yaml`, `config/dogfood-matrix.yaml`, dependency engine `src/` | Require shipped-inventory / active / backlog / README updates |
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
| [roadmap/active.md](roadmap/active.md) | Selected immediate product work |
| [roadmap/backlog.md](roadmap/backlog.md) | Parked product / UX work |
| [roadmap/dependency/active.md](roadmap/dependency/active.md) | Selected dependency expansion |
| [roadmap/dependency/backlog.md](roadmap/dependency/backlog.md) | Parked dependency work |
| [specs/dependency-engine/shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) | Shipped dependency spec |
| [sdlc/dependency-validation.md](sdlc/dependency-validation.md) | Dogfood gate + ship checklist |
| [history/dependency-priorities.md](history/dependency-priorities.md) | Archived Priority 1–8 grid |
| [history/changelog.md](history/changelog.md) | Recent ships |
| [specs/deck-analysis.md](specs/deck-analysis.md) | Dogfood matrix runner |
