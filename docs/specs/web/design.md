# Web UI — visual design

**Status:** Planning — UX7c tokens locked; dark mode deferred.

Overall UI design decisions for `packages/web/`. Layout per screen: [screens.md](screens.md). Mock and review process: [wireframes/README.md](wireframes/README.md).

---

## Theme

| Topic | UX7c | Later |
| --- | --- | --- |
| Color mode | **Light only** | Dark mode after GUI stabilizes |
| Reference apps | None — major layout decisions require product confirmation | — |

---

## Palette and typography

| Token | Value |
| --- | --- |
| Background / surfaces | White |
| Primary UI | Blue — **≤4 fixed shades** (designer discretion within constraint) |
| Text | Black |
| Accent / highlight | Magenta (single accent family) |
| Font | **Verdana** (system sans-serif fallback acceptable) |

---

## Media

| Asset | UX7c | Later |
| --- | --- | --- |
| Card art (Scryfall CDN) | Not used — result is MD HTML | **UX7e** enhanced deck view |
| Icons | TBD at implementation — keep minimal | — |

---

## Layout baseline

- **Mobile-first:** design at **375px** width; no horizontal scroll on wizard steps ([architecture.md](architecture.md) success criteria).
- Single-column wizard; touch-friendly controls for future swap/lock (**UX11**).

---

## References

- [architecture.md](architecture.md) — mobile-first principles
- [routes.md](routes.md) — client routes
