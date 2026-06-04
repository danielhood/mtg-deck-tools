# Documentation map — agent SDLC

**Canonical guide** for which docs to update when code or product status changes. Cursor agents must follow this map on **every pull request**.

Related: [AGENTS.md](../AGENTS.md) · [docs/README.md](README.md) · Cursor rules · skills `/sync-documentation`, `/ship-dependency-feature`.

---

## Agent responsibilities (every PR)

1. **Classify** the change using the table below.
2. **Update** every listed doc in the same PR as the code.
3. **Run** `/sync-documentation` or `/ship-dependency-feature` (dependency engine).
4. **Verify** the PR description lists docs touched or states why none.

---

## Change type → documentation

| If you changed… | Update these docs |
| --- | --- |
| **CLI commands, flags, wizard steps** | [README.md](../README.md) |
| **User-facing generate / analyze** | [README.md](../README.md); [user-experience.md](specs/dependency-engine/user-experience.md) if dependency UX |
| **Shipped feature or priority shift** | [roadmap/active.md](roadmap/active.md); relevant [roadmap/backlog/](roadmap/backlog/) file; [history/changelog.md](history/changelog.md) |
| **New / changed dependency profile, rule, pattern** | [dependency-validation.md](sdlc/dependency-validation.md); [shipped-inventory.md](specs/dependency-engine/shipped-inventory.md); [README.md](../README.md) if user-facing |
| **Dogfood matrix or analyze semantics** | [deck-analysis.md](specs/deck-analysis.md); [config/dogfood-matrix.yaml](../config/dogfood-matrix.yaml) |
| **Effect extraction contract** | [overview.md](specs/dependency-engine/overview.md); [effect-extraction-policy.md](specs/dependency-engine/effect-extraction-policy.md); golden fixtures |
| **Architecture / data layout** | `docs/architecture/` or `docs/product/`; [oracle-bulk-contract.md](specs/data/oracle-bulk-contract.md) if import fields change |
| **Locked v1 dependency decisions** | [decisions.md](specs/dependency-engine/decisions.md) |
| **Major milestone (rare)** | [milestones.md](history/milestones.md) |

**Roadmap rule:** Only [roadmap/active.md](roadmap/active.md) lists **selected** work. Parked items stay in [roadmap/backlog/](roadmap/backlog/) by component.

---

## Shipping a dependency expansion feature

When a row in [roadmap/active.md](roadmap/active.md) (cli-engine) is **completed**:

| Step | File | Action |
| --- | --- | --- |
| 1 | `docs/specs/dependency-engine/shipped-inventory.md` | Update inventory tables |
| 2 | `docs/history/changelog.md` | One dated bullet |
| 3 | `docs/roadmap/active.md` | Remove task row from register |
| 4 | `docs/history/dependency-priorities.md` | Strike through **only** if in archived Priority 1–8 grid |
| 5 | `README.md` | User-facing blurb if applicable |

Checklist: [dependency-validation.md](sdlc/dependency-validation.md). Skill: **`/ship-dependency-feature`**.

---

## Path triggers (Cursor rules)

| Rule | Purpose |
| --- | --- |
| `sdlc-documentation` | Always — doc map + sync |
| `dependency-documentation` | Dependency config + engine `src/` |
| `cli-documentation` | CLI + wizard |

---

## PR description template

```markdown
## Documentation
- [ ] Updated per [docs/DOC-MAP.md](DOC-MAP.md)
- Docs touched: _paths or "none — reason"_

## Verification
- _commands run_
```

---

## References

| Doc | Role |
| --- | --- |
| [roadmap/active.md](roadmap/active.md) | Unified active register (all components) |
| [roadmap/backlog/](roadmap/backlog/) | Per-component backlog |
| [shipped-inventory.md](specs/dependency-engine/shipped-inventory.md) | Dependency spec |
| [dependency-validation.md](sdlc/dependency-validation.md) | Dogfood + ship steps |
| [history/changelog.md](history/changelog.md) | Recent ships |
