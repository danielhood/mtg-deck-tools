# Web UI — navigation patterns

**Status:** **UX7 MVP shipped** (UX7c + **UX7e** + **UX7f** + **UX7d**). **UX11** iterate patterns planned — [navigation.md](navigation.md) § Deck view — iterate.

How users move between routes. Route map: [routes.md](routes.md). Screen details: [screens.md](screens.md).

---

## Build wizard (steps 1–7)

Applies to `/build/1` … `/build/7`.

| Pattern | Rule |
| --- | --- |
| Flow | **Linear only** — no jump to arbitrary steps (differs from CLI UX4 jump menu) |
| Primary controls | **Next** / **Back** always visible |
| Step indicator | “Step N of 7” — review is separate, not counted in the 7 |
| Mobile enhancement | Optional **back swipe** only; never replaces buttons |

**Forward:** Next on step 7 → `/build/review`.

---

## Review and preflight

Applies to `/build/review`.

| Pattern | Rule |
| --- | --- |
| Back | → `/build/7` only; user walks forward through steps to reach review again |
| Preflight warnings | Inline on review screen (not modal) — see [screens.md](screens.md) |
| Generate | Enabled even when warnings present (warn-only, same as CLI) |
| Jump to step N | **Not in UX7c** — no fix links from review |

**Forward:** Generate → `/deck/:id` on success (**UX7e**). `/build/result` redirects to active deck id when session has one.

---

## Home

Applies to `/`.

| Pattern | Rule |
| --- | --- |
| Primary action | **Build new deck** → `/build/1` when DB ready |
| DB missing | Build disabled; banner on home — see [architecture.md](architecture.md) § Database gate |
| View last deck | → `/deck/:id` for most recently saved library deck (**UX7f**) |
| Saved library | → `/library` when DB ready (**UX7f**) |

---

## Result (compat)

Applies to `/build/result`.

| Pattern | Rule |
| --- | --- |
| Redirect | → `/library` on load |
| Generate | Review **Generate** → `/deck/:id` directly (skips result route) |
| Build another | Deck view footer — clears wizard draft → `/build/1` |

---

## Deck view

Applies to `/deck/:id`.

| Pattern | Rule |
| --- | --- |
| Entry | After generate (auto-saved); home **View last deck**; library **Open** (**UX7f**) |
| Unknown id | → `/` |
| Build another | Footer — clear wizard draft → `/build/1` |
| Delete deck | Footer — confirm modal → `DELETE /api/v1/decks/{id}` → `returnTo` from session cache (default `/library`) (**UX7f**) |
| Rename | Pencil beside deck label — confirm modal → `PATCH /api/v1/decks/{id}` (**UX7f**) |
| Dependencies | Collapsible **Dependencies** panel — profile summaries + issue drill-down; see [screens.md](screens.md) § Dependency dashboard |
| Library | Footer bottom row — → `/library` |
| Home | Footer bottom row — → `/` |

`returnTo` is stored in session cache (`mtg-deck-cache-{id}`) when navigating from home, library, or generate. It is used for **delete** redirect, not for a single context-sensitive Back label.

**Iterate (UX11):** see § Deck view — iterate below.

---

## Deck view — iterate (**UX11**)

Applies to `/deck/:id` edit mode. API: [iterate-api.md](iterate-api.md).

| Pattern | Rule |
| --- | --- |
| Enter edit | **Edit deck** in label row |
| Lock toggle | Available in view and edit mode — `PATCH` deck body |
| Slot regen | **Regenerate** on slot heading — confirm → stay on deck view |
| Swap | Select rows → **Swap (N)** (center of bar) → inline diff → stay on deck view |
| Cancel selection | **Clear** (left on swap bar) |
| Advanced swap | **Advanced…** (right on swap bar) |
| Loading | Disable iterate controls + footer actions while API in flight |
| Cache | Update `mtg-deck-cache-{id}` after every successful PATCH/refill/swap |

---

## Library

Applies to `/library` (**UX7f**).

| Pattern | Rule |
| --- | --- |
| Entry | Home **Saved library**; deck view back navigation |
| DB missing | Blocked — same gate as wizard |
| Open card | Tap library card → load deck into session cache → `/deck/:id` |
| Rename | Deck view — pencil beside deck label → modal; `PATCH /api/v1/decks/{id}` |
| Delete | **Deck view only** — footer **Delete deck** → confirm modal; `DELETE /api/v1/decks/{id}` → redirect `/` (not on library grid) |
| Search / sort | Client or query params on `GET /api/v1/decks` |

**Deferred:** folders; import; JSON download; save-as / clone.

---

## References

- [routes.md](routes.md) — path map
- [user-experience.md](../dependency-engine/user-experience.md) § UX7c — scope and wizard decisions
- [iterate-api.md](iterate-api.md) — UX11 iterate HTTP API
