---
name: sync-documentation
description: Verify and update docs for planning or implementation before commit or PR. Use on every agent task touching src/, config/, tests/, docs/, or roadmap status.
paths: src/**,config/**,tests/**,docs/**,README.md,AGENTS.md
---

# Sync documentation

Read [docs/sdlc/agent-phases.md](../../docs/sdlc/agent-phases.md) first to determine **planning** vs **implementation**, then [docs/DOC-MAP.md](../../docs/DOC-MAP.md) for file targets.

---

## 1. Determine phase

| Phase | Indicators |
| --- | --- |
| **Planning** | Docs-only or promoting backlog → active; spec/UX design; no feature-complete code |
| **Implementation** | `src/`, `config/`, `tests/` changed for a feature |
| **Ship** (end of implementation) | Active task is complete; ready to merge |

---

## 2. Planning phase

**Read:** [roadmap/active.md](../../docs/roadmap/active.md), relevant [roadmap/backlog/](../../docs/roadmap/backlog/), domain `docs/specs/`.

**Update:**

| Action | Files |
| --- | --- |
| Promote task | Add row to `roadmap/active.md`; remove from `roadmap/backlog/<component>.md`; set Depends on / Parallel |
| Park / defer | Keep in backlog; ensure not in active |
| Design behavior | `docs/specs/`, `docs/product/` as needed |

**Do not:** `history/changelog.md`, `shipped-inventory.md` (until code ships).

---

## 3. Implementation phase

**Read:** DOC-MAP change-type row + domain specs + active task row.

**Update (same PR as code):**

| Signal | Files |
| --- | --- |
| CLI / wizard | `README.md`, `specs/dependency-engine/user-experience.md` if UX |
| Dependency engine | `shipped-inventory.md`, `config/dogfood-matrix.yaml`, see dependency-validation |
| Dogfood runner semantics | `specs/deck-analysis.md` |
| WIP | Keep task in **active**; no changelog yet |

---

## 4. Ship (feature complete)

| Step | Files |
| --- | --- |
| 1 | Remove task from `docs/roadmap/active.md` |
| 2 | Append `docs/history/changelog.md` |
| 3 | Other paths per DOC-MAP (inventory, README, milestones rare) |

Dependency expansion: use **`/ship-dependency-feature`** instead of duplicating this list.

---

## 5. Self-check

- [ ] Phase stated in PR body (planning | implementation)
- [ ] No shipped task still in **active**
- [ ] No changelog entry for planning-only work
- [ ] README matches CLI when user-facing
- [ ] Docs touched listed or "none — reason"
