# Documentation changelog (recent ships)

Append a dated line when merging a user-visible or roadmap-closing feature. Agents: update this instead of duplicating long “recently shipped” prose in [active.md](../roadmap/active.md).

Format: `- **YYYY-MM-DD** — Short title — optional PR/issue`

---

## 2026-06

- **2026-06-27** — UX10c curve advisories shipped — warn-only `CURVE_MISSING_EARLY` and `CURVE_TOP_HEAVY` from `config/curve-advisories.yaml` (theme overrides for ramp/tokens/voltron); `stats.curve_advisories` in `.deck.json`; **Curve advisories** in Markdown + web deck metrics panel
- **2026-06-26** — UX10 deck composition metrics shipped — **UX10a** CMC histograms, type counts, and summary stats in Markdown + `.deck.json` `stats` (`deck_metrics.py`); **UX10b** collapsible **Deck metrics** panel on `/deck/:id` with interactive bar chart and All nonlands / Creatures only toggle (#85, UX10b PR)
- **2026-06-26** — UX11 GUI deck editor shipped — per-card lock (`PATCH` deck body), slot regen (`POST …/refill-slot`), multi-select swap (`POST …/swap`); edit mode on `/deck/:id`; lock-aware engine refill — home **Download card data** / **Refresh card data** via `POST /api/v1/import` (`DbBanner`, `HomePage`); poll `GET /api/v1/wizard/meta` until `db_ready` (#81)
- **2026-06-25** — UX7d dependency dashboard shipped — collapsible **Dependencies** panel on deck view (`/deck/:id`); profile summaries and expandable issues with **Show in deck** highlight; generate rejects invalid/incomplete decks; commander step defaults color filter to Exact (#77, #78)
- **2026-06-24** — UX7f saved deck library shipped (server SQLite store, `GET/PATCH/DELETE /api/v1/decks`, generate auto-save; `/library` grid; deck view rename/delete; JSON-first deck view; home library CTAs)
- **2026-06-24** — Fix Docker generate ignoring `MTG_DB_PATH` (deck builder used `/app/data/cards.db` instead of `/data/cards.db`)
- **2026-06-07** — UX7e enhanced deck view shipped (`/deck/:id` — filters, summaries, dependency notes, Scryfall art; session deck cache; home resume CTA). *Superseded by UX7f for persistence — deck view now JSON-first with server library.*
- **2026-06-07** — UX7c web build wizard shipped (`packages/web` — 7 steps, review, generate, MD result; 375px layout; loading/error states)
- **2026-06-04** — UX7b `mtg-deck-tools serve` (uvicorn launcher, `MTG_*` env defaults, `--with-ui` static mount)
- **2026-06-04** — UX7a service layer + OpenAPI (`service/`, `api/`, CLI facades; `pip install -e ".[web]"` for FastAPI) (#44)
- **2026-06-04** — UX5 wizard prepopulate on regen (`generate --wizard --from`, `wizard --from`)
- **2026-06-04** — UX4 wizard step back-navigation (continue / back / cancel; preserved defaults)
- **2026-06-04** — UX3 criteria linter (end-of-wizard preflight)
- **2026-06** — Token subtype buffs (`TOKEN_SUBTYPE_BUFF_SUPPORT`, dogfood `treasure-prosper`)
- **2026-06** — Graveyard filler atoms (surveil/discover/discard; dogfood `surveil-mirko`)
- **2026-06** — UX2 wizard synergy step (strict/repair/focus for activated profiles)
- **2026-06-03** — Rad / oil / charge counter profiles and balance rules
- **2026-06-03** — Dogfood matrix restored 25/25 → 30/30 after bulk refresh fixes
- **2026-06** — Equipment depth, graveyard/landfall heuristics, sacrifice/token refinements, resource counters, tutor payload upgrades, enchantment matters, subtype lords, tokens/vehicles packages

Older milestone narrative: [milestones.md](milestones.md).
