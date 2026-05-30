# Dependency engine — pre-implementation checklist

Gate for starting **D1+ engine code** (extraction, validation, scoring). Planning direction lives in [10-card-dependency-engine.md](10-card-dependency-engine.md) and [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md); this doc tracks **evidence and contracts** that must exist first.

**Product context:** Static oracle snapshot, used-card audience — [01-goals-and-scope.md](01-goals-and-scope.md), [02-data-sources.md](02-data-sources.md).

---

## How to use this checklist

| Status | Meaning |
| --- | --- |
| ☐ | Not started |
| ◐ | In progress |
| ☑ | Done — link PR, commit, or artifact path in notes column |

**Rule:** Do not merge D1 (import writes `card_effects`) until all items in **§ Must complete before D1** are ☑. **D0.5 complete; D1 implemented** — proceed to D2 (validator).

**Suggested order:** § Snapshot → § D0 → § D0.5 → § Decisions → § Output contract → then D1 → D2.

---

## Must complete before D1

### Static snapshot

| ☐ | Item | Notes / artifact |
| --- | --- | --- |
| ☑ | Oracle bulk file pinned for the team (`resources/scryfall/oracle-cards-<date>.json` or documented CI fetch) | [resources/scryfall/README.md](../resources/scryfall/README.md) — gitignored bulk |
| ☑ | `mtg-deck-tools import` run on that file → `data/cards.db` | Local `data/cards.db` (gitignored) |
| ☑ | Bulk date recorded in `import_metadata` (and noted in release/README) | `oracle-cards-20260530090316.json` |

### D0 — Spec and pattern contract

| ☐ | Item | Notes / artifact |
| --- | --- | --- |
| ☑ | `config/effect-patterns.yaml` skeleton with version field | `config/effect-patterns.yaml` |
| ☑ | Canonical **effect atom** schema (Pydantic models + `payload` JSON shape) | `src/mtg_deck_tools/models/effects.py` |
| ☑ | Pattern ID → `effect_kind` mapping documented | `config/effect-patterns.yaml` + [14-effect-extraction-face-policy.md](14-effect-extraction-face-policy.md) |
| ☑ | Face policy documented (per `face_index` vs merged oracle; align with `normalize.py`) | [14-effect-extraction-face-policy.md](14-effect-extraction-face-policy.md) |
| ☑ | **Golden tests:** ≥20 oracle texts → expected atoms (pass / warn-only / no atom) | `tests/fixtures/effect_golden.yaml`, `tests/test_effect_extraction.py` (20 cases) |
| ☑ | **Hard-case sample set:** ≥50 cards (modal DFC, adventure, choose-one, changeling, partner) reviewed manually | `resources/dependency/hard-cases.yaml` (50 cases, v1_stance) |

### D0.5 — Inventory audit

| ☐ | Item | Notes / artifact |
| --- | --- | --- |
| ☑ | `dependency-audit` command or maintainer script runs over commander-legal cards | `mtg-deck-tools dependency-audit` |
| ☑ | `reports/dependency-pattern-hits.json` (or committed under `resources/dependency/`) | `resources/dependency/reports/` (gitignored) |
| ☑ | `reports/dependency-profile-summary.json` — producer/consumer counts per profile | same |
| ☑ | `reports/tutor-predicates.csv` — clustered search constraints + frequencies | same |
| ☑ | False-positive review queue (top N unmatched / low-confidence hits) | `dependency-review-queue.json` (447 unmatched search) |
| ☑ | `dependency-profiles.yaml` updated with **evidence-based** defaults (counts in comments or companion JSON) | + `audit-evidence-20260530.json` |
| ☑ | Profiles with negligible pool size marked **deferred** or warn-only in doc 10/11 | `sacrifice` deferred in profiles YAML |

### Decisions locked (avoid D1 rework)

Record answers in [13-dependency-engine-decisions.md](13-dependency-engine-decisions.md).

| ☐ | Decision | Recommended v1 answer |
| --- | --- | --- |
| ☑ | Threshold source | `dependency-profiles.yaml`; optional theme multiplier later |
| ☑ | Tutor matching depth | Type/subtype + simple CMC; defer “nonbasic land”, “basic Plains” |
| ☑ | Commander as tutor target | Yes for creature/legendary searches where CI allows; document edge cases |
| ☑ | `strict_dependencies` default | **Off** until D2 false-positive rate reviewed |
| ☑ | Storage | `card_effects` + JSON `payload`; no `effect_predicates` table until needed |
| ☑ | Include mechanic vs `mechanic_focus` | Independent unless product decides otherwise |
| ☑ | Combined themed share cap | Defer to UX6 |

### Output contract (before D2, design before D1)

| ☐ | Item | Notes / artifact |
| --- | --- | --- |
| ☑ | `dependency_report` JSON schema documented in [07-deck-output-format.md](07-deck-output-format.md) | Optional field on schema 1.0 |
| ☑ | Markdown **Deck dependencies** Notes group format | Section + Notes bucket `dependencies` |
| ◐ | `.deck.json` schema bump plan (`1.0` vs `1.1`) for `dependency_preferences` / `mechanic_focus` | Deferred — criteria unchanged |
| ☑ | `generate --from` behavior when report fields absent | Report omitted when DB has no effects / not run |

### v1 rule scope (agreed set)

Agree the **first validator rules** to implement (suggest 4–6, not the full catalog):

| ☐ | Rule ID | Trigger | Default severity |
| --- | --- | --- | --- |
| ☑ | `TUTOR_TARGET_EXISTS` | `search_library` atom | warn |
| ☑ | `ENERGY_BALANCE` | energy producers in deck | warn |
| ☑ | `TYPE_SYNERGY_MIN` | type/subtype amplifier atoms | warn |
| ☑ | `AURA_SUPPORT_MIN` | aura cast / aura tutor (if audit justifies) | warn |
| ☐ | _(optional)_ `SUBTYPE_SYNERGY_MIN` | e.g. Elf lords | warn |
| ☐ | _(defer)_ graveyard / delve / escape | — | v2 |

| ☐ | **False-positive budget** agreed (e.g. &lt;5% warn rate on N hand-reviewed generated decks) | N = ___ |

---

## Investigate during D0 / D0.5 (feeds patterns, not blocking D0)

| ☐ | Investigation | Outcome |
| --- | --- | --- |
| ☐ | Cards with “search your library” vs pattern hit rate | Tutor regex priority |
| ☐ | Tag vs atom gap for `energy` (and 1–2 other tags) | Confirms value over include/avoid alone |
| ☐ | Blood / oil / experience hit counts in legal pool | Profile vs warn-only |
| ☐ | Token creators vs subtype “each other X” payoffs | Soft vs hard rules |
| ☐ | 10–20 staple commanders → implied `mechanic_focus` vs audit | Commander auto-suggest feasibility |
| ☐ | `deck_stats` field list for validator + future D3 | API sketch in doc 10 or code comment |

---

## Builder integration (before D3, not before D1)

| ☐ | Item | Notes |
| --- | --- | --- |
| ☐ | `deck_stats` computation module spec | Counts by type/subtype, profile roles, name set |
| ☐ | Incremental `deck_stats` update during slot fill order | Matches `filler.py` order |
| ☐ | Scorer: dependency penalty/bonus weights vs existing heuristics | |
| ☐ | `budget_backfill`: do not remove sole tutor target | |
| ☐ | Module layout: `effects/extract.py`, `rules/dependencies.py` (no logic in `validate.py`) | |

---

## Explicitly deferred (do not block D1–D2)

| Topic | Defer until |
| --- | --- |
| Progressive wizard restrictions (UX6) | D2 calibrated + D0.5 `profile_counts_by_ci` |
| `ConstraintState` / criteria linter (UX3) | D2 rules stable; can parallel D2 |
| Pick-time strict pool filter (D4) | **Shipped** — `--strict-dependencies` |
| Repair / swap pass (D5) | **Shipped** — `--repair-dependencies` |
| Web constraint panel (UX7) | Separate milestone |
| Wizard reorder (colors → commander first) | UX6c |
| Live Scryfall sync | Out of product scope |

---

## Implementation phase gates

| Phase | Enter when | Exit criteria |
| --- | --- | --- |
| **D0** | Checklist § D0 rows started | Patterns + golden tests + atom schema ☑ — **complete** (2026-05-30) |
| **D0.5** | D0 ☑ + snapshot ☑ | Audit reports ☑ + profiles revised ☑ |
| **D1** | All **§ Must complete before D1** ☑ | Import writes `card_effects`; golden tests pass |
| **D2** | D1 ☑ + output contract ☑ | Warn-only report in MD/JSON; dogfood review — **implemented** |
| **D3** | D2 false-positive budget met | Scorer uses `deck_stats` during fill — **implemented** |
| **D4** | D3 ☑ | Optional `--strict-dependencies` at pick time — **implemented** |
| **D5** | D4 ☑ | Repair pass for top failure classes — **implemented** |

---

## Dogfood acceptance (after D2)

Before D3, manually review generated decks:

| ☐ | Scenario | Pass? |
| --- | --- | --- |
| ☐ | Land tutor deck — no “no land” false warn | |
| ☐ | Energy producers, zero consumers — clear Energy note with names | |
| ☐ | Elf lord, &lt;5 elves — warning with suggested minimum | |
| ☐ | Enchantress / low aura count + aura tutor | |
| ☐ | Goodstuff deck — no spam warnings from arbitrary thresholds | |

---

## References

- [10-card-dependency-engine.md](10-card-dependency-engine.md) — D0–D5 technical phases
- [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md) — UX phases, progressive constraints
- [09-next-steps.md](09-next-steps.md) — backlog
- [`config/dependency-profiles.yaml`](../config/dependency-profiles.yaml) — thresholds (update after D0.5)
