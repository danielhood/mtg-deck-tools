<script lang="ts">
  import type { Snippet } from "svelte";
  import type { WizardMeta } from "../lib/api";

  interface Props {
    meta: WizardMeta | null;
    wizardStep?: number | null;
    phasePill?: "review" | "result" | "deck" | "library" | null;
    children: Snippet;
    footer?: Snippet;
  }

  let { meta, wizardStep = null, phasePill = null, children, footer }: Props = $props();

  const subtitle = $derived.by(() => {
    if (phasePill === "library") return "Saved decks";
    if (wizardStep != null || phasePill === "review" || phasePill === "result") {
      return "Build wizard";
    }
    return "Commander builder";
  });
  const statusLabel = $derived(
    meta == null ? null : meta.db_ready ? "Ready" : "DB missing",
  );

  const isWizardShell = $derived(wizardStep != null || phasePill === "review");
</script>

<div class="app-root" class:app-root-wizard={isWizardShell}>
  <header class="app-header">
    <div class="app-brand">
      <div class="app-mark" aria-hidden="true"></div>
      <div>
        <div class="app-title">MTG Deck Tools</div>
        <div class="app-subtitle">{subtitle}</div>
      </div>
    </div>
    {#if wizardStep != null}
      <span class="step-pill">Step {wizardStep} of 7</span>
    {:else if phasePill === "review"}
      <span class="review-pill">Review</span>
    {:else if phasePill === "result"}
      <span class="result-pill">Result</span>
    {:else if phasePill === "deck"}
      <span class="deck-pill">Deck</span>
    {:else if phasePill === "library"}
      <span class="library-pill">Library</span>
    {:else if statusLabel}
      <span class="status-pill" class:warn={meta && !meta.db_ready}>{statusLabel}</span>
    {/if}
  </header>

  <main class="app-main" class:app-main-wizard={isWizardShell}>
    {@render children()}
  </main>

  {#if footer}
    {@render footer()}
  {/if}
</div>
