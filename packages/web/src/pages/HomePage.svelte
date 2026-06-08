<script lang="ts">
  import type { WizardMeta } from "../lib/api";
  import { listDecks } from "../lib/api";
  import DbBanner from "../components/DbBanner.svelte";
  import { cacheDeck } from "../lib/deck-cache";
  import { resetDraft } from "../lib/criteria";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let latestDeckId = $state<string | null>(null);
  let libraryReady = $state(false);

  $effect(() => {
    if (!meta.db_ready) {
      latestDeckId = null;
      libraryReady = false;
      return;
    }
    listDecks({ limit: 1 })
      .then((rows) => {
        libraryReady = true;
        latestDeckId = rows.length ? rows[0].id : null;
      })
      .catch(() => {
        latestDeckId = null;
        libraryReady = false;
      });
  });

  function startBuild(): void {
    if (!meta.db_ready) return;
    resetDraft();
    navigate("/build/1");
  }

  async function viewLastDeck(): Promise<void> {
    if (!latestDeckId) return;
    try {
      const { getDeck } = await import("../lib/api");
      const detail = await getDeck(latestDeckId);
      cacheDeck({
        id: detail.id,
        name: detail.name,
        deck: detail.deck,
        returnTo: "/",
      });
      navigate(`/deck/${detail.id}`);
    } catch {
      navigate("/library");
    }
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
  {#if latestDeckId}
    <button class="btn btn-secondary" type="button" onclick={() => void viewLastDeck()}>
      View last deck
    </button>
  {/if}
  {#if meta.db_ready}
    <button class="btn btn-secondary" type="button" onclick={() => navigate("/library")}>
      Saved library
    </button>
  {/if}
</section>

{#if meta.db_ready && libraryReady && !latestDeckId}
  <section class="future-section">
    <p class="future-label">Library</p>
    <p class="library-hint">Your generated decks will appear in the saved library.</p>
  </section>
{/if}

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

  .actions .btn-secondary {
    width: 100%;
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
    margin-bottom: 8px;
  }

  .library-hint {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.45;
  }
</style>
