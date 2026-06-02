---
name: sync-documentation
description: Verify and update repository documentation to match code changes before commit or PR. Use on every agent task that touches src/, config/, tests/, or product status; required before opening or updating any pull request.
paths: src/**,config/**,tests/**,planning/**,README.md,AGENTS.md
---

# Sync documentation

Run at the **end** of every coding task, before commit/push/PR.

## 1. Classify the change

Open [planning/DOC-MAP.md](../../planning/DOC-MAP.md) and identify which rows apply to files changed in this branch.

## 2. Update required docs

Edit every doc listed for those change types. Common gaps to check:

| Signal | Doc action |
| --- | --- |
| New CLI flag or command | `README.md` |
| Shipped roadmap item | Doc 15 strike-through + shipped line; doc 09 recently shipped |
| New dependency profile/rule | Doc 15 inventory tables; README mechanic blurb |
| Dogfood scenario added | `config/dogfood-matrix.yaml`; doc 14 only if runner semantics change |
| Backlog priority shift | Doc 09 active work table; doc 15 suggested sequence |

## 3. Self-check (must pass)

- [ ] No shipped feature still listed as "next" in doc 15 Priority grid or doc 09 active table
- [ ] README commands/flags match `src/mtg_deck_tools/cli/`
- [ ] PR body will list docs touched OR explicit "none — reason"

## 4. Commit docs with code

Documentation updates belong in the **same PR** as the implementation, not a follow-up.

## When to use `/ship-dependency-feature` instead

If the branch adds or ships dependency engine behavior (patterns, profiles, packages, dogfood), run **`/ship-dependency-feature`** — it includes this sync plus the full dependency checklist.
