# Dependency engine — user experience and control model

Planning for **how users discover, constrain, and refine** card-dependency behavior alongside the technical engine in [10-card-dependency-engine.md](10-card-dependency-engine.md).

**Status (2026-05-31):** Engine **D0–D5 shipped**. UX1 (Markdown/JSON report + `--strict-dependencies` / `--repair-dependencies` on CLI) is done. **UX2** (wizard synergy strictness + `mechanic_focus` presets) is the next milestone — see [09-next-steps.md](09-next-steps.md).

This document is intentionally **UI-agnostic at the core** (criteria + reports in `.deck.json`) but evaluates **terminal CLI vs richer UI** per interaction type, and defines schema hooks the engine must support so any future shell can reuse the same logic.

---

## Relationship to the dependency engine

| Concern | Owner doc | Notes |
| --- | --- | --- |
| What atoms exist, how they are extracted, validation rules | [10-card-dependency-engine.md](10-card-dependency-engine.md) | D0–D5 implementation phases |
| What users can **ask for**, **see**, and **change** | **This doc** | Drives `DeckCriteria` extensions and `dependency_report` shape |
| Deck file contract | [07-deck-output-format.md](07-deck-output-format.md) | `criteria`, Notes groups, future swap metadata |

**Design principle:** The engine evaluates **facts** (producers, consumers, tutor predicates). The UX layer expresses **intent** (which mechanics matter, how “focused” the deck should be). Keep intent in `DeckCriteria` / YAML profiles; keep evaluation in `rules/dependencies.py` + `card_effects`.

```mermaid
flowchart TB
  subgraph user [User intent]
    Profiles[Mechanic profiles / focus]
    Thresholds[Min-max and ratio targets]
    Strict[Strict vs warn-only]
  end
  subgraph engine [Dependency engine]
    Extract[Effect extraction]
    Stats[deck_stats aggregation]
    Rules[Rule evaluation]
  end
  subgraph out [Feedback]
    Report[dependency_report]
    Notes[Markdown Notes]
    Suggest[Swap suggestions - later]
  end
  Profiles --> Criteria[DeckCriteria]
  Thresholds --> Criteria
  Strict --> Criteria
  Criteria --> Rules
  Extract --> Stats --> Rules
  Rules --> Report --> Notes
  Rules --> Suggest
```

---

## What users are trying to control

Users rarely think in “effect atoms.” They think in **mechanics**, **roles**, and **how much** of the deck should revolve around them.

| User mental model | Engine mapping | Example |
| --- | --- | --- |
| “I want an energy deck” | `PRODUCES_RESOURCE` + `CONSUMES_RESOURCE` for `energy` | Aether Hub + payoffs |
| “Don’t make energy the whole deck” | **Focus cap** on energy-tagged cards (e.g. ≤12% of nonlands) | 4–5 energy cards, not 15 |
| “I need auras for this commander” | `SEARCH_FOR` + `REQUIRES_TYPE` for Aura | Tutors + enchantment density |
| “Enough elves for my lord” | `TYPE_SYNERGY_MIN` for subtype Elf | ≥5 other elves |
| “Strict — no dead tutors” | `strict_dependencies` + pick-time filter | Exclude tutors with 0 targets |

Three control dimensions:

1. **Enablement** — which dependency *classes* and *mechanics* are in scope for this build.
2. **Balance** — min/max counts and ratios for producers, consumers, and type payoffs.
3. **Enforcement** — warn in Notes vs block picks / fail validation.

---

## Mechanic and dependency catalog (user-facing)

Below is a **curated catalog** for UX copy and profile presets. The engine may implement subsets per phase (see doc 10); the UI should still list deferred items as “coming soon” only if exposed.

### Resource counters (produce / consume)

| Mechanic | Producer signal | Consumer signal | Typical user goal |
| --- | --- | --- | --- |
| **Energy** | `{E}`, “energy counter(s)” | “pay {E}”, “you may pay {E}” | Both sides present; 3–6 total cards often feels “supported” without dominating |
| **Experience** | “experience counter(s)” | “pay … experience” | Commander-centric; often 1–3 payoffs |
| **Rad counters** | “rad counter(s)” | “pay … rad” | Similar to energy; smaller card pool |
| **Oil / charge / brick** | set-specific oracle | spend counters | Lower priority unless theme selected |
| **Blood** (counters on players) | “blood counter” on opponent | cards that care about blood | Niche; warn-only unless user enables `blood` profile |
| **+1/+1 counters** | “put a +1/+1 counter” | “remove … counter”, “with a +1/+1 counter” | Often overlaps `counters` theme; use **type synergy** not just resource balance |

**User-facing knob:** “Energy focus” — *light* (incidental), *supported* (3–6 cards), *focused* (7–12), *engine* (13+). Maps to min/max nonland slots with energy atoms or `energy` tag.

### Tutors and search (target must exist)

| Pattern | User cares because | Default strictness |
| --- | --- | --- |
| Search for **land** | Obvious failure if 0 lands | Warn (should never happen) |
| Search for **Aura** | Enchantress / Voltron | Warn; strict optional |
| Search for **creature** with CMC cap | Toolbox / reanimator | Warn |
| Search for **artifact** / **enchantment** | Narrow tutors | Warn |
| **Any card** | Hard to validate | Skip or soft warn |

**User-facing knob:** “Honor tutor targets” (on/off) + per-type minimum targets in deck (usually ≥1).

### Type / subtype payoffs (“each other X”)

| Pattern | Example | Suggested min (nonland) when theme selected |
| --- | --- | --- |
| Subtype lord | “Other Elves get +1/+1” | 5–8 other Elves |
| Type matters | “Whenever you cast an Artifact spell” | 8–12 artifacts |
| **Vehicle** + crew | Vehicles without creatures | Vehicles ≥3, creatures ≥25 |
| **Aura** density | “Whenever you cast an Aura” | Auras ≥6–8 |

**User-facing knob:** “Synergy density” — *low* / *medium* / *high* maps to threshold multipliers (see Balance model).

### Sacrifice / aristocrats (paired roles)

Overlaps `aristocrats` theme but dependency engine can count:

| Role | Examples |
| --- | --- |
| **Fodder** | creatures that die easily, tokens |
| **Outlet** | “sacrifice a creature” |
| **Payoff** | “whenever a creature you control dies” |

**User-facing knob:** “Sacrifice package” — ensure ≥1 outlet and ≥1 payoff when fodder theme is on.

### Auras and equipment (Voltron / enchantress)

| Concern | Dependency |
| --- | --- |
| Aura tutors | `SEARCH_FOR` → Aura in library |
| Aura payoffs | `REQUIRES_TYPE` / cast triggers |
| **Aura removal risk** | Not a static dependency; UX note only |

**User-facing knob:** “Aura support” — min aura count + tutor target check.

### Graveyard / zone (soft, v1)

Delve, escape, reanimation — often **warning-only** with heuristics (creature count, mill). Defer strict balance to later phases.

---

## Balance model: counts, ratios, and “deck dominance”

### Problem

Including `energy` in **include mechanics** today boosts any card tagged `energy` but does **not**:

- Distinguish producers vs consumers.
- Cap how many energy cards appear.
- Tell the user when the deck is **too thin** (1 producer, 0 payoffs) or **too thick** (9 producers, 1 payoff — mechanic dominates).

### Proposed metrics (computed in `deck_stats`)

For each **mechanic profile** `M` (e.g. `energy`, `auras`, `elves`):

| Metric | Definition |
| --- | --- |
| `producers(M)` | Cards with `PRODUCES_RESOURCE` or profile-specific atom |
| `consumers(M)` | Cards with `CONSUMES_RESOURCE` |
| `payoffs(M)` | Type/subtype amplifiers, “whenever you …” for M |
| `tutors(M)` | `SEARCH_FOR` predicates referencing M |
| `total(M)` | Union of above (dedupe by `oracle_id`) |
| `share(M)` | `total(M) / nonland_count` (excludes commander from 99 if desired) |

### Default targets (configurable)

Store defaults in **`config/dependency-profiles.yaml`** (new), not hard-coded in Python:

```yaml
# Illustrative — balances are starting points for feedback text
profiles:
  energy:
  label: Energy counters
  roles: [producer, consumer]
  defaults:
    producer_min: 2
    producer_max: 6
    consumer_min: 2
    consumer_max: 8
    share_max: 0.12        # 12% of nonlands ≈ 7–8 cards at 60 nonlands
    consumer_per_producer_min: 0.5
  aura_support:
  label: Auras
  roles: [aura_spell, aura_tutor_target]
  defaults:
    aura_spell_min: 6
    aura_spell_max: 15
    share_max: 0.18
```

**Focus presets** (user selects one per profile or globally):

| Preset | `share_max` (approx) | Producer/consumer band | User message tone |
| --- | --- | --- | --- |
| **Incidental** | 5% | 1–2 each | “A splash of energy — don’t expect a full engine” |
| **Supported** | 10% | 2–5 producers, 2–6 consumers | “Energy should work when you draw it” |
| **Focused** | 15% | 3–6 / 3–8 | “Energy is a main plan” |
| **Engine** | 20%+ | User accepts dominance | “This deck is built around energy” |

### Ratio rules

| Rule | Condition | Severity |
| --- | --- | --- |
| `ONE_SIDED_RESOURCE` | producers ≥ 1 and consumers == 0 | Warn (Fail if strict) |
| `CONSUMER_WITHOUT_PRODUCER` | consumers ≥ 2 and producers == 0 | Warn |
| `IMBALANCED_RATIO` | consumers < 0.5 × producers (when producers ≥ 3) | Warn — “too much setup, not enough payoffs” |
| `OVER_CAP` | total(M) > profile.share_max × nonlands | Warn — “deck may feel one-note” |
| `UNDER_FLOOR` | user set `mechanic_focus[M]=supported` but total(M) < floor | Warn — “you asked for energy support but only 1 card” |

Thresholds should **scale with themes**: if `tokens` + `energy` both selected, apply the **stricter** share cap or sum caps with a global `max_themed_share`.

---

## User feedback: too little, too much, conflicting intent

### Feedback channels (all phases)

| Channel | When | Content |
| --- | --- | --- |
| **Post-build `dependency_report`** | Always (D2+) | Structured pass/warn/fail per rule |
| **Markdown Notes → “Deck dependencies”** | Always | Human summary + card names |
| **Wizard / CLI inline** | During criteria entry | Prevent impossible combos before generate |
| **Pick-time hints** | D3+ (optional verbose) | “Adding this leaves 0 aura targets for …” |

### Example messages (tone: actionable, not judgmental)

| Situation | Message |
| --- | --- |
| Too little energy | “You selected **Supported energy** but the list has 1 producer and 0 payoffs. Add 2–4 `{E}` payoffs or lower focus to Incidental.” |
| Too much energy | “12 cards reference energy (~20% of nonlands). Consider raising focus to **Engine** or removing 4–5 setup cards.” |
| Tutor gap | “**Enlightened Tutor** searches for enchantments; only 2 auras in the deck. Add auras or remove the tutor.” |
| Conflicting criteria | “**Avoid artifacts** conflicts with **Artifact synergy** thresholds. Artifact payoffs will be excluded from the pool.” |
| Strict mode block | “Generation skipped **Vampiric Tutor** — no creature with MV ≤3 in the remaining pool.” |

### “Spec health” preflight (before generate)

Run a lightweight **criteria linter** (no full deck):

| Check | Example |
| --- | --- |
| Conflicting include/avoid | include `energy` + avoid same tag |
| Unreachable profile | `aura_support: focused` with colors that ban enchantments |
| Over-constrained budget | strict budget + high rare minimum + 3 focused profiles |
| Too many focused profiles | >2 profiles at `focused` or `engine` → warn “deck may not have room for all plans” |

Return `criteria_warnings: []` in wizard output and optionally block until acknowledged.

---

## User control surface (criteria schema)

Extend `DeckCriteria` (and `.deck.json` `criteria`) in phases. Names are illustrative.

```python
# Illustrative Pydantic fields — align with implementation PRs
class MechanicFocus(BaseModel):
    profile_id: str           # energy, aura_support, elves, ...
    level: Literal["off", "incidental", "supported", "focused", "engine"]
    producer_min: int | None = None   # override preset
    consumer_min: int | None = None
    share_max: float | None = None

class DependencyPreferences(BaseModel):
    enabled: bool = True
    strict: bool = False              # maps to strict_dependencies
    honor_tutor_targets: bool = True
    mechanic_focus: list[MechanicFocus] = []
    disabled_rule_ids: list[str] = [] # power users
```

| Field | CLI v1 | Rich UI later |
| --- | --- | --- |
| `strict` | `--strict-dependencies` flag | Toggle |
| `mechanic_focus[]` | Subcommand or wizard step 2b | Sliders / presets per mechanic |
| Per-profile overrides | JSON edit in `.deck.json` | Advanced panel |
| `disabled_rule_ids` | Hidden / env var | Expert mode |

**Important:** Wizard step 2 today is flat **include/avoid mechanics** ([`mechanic-taxonomy.yaml`](../config/mechanic-taxonomy.yaml)). Do **not** replace it; **add** an optional “Synergy focus” step or flags so casual users stay on simple checkboxes.

---

## Understanding and swapping dependencies (future)

Not required for first engine release, but the **data model should not block** interactive editing.

### Transparency (what did the builder assume?)

Each card in `.deck.json` may gain optional:

```json
{
  "name": "Aether Hub",
  "dependency_roles": ["energy_producer"],
  "satisfies": ["rule:ENERGY_BALANCE.producer"],
  "introduces_gaps": []
}
```

Deck-level `dependency_report`:

```json
{
  "profiles": [
    {
      "id": "energy",
      "producers": 4,
      "consumers": 2,
      "share": 0.10,
      "status": "warn",
      "messages": ["consumers < recommended minimum (4)"]
    }
  ],
  "rules": [
    {
      "id": "TUTOR_TARGET_EXISTS",
      "card": "Enlightened Tutor",
      "status": "warn",
      "detail": "No Aura card in deck matches search"
    }
  ]
}
```

### Swap workflow (user replaces a dependency “package”)

| Step | Action |
| --- | --- |
| 1 | User opens dependency summary → selects “Energy package (6 cards)” |
| 2 | UI offers **alternatives** with same role histogram (4 prod / 2 cons) |
| 3 | `generate --from deck.json --swap-profile energy --seed N` or UI button |
| 4 | Re-run validator; show diff |

Engine requirements for swaps:

- Tag cards with **profile membership** at build time.
- Repair pass (D5) searches pool preserving `deck_stats` deltas per role.
- Swaps should prefer same **slot** (`synergy`, `flex`) before cross-slot.

---

## Is the terminal CLI appropriate?

### Summary

| Interaction | CLI fit | Recommendation |
| --- | --- | --- |
| On/off strict dependencies | **Good** | Flag on `generate` |
| Include/avoid mechanics (existing) | **Good** | Keep as-is |
| Post-build dependency report | **Good** | Markdown Notes + JSON |
| Focus presets (incidental → engine) | **Adequate** | Wizard step with numbered menu |
| Per-mechanic min/max overrides | **Poor** | JSON edit or defer to UI |
| Visual tutor target preview | **Poor** | Needs card images / list UI |
| Multi-profile balance dashboard | **Poor** | Web or desktop |
| Swap dependency package | **Poor** | Interactive selection |

**Conclusion:** CLI remains the **right first shell** for D0–D3 (reporting, strict flag, simple presets). Plan a **local web or desktop UI** when swap workflows, dashboards, and side-by-side card previews become requirements — reuse Option B/C from [04-architecture-options.md](04-architecture-options.md) without forking the engine.

### Phased UX roadmap

| Phase | UX deliverable | Engine dependency |
| --- | --- | --- |
| **UX0** | Document + `dependency-profiles.yaml` skeleton | None |
| **UX1** | Notes + `dependency_report`; `--strict-dependencies` | D2 |
| **UX2** | Wizard: “Synergy strictness” + 1–2 focus presets (energy, auras) | D2–D3 |
| **UX3** | `criteria` linter warnings in wizard | D2 + profiles |
| **UX4** | `.deck.json` per-card `dependency_roles` | D2 |
| **UX5** | Local web: dependency dashboard + swap | D5 + API wrapper |
| **UX6** | **Progressive constraints** — restrict wizard/build choices as criteria commit | D1 + inventory audit + D3–D4 |

---

## Progressive constraints during deck building (parked — plan now, ship later)

**Goal (future):** As the user moves through criteria collection and (eventually) interactive deck construction, **narrow valid choices** so they cannot easily commit to combinations that the dependency engine would flag — or that the card pool cannot support in their colors.

**Is this the right time?**

| Action | Timing | Rationale |
| --- | --- | --- |
| **Add to the plan** (interaction model, phases, data prerequisites) | **Now** | Shapes `card_effects` schema, inventory audit, and criteria fields before code hardens |
| **Implement restrictive wizard UI** | **Not yet** | Needs reliable atoms, inventory-backed feasibility tables, and warn-only calibration first |
| **Implement generate-time pool restriction** | **After D2–D3** | Same engine as post-build report; start warn-only, then opt-in strict |
| **Full “dependency tree” UI** | **After UX5+** | Rich UI for hierarchy visualization and per-node overrides |

Treat progressive constraints as **UX6**, dependent on **D0.5 inventory audit** and **D1–D4** — not a v1 wizard change.

### Three layers of “restriction” (do not conflate)

```mermaid
flowchart TB
  L1[Layer 1 - Criteria feasibility]
  L2[Layer 2 - Slot fill pool]
  L3[Layer 3 - Post-build / edit]
  L1 -->|colors commander themes focus| L2
  L2 -->|each card pick updates deck_stats| L3
```

| Layer | When | What gets restricted | Inventory data needed |
| --- | --- | --- | --- |
| **1 — Criteria feasibility** | Wizard steps 1–5 (and future step 2b) | Disable or warn on theme/mechanic/focus combos that **cannot** be satisfied in chosen colors | Per-CI counts: e.g. `energy_producer` cards in `WUBRG`, aura spells in `GW` |
| **2 — Slot fill** | `generate` / future interactive builder | Remove or deprioritize candidates that **worsen** open dependencies (tutor with 0 targets in partial deck) | `card_effects` + running `deck_stats` + remaining pool |
| **3 — Post-build edit** | `--from`, `--refill-slot`, swap UI | Limit replacements that break satisfied rules | Full deck + same as layer 2 |

Layer 1 can use **precomputed inventory aggregates** (no deck yet). Layers 2–3 need the **dependency engine** and trustworthy extraction.

### Constraint hierarchy (order of precedence)

When multiple rules apply, evaluate in this order (highest wins first):

| Priority | Source | Example restriction |
| ---: | --- | --- |
| 1 | **Comprehensive Rules / format** | Singleton, CI, 903.5d — already in pool |
| 2 | **Explicit user avoid** | `avoid_mechanics` — hard exclude |
| 3 | **Budget / availability** | `--strict-budget`, `--prefer-available` |
| 4 | **Explicit user include** | Boost, do not auto-disable include tag |
| 5 | **Dependency strict mode** | No tutor without target in deck+commander |
| 6 | **Mechanic focus floors/ceilings** | Cannot select `engine` energy if CI has &lt; N producers in pool |
| 7 | **Dependency warn-only** | Allow selection but show inline warning |
| 8 | **Scoring preferences** | Soft nudge only |

**Plan implication:** Progressive UI must respect **user include** over automatic dependency narrowing unless user enables strict mode or acknowledges a conflict.

### “Dependency tree” vs rule list

Colloquial “dependency tree” maps to:

| Concept | Implementation |
| --- | --- |
| **Nodes** | Committed criteria + commander + cards in partial deck |
| **Edges** | Rules triggered by atoms on cards (tutor → needs Aura in deck) |
| **Hierarchy** | Rule priority table above + profile parent/child (e.g. `aura_support` ⊃ `SEARCH_FOR` Aura) |

A literal tree UI is **optional** (web). Minimum viable product is a **flat list of active constraints** with status (satisfied / at risk / violated) updating after each wizard answer or card pick.

### Inventory companion data for accurate restriction

Operate on the main inventory (`cards.db` after import) to build **feasibility indexes** (companion tables or gitignored audit JSON):

| Dataset | Used for |
| --- | --- |
| `profile_counts_by_ci` | “Energy focused” greyed out in mono-R if producers &lt; floor |
| `predicate_target_counts` | Tutor for Aura: count aura spells legal in CI |
| `role_counts_by_ci` | producer/consumer counts per profile per color identity |
| `commander_implied_profiles` | Auto-suggest focus when commander extracts Elf lord, enchantress, etc. |
| `confidence_by_pattern` | Only **hard-disable** wizard options when extraction confidence ≥ threshold |

See **D0.5 inventory audit** in [10-card-dependency-engine.md](10-card-dependency-engine.md) — restriction quality is bounded by audit accuracy.

**Static card pool:** Feasibility indexes (`profile_counts_by_ci`, etc.) are built from the **same versioned** `cards.db` as deck generation. The product targets **older used cards** ([01-goals-and-scope.md](01-goals-and-scope.md)); refreshing companion data is a **maintainer** step alongside `import`, not an end-user concern.

### UI interaction patterns (parked — specify now)

These apply to **CLI wizard**, future **local web**, and **interactive refill** alike. Use a shared `ConstraintState` model in the core library; shells only render it.

#### Restriction strength (per option)

| Mode | UX behavior | Default phase |
| --- | --- | --- |
| **hidden** | Option not shown | Strict + high-confidence rule only |
| **disabled** | Visible, cannot select; short reason | Layer 1 feasibility (later UX6) |
| **warn** | Selectable; confirmation prompt | UX3 linter, early UX6 |
| **info** | Selectable; badge “needs payoffs” | UX2 focus presets |
| **off** | No restriction | Until dependency engine enabled |

**Escape hatch (required):** “Show incompatible options” / `--no-progressive-constraints` so experts are not blocked by false positives.

#### Wizard step behaviors (future UX6)

Current order: themes → mechanics → colors → commander → budget ([`wizard/run.py`](../src/mtg_deck_tools/wizard/run.py)).

| Step | Progressive behavior (when enabled) |
| --- | --- |
| **1 — Themes / slots** | Warn if theme implies profile (tokens + aristocrats) that shares `max_themed_share` |
| **2 — Include / avoid** | Disable include tags with **zero** matching cards in pool (all colors) or later in chosen CI |
| **2b — Mechanic focus** | Disable `engine` if `profile_counts_by_ci` below floor; suggest `supported` |
| **3 — Colors** | Recompute feasibility; disable focuses that fail in this CI |
| **4 — Commander** | Merge commander atoms into implied profiles; narrow mechanics (“your commander wants auras”) |
| **5 — Budget** | Warn if strict budget makes focus floors unreachable (inventory + price histogram) |
| **After wizard** | `criteria_warnings` + optional “Fix” loop before `generate` |

**Open product question:** Reorder to **colors → commander → themes → mechanics** so layer-1 restrictions use CI + commander earlier. Defer reorder until UX6; document as breaking wizard UX change.

#### During generate (layer 2 — not wizard, but same mental model)

| Behavior | Strict off | Strict on |
| --- | --- | --- |
| Tutor in ramp slot with 0 targets in deck+commander | Pick allowed; post-build warn | Candidate excluded from pool |
| Energy producer when consumers = 0 | Allowed; warn | Penalize heavily or exclude |
| Profile over `share_max` | Allowed; warn | Deprioritize matching tags |

This is **D3–D4** engine work; UI “restriction” here is the generator silently narrowing picks unless user passes `--strict-dependencies`.

#### Interactive deck build (future, beyond batch generate)

| Interaction | Description |
| --- | --- |
| **Constraint panel** | Live list: “Need ≥2 energy payoffs (0 now)” |
| **Pick preview** | Hover card → “Would add 1 producer; still need 2 consumers” |
| **Slot lock** | User locks “aura package”; refill only swaps within profile |
| **Undo** | Revert pick; recompute `ConstraintState` |

Batch CLI `generate` may never expose pick-by-pick UI; `.deck.json` reload + `--refill-slot` is the interim.

### What to build before restricting choices

| Prerequisite | Why |
| --- | --- |
| D0.5 inventory audit | Know which profiles exist in pool and per-CI |
| D1 `card_effects` | Atoms for predicates and roles |
| D2 warn-only report | Calibrate false positive rate before disabling UI options |
| Golden tests on patterns | Avoid hiding valid commander strategies |
| `ConstraintState` API in core | One module consumed by wizard, filler, web |

### Phased delivery for progressive constraints

| Sub-phase | User-visible | Restricts? |
| --- | --- | --- |
| **UX3** | End-of-wizard warnings; user confirms | No — warn only |
| **UX6a** | Disable wizard options with **zero** pool support in CI (high confidence) | Yes — layer 1, narrow |
| **UX6b** | `--strict-dependencies` on generate | Yes — layer 2 |
| **UX6c** | Reorder wizard; commander-driven suggestions | Yes — layer 1 enriched |
| **UX7** | Web constraint panel + pick preview | Yes — layers 2–3 interactive |

### Success criteria (when UX6 ships)

- With progressive constraints **on** and strict **off**, user never sees a disabled option unless pool count in CI is 0 for that tag/profile.
- With strict **on**, generated deck has no `fail` rows in `dependency_report` for enabled rule classes.
- User can always override via escape hatch or by lowering focus / disabling profile.
- Every disabled/warn state cites `rule_id` + count (“only 1 Aura spell legal in UWR”).

---

## Impact on dependency engine design

Decisions here should **constrain** doc 10 implementation early:

| UX requirement | Engine consequence |
| --- | --- |
| Focus presets | Profiles in YAML; evaluator reads `criteria.mechanic_focus` |
| “Too much / too little” | `deck_stats` must expose per-profile counts and `share` |
| User disables a rule | Rule IDs stable and documented; evaluator skips disabled IDs |
| Future swaps | Persist `profile_id` on cards in build result; repair keyed by profile |
| Conflicting intent | Criteria linter runs **before** fill; pool already respects avoid list |
| Commander as target | Document in report when tutor satisfied **only** by commander |
| Feedback clarity | Every warn includes `profile_id`, `rule_id`, affected `oracle_id`s |

### Open questions (UX + engine joint)

1. **Global vs per-profile strictness** — one `strict` flag or per `MechanicFocus`?
2. **Auto-focus from commander** — pre-fill `elves` when commander is Elf tribal?
3. **Include mechanic vs focus** — does checking `energy` in include imply `supported` focus, or remain independent?
4. **Deck dominance across profiles** — single `max_themed_nonland_share` (e.g. 35%) for all focused mechanics combined?
5. **CLI wizard length** — new step 2b vs optional `mtg-deck-tools wizard --advanced`?

---

## Success criteria (UX)

- User enabling **Supported energy** receives a post-build note when producers/consumers fall outside the band, with **counts and card names**.
- User enabling **Engine** energy does **not** get “too much energy” warnings unless they also set a lower `share_max`.
- Preflight warns when **include/avoid** and **mechanic_focus** conflict before a 30s generate.
- `.deck.json` round-trips `dependency_preferences` so `generate --from` preserves user intent.
- Planning docs 10 and 11 stay cross-linked; implementation PRs cite which UX phase they satisfy.

---

## References

- [12-dependency-engine-pre-implementation-checklist.md](12-dependency-engine-pre-implementation-checklist.md) — D0–D5 gate (complete); dogfood acceptance open
- [10-card-dependency-engine.md](10-card-dependency-engine.md) — atoms, rules, D0–D5
- [07-deck-output-format.md](07-deck-output-format.md) — `.deck.json` schema
- [04-architecture-options.md](04-architecture-options.md) — CLI vs web vs desktop
- [06-open-questions.md](06-open-questions.md) — deferred power level; UI timing
- [09-next-steps.md](09-next-steps.md) — backlog ordering
- [`config/mechanic-taxonomy.yaml`](../config/mechanic-taxonomy.yaml) — current include/avoid tags
