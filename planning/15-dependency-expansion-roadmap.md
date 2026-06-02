# Dependency engine — expansion roadmap (post D0–D5)

Status as of 2026-06-02. **D0–D5 is shipped** (validate, score, strict filter, repair, mechanic packages). This doc captures **what runs today**, **candidate effect atoms and rules**, and a **suggested build order** for the next dependency work.

Related: [10-card-dependency-engine.md](10-card-dependency-engine.md) (architecture), [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) (UX knobs), [`config/effect-patterns.yaml`](../config/effect-patterns.yaml), [`config/dependency-profiles.yaml`](../config/dependency-profiles.yaml), [`resources/dependency/hard-cases.yaml`](../resources/dependency/hard-cases.yaml).

---

## How dependencies participate in deck build

```mermaid
flowchart TD
  Import["import → card_effects"]
  Fill["slot fill + dependency_scoring"]
  Packages["ensure_included_mechanic_packages"]
  Validate["validate_dependencies"]
  Repair["repair_dependency_issues optional"]
  Import --> Fill --> Packages --> Validate
  Validate --> Repair
```

1. **Import** — `effect-patterns.yaml` → `card_effects` (required; rules no-op if table empty).
2. **Pick time (D3/D4)** — `dependency_scoring.py` biases or excludes candidates using partial-deck stats.
3. **Post-fill packages** — `mechanic_packages.py` swaps cards to meet profile floors when user intent or card-driven rules apply.
4. **Post-build (D2/D5)** — `validate_dependencies` emits warnings; `--repair-dependencies` attempts targeted swaps.

**Theme tags** (`card_mechanic_tags`) drive slot scoring and taxonomy; **dependency rules** primarily use **oracle-derived atoms**, not tags alone.

---

## Shipped inventory (2026-06-02)

### Effect kinds in `card_effects`

| `effect_kind` | Role |
| --- | --- |
| `search_library` | Tutor / search predicates (land, creature, artifact, enchantment, aura, CMC cap, any card) |
| `energy_produce` / `energy_consume` | Energy counter balance |
| `sacrifice_outlet` / `sacrifice_payoff` / `sacrifice_fodder` | Aristocrats package roles |
| `buff_subtype` | “Other Elves …” (and similar) subtype lords |
| `whenever_cast_type` | “Whenever you cast an Artifact spell …” |
| `whenever_cast_aura` | “Whenever you cast an Aura spell …” (voltron / aura support trigger) |
| `type_line_aura` | Aura on type line (extraction aid) |
| `token_produce` / `token_payoff` | Token producers vs “whenever you create a token” payoffs |
| `type_line_vehicle` | Vehicle on type line (crew density checks) |

### Validation rules (`rule_id`)

| Rule | Trigger | Scoped by |
| --- | --- | --- |
| `TUTOR_TARGET_EXISTS` | Tutor with zero matching targets in deck + commander pool | Always (card-driven) |
| `ENERGY_BALANCE` | Producers without consumers or reverse | `include_mechanics: [energy]` or ≥2 imbalanced cards |
| `SACRIFICE_BALANCE` | Outlets without payoffs or reverse | `themes: [aristocrats]` or ≥2 imbalanced cards |
| `TOKEN_BALANCE` | Producers without payoffs or reverse | `themes: [tokens]` or ≥2 imbalanced cards |
| `VEHICLE_BALANCE` | Vehicle count or crew creatures below floor | `include_mechanics: [vehicles]`, Vehicle lord in deck, or ≥2 vehicles |
| `TYPE_SYNERGY_MIN` | Subtype lord or type-matters payoff below suggested minimum | Card-driven (lord / cast trigger in deck) |
| `AURA_SUPPORT_MIN` | Aura count below floor | `themes: [voltron]`, aura tutors, or `whenever_cast_aura` payoffs |

### Mechanic packages (post-fill swaps)

| Package | Activation | Floors (defaults) |
| --- | --- | --- |
| Energy | `include_mechanics: [energy]` | ≥2 producers, ≥2 consumers |
| Sacrifice / aristocrats | `themes: [aristocrats]` | ≥2 outlets, ≥3 payoffs, ≥8 fodder |
| Auras | Voltron theme or card-driven aura check | ≥6 Aura spells |
| Artifacts | `include_mechanics: [equip, vehicles]` or artifact cast payoff in deck | ≥8 artifacts |
| Subtype lords | Any `buff_subtype` lord detected | Per-subtype minimums in profile (Elf default 5) |
| Tokens | `themes: [tokens]` | ≥5 producers, ≥3 payoffs |
| Vehicles | `include_mechanics: [vehicles]` or Vehicle lord in deck | ≥3 Vehicles, ≥25 crew creatures |

### Dogfood coverage

[`config/dogfood-matrix.yaml`](../config/dogfood-matrix.yaml) — **22 scenarios** (tokens, voltron, energy, elves, artifacts, aristocrats, landfall, goblins, vampires, enchantress, budget, strict/repair). Run: `mtg-deck-tools analyze run --fail-on-expect` after import.

---

## High-value additions (recommended next)

Each row follows the same delivery pattern: **patterns → import → rule → optional package → profile activation → dogfood scenario**.

### Priority 1 — Extend existing atoms (lowest risk)

| Work item | New / extended atoms | Rule / package | Activation | Notes |
| --- | --- | --- | --- | --- |
| ~~**Generic subtype lords**~~ | Extend `buff_subtype` capture (Goblin, Vampire, Dragon, Pirate, …) | Per-subtype floors in `subtype_lords` profile; lord package runs for any lord | Card-driven + optional tribal themes | **Shipped 2026-06** — per-subtype minimums (Elf, Goblin, Vampire, Pirate, Zombie, Dragon); Krenko/Edgar dogfood |
| ~~**Tokens package**~~ | `token_produce`, `token_payoff` | `TOKEN_BALANCE` | `themes: [tokens]` | **Shipped 2026-06** |
| ~~**Vehicles profile**~~ | `type_line_vehicle` + crew creature count | `VEHICLE_BALANCE` | `include_mechanics: [vehicles]` | **Shipped 2026-06** — `vehicle_min: 3`, `creature_min: 25` |
| **Enchantment matters** | `whenever_cast_enchantment` (non-Aura) | Enchantment density floor separate from `AURA_SUPPORT_MIN` | Enchantress commanders / `themes` TBD | Sythis dogfood scenario guards against voltron aura noise; package could still add enchantments |

### Priority 2 — Tutor payload upgrades

Extend `search_library` payload matching (see gaps in [`hard-cases.yaml`](../resources/dependency/hard-cases.yaml)):

| Gap | Example cards | Build impact |
| --- | --- | --- |
| **CMC bands** | “MV 6 or greater”, “X or less” beyond current capture | Stronger `TUTOR_TARGET_EXISTS` |
| **Color in search** | Green Sun’s Zenith | Identity-aware target pool |
| **Named basic / subtype land** | Nature’s Lore, Three Visits (“Forest”) | Land subtype in payload |
| **Multi-type tutors** | Finale of Devastation (creature or planeswalker) | Union target matching |
| **Named card search** | “Search for a card named …” | New `REQUIRES_CARD` rule (high severity, rare) |
| **`any_card` tutors** | Demonic Tutor, Gamble | Keep soft warn / low confidence (already `search_any`) |

### Priority 3 — Resource counters (energy-shaped profiles)

| Resource | Detection sketch | Profile idea | Audit stance |
| --- | --- | --- | --- |
| **+1/+1 / proliferate** | “proliferate”, “put a +1/+1 counter” | Producer vs payoff balance | `defer_counters` (Atraxa) |
| **Experience** | “experience counter” | Consumers need producers | — |
| **Blood** | Blood counter text | Yawgmoth-style | `defer_blood` |
| **Rad, oil, charge** | Format-specific regex sets | Theme-selected only | Lower priority |

Same implementation shape as energy: `*_produce` / `*_consume` kinds, `*_BALANCE` rule, `ensure_*_package`, `dependency-profiles.yaml` activation.

### Priority 4 — Sacrifice / tokens refinements

| Work item | Purpose |
| --- | --- |
| Token producers vs aristocrats fodder | `sacrifice_fodder` uses “create … token”; token *payoffs* are a separate axis |
| Opponent-sacrifice effects | Grave Pact-style — optional tag or pattern, not outlet |
| Persist / undying / escape | Death triggers without full aristocrats package |

### Priority 5 — Graveyard / landfall (warn-only first)

Planning doc [10](10-card-dependency-engine.md) §5: **soft dependencies** — deck composition + curve, not pure regex.

| Archetype | Heuristic | Strict package? |
| --- | --- | --- |
| **Reanimation** | “Return … from graveyard” + creature density / CMC | Warn first |
| **Delve / escape / flashback** | Nonland count in graveyard over time | Warn first |
| **Self-mill** | Mill enablers vs graveyard payoffs | Warn first |
| **Landfall** | Land ramp count vs landfall payoffs | Warn when `themes: [landfall]`; matrix today only checks “no unrelated noise” |

### Priority 6 — Equipment depth

Beyond artifact count: equip cost, “whenever equipped”, bodies to carry equipment — overlaps vehicles/ voltron; profile under `equip` / `voltron`.

---

## Explicit non-goals (stay out of `card_effects` for now)

| Concern | Why deferred | Where handled today |
| --- | --- | --- |
| Removal / wipe density | Slot template, not oracle atoms | `slot-templates.yaml`, themes |
| Curve / land count | Mana base planner | `mana_base.py`, validation |
| Named combo pairs | Needs external combo data | — |
| Power level / salt | No simple dial | [06-open-questions.md](06-open-questions.md) |
| Aura removal risk | Not statically provable | UX note in [11](11-dependency-engine-user-experience.md) |
| Commander partners / companion | Construction layer | `validate.py`, commander pick |
| In-game timing / stack | Non-goal per [10](10-card-dependency-engine.md) | — |

---

## Implementation checklist (per feature)

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

Aligned with [09-next-steps.md](09-next-steps.md) and dogfood matrix coverage:

| Order | Deliverable | Rationale |
| --- | --- | --- |
| 1 | **Enchantment matters profile** | Sythis / enchantress without conflating auras |
| 2 | **Tutor payload upgrades** | Incremental `TUTOR_TARGET_EXISTS` accuracy |
| 3 | **Graveyard / landfall heuristics** | Warn-only rules before packages |
| 4 | **Counter resources** | After audit evidence (proliferate, blood, …) |

**Shipped (2026-06):** Subtype lord generalization (`TYPE_SYNERGY_MIN`, `ensure_subtype_lord_packages`, `subtype_lords` profile); Tokens package (`TOKEN_BALANCE`); Vehicles profile (`VEHICLE_BALANCE`, crew density).

**Parallel track:** **UX2** wizard controls for `strict_dependencies`, `repair_dependencies`, and `mechanic_focus` ([11](11-dependency-engine-user-experience.md)) — does not block pattern work but improves user-facing control.

---

## References

- Deferred card stances: [`resources/dependency/hard-cases.yaml`](../resources/dependency/hard-cases.yaml) (`v1_stance`: `defer_tokens`, `defer_vehicles`, `defer_graveyard`, `defer_counters`, …)
- Profile thresholds: [`config/dependency-profiles.yaml`](../config/dependency-profiles.yaml)
- Automated regression: [14-deck-analysis.md](14-deck-analysis.md)
- Locked v1 scope: [13-dependency-engine-decisions.md](13-dependency-engine-decisions.md)
