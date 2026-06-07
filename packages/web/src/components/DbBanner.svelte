<script lang="ts">
  import type { WizardMeta } from "../lib/api";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();
</script>

{#if !meta.db_ready}
  <div class="db-banner" role="alert">
    Card database not found at <code>{meta.db_path}</code>. Import once with
    <code>mtg-deck-tools import</code> before building decks.
  </div>
{/if}
