# Roadmap

How work is **selected**, **parked**, and **recorded** in this repo. Specs live in `docs/specs/`; shipped history in `docs/history/`.

---

## Three layers

| Layer | File | Question it answers |
| --- | --- | --- |
| **Active** | [active.md](active.md) | What are we building **now**? |
| **Backlog** | [backlog/](backlog/) | What is **parked** until promoted? |
| **History** | [changelog.md](../history/changelog.md) · [milestones.md](../history/milestones.md) | What **shipped**? |

**Rule:** Only [active.md](active.md) lists selected work. Backlog rows move to active when promoted; active rows are removed when shipped. Do not duplicate ship narratives or shipped feature detail in active or backlog — append [changelog.md](../history/changelog.md) and update specs instead.

---

## Current snapshot

*Updated 2026-06-27. Detail and dependencies: [active.md](active.md).*

| Priority | ID | Component | Task |
| --- | --- | --- | --- |
| Ongoing | **ENG-MAINT** | cli-engine | Profile tuning vs `dependency-audit` when adding rules |
| Always | **GATE** | cli-engine | `analyze run --fail-on-expect` (**30/30**) after engine changes |

**Not active:** cli-engine expansion (P7 remainder), cli-ui UX8, product-data export, web-ui — promote from [backlog/](backlog/) before starting.

---

## Layout

```
roadmap/
  README.md           # This index + snapshot
  active.md           # Unified active register (all components)
  backlog/
    README.md         # Backlog index
    cli-engine.md     # Dependency engine expansion
    cli-ui.md         # Terminal wizard / CLI UX
    web-ui.md         # Web app
    product-data.md   # Export, formats, data pipeline
```

---

## Components

| Component | Code / package | Backlog |
| --- | --- | --- |
| **cli-engine** | `src/mtg_deck_tools/` (import, builder, rules, effects, analyze) | [cli-engine.md](backlog/cli-engine.md) |
| **cli-ui** | `src/mtg_deck_tools/cli/`, `wizard/` | [cli-ui.md](backlog/cli-ui.md) |
| **web-ui** | `packages/web/` | [web-ui.md](backlog/web-ui.md) |
| **product-data** | Cross-cutting data, export, formats | [product-data.md](backlog/product-data.md) |

---

## Agent workflow (summary)

1. **Planning** — promote backlog → active; design specs; no changelog.
2. **Implementation** — code + doc updates in one PR; keep task in active until done.
3. **Ship** — remove from active; append changelog; update inventory/README per DOC-MAP.

Before every PR: skill **`/sync-documentation`**. Dependency expansion ship: **`/ship-dependency-feature`**.
