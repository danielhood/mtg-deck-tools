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

Edit every doc listed for those change types. Common gaps to check:

| Signal | Doc action |
| --- | --- |
| New CLI flag or command | `README.md` |
| Shipped roadmap item | `docs/roadmap/dependency-expansion.md` strike-through + shipped line; `docs/history/changelog.md` one line; `docs/roadmap/active.md` if listed |
| New dependency profile/rule | dependency-expansion inventory tables; README mechanic blurb |
| Dogfood scenario added | `config/dogfood-matrix.yaml`; `docs/specs/deck-analysis.md` only if runner semantics change |
| Backlog priority shift | `docs/roadmap/active.md`; dependency-expansion suggested sequence |

## 3. Self-check (must pass)

- [ ] No shipped feature still listed as "next" in dependency-expansion Priority grid or active.md open table
- [ ] README commands/flags match `src/mtg_deck_tools/cli/`
- [ ] PR body will list docs touched OR explicit "none — reason"

## 4. Commit docs with code

Documentation updates belong in the **same PR** as the implementation, not a follow-up.

## When to use `/ship-dependency-feature` instead

If the branch adds or ships dependency engine behavior (patterns, profiles, packages, dogfood), run **`/ship-dependency-feature`** — it includes this sync plus the full dependency checklist.
