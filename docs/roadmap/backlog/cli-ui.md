# Backlog — CLI UI

Terminal wizard and CLI flags. Code: `src/mtg_deck_tools/cli/`, `src/mtg_deck_tools/wizard/`.

Promote to [active.md](../active.md) before starting. **Index:** [backlog/README.md](README.md).

---

## Wizard / CLI UX

| ID | Topic | Notes | Spec |
| --- | --- | --- | --- |
| UX8 | Progressive wizard constraints | Restrict choices by CI/commander/partial deck | [user-experience.md](../../specs/dependency-engine/user-experience.md) § Progressive constraints |
| CLI-SWAP | Dependency swap packages | `generate --swap-profile` — needs web or CLI design | [user-experience.md](../../specs/dependency-engine/user-experience.md) |

**Promoted (2026-06-28):** **CLI-IN** → **UX13-MVP** in [active.md](../active.md).

**Depends on:** **UX8** — soft dependency on stable wizard flow. **CLI-SWAP** — design coupling to [web-ui.md](web-ui.md).

**Parallel:** **UX8** can proceed **in parallel with web-ui work** (disjoint paths). **CLI-SWAP** best after web API direction is clear.
