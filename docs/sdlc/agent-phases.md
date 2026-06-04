# Agent phases — planning vs implementation

How agents should **read** and **write** under `docs/` during planning (design, prioritize) versus implementation (code, ship). Canonical change-type table: [DOC-MAP.md](../DOC-MAP.md).

---

## Doc tree roles (do not mix)

| Area | Purpose | Planning | Implementation |
| --- | --- | --- | --- |
| [product/](../product/) | Goals, scope, output formats | Update when intent or schema **design** changes | Update when user-visible contract ships |
| [architecture/](../architecture/) | Pipeline, stack, data overview | Update when structure or policies change | Rare — only if layout paths move |
| [specs/](../specs/) | Technical contracts | **Write/update** behavior before code (UX, web API, extraction policy) | Update **shipped-inventory** and runner docs when behavior ships |
| [roadmap/active.md](../roadmap/active.md) | **Selected** work (all components) | Promote tasks; set Depends on / Parallel | Remove row when **shipped**; never list shipped work as active |
| [roadmap/backlog/](../roadmap/backlog/) | Parked work by component | Add/reorder ideas; remove row when promoted | Remove row when promoted to active |
| [history/](../history/) | Shipped record | **Do not** write changelog/milestones for design-only PRs | **changelog** (every ship); **milestones** (rare phase closes) |
| [sdlc/](../sdlc/) | Agent procedures | Read agent-phases, validation checklists | Follow ship steps in DOC-MAP |

**Rule:** Specs and roadmap = living plan. History = append-only ship log. Do not copy backlog tables into changelog.

---

## Phase 1 — Planning

**When:** Scoping a feature, promoting backlog → active, designing API/UX/contracts, docs-only PRs before code.

### Read first

1. [roadmap/active.md](../roadmap/active.md) — what is already selected; parallel constraints.
2. Relevant [roadmap/backlog/](../roadmap/backlog/) file for the component.
3. Specs for the domain (e.g. [user-experience.md](../specs/dependency-engine/user-experience.md), [specs/web/README.md](../specs/web/README.md)).
4. [product/goals-and-scope.md](../product/goals-and-scope.md) if scope is ambiguous.

### Write (planning)

| Action | Files |
| --- | --- |
| Promote work to start soon | Add row to **active** register; remove from **backlog**; fill Depends on / Parallel OK with |
| Defer / park work | Add or keep in **backlog**; ensure **not** in active |
| Design new behavior | Update or add under **specs/** (and **product/** if output format changes) |
| New open product question | [product/open-questions.md](../product/open-questions.md) |
| Web or UX tranche | [specs/web/README.md](../specs/web/README.md), [user-experience.md](../specs/dependency-engine/user-experience.md) |

### Do not (planning-only)

- Append [history/changelog.md](../history/changelog.md) — no ship yet.
- Edit [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md) — until code exists and ships.
- Strike through [history/dependency-priorities.md](../history/dependency-priorities.md) — archive is for completed grid rows only.

### Planning PR checklist

- [ ] active/backlog reflect promotion and dependencies
- [ ] Specs updated for designed behavior
- [ ] No false “shipped” language in active register
- [ ] PR body: **Documentation** lists paths; **Phase: planning**

---

## Phase 2 — Implementation

**When:** Writing code, config, tests; feature complete in branch.

### Read first

1. [DOC-MAP.md](../DOC-MAP.md) — classify change type.
2. Task row in [roadmap/active.md](../roadmap/active.md) — component and parallel rules.
3. Domain spec(s) you are implementing.
4. [dependency-validation.md](dependency-validation.md) if touching dependency engine.

### Write (implementation)

Use [DOC-MAP.md](../DOC-MAP.md) change-type table. Minimum expectations:

| Change | Docs (same PR as code) |
| --- | --- |
| CLI / wizard | [README.md](../../README.md); UX spec if behavior visible |
| Dependency engine | [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md); dogfood matrix; [dependency-validation.md](dependency-validation.md) steps |
| Analyze / dogfood semantics | [deck-analysis.md](../specs/deck-analysis.md) |
| Any **completed** active task | Remove from **active**; [changelog.md](../history/changelog.md) one bullet |

### Work-in-progress (not shipping)

- Keep task in **active** until the feature is **done**.
- Do **not** append changelog or trim active for partial PRs.
- May update specs if contract stabilizes mid-implementation.

### Implementation PR checklist

- [ ] Run **`/sync-documentation`** (or **`/ship-dependency-feature`** for dependency expansion).
- [ ] README matches CLI if user-facing.
- [ ] `analyze run --fail-on-expect` if dependency/matrix changed (note in PR).
- [ ] PR body: **Documentation** section; **Phase: implementation**

---

## Phase 3 — Ship (subset of implementation)

**When:** Active task is **complete** and merge-ready.

| Step | File |
| --- | --- |
| 1 | Remove task ID from [roadmap/active.md](../roadmap/active.md) |
| 2 | [history/changelog.md](../history/changelog.md) — one dated line |
| 3 | Domain spec updates (inventory, README, etc.) per DOC-MAP |
| 4 | Confirm task not still in [backlog/](../roadmap/backlog/) |

Dependency expansion: full table in [dependency-validation.md](dependency-validation.md); skill **`/ship-dependency-feature`**.

---

## Which skill / rule?

| Situation | Use |
| --- | --- |
| Any task before PR | **`/sync-documentation`** |
| Dependency profiles, patterns, dogfood | **`/ship-dependency-feature`** (includes sync) |
| Always | Rule `sdlc-documentation` |
| Edits under `cli/`, `wizard/` | Rule `cli-documentation` |
| Edits under dependency config/engine | Rule `dependency-documentation` |

---

## Quick decision tree

```
Starting work?
  → Read roadmap/active.md + component backlog
  → Planning-only? Update specs + active/backlog; no changelog
  → Coding? DOC-MAP + domain spec

Feature complete?
  → Remove from active + changelog + DOC-MAP row types
  → Dependency? shipped-inventory + analyze gate

Docs-only PR?
  → Phase: planning (unless correcting ship history)
```
