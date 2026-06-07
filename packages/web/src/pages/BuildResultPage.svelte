<script lang="ts">
  import { clearDraft } from "../lib/criteria";
  import { renderMarkdown } from "../lib/markdown";
  import { clearResult, loadResult, type GenerateResultState } from "../lib/result";
  import { navigate } from "../lib/router";

  let stored = $state<GenerateResultState | null>(loadResult());

  $effect(() => {
    if (!stored) navigate("/", true);
  });

  const html = $derived(stored ? renderMarkdown(stored.markdown) : "");

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

    <article class="deck-preview" aria-label="Rendered deck Markdown">
      {@html html}
    </article>
  </div>

  <div class="result-footer">
    <button class="btn btn-primary" type="button" onclick={buildAnother}>Build another deck</button>
  </div>
{/if}
