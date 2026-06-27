# Active roadmap

**Single register** of work selected for immediate delivery. Parked work: [backlog/](backlog/). Shipped record: [changelog.md](../history/changelog.md) · [milestones.md](../history/milestones.md).

*Last updated: 2026-06-27.*

---

## Current focus

| Priority | What | Why now |
| --- | --- | --- |
| **ENG-MAINT** | Engine profile tuning | As needed when touching dependency rules or dogfood matrix |
| **GATE** | Dogfood gate | Required after any engine change |

**Primary thread:** None — promote next row from [backlog/web-ui.md](backlog/web-ui.md) when ready.

---

## Active task register

| ID | Component | Task | Status | Depends on | Parallel OK with |
| --- | --- | --- | --- | --- | --- |
| **ENG-MAINT** | cli-engine | Threshold tuning vs latest `dependency-audit` when adding profiles | Ongoing | — | doc-only, dogfood gate |
| **GATE** | cli-engine | `analyze run --fail-on-expect` (**30/30**) after engine changes | Always | Fresh `import` after bulk refresh | Other work if gate unchanged |

**Not active:** cli-engine expansion rows (P7 remainder, new profiles). Post-MVP web backlog: [backlog/web-ui.md](backlog/web-ui.md).

---

## UX7 context (MVP complete)

UX7 is the cross-platform web shell. All sub-phases **UX7a–UX7d** are **shipped** — see [changelog.md](../history/changelog.md).

| Sub-phase | Deliverable | Status |
| --- | --- | --- |
| UX7a | `service/` extraction + OpenAPI | Shipped |
| UX7b | `mtg-deck-tools serve` | Shipped |
| UX7c | Build wizard + result | Shipped |
| UX7e | Enhanced deck view | Shipped |
| UX7f | Saved deck library | Shipped |
| UX7d | Dependency dashboard | Shipped |
| UX7g | Database init / refresh (server bootstrap + web import UI) | Shipped |

Post-MVP web work: [backlog/web-ui.md](backlog/web-ui.md) (**UX10** shipped).

---

## Dependency graph

```mermaid
flowchart LR
  subgraph shipped["Shipped"]
    UX7a[UX7a service]
    UX7b[UX7b API]
    UX7c[UX7c wizard]
    UX7e[UX7e deck view]
    UX7f[UX7f library]
    UX7d[UX7d dashboard]
    UX7g[UX7g DB import]
    UX11[UX11 editor]
    UX10[UX10 metrics]
  end

  subgraph backlog["Backlog"]
  end

  CORE[cli-engine core]

  CORE --> UX7a
  UX7a --> UX7b
  UX7b --> UX7c
  UX7c --> UX7e
  UX7e --> UX7f
  UX7f --> UX7d
  UX7e --> UX11
  UX11 --> UX10
```

- **UX10** shipped — CLI deck metrics (UX10a) + web CMC charts on `/deck/:id` (UX10b) + YAML curve advisories (UX10c). **UX11** shipped — GUI deck editor.
- New cli-engine dependency profiles should not run in parallel with a large web API refactor on the same modules without coordination.

---

## Parallel work streams

| Stream | Component | Safe in parallel with |
| --- | --- | --- |
| A — Engine maintenance / dogfood | cli-engine | doc-only, planning |
| B — CLI feature work | cli-ui | *None active* — [backlog/cli-ui.md](backlog/cli-ui.md) only |

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
