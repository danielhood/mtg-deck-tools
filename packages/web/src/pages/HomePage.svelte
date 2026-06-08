<script lang="ts">
  import type { WizardMeta } from "../lib/api";
  import DbBanner from "../components/DbBanner.svelte";
  import { resetDraft } from "../lib/criteria";
  import { getActiveDeckId } from "../lib/result";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  const activeDeckId = $derived(getActiveDeckId());

  function startBuild(): void {
    if (!meta.db_ready) return;
    resetDraft();
    navigate("/build/1");
  }

  function viewLastDeck(): void {
    const id = getActiveDeckId();
    if (id) navigate(`/deck/${id}`);
  }
</script>

<DbBanner {meta} />

<section class="hero">
  <h1>Build a new deck</h1>
  <p>
    Walk through the <span class="hero-accent">7-step wizard</span> to generate a Commander deck with
    dependency-aware card selection.
  </p>
</section>

<section class="actions">
  <button class="btn btn-primary" type="button" disabled={!meta.db_ready} onclick={startBuild}>
    Build new deck
  </button>
  {#if activeDeckId}
    <button class="btn btn-secondary" type="button" onclick={viewLastDeck}>View last deck</button>
  {/if}
</section>

<section class="future-section">
  <p class="future-label">Coming later</p>
  <button class="btn btn-secondary" type="button" disabled>Saved library</button>
</section>

<style>
  .hero h1 {
    font-size: 22px;
    font-weight: 700;
    color: var(--blue-900);
    margin-bottom: 8px;
  }

  .hero p {
    font-size: 14px;
    line-height: 1.5;
    color: var(--text-muted);
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .actions .btn-primary {
    width: 100%;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
  }

  .future-section {
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  }

  .future-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 12px;
  }

  .future-section .btn-secondary {
    width: 100%;
  }
</style>
