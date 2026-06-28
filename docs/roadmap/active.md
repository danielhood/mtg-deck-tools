# Active roadmap

**Single register** of work selected for immediate delivery. Parked work: [backlog/](backlog/). Shipped record: [changelog.md](../history/changelog.md) · [milestones.md](../history/milestones.md).

*Last updated: 2026-06-28.*

---

## Current focus

| Priority | What | Why now |
| --- | --- | --- |
| **UX13c** | Deck import preview | Next text-import slice; reduces exact-match frustration before save |
| **UX12** | Advanced swap & guided rebalance | Implementation complete — dogfood + ship |
| **ENG-MAINT** | Engine profile tuning | As needed when touching dependency rules or dogfood matrix |
| **GATE** | Dogfood gate | Required after any engine change |

**Primary thread:** **UX13c** — parse + resolve preview on home import ([deck-input.md](../specs/product/deck-input.md) § UX13c).

---

## Active task register

| ID | Component | Task | Status | Depends on | Parallel OK with |
| --- | --- | --- | --- | --- | --- |
| **UX13c** | web-ui + product-data | Deck import **preview** — resolve without save; line-level status; commit only when clean | Planning locked | **UX13-MVP**, **UX13b** (shipped) | doc-only, GATE |
| **UX12** | web-ui | Advanced swap & guided rebalance — constraints, preview, issue playbooks, named card; Quick fix prototype | Implementation complete — dogfood + ship | **UX11** (shipped) | doc-only, ENG-MAINT |
| **ENG-MAINT** | cli-engine | Threshold tuning vs latest `dependency-audit` when adding profiles | Ongoing | — | doc-only, dogfood gate |
| **GATE** | cli-engine | `analyze run --fail-on-expect` (**30/30**) after engine changes | Always | Fresh `import` after bulk refresh | Other work if gate unchanged |

**Not active:** cli-engine expansion (P7 remainder, new profiles); cli-ui UX8; product-data export; UX13 resolver v2 / JSON / fill — [backlog/](backlog/).

### UX13c slices — import preview

| Slice | Deliverable | Status |
| --- | --- | --- |
| **UX13c-a** | Planning + promotion (this doc) | Planning shipped |
| **UX13c-b** | `preview_deck_import()` service + DTO; `POST /api/v1/decks/import/preview` | Pending |
| **UX13c-c** | Home UI — **Preview** step, line table, **Import** gated on clean preview | Pending |
| **UX13c-d** | CLI `deck import --file … --dry-run` (optional) | Pending |

Spec: [deck-input.md](../specs/product/deck-input.md) § UX13c · API: [library-api.md](../specs/web/library-api.md).

### UX12 slices

| Slice | Deliverable | Status |
| --- | --- | --- |
| **UX12a** | Planning + playbook YAML + OpenAPI contract | Planning shipped |
| **UX12a-wf** | P0 wireframes (advanced sheet, issue strategies, named swap) | Approved |
| **UX12b** | Engine `SwapConstraints` + `swap/preview` endpoint | Implemented |
| **UX12c** | Advanced sheet UI + filters + preview + cross-slot toggle | Implemented |
| **UX12d** | Issue **Fix issue…** + playbooks + Quick fix prototype | Implemented |
| **UX12e** | Named-card replacement | Implemented |
| **UX12f** | Curve advisory actions | Deferred post-v1 |

Spec: [advanced-swap-ux.md](../specs/web/advanced-swap-ux.md) · Wireframes: [wireframes/README.md](../specs/web/wireframes/README.md) § UX12.

---

## Parallel work streams

| Stream | Component | Safe in parallel with |
| --- | --- | --- |
| A — UX13c import preview | web-ui, service | doc-only, GATE |
| B — UX12 ship / dogfood | web-ui | doc-only |
| C — Engine maintenance / dogfood | cli-engine | doc-only |
| D — CLI wizard backlog | cli-ui | *UX8 not active* — [backlog/cli-ui.md](backlog/cli-ui.md) |

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
