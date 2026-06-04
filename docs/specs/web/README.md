# Web UI specification (planned)

**Status:** Not started — **UX7** in [user-experience.md](../dependency-engine/user-experience.md).

## Code location

- Application: [`packages/web/`](../../../packages/web/) (`.gitkeep` until implementation)
- Package index: [packages/web/README.md](../../packages/web/README.md)

## When UX7 starts, document here

| Topic | Notes |
| --- | --- |
| API surface | How the frontend calls Python core (HTTP, IPC, or subprocess) |
| Routes / screens | Wizard parity, dependency dashboard, deck editor (UX11) |
| Auth / deployment | Local-first default; hosting TBD |
| Shared contracts | Reuse [deck-output-format.md](../../product/deck-output-format.md), [user-experience.md](../dependency-engine/user-experience.md) |

## Out of scope for v1 web MVP

- Duplicating dependency rules or validation in TypeScript
- Live Scryfall sync (same static snapshot policy as CLI)

## References

- [active.md](../../roadmap/active.md) — UX7 is the suggested next product task
- [pipeline-and-components.md](../../architecture/pipeline-and-components.md) — CLI vs web vs desktop options
