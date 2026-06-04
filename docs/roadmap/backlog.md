# Product backlog

Parked work — **not** the immediate focus. Promote to [active.md](active.md) only when selected as the next deliverable (typically after **UX7** or other active items complete).

Status as of 2026-06-04.

---

## UX and UI

| ID | Topic | Notes | Spec |
| --- | --- | --- | --- |
| UX8 | Progressive wizard constraints | Restrict choices by CI/commander/partial deck | [user-experience.md](../specs/dependency-engine/user-experience.md) § Progressive constraints |
| UX10 | Deck composition metrics | CMC distribution in MD/JSON; charts in UX7 | [deck-output-format.md](../product/deck-output-format.md) · [user-experience.md](../specs/dependency-engine/user-experience.md) § UX10 |
| UX11 | GUI deck editor (swap / lock) | Pinned cards survive refill/regen | [user-experience.md](../specs/dependency-engine/user-experience.md) § UX11 |
| — | Dependency swap packages CLI | `generate --swap-profile` — needs UX7 or CLI design | [user-experience.md](../specs/dependency-engine/user-experience.md) |

---

## Export and data

| Topic | Doc |
| --- | --- |
| Power level / salt | [open-questions.md](../product/open-questions.md) |
| Moxfield / Archidekt export | [deck-output-format.md](../product/deck-output-format.md) |
| Related token companion list | [deck-output-format.md](../product/deck-output-format.md) § Related token cards |
| Image gallery / diff on `.deck.json` | [deck-output-format.md](../product/deck-output-format.md) |
| Parquet / faster import | [technology-stack.md](../architecture/technology-stack.md) |
| DFC / adventure normalization | [problem-decomposition.md](../architecture/problem-decomposition.md) |
| Post-validation CR repair | Deferred — fill-time filters sufficient today |

---

## Dependency engine (domain backlog)

Optional dependency expansion rows: [dependency/backlog.md](dependency/backlog.md) (Priority 7 remainder, future candidates).

---

## References

| Doc | Role |
| --- | --- |
| [active.md](active.md) | Selected immediate work |
| [dependency/README.md](dependency/README.md) | Dependency roadmap index |
