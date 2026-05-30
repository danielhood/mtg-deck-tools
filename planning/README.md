# MTG Commander Deck Builder — Planning

Planning documents for a local Windows utility that walks users through deck-building criteria and produces a playable Commander (100-card, singleton) deck list.

## Documents

| Doc | Purpose |
| --- | --- |
| [01-goals-and-scope.md](01-goals-and-scope.md) | Problem statement, v1 scope, success criteria |
| [02-data-sources.md](02-data-sources.md) | Oracle cards JSON, rules text, field reference gap |
| [03-problem-decomposition.md](03-problem-decomposition.md) | Sub-problems: wizard, filtering, tagging, slots, mana base |
| [04-architecture-options.md](04-architecture-options.md) | End-to-end pipeline and component options |
| [05-technology-options.md](05-technology-options.md) | Stack comparison for local Windows + database |
| [06-open-questions.md](06-open-questions.md) | Resolved planning decisions |
| [07-deck-output-format.md](07-deck-output-format.md) | Markdown + `.deck.json` schema |
| [08-card-availability.md](08-card-availability.md) | Budget null prices; future availability heuristic |
| [09-next-steps.md](09-next-steps.md) | **Post-v1 roadmap** — Phase 3 priorities and backlog |
| [10-card-dependency-engine.md](10-card-dependency-engine.md) | **Planned** — cross-card synergy / tutor-target / resource-balance checks (not full CR) |
| [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) | **Planned** — user control, balance presets, feedback, CLI vs UI (parallel to doc 10) |
| [12-dependency-engine-pre-implementation-checklist.md](12-dependency-engine-pre-implementation-checklist.md) | **Gate** — checklist before D1+ engine code (D0, D0.5, decisions, contracts) |

## Current preferences

- **Deck generation:** Guided slot template (ramp / draw / removal / win-con / lands, etc.)
- **Mechanics matching:** Curated taxonomy + rule-based tagging from `oracle_text`
- **Include / avoid:** User selects keyword-level mechanics to want or exclude (trample, scry, energy, vehicles, …)
- **Wizard flow:** Theme → colors → commander (partners supported in v1)
- **Constraints:** Commander rules, budget, commander synergy, include/avoid mechanics
- **Export:** Markdown (human) + `.deck.json` (machine reload / images / future edits)
- **UI:** Terminal CLI — Python + `typer` / `questionary` / `rich`
- **Runtime:** Python + SQLite

- **Budget:** Allow with warning when `prices.usd` is null; optional `--strict-budget`
- **Variety:** Seeded random slot picks (`--seed`)
- **Power level:** Deferred (not a simple dial)
- **Card data:** Static Scryfall oracle snapshot; manual refresh — used-card audience (6+ months), not day-one meta
- **Availability:** v1 EDHREC bias + import-time score; deprioritize obscure over chasing new printings

## Completed

### Phase 1
- Oracle import, mechanic taxonomy v0, SQLite schema, CLI stub

### Phase 2
1. ~~Wizard steps 1–5~~ — full criteria wizard (`mtg-deck-tools wizard` or `generate --wizard`)
2. ~~Full slot filling~~ — `mtg-deck-tools generate` fills all template slots
3. ~~Dynamic mana base~~ — ramp/curve/colors land count heuristic, pip-aware mix
4. ~~Commander rule validation~~ — CR 903/702.124 checks in generate output

### v1 polish
- Budget pool filter excludes cards priced above remaining budget
- Post-fill budget trim swaps expensive cards for cheaper slot alternatives (incremental when over cap)
- `--strict-budget` excludes unpriced cards from the pool
- Tighter `board_wipe` / new `wincon` theme tags for slot filling
- Land scoring deprioritizes expensive nonbasics when a budget cap is set

### Phase 3 (v1 closure)
- Build-time legality filters (903.5d land colors, land/nonland slot separation)
- Slot pool quality (oracle guards, tag relaxation, slot-specific scoring)
- `.deck.json` reload / `--refill-slot` workflow
- Availability scoring, `--prefer-available`, unpriced classification in Notes
- **v1 success criteria** — checked off 2026-05-30 ([01-goals-and-scope.md](01-goals-and-scope.md))

## What's next

See **[09-next-steps.md](09-next-steps.md)** for the post-v1 backlog.

**Recommended first task:** card dependency engine ([10-card-dependency-engine.md](10-card-dependency-engine.md)). Complete [12-dependency-engine-pre-implementation-checklist.md](12-dependency-engine-pre-implementation-checklist.md) before D1.
