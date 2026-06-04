# Next steps — post-v1

Status as of 2026-06-04. **v1 is complete.** Phase 1, Phase 2, v1 polish, **Phase 3 (§1–§5)**, and the **card dependency engine (D0–D5)** are **shipped**. Dogfood matrix (**28 scenarios**) and mechanic packages (energy, experience, blood, +1/+1, rad, oil, charge counters, sacrifice, auras, artifacts, subtype lords, tokens, vehicles) — see [14-deck-analysis.md](14-deck-analysis.md) and [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md).

## Current state

| Milestone | Status |
| --- | --- |
| Oracle import + mechanic tags + SQLite | Done |
| Wizard (steps 1–7; UX2 synergy step 3) | Done |
| Slot-filled 99-card generation | Done |
| Dynamic mana base | Done |
| Commander validation (CR 903 / 702.124) | Done |
| Budget enforcement + trim pass | Done |
| `--strict-budget` | Done (CLI flag; wizard references it at generate time) |
| Per-card USD price min/max | Done — wizard step 5 (filters commander search in step 6) + `--card-price-min` / `--card-price-max` |
| Build-time legality filters (903.5d, land/nonland slots) | Done |
| Deck Markdown output polish | Done — grouped notes, card details, mana text, header metadata |
| Commander price + release date (wizard + MD) | Done |
| Card name + type display (wizard + MD) | Done |
| Taxonomy display names in MD header | Done |
| Linux/bash setup in README | Done |
| `.deck.json` reload / edit workflow | Done |
| Slot pool quality (themed slot misfills) | Done |
| Unpriced / availability handling | Done |
| Effect extraction (`card_effects`) | Done — D1 import pass |
| Dependency validation report | Done — D2 `dependency_report` in MD/JSON |
| Pick-time dependency scoring | Done — D3 during slot fill |
| `--strict-dependencies` | Done — D4 pick-time filter |
| `--repair-dependencies` | Done — D5 post-build swap pass |
| Wizard dependency controls (UX2) | **Done** — wizard step 3: `strict_dependencies`, `repair_dependencies`, optional `mechanic_focus` per activated profile |
| Wizard criteria linter (UX3) | **Done** — end-of-wizard preflight (`rules/criteria_linter.py`); user confirms before summary |
| Dependency dogfood calibration | **Done** — `analyze run --fail-on-expect`: **25/25** after 2026-06 bulk refresh (blood consume patterns, +1/+1 incidental threshold) |
| Mechanic packages | **Done** — energy, experience, blood, +1/+1 counters, sacrifice/aristocrats, voltron auras, enchantments, equip/vehicles artifacts, subtype lords, tokens, vehicles, equipment |
| Sacrifice / aristocrats profile | **Done** — `SACRIFICE_BALANCE` + `ensure_sacrifice_package` |
| Tokens profile | **Done** — `TOKEN_BALANCE` + `ensure_token_package` (`themes: [tokens]`) |
| Vehicles profile | **Done** — `VEHICLE_BALANCE` + `ensure_vehicle_package` (`include_mechanics: [vehicles]`) |
| Equipment depth | **Done** — `EQUIPMENT_BALANCE` + `ensure_equipment_package` (`include_mechanics: [equip]`, `themes: [voltron]`) |
| Aura calibration | **Done** — `whenever_cast_aura` vs generic enchantment payoffs; card-driven aura package |
| Dependency expansion (enchantment matters, tutors, …) | **Planned** — [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) |

## Dogfooding snapshot (v1 closure)

Latest pass: `output/dogfood-v1-closure/` (`seed=42`).

| Area | Result |
| --- | --- |
| Validation (903 / 702.124) | **PASSED** — all five closure decks legal (100 cards, singleton, identity, 903.5d lands) |
| Budget trim | **Works** — Pantlaza `$65.50` vs `$75` cap; Dromoka `$86.91` vs `$150` |
| Per-card price range | **Works** — `$3` and `$5` per-card caps honored in MD header and fill |
| Unpriced cards | Classified in Notes (`price_pending` / `likely_obscure`); budget warnings when not strict |
| Slot quality | **Improved** — oracle guards and tag relaxation reduce misfills (Phase 3 §2) |
| MD output | Card names + type line; Scryfall links; commander price/release; taxonomy display names |
| Reload | **Works** — `--from` full regen and `--refill-slot synergy` verified |

## Dogfooding snapshot (dependency engine)

Early pass: `output/muldrotha-the-gravetide-20260530180919.md` (`seed=42`, tokens theme).

| Area | Result |
| --- | --- |
| Validation | **PASSED** |
| Dependency report | **WARNINGS** — `AURA_SUPPORT_MIN` (2 auras vs suggested min 6) on a tokens build |
| Strict / repair / focus | Wizard step 3 and CLI flags (`--strict-dependencies`, `--repair-dependencies`) |

**Calibration note:** Deck-level rules are now scoped to themes / `include_mechanics` / `mechanic_focus` (see `dependency_scope.py`). Incidental single-card energy no longer warns unless the user includes `energy`. Card-level rules (tutors, lords, enchantress payoffs) still fire when relevant cards are present.

---

## Phase 3 — complete

All five Phase 3 items shipped 2026-05-30. Summary:

| # | Item | Status |
| --- | --- | --- |
| 1 | Build-time legality filters (903.5d, land/nonland) | **Done** |
| 2 | Slot pool quality (oracle guards, tag relaxation) | **Done** |
| 3 | `.deck.json` reload / `--refill-slot` | **Done** |
| 4 | Availability scoring, `--prefer-available`, unpriced classification | **Done** |
| 5 | v1 success criteria closure | **Done** — 142 automated tests |

Details and acceptance criteria remain in the sections below for reference.

### 1. Build-time legality filters — **Done**

Pool queries and post-filters enforce 903.5d land colors and land/nonland slot separation. Optional post-validation repair for illegal cards was deferred — fill-time filters hold.

### 2. Slot pool quality — **Done**

Graduated tag relaxation, oracle guards, and slot-specific scoring reduce misfills when tagged pools are thin. Re-import after taxonomy changes to refresh `card_mechanic_tags`.

### 3. `.deck.json` reload workflow — **Done**

```bash
mtg-deck-tools generate --from output/dragonlord-dromoka-....deck.json
mtg-deck-tools generate --from deck.deck.json --refill-slot synergy --seed 42
```

### 4. Unpriced / availability handling — **Done**

Policy in [08-card-availability.md](08-card-availability.md). Wizard step 5 defaults to strict + prefer-available when a budget is set.

### 5. v1 success criteria closure — **Done**

Checked off all items in [01-goals-and-scope.md](01-goals-and-scope.md) after dogfood pass (five commanders, varied budgets, `seed=42`).

---

## Dependency engine — complete (D0–D5)

Shipped 2026-05-30 / 2026-05-31. Technical phases in [10-card-dependency-engine.md](10-card-dependency-engine.md); pre-implementation gate in [12-dependency-engine-pre-implementation-checklist.md](12-dependency-engine-pre-implementation-checklist.md).

| Phase | Deliverable | CLI / module |
| --- | --- | --- |
| **D0** | Pattern spec + golden tests | `config/effect-patterns.yaml`, `effects/extract.py` |
| **D0.5** | Inventory audit | `mtg-deck-tools dependency-audit` |
| **D1** | Import writes `card_effects` | `import` command |
| **D2** | Post-build report (warn default) | **Deck dependencies** in MD/JSON |
| **D3** | Pick-time scoring | `dependency_scoring.py`, `scorer.py` |
| **D4** | Strict pick-time filter | `--strict-dependencies` |
| **D5** | Post-build repair swaps | `--repair-dependencies` |

**v1 rules:** `TUTOR_TARGET_EXISTS`, `ENERGY_BALANCE`, `EXPERIENCE_BALANCE`, `BLOOD_BALANCE`, `PLUS_ONE_BALANCE`, `SACRIFICE_BALANCE`, `TOKEN_BALANCE`, `VEHICLE_BALANCE`, `EQUIPMENT_BALANCE`, `TYPE_SYNERGY_MIN`, `AURA_SUPPORT_MIN`, `ENCHANTMENT_SUPPORT_MIN`, `REANIMATION_SUPPORT`, `GRAVEYARD_COST_SUPPORT`, `SELF_MILL_BALANCE`, `LANDFALL_BALANCE` — thresholds in [`config/dependency-profiles.yaml`](../config/dependency-profiles.yaml).

**Mechanic packages:** energy, experience, blood, +1/+1 counters, sacrifice/aristocrats, auras, artifacts, subtype lords, tokens, vehicles, equipment — see [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) for shipped inventory.

**Maintainer workflow:** After bulk refresh, run `import` then `dependency-audit` to refresh `card_effects` and audit reports. Run `analyze run --fail-on-expect` after dependency changes.

---

## Active work — dependency expansion and UX

Recommended order:

### ~~0. Dogfood matrix — fix scenario failures~~ **Done (2026-06-03)**

Restored **25/25** on `analyze run --fail-on-expect` after 2026-06 Scryfall bulk refresh:

| Scenario | Fix |
| --- | --- |
| `blood-yawgmoth` | Extended `blood_consume` extraction (remove/spend/for-each on permanent); cards like Font of Agonies now produce **and** consume |
| `elves-lathril` | Raised `plus_one` `incidental_imbalance_min` to 5 so token elf shells ignore ≤4 incidental +1/+1 producers |

### ~~1. Rad / oil / charge counters~~ **Done (2026-06-03)**

Shipped `rad_*`, `oil_*`, `charge_*` effect atoms; `RAD_BALANCE`, `OIL_BALANCE`, `CHARGE_BALANCE`; profiles in `dependency-profiles.yaml`; wizard `include_mechanics: [rad, oil, charge]`. Dogfood: `rad-mothman`, `oil-migloz`, `charge-immard`. Post-import: **13,070** effect atoms (+486 vs prior import).

### ~~1. Dependency expansion (high-value additions)~~ **Done**

Full analysis: **[15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md)**. Priority 1–6 expansion items are shipped.

**Suggested next task (UX):** **UX5** local web dependency dashboard ([11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md)).

**Suggested next task (dependency):** None — dependency expansion sequence complete through Priority 8; next dependency work is backlog-driven (see doc 15 non-goals).

**Recently shipped (2026-06):** **UX3** criteria linter (end-of-wizard preflight: include/avoid overlap, avoid vs activated profiles/focus, voltron+avoid equip, tokens+aristocrats theme stack, too many focused profiles, over-constrained budget); **Token subtype buffs** (`TOKEN_SUBTYPE_BUFF_SUPPORT`, `token_buff_subtype`, subtype capture on `token_produce`; dogfood `treasure-prosper`); **Graveyard filler atoms** (`mill_enabler_surveil_discover`, `graveyard_filler_discard`; dogfood `surveil-mirko`); **UX2** wizard synergy step (`strict_dependencies`, `repair_dependencies`, optional `mechanic_focus` for all activated profiles); **Equipment depth** (`EQUIPMENT_BALANCE`, `ensure_equipment_package`, `type_line_equipment`, `whenever_equipped`; profile `equipment`); **Rad / oil / charge counters** (`RAD_BALANCE`, `OIL_BALANCE`, `CHARGE_BALANCE`; `include_mechanics: [rad, oil, charge]`); **Graveyard / landfall heuristics** (`REANIMATION_SUPPORT`, `GRAVEYARD_COST_SUPPORT`, `SELF_MILL_BALANCE`, `LANDFALL_BALANCE`; `graveyard` / `landfall` profiles; `rules/graveyard_landfall.py`); **Sacrifice / token refinements** (`sacrifice_opponent`, `death_recursion`, aristocrats fodder counts `token_produce`, shared role helpers in `sacrifice_roles.py`); **Resource counters** (`EXPERIENCE_BALANCE`, `BLOOD_BALANCE`, `PLUS_ONE_BALANCE`, `include_mechanics: [experience, blood, counters]`); **Tutor payload upgrades** (CMC min/max, colored creatures, land subtypes, multi-type OR, creature-or-planeswalker); **Enchantment matters** (`ENCHANTMENT_SUPPORT_MIN`, `whenever_cast_enchantment`, wizard `themes: [enchantress]`); **Subtype lord generalization** (`TYPE_SYNERGY_MIN`, `subtype_lords` profile); **Tokens package** (`TOKEN_BALANCE`); **Vehicles profile** (`VEHICLE_BALANCE`).

Each feature: patterns → import → rule → optional package → dogfood scenario (checklist in doc 15). **Doc updates:** [DOC-MAP.md](DOC-MAP.md); agents run `/ship-dependency-feature` before PR.

### ~~2. UX2 — wizard synergy controls~~ **Done**

Shipped wizard **step 3** (synergy & dependencies): `strict_dependencies`, `repair_dependencies`, optional `mechanic_focus` presets (incidental/supported/focused/engine) for every profile activated in steps 1–2. Criteria summary shows dependency settings. See [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md).

### ~~3. UX3 — criteria linter~~ **Done (2026-06-04)**

Shipped end-of-wizard **criteria preflight** (`rules/criteria_linter.py`, `wizard/preflight.py`): warn-only checks for include/avoid overlap, avoid vs activated dependency profiles or `mechanic_focus`, voltron + avoid equip, tokens + aristocrats theme stack, more than two focused/engine profiles, and strict budget + rare minimum + three focused profiles. User confirms before the criteria summary. See [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md).

### 4. Graveyard filler dependency enhancement (Priority 7) — **planned**

Extend graveyard **enabler** extraction so dependency balancing sees cards that fill the yard without explicit “mill” or “put top … of library” wording.

| Item | Notes |
| --- | --- |
| **Surveil / discover** | Not referenced in repo; do not match current `mill_enabler` regex |
| **`SELF_MILL_BALANCE`** | Only compares `mill_enabler` vs `graveyard_payoff` when `graveyard` profile active (`themes: [recursion]`) |
| **Delivery** | Patterns → import → graveyard role collection / balance rules → dogfood scenario; optional post-fill package only if needed |
| **Spec** | [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) § Priority 7 |

### 3. Rule scoping and threshold tuning — **mostly done**

- ☑ Scope deck-level profile rules to themes / `include_mechanics` / `mechanic_focus` (`rules/dependency_scope.py`, `activation` in `dependency-profiles.yaml`)
- ☑ Suppress `ENERGY_BALANCE` for a lone incidental producer unless user includes `energy` or has 2+ imbalanced cards
- ☑ Sacrifice profile + `SACRIFICE_BALANCE` for aristocrats intent
- ☑ `whenever_cast_aura` — enchantment payoffs no longer trigger voltron aura floor
- ☑ Dogfood matrix — 28 scenarios; `analyze run --fail-on-expect` gate (**28/28** as of 2026-06-03 rad/oil/charge ship)
- ☐ Threshold review against latest audit evidence when adding new profiles (doc 15)

---

## Backlog (post–dependency v1)

| Topic | Notes | Doc |
| --- | --- | --- |
| Progressive wizard/build constraints | Parked UX6 — restrict choices by CI/commander/partial deck | [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) § Progressive constraints |
| Dependency swap packages | `generate --swap-profile energy` — needs UX5 or CLI design | [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) |
| Power level / salt | No simple dial; needs richer model | [06-open-questions.md](06-open-questions.md) |
| Moxfield / Archidekt export | Translate from `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| **Related token companion list** | MD + `.deck.json` section: tokens linked to the built deck via `all_parts`; **not** in the 100-card count; acquisition aid | [07-deck-output-format.md](07-deck-output-format.md) § Related token cards |
| **Deck composition metrics (UX8)** | CMC distribution report/visualization in MD/JSON; optional curve advisories; charts in UX5 | [07-deck-output-format.md](07-deck-output-format.md) § Deck composition metrics; [11](11-dependency-engine-user-experience.md) § UX8 |
| **GUI deck editor (UX9)** | **Swap** selected card(s) under current build rules; **lock** flag so refills/regen do not replace pinned cards | [11](11-dependency-engine-user-experience.md) § UX9; [07](07-deck-output-format.md) § GUI deck editor |
| Local web / desktop UI | Reuse Python core; dependency dashboard, deck metrics (UX8), swap/lock editor (UX9) | [06-open-questions.md](06-open-questions.md) |
| Image gallery / diff | Utility ops on `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Parquet / faster import | Only if import time hurts | [05-technology-options.md](05-technology-options.md) |
| DFC / adventure normalization | Risk in [03-problem-decomposition.md](03-problem-decomposition.md) | Import layer |
| Post-validation CR repair | Swap illegal cards after validate | Deferred — fill-time filters sufficient today |
| **Token subtype buffs (Priority 8)** | Capture token type on `token_produce`; buff atoms for “Angel/Treasure/Goblin … tokens”; warn/package when makers lack matching payoffs — generic `TOKEN_BALANCE` only today | [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) § Priority 8 |

---

## Suggested next task

**UX5** local web dependency dashboard ([11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md)). UX3 criteria linter shipped 2026-06-04 (wizard preflight after step 7). UX2 wizard synergy controls shipped 2026-06-03 (step 3: strict/repair flags + `mechanic_focus` for activated profiles).

**Dependency (next enhancement):** [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md) **Priority 7** — surveil, discover, and other graveyard-filler patterns for `SELF_MILL_BALANCE` (engineering sequence item **3** in doc 15). **Priority 8** — token subtype buffs (sequence item **4**).

Dogfood regression: `mtg-deck-tools analyze run --fail-on-expect` — **28/28** ([14-deck-analysis.md](14-deck-analysis.md), [`config/dogfood-matrix.yaml`](../config/dogfood-matrix.yaml)).

See [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) for the UX roadmap (UX5 local web → UX6 progressive constraints).
