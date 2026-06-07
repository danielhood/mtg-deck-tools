<script lang="ts">
  import type { Snippet } from "svelte";
  import type { WizardMeta } from "../lib/api";

  interface Props {
    meta: WizardMeta | null;
    children: Snippet;
    footer?: Snippet;
  }

  let { meta, children, footer }: Props = $props();
</script>

<div class="app-root">
  <header class="app-header">
    <div class="app-brand">
      <div class="app-mark" aria-hidden="true"></div>
      <div>
        <div class="app-title">MTG Deck Tools</div>
        <div class="app-subtitle">Commander deck builder</div>
      </div>
    </div>
    {#if meta}
      <span class="status-pill" class:warn={!meta.db_ready}>
        {meta.db_ready ? "DB ready" : "DB missing"}
      </span>
    {/if}
  </header>

  <main class="app-main">
    {@render children()}
  </main>

  {#if footer}
    {@render footer()}
  {/if}
</div>
