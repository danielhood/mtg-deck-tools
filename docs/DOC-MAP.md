# Documentation map — agent SDLC

**Which files to update** when code or product status changes. **When to read/write them by phase:** [sdlc/agent-phases.md](sdlc/agent-phases.md).

Related: [AGENTS.md](../AGENTS.md) · [docs/README.md](README.md) · skills `/sync-documentation`, `/ship-dependency-feature`.

---

## Agent workflow (summary)

| Phase | Goal | Primary docs |
| --- | --- | --- |
| **Planning** | Prioritize, design contracts | [roadmap/active.md](roadmap/active.md), [roadmap/backlog/](roadmap/backlog/), `docs/specs/`, `docs/product/` |
| **Implementation** | Code + matching doc updates | [DOC-MAP.md](DOC-MAP.md) table below + domain specs |
| **Ship** | Close an active task | Remove from **active**; [history/changelog.md](history/changelog.md); inventory/README per row type |

Do **not** update changelog or remove active rows for planning-only or WIP PRs. See [agent-phases.md](sdlc/agent-phases.md).

---

## Agent responsibilities (every PR)

1. State phase: **planning**, **implementation**, or **docs-only fix**.
2. **Classify** the change (table below).
3. **Update** every listed doc in the **same PR** as code (or same PR for docs-only planning).
4. Run **`/sync-documentation`** before opening/updating a PR.
5. Dependency expansion: **`/ship-dependency-feature`**.

If no doc updates apply: PR body must say *No doc changes — [reason]*.

---

## Change type → documentation

| If you changed… | Update these docs |
| --- | --- |
| **CLI commands, flags, wizard steps** | [README.md](../README.md) |
| **User-facing generate / analyze** | [README.md](../README.md); [user-experience.md](specs/dependency-engine/user-experience.md) if dependency UX |
| **Promoted or re-prioritized work (no code ship)** | [roadmap/active.md](roadmap/active.md); [roadmap/backlog/](roadmap/backlog/) — *planning*; no changelog |
| **Shipped feature (task complete)** | [roadmap/active.md](roadmap/active.md); [history/changelog.md](history/changelog.md); component backlog if needed |
| **New / changed dependency profile, rule, pattern** | [shipped-inventory.md](specs/dependency-engine/shipped-inventory.md); [dependency-validation.md](sdlc/dependency-validation.md); [README.md](../README.md) if user-facing |
| **Dogfood matrix or analyze semantics** | [deck-analysis.md](specs/deck-analysis.md); [config/dogfood-matrix.yaml](../config/dogfood-matrix.yaml) |
| **Effect extraction contract** | [overview.md](specs/dependency-engine/overview.md); [effect-extraction-policy.md](specs/dependency-engine/effect-extraction-policy.md); golden fixtures |
| **Architecture / data layout** | `docs/architecture/` or `docs/product/`; [oracle-bulk-contract.md](specs/data/oracle-bulk-contract.md) if import fields change |
| **UX / web design (pre-code)** | [user-experience.md](specs/dependency-engine/user-experience.md), [specs/web/README.md](specs/web/README.md), [specs/web/wireframes/README.md](specs/web/wireframes/README.md) — *planning* |
| **Locked v1 dependency decisions** | [decisions.md](specs/dependency-engine/decisions.md) |
| **Major milestone (rare)** | [milestones.md](history/milestones.md) |

**Roadmap rule:** Only [roadmap/active.md](roadmap/active.md) lists **selected** work. Parked items stay in [roadmap/backlog/](roadmap/backlog/). Do **not** duplicate shipped features, sub-phase tables, or ship narratives in active or backlog — record those in [changelog.md](history/changelog.md), [milestones.md](history/milestones.md), and domain specs.

---

## Shipping a dependency expansion feature

When a **cli-engine** row in [roadmap/active.md](roadmap/active.md) is **completed**:

| Step | File | Action |
| --- | --- | --- |
| 1 | `docs/specs/dependency-engine/shipped-inventory.md` | Update inventory tables |
| 2 | `docs/history/changelog.md` | One dated bullet |
| 3 | `docs/roadmap/active.md` | Remove task row |
| 4 | `docs/history/dependency-priorities.md` | Strike through **only** if in archived Priority 1–8 grid |
| 5 | `README.md` | User-facing blurb if applicable |

Checklist: [dependency-validation.md](sdlc/dependency-validation.md). Skill: **`/ship-dependency-feature`**.

---

## Path triggers (Cursor rules)

| Rule | When | Also read |
| --- | --- | --- |
| `sdlc-documentation` | Always | [agent-phases.md](sdlc/agent-phases.md) |
| `dependency-documentation` | Dependency config + engine `src/` | [dependency-validation.md](sdlc/dependency-validation.md) |
| `cli-documentation` | `cli/`, `wizard/` | [user-experience.md](specs/dependency-engine/user-experience.md) if UX |

---

## PR description template

```markdown
## Phase
planning | implementation

## Documentation
- [ ] [agent-phases.md](docs/sdlc/agent-phases.md) + [DOC-MAP.md](docs/DOC-MAP.md)
- Docs touched: _paths or "none — reason"_

## Verification
- _pytest / analyze run / N/A for planning-only_
```
