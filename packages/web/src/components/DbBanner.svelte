<script lang="ts">
  import type { WizardMeta } from "../lib/api";
  import { IMPORT_BUSY_LEAD, IMPORT_BUSY_NOTE } from "../lib/card-import";

  interface Props {
    meta: WizardMeta;
    importing?: boolean;
    importError?: string;
    progressMessage?: string;
    onDownload?: () => void;
  }

  let {
    meta,
    importing = false,
    importError = "",
    progressMessage = IMPORT_BUSY_LEAD,
    onDownload,
  }: Props = $props();
</script>

{#if !meta.db_ready}
  <div class="db-banner" role="alert">
    <div class="db-banner-icon" aria-hidden="true">!</div>
    <div class="db-banner-body">
      <h2>Card database not found</h2>
      {#if importing}
        <div class="db-banner-progress" role="status" aria-live="polite" aria-busy="true">
          <span class="status-spinner" aria-hidden="true"></span>
          <div class="db-banner-progress-copy">
            <p>{progressMessage}</p>
            {#if progressMessage === IMPORT_BUSY_LEAD}
              <p class="db-banner-progress-note">{IMPORT_BUSY_NOTE}</p>
            {/if}
          </div>
        </div>
      {:else if importError}
        <p class="db-banner-error">{importError}</p>
        <button class="btn btn-primary db-banner-cta" type="button" onclick={() => onDownload?.()}>
          Try again
        </button>
      {:else}
        <p>
          Download Scryfall oracle bulk data and build the local database to use the build wizard.
        </p>
        <button class="btn btn-primary db-banner-cta" type="button" onclick={() => onDownload?.()}>
          Download card data
        </button>
      {/if}
    </div>
  </div>
{/if}
