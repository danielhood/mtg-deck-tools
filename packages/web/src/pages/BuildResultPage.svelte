<script lang="ts">
  import CardLightbox from "../components/CardLightbox.svelte";
  import { clearDraft } from "../lib/criteria";
  import { buildCardIndex, lookupCard, type DeckCardPreview } from "../lib/deck-cards";
  import { renderMarkdown } from "../lib/markdown";
  import { clearResult, loadResult, type GenerateResultState } from "../lib/result";
  import { navigate } from "../lib/router";

  let stored = $state<GenerateResultState | null>(loadResult());
  let previewCard = $state<DeckCardPreview | null>(null);
  let previewEl = $state<HTMLElement | null>(null);

  $effect(() => {
    if (!stored) navigate("/", true);
  });

  const html = $derived(stored ? renderMarkdown(stored.markdown) : "");
  const cardIndex = $derived(buildCardIndex(stored?.deck ?? null));

  $effect(() => {
    const el = previewEl;
    if (!el) return;

    const handlePreviewClick = (event: MouseEvent): void => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest("a");
      if (!anchor || !anchor.href.includes("scryfall.com")) return;
      event.preventDefault();
      const card = lookupCard(cardIndex, anchor.href);
      if (card) previewCard = card;
    };

    el.addEventListener("click", handlePreviewClick);
    return () => el.removeEventListener("click", handlePreviewClick);
  });

  function buildAnother(): void {
    clearDraft();
    clearResult();
    navigate("/");
  }
</script>

{#if stored}
  <div class="result-body">
    <section class="result-intro">
      <h1>Deck generated</h1>
      <p>Preview of the Markdown deck file returned by generate.</p>
    </section>

    <article class="deck-preview" aria-label="Rendered deck Markdown" bind:this={previewEl}>
      {@html html}
    </article>
  </div>

  <div class="result-footer">
    <button class="btn btn-primary" type="button" onclick={buildAnother}>Build another deck</button>
  </div>

  <CardLightbox
    open={previewCard != null}
    name={previewCard?.name ?? ""}
    imageUri={previewCard?.image_uri ?? null}
    subtitle={previewCard?.type_line ?? null}
    onclose={() => (previewCard = null)}
  />
{/if}
