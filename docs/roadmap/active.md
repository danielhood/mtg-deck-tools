# Active roadmap

**Single register** of work selected for immediate delivery. Parked work: [backlog/](backlog/). Shipped record: [changelog.md](../history/changelog.md) · [milestones.md](../history/milestones.md).

*Last updated: 2026-06-27.*

---

## Current focus

| Priority | What | Why now |
| --- | --- | --- |
| **UX12** | Advanced swap & guided rebalance | Planning merged; wireframes + implementation |
| **ENG-MAINT** | Engine profile tuning | As needed when touching dependency rules or dogfood matrix |
| **GATE** | Dogfood gate | Required after any engine change |

**Primary thread:** **UX12** — constrained swap, preview API, issue playbooks ([advanced-swap-ux.md](../specs/web/advanced-swap-ux.md)).

---

## Active task register

| ID | Component | Task | Status | Depends on | Parallel OK with |
| --- | --- | --- | --- | --- | --- |
| **UX12** | web-ui | Advanced swap & guided rebalance — constraints, preview, issue playbooks, named card; Quick fix prototype | Wireframes | **UX11** (shipped) | doc-only, ENG-MAINT (coordinate on `iterate.py` / OpenAPI) |
| **ENG-MAINT** | cli-engine | Threshold tuning vs latest `dependency-audit` when adding profiles | Ongoing | — | doc-only, dogfood gate |
| **GATE** | cli-engine | `analyze run --fail-on-expect` (**30/30**) after engine changes | Always | Fresh `import` after bulk refresh | Other work if gate unchanged |

**Not active:** cli-engine expansion (P7 remainder, new profiles); cli-ui UX8; product-data export — promote from [backlog/](backlog/) before starting.

### UX12 slices

| Slice | Deliverable | Status |
| --- | --- | --- |
| **UX12a** | Planning + playbook YAML + OpenAPI contract | Planning shipped |
| **UX12a-wf** | P0 wireframes (advanced sheet, issue strategies, named swap) | Draft |
| **UX12b** | Engine `SwapConstraints` + `swap/preview` endpoint | Pending |
| **UX12c** | Advanced sheet UI + filters + preview + cross-slot toggle | Pending |
| **UX12d** | Issue **Fix issue…** + playbooks + Quick fix prototype | Pending |
| **UX12e** | Named-card replacement | Pending |
| **UX12f** | Curve advisory actions | Deferred post-v1 |

Spec: [advanced-swap-ux.md](../specs/web/advanced-swap-ux.md) · Wireframes: [wireframes/README.md](../specs/web/wireframes/README.md) § UX12.

---

## Parallel work streams

| Stream | Component | Safe in parallel with |
| --- | --- | --- |
| A — UX12 web iterate | web-ui | doc-only |
| B — Engine maintenance / dogfood | cli-engine | doc-only, UX12b if `dependency_repair` patterns reused |
| C — CLI feature work | cli-ui | *None active* — [backlog/cli-ui.md](backlog/cli-ui.md) only |

UX12b engine work touches `builder/iterate.py` and OpenAPI — coordinate with any concurrent cli-engine profile changes on the same modules.

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
