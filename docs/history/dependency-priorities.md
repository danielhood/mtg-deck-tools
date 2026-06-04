# Dependency expansion — priority delivery history

Archived record of Priority 1–8 expansion work (2026-06). **Open dependency work:** [backlog/cli-engine.md](../roadmap/backlog/cli-engine.md). **Shipped capability spec:** [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md).

---

## Priority 1–8 delivery archive

Each shipped row followed: **patterns → import → rule → optional package → profile activation → dogfood scenario**.

### Priority 1 — Extend existing atoms (lowest risk)

| Work item | New / extended atoms | Rule / package | Activation | Notes |
| --- | --- | --- | --- | --- |
| ~~**Generic subtype lords**~~ | Extend `buff_subtype` capture (Goblin, Vampire, Dragon, Pirate, …) | Per-subtype floors in `subtype_lords` profile; lord package runs for any lord | Card-driven + optional tribal themes | **Shipped 2026-06** — per-subtype minimums (Elf, Goblin, Vampire, Pirate, Zombie, Dragon); Krenko/Edgar dogfood |
| ~~**Tokens package**~~ | `token_produce`, `token_payoff` | `TOKEN_BALANCE` | `themes: [tokens]` | **Shipped 2026-06** — generic producers/payoffs only; subtype buff pairing → **Priority 8** |
| ~~**Vehicles profile**~~ | `type_line_vehicle` + crew creature count | `VEHICLE_BALANCE` | `include_mechanics: [vehicles]` | **Shipped 2026-06** — `vehicle_min: 3`, `creature_min: 25` |
| ~~**Enchantment matters**~~ | `whenever_cast_enchantment` (non-Aura) | `ENCHANTMENT_SUPPORT_MIN` | `themes: [enchantress]` + card-driven | **Shipped 2026-06** — `enchantment_min: 8`; Sythis dogfood; separate from `AURA_SUPPORT_MIN` |

### ~~Priority 2 — Tutor payload upgrades~~

**Shipped 2026-06** — [`rules/tutor_payload.py`](../../src/mtg_deck_tools/rules/tutor_payload.py): OR type matching (`type_match: any`), `min_cmc` / `max_cmc`, `colors`, land subtypes (Forest, …), creature-or-planeswalker patterns; validator loads card `colors` from DB. Patterns: `search_library_creature_cmc_min`, `search_library_colored_creature`, `search_library_land_subtype`, `search_library_creature_or_planeswalker`.

| Gap | Status |
| --- | --- |
| CMC bands (min / max) | Shipped |
| Color in search | Shipped |
| Named subtype land | Shipped |
| Multi-type tutors | Shipped |
| Named card search | Deferred (`REQUIRES_CARD` — rare) |
| `any_card` tutors | Unchanged (low confidence soft warn) 

### ~~Priority 3 — Resource counters (energy-shaped profiles)~~

**Shipped 2026-06** — [`rules/resource_counters.py`](../../src/mtg_deck_tools/rules/resource_counters.py): experience, blood, +1/+1, rad, oil, and charge counter produce/consume atoms; `EXPERIENCE_BALANCE`, `BLOOD_BALANCE`, `PLUS_ONE_BALANCE`, `RAD_BALANCE`, `OIL_BALANCE`, `CHARGE_BALANCE`; `ensure_resource_counter_packages`; wizard `include_mechanics: [experience]`, `[blood]`, `[counters]`, `[rad]`, `[oil]`, `[charge]`.

| Resource | Status |
| --- | --- |
| **+1/+1 / proliferate** | Shipped — `plus_one_*` kinds, `PLUS_ONE_BALANCE` |
| **Experience** | Shipped — `experience_*`, `EXPERIENCE_BALANCE` |
| **Blood** | Shipped — `blood_*`, `BLOOD_BALANCE` |
| ~~**Rad, oil, charge**~~ | **Shipped 2026-06** — `rad_*`, `oil_*`, `charge_*`; theme-selected via `include_mechanics`; charge/oil use higher `incidental_imbalance_min` (5 / 3) |

### ~~Priority 4 — Sacrifice / tokens refinements~~

**Shipped 2026-06** — [`rules/sacrifice_roles.py`](../../src/mtg_deck_tools/rules/sacrifice_roles.py): `token_produce` counts toward aristocrats fodder; `sacrifice_opponent` and `death_recursion` atoms; opponent/ recursion enablers satisfy `SACRIFICE_BALANCE` without player sacrifice outlets.

| Work item | Status |
| --- | --- |
| ~~Token producers vs aristocrats fodder~~ | Shipped — shared fodder axis; token payoffs stay on `TOKEN_BALANCE` |
| ~~Opponent-sacrifice effects~~ | Shipped — `sacrifice_opponent`; excluded from `sacrifice_outlet` |
| ~~Persist / undying / escape~~ | Shipped — `death_recursion`; ≥2 pieces support payoffs without outlets |

### ~~Priority 5 — Graveyard / landfall (warn-only first)~~

**Shipped 2026-06** — [`rules/graveyard_landfall.py`](../../src/mtg_deck_tools/rules/graveyard_landfall.py): `reanimate`, `graveyard_cost`, `mill_enabler`, `graveyard_payoff`, `landfall_payoff`, `land_ramp` atoms; `REANIMATION_SUPPORT`, `GRAVEYARD_COST_SUPPORT`, `SELF_MILL_BALANCE`, `LANDFALL_BALANCE` (warn-only; no packages yet). Profiles: `graveyard` (`themes: [recursion]`), `landfall` (`themes: [landfall]`).

| Archetype | Heuristic | Status |
| --- | --- | --- |
| ~~**Reanimation**~~ | “Return … from graveyard” + creature density / CMC | Shipped — `REANIMATION_SUPPORT` |
| ~~**Delve / flashback**~~ | Nonland count proxy for graveyard fodder | Shipped — `GRAVEYARD_COST_SUPPORT` |
| ~~**Self-mill**~~ | Mill enablers vs graveyard payoffs | Shipped — `SELF_MILL_BALANCE` |
| ~~**Landfall**~~ | Land ramp count vs landfall payoffs | Shipped — `LANDFALL_BALANCE` when `themes: [landfall]` or ≥2 payoffs |

### ~~Priority 7 — Graveyard filler atoms (surveil, discover, discard)~~ **Shipped 2026-06 (core)**

Priority 5 shipped narrow `mill_enabler` (explicit mill / library→GY). **Priority 7 core** extended `mill_enabler` extraction and `SELF_MILL_BALANCE` coverage:

| Deliverable | Status |
| --- | --- |
| **Surveil / discover** | Shipped — [`mill_enabler_surveil_discover`](../../config/effect-patterns.yaml) → `effect_kind: mill_enabler` |
| **Looting-style discard** | Shipped — `graveyard_filler_discard` |
| **Validate** | Shipped — [`collect_graveyard_roles`](../../src/mtg_deck_tools/rules/graveyard_landfall.py) counts all `mill_enabler` atoms |
| **Wizard keyword** | Shipped — `surveil` in [`mechanic-taxonomy.yaml`](../../config/mechanic-taxonomy.yaml) |
| **Dogfood** | Shipped — `surveil-mirko` in [`config/dogfood-matrix.yaml`](../../config/dogfood-matrix.yaml) |
| **Generic library → GY** | Shipped — original `mill_enabler` pattern (Priority 5) |

**Activation:** `graveyard` profile (`themes: [recursion]`); surveil via `include_mechanics: [surveil]`.

**Non-goals (unchanged):** Reanimation and delve/flashback stay on `REANIMATION_SUPPORT` and `GRAVEYARD_COST_SUPPORT`.

**Priority 7 remainder** (golden cases, broader GY, post-fill package) was never part of the shipped grid — tracked in [backlog/cli-engine.md](../roadmap/backlog/cli-engine.md).

### ~~Priority 8 — Token subtype buffs (match payoffs to produced token types)~~

**Shipped 2026-06** — `token_produce` subtype capture; `token_buff_subtype`; `TOKEN_SUBTYPE_BUFF_SUPPORT`; scoring/package/repair; dogfood `treasure-prosper`.

### ~~Priority 6 — Equipment depth~~

**Shipped 2026-06** — [`rules/equipment_depth.py`](../../src/mtg_deck_tools/rules/equipment_depth.py): `type_line_equipment`, `whenever_equipped`; `EQUIPMENT_BALANCE`; `ensure_equipment_package`; profile `equipment` (`equipment_min: 4`, `carrier_creature_min: 22`; activation `include_mechanics: [equip]`, `themes: [voltron]`).

| Work item | Status |
| --- | --- |
| ~~Equip pieces beyond artifact count~~ | Shipped — `type_line_equipment` + `EQUIPMENT_BALANCE` floor |
| ~~“Whenever equipped” payoffs~~ | Shipped — `whenever_equipped`; warns when payoffs lack Equipment |
| ~~Bodies to carry equipment~~ | Shipped — carrier creature minimum when Equipment present |

---

## Explicit non-goals (stay out of `card_effects` for now)

| Concern | Why deferred | Where handled today |
| --- | --- | --- |
| Removal / wipe density | Slot template, not oracle atoms | `slot-templates.yaml`, themes |
| Curve / land count | Mana base planner (avg CMC + ramp → land count) | `mana_base.py`, validation |
| Deck-wide CMC distribution / “good curve” UX | Post-build metrics & optional advisories, not `card_effects` | Planned **UX10** — [deck-output-format.md](../product/deck-output-format.md), [user-experience.md](../specs/dependency-engine/user-experience.md) |
| Named combo pairs | Needs external combo data | — |
| Power level / salt | No simple dial | [open-questions.md](../product/open-questions.md) |
| Aura removal risk | Not statically provable | UX note in [user-experience.md](../specs/dependency-engine/user-experience.md) |
| Commander partners / companion | Construction layer | `validate.py`, commander pick |
| In-game timing / stack | Non-goal per [overview.md](../specs/dependency-engine/overview.md) | — |

---

## Implementation checklist (per feature)

Canonical doc-update map: **[DOC-MAP.md](../DOC-MAP.md)**. Agents: invoke **`/ship-dependency-feature`** for this checklist plus ship-status edits.

Use this for each expansion PR:

1. **Patterns** — Add ids to `config/effect-patterns.yaml`; golden cases in `tests/fixtures/effect_golden.yaml`.
2. **Import** — Re-run `mtg-deck-tools import`; note new `effect_count` in PR.
3. **Audit** — Optional `dependency-audit` refresh for pool-size evidence.
4. **Profile** — `config/dependency-profiles.yaml`: `activation`, `defaults`, `roles`.
5. **Scope** — `rules/dependency_scope.py` if deck-level gating needed.
6. **Validate** — New or extended `rule_id` in `rules/dependencies.py`.
7. **Build** — Floors in `rules/dependency_profiles.py`; scoring in `dependency_scoring.py`; package in `mechanic_packages.py`; repair in `dependency_repair.py`.
8. **Rubric** — `analysis/rubric.py` inappropriate vs appropriate for dogfood metrics.
9. **Dogfood** — Scenario in `config/dogfood-matrix.yaml` with `expect.dependency`.
10. **Tests** — Unit tests + `analyze run --fail-on-expect`.

---

## Suggested sequence (engineering)

Aligned with [active.md](active.md) and dogfood matrix coverage:

| Order | Deliverable | Rationale |
| --- | --- | --- |
| ~~0~~ | ~~**Dogfood matrix 25/25**~~ | **Done 2026-06-03** — blood consume patterns; +1/+1 incidental threshold |
| ~~1~~ | ~~**Rad / oil / charge counters**~~ | **Done 2026-06-03** — `rad_*`, `oil_*`, `charge_*`; dogfood `rad-mothman`, `oil-migloz`, `charge-immard` |
| ~~2~~ | ~~**Equipment depth**~~ | **Done 2026-06** — `EQUIPMENT_BALANCE`, `type_line_equipment`, `whenever_equipped` |

**Shipped (2026-06):** **Token subtype buffs** (`TOKEN_SUBTYPE_BUFF_SUPPORT`, `token_buff_subtype`, subtype `token_produce`; dogfood `treasure-prosper`); **Graveyard filler atoms** (`mill_enabler_surveil_discover`, `graveyard_filler_discard`; dogfood `surveil-mirko`); **Equipment depth** (`EQUIPMENT_BALANCE`, `ensure_equipment_package`, `type_line_equipment`, `whenever_equipped`; profile `equipment`); **Rad / oil / charge counters** (`RAD_BALANCE`, `OIL_BALANCE`, `CHARGE_BALANCE`; profiles `rad`, `oil`, `charge`; wizard `include_mechanics`); **Resource counters** (experience, blood, +1/+1); tutor payload upgrades (`TUTOR_TARGET_EXISTS` matching: CMC bands, colors, land subtypes, multi-type OR); enchantment matters profile (`ENCHANTMENT_SUPPORT_MIN`, `whenever_cast_enchantment`, `themes: [enchantress]`); subtype lord generalization (`TYPE_SYNERGY_MIN`, `ensure_subtype_lord_packages`, `subtype_lords` profile); Tokens package (`TOKEN_BALANCE`); Vehicles profile (`VEHICLE_BALANCE`, crew density); **Sacrifice / token refinements** (`sacrifice_opponent`, `death_recursion`, aristocrats fodder includes `token_produce`); **Graveyard / landfall heuristics** (`REANIMATION_SUPPORT`, `GRAVEYARD_COST_SUPPORT`, `SELF_MILL_BALANCE`, `LANDFALL_BALANCE`; profiles `graveyard`, `landfall`).

**Parallel track:** ~~**UX2**~~ wizard controls for `strict_dependencies`, `repair_dependencies`, and `mechanic_focus` — **Shipped 2026-06-03** (wizard step 3; [user-experience.md](../specs/dependency-engine/user-experience.md)).

---
