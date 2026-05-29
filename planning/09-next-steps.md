# Next steps — post-v1

Status as of 2026-05-29. Phase 1, Phase 2, and v1 polish are **shipped**. This doc captures what to do next, informed by dogfooding (Dragonlord Dromoka, `$150` cap, `seed=42`).

## Current state

| Milestone | Status |
| --- | --- |
| Oracle import + mechanic tags + SQLite | Done |
| Wizard (steps 1–5) | Done |
| Slot-filled 99-card generation | Done |
| Dynamic mana base | Done |
| Commander validation (CR 903 / 702.124) | Done |
| Budget enforcement + trim pass | Done |
| `--strict-budget` | Done |
| `.deck.json` reload / edit workflow | **Not started** |
| Build-time rule enforcement (pre-validation) | **Partial** — validate runs after fill; illegal cards can still be picked |

## Dogfooding snapshot

Latest output: `output/dragonlord-dromoka-20260529033745.md`

| Area | Result |
| --- | --- |
| Budget trim | **Works** — `$135.42` estimated vs `$150` cap; two swap notes |
| Validation | **FAILED** — Command Tower in ramp slot (903.5d: produces B/R/U outside W/G) |
| Unpriced cards | 15 cards at `$0` toward budget (wincon, flex, two nonbasic lands) |
| Slot quality | Board wipes slot has Nettlecyst / Ghost Ark (not wipes); wincon/flex are unpriced bulk |

These are the highest-signal gaps for Phase 3.

---

## Phase 3 — recommended order

### 1. Build-time legality filters (priority)

Validation currently runs **after** fill. Illegal picks should be excluded from the pool (or repaired before output).

| Issue | Example | Fix direction |
| --- | --- | --- |
| **903.5d land colors** | Command Tower in a W/G deck | Filter candidates by `produced_mana ⊆ identity` in pool queries and budget trim |
| **Land vs nonland slot bleed** | Command Tower listed under Ramp | Tighten `nonlands_only` SQL — `type_line = 'Land'` may bypass `NOT LIKE '% Land%'`; use `is_basic_land` + land type detection |
| **Post-validation repair** | Deck marked FAILED but still written | Optional: swap illegal cards after validate (mirror budget trim), or fail fast and re-fill |

**Acceptance:** `generate --wizard` for Dromoka W/G at `$150` produces validation **PASSED** without manual edits.

### 2. Slot pool quality

When tagged pools are thin, filler relaxes to “any nonland” and misfills slots.

| Slot | Symptom | Fix direction |
| --- | --- | --- |
| `board_wipe` | Stax / equipment instead of mass removal | Re-run `import` after taxonomy changes; add slot-specific oracle guards in scorer; avoid relaxing to untagged pool too early |
| `wincon` | Unpriced legacy cards | Expand `wincon` taxonomy; prefer priced cards when budget set; fall back to synergy-themed threats |
| `flex` | No theme tag requirement today | Light tag preference or “any theme overlap” scoring floor |
| `ramp` | Lands classified as ramp | Exclude all lands from nonland slots; consider `{T}: Add` artifact/enchantment ramp only |

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

**Acceptance:** User can tweak `budget_usd` or `themes` in JSON and regenerate without re-running the wizard.

### 4. Unpriced / availability handling

Policy is documented in [08-card-availability.md](08-card-availability.md). Dogfooding shows 15 unpriced cards inflating slot count while hiding real cost.

| Step | Scope |
| --- | --- |
| **`--strict-budget` in wizard** | Offer during step 5 or as generate default when budget set |
| **Availability score at import** | `released_at`, `edhrec_rank`, `reprint`, `set_type` → score column |
| **Output classification** | Label null-price cards as `likely_obscure` vs `price_pending` in notes |
| **`--prefer-available`** | Optional filter excluding bottom-quartile availability |

**Acceptance:** Budget builds default to priced, obtainable cards; obscure null-price picks are rare or flagged.

### 5. v1 success criteria closure

Check off [01-goals-and-scope.md](01-goals-and-scope.md) after a short dogfood pass (3–5 commanders, varied budgets). Remaining unchecked items mostly work; document known gaps (903.5d at fill time, unpriced cards).

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

**Start with Phase 3 §1 (build-time legality filters).** The Dromoka deck proves budget trim works but a single illegal land pick fails validation — fixing pool filters and land typing has the best ratio of user-visible improvement to scope.

After that: slot pool quality (§2), then `.deck.json` reload (§3).
