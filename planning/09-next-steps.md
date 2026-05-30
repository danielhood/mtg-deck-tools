# Next steps — post-v1

Status as of 2026-05-30. Phase 1, Phase 2, v1 polish, and **Phase 3 §1** are **shipped**. Recent dogfooding (Dragonlord Dromoka, Jetmir, Pantlaza, Yawgmoth at `$150`, `seed=42`) confirms validation passes after build-time legality filters.

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
| `.deck.json` reload / edit workflow | **Not started** |
| Post-validation repair pass | **Not started** — illegal picks are prevented at fill time; no swap-after-validate |
| Slot pool quality (themed slot misfills) | **Partial** — oracle guards and graduated relaxation shipped; re-import needed for taxonomy tag refresh |
| Unpriced / availability handling | **Partial** — per-card max helps; null-price cards still allowed by default |

## Dogfooding snapshot

Latest outputs: `output/jetmir-nexus-of-revels-20260530000000.md`, `output/dragonlord-dromoka-20260529235137.md`

| Area | Result |
| --- | --- |
| Validation (903.5d) | **PASSED** — Command Tower no longer appears in W/G ramp; land color filtering at pool fill works |
| Budget trim | **Works** — Jetmir `$78.39` vs `$150` cap with `$5` per-card max |
| Per-card price range | **Works** — wizard step 5 and MD header show min/max when set |
| Unpriced cards | Still present — Jetmir: 4 null-price cards with budget warning |
| Slot quality | **Still weak** — Jetmir `board_wipe`: Worldslayer (equipment); Dromoka ramp/draw slots mix on-theme and filler bulk |
| MD output | Card names show type line; commander/details/maindeck linked to Scryfall; friendly dates and color names |

These point to **slot pool quality** as the next highest-signal gap.

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

### 2. Slot pool quality — **Partial (shipped core)**

Graduated tag relaxation, oracle guards, and slot-specific scoring reduce misfills when tagged pools are thin.

| Slot | Fix shipped |
| --- | --- |
| `board_wipe` | Tighter taxonomy matcher; oracle guard rejects equipment triggers (e.g. Worldslayer) |
| `wincon` | Themed fallback step before untagged pool; penalize unpriced cards when budget set |
| `flex` | Prefer deck `themes` before falling back to any nonland |
| `ramp` | Oracle guard excludes lands and off-theme picks from relaxed pool |

**Remaining:** Re-run `import` to refresh tags from updated taxonomy; expand `wincon` taxonomy further; slot-specific oracle guards for `draw`/`removal`.

**Acceptance:** Board wipe and wincon slots contain on-theme, priced cards for a standard GW voltron/landfall list.

### 3. `.deck.json` reload workflow

Planned in [07-deck-output-format.md](07-deck-output-format.md) but not implemented. Enables the review loop in [01-goals-and-scope.md](01-goals-and-scope.md).

```powershell
# Proposed
mtg-deck-tools generate --from output/dragonlord-dromoka-....deck.json
mtg-deck-tools generate --from deck.json --refill-slot synergy --seed 42
```

| Step | Scope |
| --- | --- |
| Load criteria + commanders from `.deck.json` | Read `criteria`, `commanders`, optional `seed` |
| Regenerate full deck | Skip wizard; call `run_generate` with loaded criteria |
| Regenerate one slot (later) | Keep other slots fixed; refill one template slot |

**Acceptance:** User can tweak `budget_usd`, `card_price_max_usd`, or `themes` in JSON and regenerate without re-running the wizard.

### 4. Unpriced / availability handling

Policy is documented in [08-card-availability.md](08-card-availability.md). Per-card max (`card_price_max_usd`) reduces expensive picks but null-price cards still slip through.

| Step | Scope | Status |
| --- | --- | --- |
| **Per-card price range** | Wizard step 5 + CLI + fill-time filter | **Done** |
| **`--strict-budget` in wizard** | Offer during step 5 or as generate default when budget set | Not started |
| **Availability score at import** | `released_at`, `edhrec_rank`, `reprint`, `set_type` → score column | Not started |
| **Output classification** | Label null-price cards as `likely_obscure` vs `price_pending` in notes | Not started |
| **`--prefer-available`** | Optional filter excluding bottom-quartile availability | Not started |

**Acceptance:** Budget builds default to priced, obtainable cards; obscure null-price picks are rare or flagged.

### 5. v1 success criteria closure

Check off [01-goals-and-scope.md](01-goals-and-scope.md) after a short dogfood pass (3–5 commanders, varied budgets). Core generation, validation, budget, and output are working; remaining gaps are slot quality and reload workflow.

---

## Backlog (post–Phase 3)

| Topic | Notes | Doc |
| --- | --- | --- |
| Power level / salt | No simple dial; needs richer model | [06-open-questions.md](06-open-questions.md) |
| Moxfield / Archidekt export | Translate from `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Local web / desktop UI | Reuse Python core | [06-open-questions.md](06-open-questions.md) |
| Image gallery / diff | Utility ops on `.deck.json` | [07-deck-output-format.md](07-deck-output-format.md) |
| Parquet / faster import | Only if import time hurts | [05-technology-options.md](05-technology-options.md) |
| DFC / adventure normalization | Risk in [03-problem-decomposition.md](03-problem-decomposition.md) | Import layer |

---

## Suggested next task

**Start with Phase 3 §3 (`.deck.json` reload).** Slot pool quality guards are in place; re-import the card database to pick up taxonomy changes, then dogfood again.

After that: unpriced/availability policy (§4).
