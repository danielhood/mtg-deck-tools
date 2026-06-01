# Next steps — post-v1

Status as of 2026-05-31. **v1 is complete.** Phase 1, Phase 2, v1 polish, **Phase 3 (§1–§5)**, and the **card dependency engine (D0–D5)** are **shipped**. Dogfood pass (`seed=42`, five commanders, varied budgets) confirms validation, budget, reload, and output polish — see [01-goals-and-scope.md](01-goals-and-scope.md#v1-closure-2026-05-30).

## Current state

| Milestone | Status |
| --- | --- |
| Oracle import + mechanic tags + SQLite | Done |
| Wizard (steps 1–5) | Done |
| Slot-filled 99-card generation | Done |
| Dynamic mana base | Done |
| Commander validation (CR 903 / 702.124) | Done |
| Budget enforcement + trim pass | Done |
| `--strict-budget` | Done (CLI flag; wizard references it at generate time) |
| Per-card USD price min/max | Done — wizard step 5 + `--card-price-min` / `--card-price-max` |
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
| Wizard dependency controls (UX2) | **Not started** — CLI flags only today |
| Dependency dogfood calibration | **In progress** — automated `analyze run`; full-matrix pass after `import` |

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
| Strict / repair flags | Available via CLI; not yet exposed in wizard |

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

**v1 rules:** `TUTOR_TARGET_EXISTS`, `ENERGY_BALANCE`, `TYPE_SYNERGY_MIN`, `AURA_SUPPORT_MIN` — thresholds in [`config/dependency-profiles.yaml`](../config/dependency-profiles.yaml).

**Maintainer workflow:** After bulk refresh, run `import` then `dependency-audit` to refresh `card_effects` and audit reports.

---

## Active work — dependency UX and calibration

Recommended order after D5:

### 1. Dogfood acceptance (dependency rules)

**Automated:** `mtg-deck-tools analyze run` (matrix: [`config/dogfood-matrix.yaml`](../config/dogfood-matrix.yaml), docs: [14-deck-analysis.md](14-deck-analysis.md)). Writes `output/analysis-*/summary.json` with false-positive rate and per-case JSON. Use `--fail-on-expect` in CI after import.

Manual spot-check optional per [12-dependency-engine-pre-implementation-checklist.md](12-dependency-engine-pre-implementation-checklist.md#dogfood-acceptance-after-d2):

| Scenario | Pass? |
| --- | --- |
| Land tutor deck — no “no land” false warn | ☐ |
| Energy producers, zero consumers — clear Energy note | ☐ |
| Elf lord, &lt;5 elves — warning with suggested minimum | ☐ |
| Enchantress / low aura count + aura tutor | ☐ |
| Goodstuff deck — no spam warnings from arbitrary thresholds | ☐ |

Set false-positive budget (e.g. &lt;5% warn rate on N hand-reviewed decks) before turning on strict mode by default.

### 2. UX2 — wizard synergy controls

From [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md):

- Wizard step or generate prompt for **synergy strictness** (`strict_dependencies`, `repair_dependencies`)
- **Focus presets** (`mechanic_focus`: energy, auras) wired to `dependency-profiles.yaml`
- Surface dependency summary during wizard review (optional)

### 3. Rule scoping and threshold tuning — **partial**

- ☑ Scope deck-level profile rules to themes / `include_mechanics` / `mechanic_focus` (`rules/dependency_scope.py`, `activation` in `dependency-profiles.yaml`)
- ☑ Suppress `ENERGY_BALANCE` for a lone incidental producer unless user includes `energy` or has 2+ imbalanced cards
- ☐ Review `AURA_SUPPORT_MIN` / `TYPE_SYNERGY_MIN` thresholds against audit evidence
- ☐ Optional: `SUBTYPE_SYNERGY_MIN` (e.g. Elf lords) — deferred in checklist

---

## Backlog (post–dependency v1)

| Topic | Notes | Doc |
| --- | --- | --- |
| Progressive wizard/build constraints | Parked UX6 — restrict choices by CI/commander/partial deck | [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) § Progressive constraints |
| Dependency swap packages | `generate --swap-profile energy` — needs UX5 or CLI design | [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) |
| Power level / salt | No simple dial; needs richer model | [06-open-questions.md](06-open-questions.md) |
| Moxfield / Archidekt export | Translate from `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Local web / desktop UI | Reuse Python core; dependency dashboard | [06-open-questions.md](06-open-questions.md) |
| Image gallery / diff | Utility ops on `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Parquet / faster import | Only if import time hurts | [05-technology-options.md](05-technology-options.md) |
| DFC / adventure normalization | Risk in [03-problem-decomposition.md](03-problem-decomposition.md) | Import layer |
| Post-validation CR repair | Swap illegal cards after validate | Deferred — fill-time filters sufficient today |

---

## Suggested next task

**Run `analyze run` on a fresh import** and confirm false-positive rate &lt; 5%, then **UX2 wizard controls** for `--strict-dependencies`, `--repair-dependencies`, and `mechanic_focus` presets. Threshold review against `dependency-audit` evidence remains optional follow-up.

See [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) for the UX roadmap (UX2 → UX3 criteria linter → UX5 local web).
