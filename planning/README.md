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
| [08-card-availability.md](08-card-availability.md) | Budget null prices; availability heuristic |
| [DOC-MAP.md](DOC-MAP.md) | **Agent SDLC** — which docs to update per change type (canonical; not duplicated here) |
| [09-next-steps.md](09-next-steps.md) | **Active roadmap** — post-v1 backlog and dependency UX |
| [14-deck-analysis.md](14-deck-analysis.md) | **Automated dogfood** — `analyze run` matrix and reports |
| [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) | **Active** — shipped dependency inventory + high-value expansion backlog |
| [10-card-dependency-engine.md](10-card-dependency-engine.md) | **Shipped (D0–D5)** — cross-card synergy / tutor-target / resource-balance checks |
| [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) | **Active** — user control, focus presets, feedback; UX2–UX5 wizard shipped; UX7+ planned |
| [12-dependency-engine-pre-implementation-checklist.md](12-dependency-engine-pre-implementation-checklist.md) | **Complete gate** — D0–D5 checklist; dogfood acceptance open |
| [13-dependency-engine-decisions.md](13-dependency-engine-decisions.md) | Locked D0 decisions and v1 rule scope |
| [14-effect-extraction-face-policy.md](14-effect-extraction-face-policy.md) | Merged-face extraction policy (v1) |

## Current preferences

- **Deck generation:** Guided slot template (ramp / draw / removal / win-con / lands, etc.)
- **Mechanics matching:** Curated taxonomy + rule-based tagging from `oracle_text`
- **Include / avoid:** User selects keyword-level mechanics to want or exclude (trample, scry, energy, vehicles, …)
- **Wizard flow:** Theme → colors → commander (partners supported in v1)
- **Constraints:** Commander rules, budget, commander synergy, include/avoid mechanics
- **Dependencies:** Warn by default; `--strict-dependencies` / `--repair-dependencies` on CLI
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

### Dependency engine (D0–D5)
- Effect pattern spec, golden tests, face policy ([10](10-card-dependency-engine.md), [14](14-effect-extraction-face-policy.md))
- Inventory audit (`dependency-audit`) and evidence-backed profiles
- Import writes `card_effects`; post-build `dependency_report` in MD/JSON
- Pick-time dependency scoring during slot fill
- `--strict-dependencies` and `--repair-dependencies` on `generate`

### Dependency expansion (2026-06)
- **Enchantment matters** — `ENCHANTMENT_SUPPORT_MIN`, `ensure_enchantment_package` (`themes: [enchantress]`)
- **Subtype lord generalization** — `TYPE_SYNERGY_MIN`, per-subtype floors in `subtype_lords` profile
- **Tokens profile** — `TOKEN_BALANCE`, `ensure_token_package` (`themes: [tokens]`)
- **Vehicles profile** — `VEHICLE_BALANCE`, `ensure_vehicle_package` (`include_mechanics: [vehicles]`)

## What's next

See **[09-next-steps.md](09-next-steps.md)** for the active backlog.

**Agent documentation SDLC:** **[DOC-MAP.md](DOC-MAP.md)** — required updates per change type; enforced via `.cursor/rules/` and skills `/sync-documentation`, `/ship-dependency-feature` (no CI doc gates).

**Recommended first tasks:** **UX7** local web ([11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md)); optional **UX10** CMC metrics; Priority 7 remainder in doc 15 is backlog only.
