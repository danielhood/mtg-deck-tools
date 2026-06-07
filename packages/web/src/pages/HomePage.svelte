<script lang="ts">
  import type { WizardMeta } from "../lib/api";
  import DbBanner from "../components/DbBanner.svelte";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  function startBuild(): void {
    if (meta.db_ready) navigate("/build/1");
  }
</script>

<DbBanner {meta} />

<section class="hero">
  <h1 class="section-title">Build a Commander deck</h1>
  <p class="section-lead">
    Walk through themes, mechanics, synergy, colors, budget, commander, and rarity — then generate a
    tuned 100-card list.
  </p>
</section>

<button class="btn btn-primary" type="button" disabled={!meta.db_ready} onclick={startBuild}>
  Build new deck
</button>

{#if meta.db_ready && meta.total_cards}
  <p class="section-lead">{meta.total_cards.toLocaleString()} cards indexed.</p>
{/if}

<style>
  .hero {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
</style>
