# Web UI — screens

**Status:** Planning — UX7c screens locked.

Screen behavior per client route. Routes: [routes.md](routes.md). Navigation: [navigation.md](navigation.md). HTTP calls: [wizard-api.md](wizard-api.md). Layout review: [wireframes/README.md](wireframes/README.md).

CLI wizard parity: [user-experience.md](../dependency-engine/user-experience.md) § UX7c and `src/mtg_deck_tools/wizard/`.

---

## Home (`/`)

| Element | Behavior |
| --- | --- |
| DB banner | Visible when DB missing; explains CLI `mtg-deck-tools import` |
| Build new deck | → `/build/1` when DB ready; disabled when blocked |
| Future | Library (**UX7f**), resume active deck (**UX7e**) — hidden or disabled until shipped |

**API:** `GET /health`, `GET /api/v1/wizard/meta` (or `GET /api/v1/stats` for DB probe). See [wizard-api.md](wizard-api.md).

---

## Step 1 — Themes & slot template (`/build/1`)

CLI: [step1.py](../../../src/mtg_deck_tools/wizard/step1.py).

| Control | UX7c |
| --- | --- |
| Theme multi-select | Chip or checkbox list |
| Slot template | **Defaults only** — custom editor deferred |

**API:** `GET /api/v1/wizard/themes`, `GET /api/v1/wizard/slot-template/defaults`.

---

## Step 2 — Include / avoid mechanics (`/build/2`)

| Control | UX7c |
| --- | --- |
| Include mechanics | Multi-select |
| Avoid mechanics | Multi-select |

**API:** `GET /api/v1/wizard/mechanics`.

---

## Step 3 — Synergy & dependencies (`/build/3`)

CLI: [step3_synergy.py](../../../src/mtg_deck_tools/wizard/step3_synergy.py).

| Control | UX7c |
| --- | --- |
| `strict_dependencies` | Toggle |
| `repair_dependencies` | Toggle |
| `mechanic_focus` per activated profile | **Horizontal chips** (default / incidental / supported / focused / engine) |

Activated profiles depend on themes + include mechanics — server computes list.

**API:** `POST /api/v1/wizard/synergy-context` — body: partial `DeckCriteria`; response: activated profiles + focus options.

---

## Step 4 — Colors (`/build/4`)

| Control | UX7c |
| --- | --- |
| Color identity | W/U/B/R/G multi-select (CLI parity) |

**API:** None required (static UI); validation via preflight on review.

---

## Step 5 — Budget & card prices (`/build/5`)

CLI: [step4.py](../../../src/mtg_deck_tools/wizard/step4.py).

| Control | UX7c |
| --- | --- |
| Budget USD | Optional number |
| Card price min/max | Optional |
| `strict_budget` | Toggle |
| `prefer_available` | Toggle if exposed in CLI step |

**API:** None required for catalogs; values stored in client `DeckCriteria` draft.

---

## Step 6 — Commander (`/build/6`)

CLI: [step5.py](../../../src/mtg_deck_tools/wizard/step5.py).

| Control | UX7c |
| --- | --- |
| Search | Search-as-you-type |
| Color match | Toggle: **`includes`** (default) vs **`exact`** |
| Partner commanders | **Out of scope** |

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
