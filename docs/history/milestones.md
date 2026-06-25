# Shipped milestones

Historical record of major capabilities. For day-to-day “what to build next,” use [roadmap/active.md](../roadmap/active.md). For dependency effect/rule inventory, use [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md).

## Phase 1

- Oracle import, mechanic taxonomy v0, SQLite schema, CLI stub

## Phase 2

- Wizard steps 1–5 (`mtg-deck-tools wizard` / `generate --wizard`)
- Full slot filling (`mtg-deck-tools generate`)
- Dynamic mana base (ramp/curve/colors heuristic, pip-aware mix)
- Commander rule validation (CR 903 / 702.124)

## v1 polish

- Budget pool filter and post-fill trim; `--strict-budget`
- Tighter `board_wipe` / `wincon` theme tags
- Land scoring deprioritizes expensive nonbasics under budget cap

## Phase 3 (v1 closure, 2026-05-30)

| Item | Notes |
| --- | --- |
| Build-time legality filters | 903.5d land colors; land/nonland slot separation |
| Slot pool quality | Oracle guards, tag relaxation, slot-specific scoring |
| `.deck.json` reload | `--from`, `--refill-slot` |
| Availability scoring | `--prefer-available`; unpriced classification in Notes |
| v1 success criteria | [goals-and-scope.md](../product/goals-and-scope.md) |

## Dependency engine (D0–D5, 2026-05-30 / 2026-05-31)

| Phase | Deliverable |
| --- | --- |
| D0 | Pattern spec + golden tests |
| D0.5 | Inventory audit (`dependency-audit`) |
| D1 | Import writes `card_effects` |
| D2 | Post-build `dependency_report` in MD/JSON |
| D3 | Pick-time dependency scoring |
| D4 | `--strict-dependencies` |
| D5 | `--repair-dependencies` |

Technical detail: [overview.md](../specs/dependency-engine/overview.md), [implementation-checklist.md](../specs/dependency-engine/implementation-checklist.md).

## Wizard UX (2026-06)

| UX | Shipped |
| --- | --- |
| UX2 | Wizard step 3 — `strict_dependencies`, `repair_dependencies`, `mechanic_focus` |
| UX3 | End-of-wizard criteria preflight |
| UX4 | Step back-navigation with preserved defaults |
| UX5 | Prepopulate from `.deck.json` (`--wizard --from`, `wizard --from`) |

## Dependency expansion (2026-06)

Enchantment matters, subtype lords, tokens, vehicles, equipment depth, rad/oil/charge counters, graveyard/landfall heuristics, sacrifice/token refinements, resource counters, tutor payload upgrades, graveyard filler atoms (surveil/discover/discard), token subtype buffs — see [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md).

## Dogfood

Matrix: **30 scenarios**; gate `analyze run --fail-on-expect` — **30/30** as of 2026-06. See [deck-analysis.md](../specs/deck-analysis.md).

## Web UI (2026-06)

| Phase | Deliverable |
| --- | --- |
| UX7a | `service/` extraction + OpenAPI |
| UX7b | `mtg-deck-tools serve` + health/stats |
| UX7c | Build wizard (7 steps + review + generate) |
| UX7e | Enhanced deck view (`/deck/:id`) |
| UX7f | Saved deck library (`/library`, server persistence, auto-save on generate) |

**Active:** UX7d dependency dashboard — [active.md](../roadmap/active.md). Detail: [specs/web/README.md](../specs/web/README.md), [changelog.md](changelog.md).
