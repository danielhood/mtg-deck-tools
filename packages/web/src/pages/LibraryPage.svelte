<script lang="ts">
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import {
    listDecks,
    type DeckLibraryEntry,
    type LibrarySort,
    type WizardMeta,
  } from "../lib/api";
  import { cacheDeck } from "../lib/deck-cache";
  import { resetDraft } from "../lib/criteria";
  import { formatPrice, formatTagLabel, pipMiniClass } from "../lib/format";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let query = $state("");
  let sort = $state<LibrarySort>("saved_at");
  let decks = $state<DeckLibraryEntry[]>([]);
  let loading = $state(true);
  let error = $state("");
  let reloadToken = $state(0);

  $effect(() => {
    if (!meta.db_ready) {
      navigate("/", true);
      return;
    }
    loading = true;
    error = "";
    void reloadToken;
    const q = query.trim();
    listDecks({ q: q || undefined, sort })
      .then((rows) => {
        decks = rows;
        loading = false;
      })
      .catch((err: Error) => {
        error = err.message;
        decks = [];
        loading = false;
      });
  });

  function formatSavedAt(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function buildAnother(): void {
    resetDraft();
    navigate("/build/1");
  }

  async function loadAndOpen(entry: DeckLibraryEntry): Promise<void> {
    try {
      const { getDeck } = await import("../lib/api");
      const detail = await getDeck(entry.id);
      cacheDeck({
        id: detail.id,
        name: detail.name,
        deck: detail.deck,
        returnTo: "/library",
      });
      navigate(`/deck/${detail.id}`);
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to load deck.";
    }
  }
</script>

<div class="library-body">
  <section class="library-toolbar" aria-label="Library filters">
    <label class="search-field">
      <span class="search-icon" aria-hidden="true">⌕</span>
      <input
        type="search"
        placeholder="Search decks…"
        bind:value={query}
        aria-label="Search saved decks"
      />
    </label>
    <div class="sort-row">
      <span class="sort-label">Sort by</span>
      <select class="sort-select" bind:value={sort} aria-label="Sort saved decks">
        <option value="saved_at">Recently saved</option>
        <option value="name">Name</option>
        <option value="commander">Commander</option>
      </select>
    </div>
  </section>

  {#if loading}
    <LoadingState message="Loading library…" />
  {:else if error}
    <ErrorState message={error} onretry={() => (reloadToken += 1)} />
  {:else if !decks.length}
    <section class="library-empty" aria-label="Empty library">
      <p>No saved decks yet.</p>
      <button class="btn btn-primary" type="button" onclick={() => navigate("/build/1")}>
        Build new deck
      </button>
    </section>
  {:else}
    <div class="deck-grid" role="list">
      {#each decks as entry (entry.id)}
        <button
          type="button"
          class="deck-card"
          role="listitem"
          onclick={() => void loadAndOpen(entry)}
        >
          {#if entry.commander_image_uri}
            <img src={entry.commander_image_uri} alt="" class="deck-card-art" />
          {:else}
            <div class="deck-card-art deck-card-art-placeholder" aria-hidden="true"></div>
          {/if}
          <div class="deck-card-body">
            <div class="deck-card-name">{entry.name}</div>
            {#if entry.commander_names.length}
              <div class="deck-card-commander">{entry.commander_names.join(" / ")}</div>
            {/if}
            {#if entry.colors.length}
              <div class="ci-pips" aria-label={`Colors ${entry.colors.join(" ")}`}>
                {#each entry.colors as color (color)}
                  <span class="ci-pip {pipMiniClass(color)}">{color}</span>
                {/each}
              </div>
            {/if}
            {#if entry.themes.length}
              <div class="theme-tags">
                {#each entry.themes as theme (theme)}
                  <span class="theme-tag">{formatTagLabel(theme)}</span>
                {/each}
              </div>
            {/if}
            <div class="deck-card-meta">
              {#if entry.estimated_price_usd != null}
                {formatPrice(entry.estimated_price_usd)}
              {:else}
                —
              {/if}
              · {formatSavedAt(entry.saved_at)}
            </div>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<div class="library-footer library-footer-stack">
  <button class="btn btn-primary" type="button" onclick={buildAnother}>Build another deck</button>
  <button class="btn btn-back" type="button" onclick={() => navigate("/")}>Home</button>
</div>
