# Web UI — navigation patterns

**Status:** Planning — UX7c patterns locked.

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

**Forward:** Generate → `/build/result` on success.

---

## Home

Applies to `/`.

| Pattern | Rule |
| --- | --- |
| Primary action | **Build new deck** → `/build/1` when DB ready |
| DB missing | Build disabled; banner on home — see [architecture.md](architecture.md) § Database gate |
| Future | Library → `/library` (**UX7f**); resume deck → `/deck/:id` (**UX7e**) — disabled or hidden until shipped |

---

## Result

Applies to `/build/result`.

| Pattern | Rule |
| --- | --- |
| Build another | → `/` or `/build/1` |
| Enhanced deck view | Deferred (**UX7e**) |

---

## Future routes (UX7e+)

Detailed iterate/view navigation (swap, slot regen, library load) is specified with **UX11** and **UX7f** in [user-experience.md](../dependency-engine/user-experience.md).

---

## References

- [routes.md](routes.md) — path map
- [user-experience.md](../dependency-engine/user-experience.md) § UX7c — scope and wizard decisions
