# Web UI — screens

**Status:** Planning — UX7c screens locked.

Screen behavior per client route. Routes: [routes.md](routes.md). Navigation: [navigation.md](navigation.md). HTTP calls: [wizard-api.md](wizard-api.md). Layout review: [wireframes/README.md](wireframes/README.md).

CLI wizard parity: [user-experience.md](../dependency-engine/user-experience.md) § UX7c and `src/mtg_deck_tools/wizard/`.

---

## Home (`/`)

**Wireframe:** [home.html](wireframes/home.html) (DB ready) · [home-db-missing.html](wireframes/home-db-missing.html) (DB gate)

| Element | Behavior |
| --- | --- |
| DB banner | Visible when DB missing; explains CLI `mtg-deck-tools import` |
| Build new deck | → `/build/1` when DB ready; disabled when blocked |
| Future | Library (**UX7f**), resume active deck (**UX7e**) — hidden or disabled until shipped |

**API:** `GET /health`, `GET /api/v1/wizard/meta` (or `GET /api/v1/stats` for DB probe). See [wizard-api.md](wizard-api.md).

---

## Step 1 — Themes & slot template (`/build/1`)

**Wireframe:** [build-step-01-themes.html](wireframes/build-step-01-themes.html)

CLI: [step1.py](../../../src/mtg_deck_tools/wizard/step1.py).

| Control | UX7c |
| --- | --- |
| Theme multi-select | Chip or checkbox list |
| Slot template | **Defaults only** — custom editor deferred |
| Commander slot row | Read-only count **1**; shows full **100**-card deck total. **Future:** possible entry point for single vs partner commander (selection still on step 6 today; partners **out of scope** UX7c) |

**API:** `GET /api/v1/wizard/themes`, `GET /api/v1/wizard/slot-template/defaults`.

---

## Step 2 — Include / avoid mechanics (`/build/2`)

**Wireframe:** [build-step-02-mechanics.html](wireframes/build-step-02-mechanics.html)

CLI: [step2.py](../../../src/mtg_deck_tools/wizard/step2.py).

| Control | UX7c |
| --- | --- |
| Mechanic triage | **3-column list** — **keyword · avoid · include**; left-aligned keyword column; tap zones on the **right** (avoid immediately left of include; include at screen edge for right-hand thumb reach) |
| Include / avoid | Mutually exclusive per mechanic; tap active side again to clear |
| Row highlight | Full-row tint when avoided (orange) or included (blue) |
| Zone affordance | Ghost **×** (avoid) and **+** (include) in inactive zones when column headers scroll away — headers not sticky |
| Overlap guard | Built into tri-state (cannot be both); no separate error state needed |

**API:** `GET /api/v1/wizard/mechanics`.

---

## Step 3 — Synergy & dependencies (`/build/3`)

**Wireframe:** [build-step-03-synergy.html](wireframes/build-step-03-synergy.html) (profiles active) · [build-step-03-synergy-empty.html](wireframes/build-step-03-synergy-empty.html) (no profiles)

CLI: [step3_synergy.py](../../../src/mtg_deck_tools/wizard/step3_synergy.py).

| Control | UX7c |
| --- | --- |
| `strict_dependencies` | Toggle — icon + short label (“Block orphan picks”) |
| `repair_dependencies` | Toggle — icon + short label (“Fix gaps after build”) |
| Activated profiles | Read-only **chip strip** above focus controls (from server) |
| `mechanic_focus` per activated profile | **Stepper list** — profile name + **segment bar** + contextual hint on the left; **−** / **+** on the right (same layout ergonomics as step 2); levels: Default → Incidental → Supported → Focused → Engine |
| Focus level help | **Collapsed** “What do focus levels mean?” — expands to definition list; default closed |
| Focus magnitude | **5-segment bar** under profile name: 1 filled = Default … 5 = Engine; updates with stepper |
| No activated profiles | Hide stepper + glossary; show dashed empty panel with links to steps 1–2 |

Activated profiles depend on themes + include mechanics — server computes list.

**API:** `POST /api/v1/wizard/synergy-context` — body: partial `DeckCriteria`; response: activated profiles + focus options.

---

## Step 4 — Colors (`/build/4`)

**Wireframe:** [build-step-04-colors.html](wireframes/build-step-04-colors.html)

CLI: [step3.py](../../../src/mtg_deck_tools/wizard/step3.py) (wizard step 4 of 7).

| Control | UX7c |
| --- | --- |
| Color identity | W/U/B/R/G multi-select — fixed **52px slot** per pip; unselected inner ring ~34px; selected fills slot (same outer radius for all colours); gold fill for White when selected; **no outer box-shadow ring** |
| Colorless (void) | **Separate control** below pips — colorless-only commanders; **mutually exclusive** with colored picks (no legendary combines empty identity with W/U/B/R/G) |
| Any | No colored pips and Colorless off — no color filter (distinct from Colorless only — **engine TBD**) |
| Selection summary | Read-only recap below controls |

**Design note (engine):** Explicit Colorless at step 4 requires `DeckCriteria` / commander search to distinguish **Colorless only** (`color_identity: []`) from **Any** (no filter). Today `colors: []` behaves as colorless-only under `exact` match and unfiltered under `includes` ([`commanders.search_commanders`](../../../src/mtg_deck_tools/wizard/commanders.py), [`test_wizard_commanders.py`](../../../tests/test_wizard_commanders.py)) — resolve before UX7c implementation (e.g. `colorless_only` flag or color-filter enum).

**API:** None required (static UI); validation via preflight on review.

---

## Step 5 — Budget & card prices (`/build/5`)

**Wireframe:** [build-step-05-budget.html](wireframes/build-step-05-budget.html)

CLI: [step4.py](../../../src/mtg_deck_tools/wizard/step4.py).

| Control | UX7c |
| --- | --- |
| Total budget | Master toggle — when on, **− / +** stepper row (48px tap zones) **plus** manual **$** text field; **≤2** cent digits on entry; display **$150** not **$150.00**, but **$3.40** always shows two cent digits |
| `strict_budget` | Toggle nested under budget — exclude cards without USD prices; **cleared when budget off** (CLI parity) |
| `prefer_available` | Toggle nested under budget — prefer readily available picks; **cleared when budget off** |
| Per-card range | Master toggle — when on, **stacked** max then min rows (full width each) |
| Per-card min / max | **− / +** steppers (**$1** / **$5**) **plus** manual text field each; **×** clear inside field when set; blank = no limit; same cent entry/display rules as budget |
| Range validation | If both bounds set and min &gt; max, inline warning — do **not** block stepper taps on the other field |
| Selection summary | Read-only recap below controls |

**API:** None required for catalogs; values stored in client `DeckCriteria` draft.

---

## Step 6 — Commander (`/build/6`)

CLI: [step5.py](../../../src/mtg_deck_tools/wizard/step5.py).

| Control | UX7c |
| --- | --- |
| Search | Search-as-you-type |
| Color match | Toggle: **`includes`** (default) vs **`exact`** |
| Partner commanders | **Out of scope** UX7c. Step 1 commander slot row is a **future** hook for single vs partner mode; step 6 remains the commander pick surface until then |

**API:** `GET /api/v1/wizard/commanders/search?q=&colors=&color_match=includes|exact&…` — budget filters from criteria query params.

---

## Step 7 — Card rarity (`/build/7`)

| Control | UX7c |
| --- | --- |
| `min_rarity` | Select (common → mythic) |

**API:** `GET /api/v1/wizard/rarities` (optional static list).

---

## Review (`/build/review`)

| Element | Behavior |
| --- | --- |
| Criteria summary | Read-only recap of all selections |
| Preflight warnings | Inline list; empty state when no issues |
| Back | → `/build/7` |
| Generate | Submits full `DeckCriteria`; random seed if absent |

**API:** `POST /api/v1/wizard/preflight` on load (body: `DeckCriteria`; response: `criteria_warnings[]`); `POST /api/v1/generate` on Generate.

---

## Result (`/build/result`)

| Element | UX7c |
| --- | --- |
| Deck output | HTML rendering of generated Markdown (CLI `.md` equivalent) |
| Download JSON | Deferred (**UX7f**) |
| Next steps | “Build another”; enhanced view deferred (**UX7e**) |

**API:** Uses `POST /api/v1/generate` response (`md_path`, optional inline `deck` / rendered markdown — TBD in UX7c-b).

---

## Planned screens (UX7e+)

Feature specs and backlog: [backlog/web-ui.md](../../roadmap/backlog/web-ui.md), [user-experience.md](../dependency-engine/user-experience.md).

### Enhanced deck view (`/deck/:id`) — UX7e

- Filters (slot, type, color).
- Summaries: balance, distribution, counts, deck cost.
- Analysis hooks (strengths, areas for improvement).
- Scryfall card art where useful.
- Entry point for **UX11** iterate controls.

### Saved deck library (`/library`) — UX7f

- Save, load, organize `.deck.json` locally (single-user, not multi-tenant).
- Load deck → **UX7e** view → iterate/regen without wizard.
- JSON download from result/history.
- Regen flows (slot regen, full regen preserving locks) tie to **UX11**.

### Dependency dashboard — UX7d

- Drill-down on `dependency_report` (D5).
- Attaches to enhanced deck view — not a separate top-level route in v1 planning.

**UX10** charts may overlap the enhanced deck view. Route map: [routes.md](routes.md).

---

## References

- [routes.md](routes.md)
- [wizard-api.md](wizard-api.md)
- [design.md](design.md)
