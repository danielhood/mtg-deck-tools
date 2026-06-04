---
name: sync-documentation
description: Verify and update repository documentation to match code changes before commit or PR.
paths: src/**,config/**,tests/**,docs/**,README.md,AGENTS.md
---

# Sync documentation

Open [docs/DOC-MAP.md](../../docs/DOC-MAP.md).

| Signal | Action |
| --- | --- |
| Shipped item | Update `changelog`; remove row from [roadmap/active.md](../../docs/roadmap/active.md) |
| New dependency code | [shipped-inventory.md](../../docs/specs/dependency-engine/shipped-inventory.md) |
| Backlog promotion | Move row backlog → [active.md](../../docs/roadmap/active.md) |
| CLI change | `README.md` |

Self-check: nothing shipped still listed in **active** register.
