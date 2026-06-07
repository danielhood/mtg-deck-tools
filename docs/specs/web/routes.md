# Web UI — client routes

**Status:** **UX7c-a–UX7c-b** — home, `/build/1`–`/build/7`, `/build/review`, and `/build/result` implemented in `packages/web/`.

SPA route map for `packages/web/`. Screen behavior: [screens.md](screens.md). Navigation: [navigation.md](navigation.md).

---

## Routing mechanism

Path-based or hash-based routing — **choose at implementation**. Logical paths below are stable either way.

---

## Route map

| Route | Screen | Phase |
| --- | --- | --- |
| `/` | Home | UX7c |
| `/build` | Build wizard — redirect to in-progress step (default `/build/1`) | UX7c |
| `/build/1` | Wizard step 1 — themes & slot template | UX7c |
| `/build/2` | Wizard step 2 — include / avoid mechanics | UX7c |
| `/build/3` | Wizard step 3 — synergy & dependencies | UX7c |
| `/build/4` | Wizard step 4 — colors | UX7c |
| `/build/5` | Wizard step 5 — budget & card prices | UX7c |
| `/build/6` | Wizard step 6 — commander | UX7c |
| `/build/7` | Wizard step 7 — card rarity | UX7c |
| `/build/review` | Criteria review & preflight | UX7c |
| `/build/result` | Generated deck (MD HTML) | UX7c |
| `/deck/:id` | Enhanced deck view | UX7e |
| `/library` | Saved deck library | UX7f |

---

## Redirects and guards

| Condition | Behavior |
| --- | --- |
| `/build` with no in-progress wizard | Redirect to `/build/1` |
| `/build` with saved wizard progress | Redirect to last completed step + 1, or `/build/review` if steps 1–7 done |
| DB not ready | `/` renders; `/build/*` redirect to `/` or show blocked state (see [architecture.md](architecture.md) § Database gate) |
| `/deck/:id`, `/library` before phase ships | 404 or placeholder — TBD at UX7e / UX7f implementation |

---

## Route parameters

| Param | Route | Meaning |
| --- | --- | --- |
| `:id` | `/deck/:id` | Saved deck identifier (**UX7f** persistence model TBD) |

---

## Client state (by route group)

| Route group | State |
| --- | --- |
| `/build/*` | Partial `DeckCriteria` draft in client memory; optional `sessionStorage` for refresh survival (implementation detail) |
| `/build/result` | Last `GenerateResponse` (or rendered markdown) for display |
| `/deck/:id`, `/library` | Loaded from server/local store — spec in **UX7e** / **UX7f** |

---

## References

- [screens.md](screens.md) — controls and behavior per route
- [navigation.md](navigation.md) — Next/Back, review, home flows
- [architecture.md](architecture.md) — product modes, phased delivery, DB gate
- [deck-output-format.md](../../product/deck-output-format.md) — `.deck.json` contract
- [backlog/web-ui.md](../../roadmap/backlog/web-ui.md) — UX7e–UX7g backlog
