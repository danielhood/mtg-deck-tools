# Next steps — post-v1

Status as of 2026-05-30. **v1 is complete.** Phase 1, Phase 2, v1 polish, and **Phase 3 (§1–§5)** are **shipped**. Dogfood pass (`seed=42`, five commanders, varied budgets) confirms validation, budget, reload, and output polish — see [01-goals-and-scope.md](01-goals-and-scope.md#v1-closure-2026-05-30).

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
| Post-validation repair pass | **Not started** — illegal picks are prevented at fill time; no swap-after-validate |
| Slot pool quality (themed slot misfills) | Done |
| Unpriced / availability handling | Done |

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

---

## Phase 3 — recommended order

### 1. Build-time legality filters — **Done**

Shipped in `a8f2894`. Pool queries and post-filters now enforce:

| Issue | Fix |
| --- | --- |
| **903.5d land colors** | `land_produces_only_identity()` filters land candidates to commander identity |
| **Land vs nonland slot bleed** | `is_land_card()` + tightened SQL/post-filter excludes lands from nonland slots |
| **Budget trim on lands** | Same identity checks applied during replacement search |

**Acceptance met:** Dromoka W/G at `$150` produces validation **PASSED** without manual edits.

**Deferred:** Optional post-validation repair (swap illegal cards after validate) — not needed while fill-time filters hold.

### 2. Slot pool quality — **Done**

Graduated tag relaxation, oracle guards, and slot-specific scoring reduce misfills when tagged pools are thin. Re-import after taxonomy changes to refresh `card_mechanic_tags`.

| Slot | Fix |
| --- | --- |
| `board_wipe` | Tighter taxonomy matcher; oracle guard rejects equipment triggers (e.g. Worldslayer) |
| `wincon` | Expanded taxonomy; themed fallback; penalize unpriced cards when budget set |
| `draw` / `removal` | Oracle guards reject ramp rocks and mass removal in single-target slots |
| `flex` | Prefer deck `themes` before falling back to any nonland |
| `ramp` | Oracle guard excludes lands and off-theme picks from relaxed pool |

**Acceptance:** Board wipe and wincon slots contain on-theme, priced cards for a standard GW voltron/landfall list.

### 3. `.deck.json` reload workflow — **Done**

Reload criteria and commanders from a saved `.deck.json`, regenerate the full maindeck, or refill a single slot.

```bash
mtg-deck-tools generate --from output/dragonlord-dromoka-....deck.json
mtg-deck-tools generate --from deck.deck.json --refill-slot synergy --seed 42
```

| Step | Scope | Status |
| --- | --- | --- |
| Load criteria + commanders from `.deck.json` | Read `criteria`, `commanders`, optional `seed` | **Done** |
| Regenerate full deck | Skip wizard; call `run_generate_from_deck` | **Done** |
| Regenerate one slot | `--refill-slot` keeps other slots fixed | **Done** |

**Acceptance:** User can tweak `budget_usd`, `card_price_max_usd`, or `themes` in JSON and regenerate without re-running the wizard.

### 4. Unpriced / availability handling — **Done**

Policy in [08-card-availability.md](08-card-availability.md). Import computes `availability_score` and stores `availability_p25` for filtering.

| Step | Scope | Status |
| --- | --- | --- |
| **Per-card price range** | Wizard step 5 + CLI + fill-time filter | **Done** |
| **`--strict-budget` in wizard** | Step 5 prompts when budget set (default: exclude unpriced) | **Done** |
| **Availability score at import** | `released_at`, `edhrec_rank`, `reprint`, `set_type` → `availability_score` | **Done** |
| **Output classification** | Notes group + stats: `likely_obscure` vs `price_pending` | **Done** |
| **`--prefer-available`** | Filter below import-time p25; wizard default when budget set | **Done** |

**Acceptance:** Budget wizard runs default to strict + prefer-available; null-price cards are classified in Notes; re-import refreshes scores.

### 5. v1 success criteria closure — **Done**

Checked off all items in [01-goals-and-scope.md](01-goals-and-scope.md) after dogfood pass (five commanders, varied budgets, `seed=42`).

| Commander | Budget | Validation | Notes |
| --- | ---: | --- | --- |
| Dragonlord Dromoka | $150 / $5 max | **PASSED** | GW landfall + voltron |
| Jetmir, Nexus of Revels | $150 / $5 max | **PASSED** | Naya voltron |
| Pantlaza, Sun-Favored | $75 / $3 max, strict | **PASSED** | Tight budget + prefer-available |
| Yawgmoth, Thran Physician | $150 / $5 max | **PASSED** | Mono-B aristocrats |
| Dragonlord Dromoka | none | **PASSED** | Uncapped sanity check |

**Acceptance met:** All v1 success criteria satisfied; 116 tests passing; `.deck.json` reload workflow verified.

---

## Backlog (post–Phase 3)

| Topic | Notes | Doc |
| --- | --- | --- |
| Card dependency engine | Tutor targets, type payoffs, energy produce/consume balance; preprocess + validate | [10-card-dependency-engine.md](10-card-dependency-engine.md) |
| Dependency UX / control model | Focus presets, producer/consumer bands, feedback, swap workflow; `dependency-profiles.yaml` | [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) |
| Power level / salt | No simple dial; needs richer model | [06-open-questions.md](06-open-questions.md) |
| Moxfield / Archidekt export | Translate from `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Local web / desktop UI | Reuse Python core | [06-open-questions.md](06-open-questions.md) |
| Image gallery / diff | Utility ops on `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Parquet / faster import | Only if import time hurts | [05-technology-options.md](05-technology-options.md) |
| DFC / adventure normalization | Risk in [03-problem-decomposition.md](03-problem-decomposition.md) | Import layer |

---

## Suggested next task

**Start with the card dependency engine** — tutor targets, type payoffs, and resource-balance checks. See [10-card-dependency-engine.md](10-card-dependency-engine.md).
