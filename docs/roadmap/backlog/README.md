# Backlog (by component)

Parked work — **not** in [active.md](../active.md) until promoted.

**Workflow:** [agent-phases.md](../../sdlc/agent-phases.md) § Phase 1 (planning) · **Snapshot of active work:** [roadmap/README.md](../README.md).

---

## Index

| Component | Backlog | Typical code |
| --- | --- | --- |
| CLI engine | [cli-engine.md](cli-engine.md) | `src/mtg_deck_tools/` (builder, rules, effects, import) |
| CLI UI | [cli-ui.md](cli-ui.md) | `cli/`, `wizard/` |
| Web UI | [web-ui.md](web-ui.md) | `packages/web/` |
| Product & data | [product-data.md](product-data.md) | formats, import pipeline, export |

---

## How backlog relates to active and history

```
backlog/  ──promote──▶  active.md  ──ship──▶  history/changelog.md
     ▲                        │
     └──── demote / defer ────┘
```

- **Promote:** remove row from component backlog; add to [active.md](../active.md) with Depends on / Parallel OK with.
- **Ship:** remove from active; append [changelog.md](../../history/changelog.md). Do **not** leave shipped items or ship narratives in active or backlog — use changelog, milestones, and specs instead.
