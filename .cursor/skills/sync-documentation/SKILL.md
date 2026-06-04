---
name: sync-documentation
description: Verify and update repository documentation to match code changes before commit or PR. Use on every agent task that touches src/, config/, tests/, or product status; required before opening or updating any pull request.
paths: src/**,config/**,tests/**,docs/**,README.md,AGENTS.md
---

# Sync documentation

Run at the **end** of every coding task, before commit/push/PR.

## 1. Classify the change

Open [docs/DOC-MAP.md](../../docs/DOC-MAP.md) and identify which rows apply to files changed in this branch.

## 2. Update required docs

| Signal | Doc action |
| --- | --- |
| New CLI flag or command | `README.md` |
| Shipped roadmap item | `shipped-inventory.md` + `changelog.md`; clear `roadmap/dependency/active.md` or `roadmap/active.md` |
| New dependency profile/rule | `shipped-inventory.md`; README mechanic blurb |
| Dogfood scenario added | `config/dogfood-matrix.yaml`; `deck-analysis.md` only if runner semantics change |
| Backlog / priority shift | Move rows between `roadmap/active.md` ↔ `roadmap/backlog.md` (and `dependency/` counterparts) |

## 3. Self-check (must pass)

- [ ] No shipped feature still listed under **active** (product or dependency)
- [ ] README commands/flags match `src/mtg_deck_tools/cli/`
- [ ] PR body will list docs touched OR explicit "none — reason"

## When to use `/ship-dependency-feature` instead

Dependency engine behavior (patterns, profiles, packages, dogfood): run **`/ship-dependency-feature`**.
