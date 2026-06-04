# Web UI package (planned)

**Status:** Not started. Tracked as **UX7** in [user-experience.md](../../specs/dependency-engine/user-experience.md) and [active.md](../../roadmap/active.md).

## Intended layout

```
packages/web/          # frontend app (framework TBD)
docs/packages/web/     # this file — package index
docs/specs/web/        # routes, API surface, deployment (add when UX7 starts)
```

## Principles

- Reuse the Python core (`src/mtg_deck_tools/`) via API or subprocess — no duplicate rules in the frontend.
- Shared product goals: `docs/product/` · shared roadmap: `docs/roadmap/`.

When implementation begins, update this README with actual paths and link new specs under `docs/specs/web/`.
