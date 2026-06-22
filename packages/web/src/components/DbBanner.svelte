<script lang="ts">
  import type { WizardMeta } from "../lib/api";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();
</script>

{#if !meta.db_ready}
  <div class="db-banner" role="alert">
    Card database not found at <code>{meta.db_path}</code>. Run
    <code>mtg-deck-tools import</code> or restart the server (automatic download on
    <code>serve</code> when <code>MTG_AUTO_DOWNLOAD=1</code>).
  </div>
{/if}
