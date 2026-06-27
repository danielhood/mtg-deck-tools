# Backlog — Web UI

Planned app: `packages/web/`. Promote the next row to [active.md](../active.md) before implementation.

Specs: [specs/web/README.md](../../specs/web/README.md) · [architecture.md](../../specs/web/architecture.md) · Package: [packages/web/README.md](../../packages/web/README.md). Shipped work: [changelog.md](../../history/changelog.md).

---

## Up next

| ID | Topic | Notes | Spec |
| --- | --- | --- | --- |
| **UX12** | Advanced swap & guided rebalance | Quick swap preserved; advanced sheet + preview API (v1); warning playbooks; named-card swap; Quick fix prototype; curve actions deferred (UX12f) | [advanced-swap-ux.md](../../specs/web/advanced-swap-ux.md) |

**Depends on:** **UX11** (shipped). **Parallel OK with:** cli-engine maintenance, doc-only.

**Slices:** UX12a contract → UX12b engine + preview → UX12c–e (sheet, issue strategies, named card) ship together; UX12f curve actions later.

---

## Platform notes (reference)

- **Platform:** Windows, Linux, macOS browsers + mobile layouts.
- **Engine:** Python only — no port.
- **Frontend:** Svelte 5 + Vite SPA.
- **CLI:** Automation and dogfood; interactive users target web.
- **Hosting:** Local-first `serve`; self-host / PaaS in [deployment.md](../../specs/web/deployment.md).
