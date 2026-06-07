# Planning decisions

All v1 planning questions are resolved. Revisit only when scope changes.

## Decided

| Question | Answer |
| --- | --- |
| Format | Commander (100-card singleton) |
| Deck generation style | Guided slot template |
| Mechanic matching | Curated taxonomy + rule-based tagging on `oracle_text` |
| v1 constraints | Commander rules, budget, commander synergy, include/avoid mechanics |
| Runtime | Local cross-platform (Windows, Linux, macOS), local DB OK |
| Preprocessing | Acceptable and recommended |
| UI (v1) | Terminal wizard (CLI) — Python + `typer` / `questionary` / `rich` |
| Include / avoid mechanics | Keyword-level want / avoid lists — see [problem-decomposition.md](../architecture/problem-decomposition.md) |
| Wizard flow | Theme → include/avoid mechanics → colors → commander |
| Partner commanders | In v1 |
| Export format | Markdown + `.deck.json` — [deck-output-format.md](deck-output-format.md) |
| Budget null price | **Allow with warning**; optional `--strict-budget` — [card-availability.md](card-availability.md) |
| Field reference | Split: `bulk-data-metadata-fields.md` + `oracle-card-fields.md` |
| Deck variety | **Seeded random** slot selection (`--seed` for reproducibility) |
| Power level dial | **Deferred** — needs richer model than a simple dial |
| Card availability | v1: EDHREC bias + `availability_score`; obscure > new-unpriced — [card-availability.md](card-availability.md) |
| Card data freshness | **Static snapshot** — manual bulk refresh; used-card audience — [goals-and-scope.md](goals-and-scope.md), [data-sources.md](../architecture/data-sources.md) |
| Interactive UI (UX7+) | **Web** primary for interactive users; **CLI** for automation/dogfood; UX7c design — [specs/web/README.md](../specs/web/README.md) |
| Web auth | **None for v1** — no login, sessions, or API keys in the product |
| Web multi-tenant | **Out of scope** — one deployment = one user; single-writer SQLite |
| Engine language (web era) | **Python** — no port; FastAPI exposes `service/` to the SPA |
| Frontend framework | **Svelte 5 + Vite** SPA (`packages/web/`) — not SvelteKit; FastAPI serves API + static build |

## Deferred (post-v1)

See [active.md](../roadmap/active.md) for the active backlog (dependency UX calibration, export, UI).

| Topic | Notes |
| --- | --- |
| **Colorless vs Any (UX7c step 4)** | Web wizard adds explicit **Colorless only** (void identity), mutually exclusive with W/U/B/R/G. Engine must distinguish Colorless-only from unfiltered Any — today `DeckCriteria.colors: []` is ambiguous (`exact` → colorless commanders only; `includes` → all). Likely needs schema flag or filter enum before UX7c ships — [screens.md](../specs/web/screens.md) § Step 4 |
| Dependency wizard UX (UX7+) | UX2–UX5 CLI wizard shipped; web build wizard UX7c — [user-experience.md](../specs/dependency-engine/user-experience.md) § UX7c |
| Power level / salt | Complicated, context-dependent; not a single dial |
| Obscure vs new null-price classification | Shipped heuristic favors obscure detection — [card-availability.md](card-availability.md) |
| Moxfield / Archidekt export | Translate from `.deck.json` |
| Product auth / accounts | User login, shared hosted multi-user DB — only if scope changes beyond v1 single-instance model |

## Historical

**Phase 1 start (2025):** import script + mechanic taxonomy v0 + SQLite schema + CLI stub — superseded by Phase 2–3 and dependency engine work above.
