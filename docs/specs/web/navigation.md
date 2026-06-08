# Web UI — navigation patterns

**Status:** UX7c patterns locked; **UX7e** deck view navigation locked.

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
| View last deck | → `/deck/:id` when session has active deck (**UX7e**) |
| Future | Library → `/library` (**UX7f**) — hidden until shipped |

---

## Result (compat)

Applies to `/build/result`.

| Pattern | Rule |
| --- | --- |
| Redirect | → `/deck/:id` when session has active deck id; else → `/` |
| Build another | Handled on deck view footer — clears session → `/` |

---

## Deck view

Applies to `/deck/:id`.

| Pattern | Rule |
| --- | --- |
| Entry | After generate; home **View last deck**; future library load (**UX7f**) |
| Unknown id | → `/` |
| Build another | Footer — clear wizard draft + session deck → `/` |
| Back | Browser back from deck view → prior route (review or home); no wizard step chrome |

**Deferred:** swap, slot regen, library picker — **UX11** / **UX7f** in [user-experience.md](../dependency-engine/user-experience.md).

---

## References

- [routes.md](routes.md) — path map
- [user-experience.md](../dependency-engine/user-experience.md) § UX7c — scope and wizard decisions
