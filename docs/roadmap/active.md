# Active roadmap

**Single register** of work selected for immediate delivery. Parked work: [backlog/](backlog/). Shipped record: [changelog.md](../history/changelog.md) · [milestones.md](../history/milestones.md).

*Last updated: 2026-06-27.*

---

## Current focus

| Priority | What | Why now |
| --- | --- | --- |
| **ENG-MAINT** | Engine profile tuning | As needed when touching dependency rules or dogfood matrix |
| **GATE** | Dogfood gate | Required after any engine change |

**Primary thread:** None — promote next row from [backlog/](backlog/) when ready.

---

## Active task register

| ID | Component | Task | Status | Depends on | Parallel OK with |
| --- | --- | --- | --- | --- | --- |
| **ENG-MAINT** | cli-engine | Threshold tuning vs latest `dependency-audit` when adding profiles | Ongoing | — | doc-only, dogfood gate |
| **GATE** | cli-engine | `analyze run --fail-on-expect` (**30/30**) after engine changes | Always | Fresh `import` after bulk refresh | Other work if gate unchanged |

**Not active:** cli-engine expansion (P7 remainder, new profiles); cli-ui UX8; product-data export — promote from [backlog/](backlog/) before starting.

---

## Parallel work streams

| Stream | Component | Safe in parallel with |
| --- | --- | --- |
| A — Engine maintenance / dogfood | cli-engine | doc-only, planning |
| B — CLI feature work | cli-ui | *None active* — [backlog/cli-ui.md](backlog/cli-ui.md) only |

New cli-engine dependency profiles should not run in parallel with a large web API refactor on the same modules without coordination.

---

## Promote / demote workflow

1. Add row to this register from the relevant [backlog/](backlog/) file.
2. Fill **Depends on** and **Parallel OK with** before coding.
3. On ship: remove row here → [changelog.md](../history/changelog.md); update specs/inventory per [DOC-MAP.md](../DOC-MAP.md).

Planning steps: [agent-phases.md](../sdlc/agent-phases.md).

---

## Maintainer gate

```bash
mtg-deck-tools analyze run --fail-on-expect
```

Config: [`config/dogfood-matrix.yaml`](../../config/dogfood-matrix.yaml) · Runner: [deck-analysis.md](../specs/deck-analysis.md) · Dependency ship checklist: [dependency-validation.md](../sdlc/dependency-validation.md).
