# Web UI — client routes

**Status:** **UX7c + UX7e + UX7f shipped** — build wizard, enhanced deck view, and saved library routes in `packages/web/`.

SPA route map for `packages/web/`. Screen behavior: [screens.md](screens.md). Navigation: [navigation.md](navigation.md).

---

## Routing mechanism

**Path-based** routing (existing SPA router in `packages/web/`).

---

## Route map

| Route | Screen | Phase |
| --- | --- | --- |
| `/` | Home | UX7c |
| `/build` | Build wizard — redirect to `/build/1` | UX7c |
| `/build/1` | Wizard step 1 — themes & slot template | UX7c |
| `/build/2` | Wizard step 2 — include / avoid mechanics | UX7c |
| `/build/3` | Wizard step 3 — synergy & dependencies | UX7c |
| `/build/4` | Wizard step 4 — colors | UX7c |
| `/build/5` | Wizard step 5 — budget & card prices | UX7c |
| `/build/6` | Wizard step 6 — commander | UX7c |
| `/build/7` | Wizard step 7 — card rarity | UX7c |
| `/build/review` | Criteria review & preflight | UX7c |
| `/build/result` | Compat redirect → `/library` | UX7c |
| `/deck/:id` | Enhanced deck view | UX7e |
| `/library` | Saved deck library | UX7f |

---

## Redirects and guards

| Condition | Behavior |
| --- | --- |
| `/build` with no path suffix | Always redirect to `/build/1` (wizard draft in `sessionStorage` does not resume mid-flow) |
| DB not ready | `/` renders with banner; `/build/*`, `/library`, `/deck/*` blocked (see [architecture.md](architecture.md) § Database gate) |
| `/deck/:id` unknown id | Redirect to `/` |
| `/library` when DB missing | Redirect to `/` |

---

## Route parameters

| Param | Route | Meaning |
| --- | --- | --- |
| `:id` | `/deck/:id` | Client UUID at generate (**UX7e**); same id reused when **UX7f** library persists decks server-side |

---

## Client state (by route group)

| Route group | State |
| --- | --- |
| `/build/*` | Partial `DeckCriteria` draft in client memory; optional `sessionStorage` for wizard refresh survival |
| `/build/result` | Compat redirect — deck lives in server library (**UX7f**) |
| `/deck/:id` | Session **cache** (`mtg-deck-cache-{id}`) of loaded deck JSON; canonical store is server library (**UX7f**) |
| `/library` | Server library index via `GET /api/v1/decks` (**UX7f**) |

---

## References

- [screens.md](screens.md) — controls and behavior per route
- [navigation.md](navigation.md) — Next/Back, review, home flows
- [architecture.md](architecture.md) — product modes, phased delivery, DB gate
- [deck-output-format.md](../../product/deck-output-format.md) — `.deck.json` contract
- [backlog/web-ui.md](../../roadmap/backlog/web-ui.md) — post-MVP backlog (**UX10**, **UX11**)
