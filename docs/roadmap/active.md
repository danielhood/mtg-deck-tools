# Active roadmap

**Immediate next work** — selected tasks in flight or explicitly chosen as the next deliverable. Parked ideas: [backlog.md](backlog.md).

Status as of 2026-06-04. Shipped history: [milestones.md](../history/milestones.md) · [changelog.md](../history/changelog.md).

---

## Suggested next task

| Priority | Task | Doc |
| --- | --- | --- |
| **1** | **UX7** — local web / desktop UI | [user-experience.md](../specs/dependency-engine/user-experience.md) · [packages/web/README.md](../packages/web/README.md) · [specs/web/README.md](../specs/web/README.md) |

CLI wizard UX2–UX5 are complete. Optional follow-on in same initiative: **UX10** CMC metrics.

**Dependency:** No row in [dependency/active.md](dependency/active.md) — optional P7 remainder remains in [dependency/backlog.md](dependency/backlog.md).

---

## Active / in-progress

| Area | Status | Notes |
| --- | --- | --- |
| UX7 local web / desktop UI | **Selected next** | Reuse Python core; dependency dashboard, UX10 charts, UX11 editor |
| Threshold tuning vs audit | Ongoing | When adding profiles — [dependency-validation.md](../sdlc/dependency-validation.md) |

---

## Regression gate (maintainers)

```bash
mtg-deck-tools analyze run --fail-on-expect
```

**30/30** — [deck-analysis.md](../specs/deck-analysis.md), [`config/dogfood-matrix.yaml`](../../config/dogfood-matrix.yaml).

After Scryfall bulk refresh: `import` → optional `dependency-audit` → analyze gate.

---

## Doc updates on ship

Per [DOC-MAP.md](../DOC-MAP.md): [changelog.md](../history/changelog.md); [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md) for dependency code; do not duplicate ship prose here.

---

## References

| Doc | Role |
| --- | --- |
| [backlog.md](backlog.md) | Parked product and UX work |
| [dependency/active.md](dependency/active.md) | Selected dependency expansion (if any) |
| [dependency/README.md](dependency/README.md) | Dependency roadmap index |
