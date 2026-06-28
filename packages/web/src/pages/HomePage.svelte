<script lang="ts">
  import {
    importDeckFromText,
    listDecks,
    previewDeckImportFromText,
    type ImportDeckPreviewResponse,
  } from "../lib/api";
  import type { WizardMeta } from "../lib/api";
  import DbBanner from "../components/DbBanner.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import { cacheDeck } from "../lib/deck-cache";
  import { IMPORT_BUSY_LEAD, IMPORT_BUSY_NOTE, REFRESH_CONFIRM_MESSAGE, runCardImport } from "../lib/card-import";
  import { downloadDeckImportTemplate } from "../lib/deck-import-template";
  import { resetDraft } from "../lib/criteria";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
    onMetaReload?: () => void;
  }

  let { meta, onMetaReload }: Props = $props();

  let latestDeckId = $state<string | null>(null);
  let libraryReady = $state(false);
  let importing = $state(false);
  let importError = $state("");
  let progressMessage = $state(IMPORT_BUSY_LEAD);
  let refreshConfirmOpen = $state(false);
  let deckImporting = $state(false);
  let deckPreviewing = $state(false);
  let deckImportError = $state("");
  let deckImportText = $state("");
  let deckPreview = $state<ImportDeckPreviewResponse | null>(null);
  let deckFileInput = $state<HTMLInputElement | null>(null);

  const actionsDisabled = $derived(!meta.db_ready || importing || deckImporting || deckPreviewing);
  const importReady = $derived(deckPreview?.summary.ready === true);

  $effect(() => {
    if (importing) refreshConfirmOpen = false;
  });

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

  function clearDeckPreview(): void {
    deckPreview = null;
  }

  async function startImport(): Promise<void> {
    if (importing) return;
    importing = true;
    importError = "";
    progressMessage = IMPORT_BUSY_LEAD;
    try {
      await runCardImport((message) => {
        progressMessage = message;
      });
      onMetaReload?.();
    } catch (err) {
      importError = err instanceof Error ? err.message : "Import failed";
    } finally {
      importing = false;
    }
  }

  async function confirmRefresh(): Promise<void> {
    if (importing || !meta.db_ready) return;
    refreshConfirmOpen = false;
    await startImport();
  }

  function openRefreshConfirm(): void {
    if (importing) return;
    refreshConfirmOpen = true;
  }

  function cancelRefreshConfirm(): void {
    refreshConfirmOpen = false;
  }

  function startBuild(): void {
    if (actionsDisabled) return;
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

  function openDeckFilePicker(): void {
    if (deckImporting || deckPreviewing || importing || !meta.db_ready) return;
    deckImportError = "";
    deckFileInput?.click();
  }

  async function previewDeckImport(): Promise<void> {
    const trimmed = deckImportText.trim();
    if (!trimmed) {
      deckImportError = "Paste a deck list or choose a text file.";
      clearDeckPreview();
      return;
    }
    if (deckPreviewing || deckImporting || importing || !meta.db_ready) return;

    deckPreviewing = true;
    deckImportError = "";
    try {
      deckPreview = await previewDeckImportFromText({ text: trimmed });
    } catch (err) {
      clearDeckPreview();
      deckImportError = err instanceof Error ? err.message : "Preview failed.";
    } finally {
      deckPreviewing = false;
    }
  }

  async function submitDeckImport(): Promise<void> {
    const trimmed = deckImportText.trim();
    if (!trimmed) {
      deckImportError = "Paste a deck list or choose a text file.";
      return;
    }
    if (!importReady) {
      deckImportError = "Preview the deck list and fix unresolved names before importing.";
      return;
    }

    deckImporting = true;
    deckImportError = "";
    try {
      const detail = await importDeckFromText({ text: trimmed });
      cacheDeck({
        id: detail.id,
        name: detail.name,
        deck: detail.deck,
        returnTo: "/",
      });
      navigate(`/deck/${detail.id}`);
    } catch (err) {
      deckImportError = err instanceof Error ? err.message : "Import failed.";
    } finally {
      deckImporting = false;
    }
  }

  async function onDeckFileSelected(event: Event): Promise<void> {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    try {
      deckImportText = await file.text();
      clearDeckPreview();
      deckImportError = "";
    } catch {
      deckImportError = "Could not read the selected file.";
    } finally {
      input.value = "";
    }
  }

  function previewStatusLabel(status: string): string {
    if (status === "resolved") return "Resolved";
    if (status === "unknown") return "Unknown";
    if (status === "ambiguous") return "Ambiguous";
    return status;
  }
</script>

<DbBanner
  {meta}
  {importing}
  {importError}
  {progressMessage}
  onDownload={() => void startImport()}
/>

{#if importing && meta.db_ready}
  <LoadingState
    message={progressMessage}
    detail={progressMessage === IMPORT_BUSY_LEAD ? IMPORT_BUSY_NOTE : undefined}
  />
{/if}

<section class="hero">
  <h1>Build a new deck</h1>
  <p>
    {#if meta.db_ready}
      Walk through the <span class="hero-accent">7-step wizard</span> to generate a Commander deck with
      dependency-aware card selection.
    {:else}
      The build wizard needs a local card database. Download card data once, then return here to start.
    {/if}
  </p>
</section>

<section class="actions">
  <button class="btn btn-primary" type="button" disabled={actionsDisabled} onclick={startBuild}>
    Build new deck
  </button>
  {#if !meta.db_ready && !importing}
    <p class="btn-hint">Unavailable until import completes.</p>
  {/if}
  {#if latestDeckId}
    <button
      class="btn btn-secondary"
      type="button"
      disabled={importing}
      onclick={() => void viewLastDeck()}
    >
      View last deck
    </button>
  {/if}
  {#if meta.db_ready}
    <button
      class="btn btn-secondary"
      type="button"
      disabled={importing}
      onclick={() => navigate("/library")}
    >
      Saved library
    </button>
  {/if}
</section>

{#if meta.db_ready}
  <section class="deck-import-section" aria-label="Import deck from text">
    <p class="future-label">Import existing deck</p>
    <p class="deck-import-copy">
      Paste a plain-text list of card names or upload a <code>.txt</code> file. Preview resolves card
      names before saving to your library.
    </p>
    <label class="deck-import-field">
      <span class="deck-import-field-label">Deck list</span>
      <textarea
        class="deck-import-textarea"
        bind:value={deckImportText}
        oninput={clearDeckPreview}
        rows="8"
        placeholder={"Commander\nYour Commander Name Here\n\nDeck\n1x Sol Ring\n..."}
        disabled={actionsDisabled}
        aria-describedby="deck-import-hint"
      ></textarea>
    </label>
    <p id="deck-import-hint" class="deck-import-hint">
      One card per line; optional Commander and Deck section headers.
    </p>
    <div class="deck-import-actions">
      <button
        class="btn btn-primary"
        type="button"
        onclick={() => void previewDeckImport()}
        disabled={actionsDisabled || !deckImportText.trim()}
        aria-busy={deckPreviewing}
      >
        {deckPreviewing ? "Previewing…" : "Preview"}
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        onclick={() => void submitDeckImport()}
        disabled={actionsDisabled || !importReady}
        aria-busy={deckImporting}
      >
        {deckImporting ? "Importing…" : "Import deck"}
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        onclick={downloadDeckImportTemplate}
        disabled={actionsDisabled}
      >
        Download template
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        onclick={openDeckFilePicker}
        disabled={actionsDisabled}
      >
        Choose text file…
      </button>
      <input
        bind:this={deckFileInput}
        class="deck-import-file"
        type="file"
        accept=".txt,text/plain"
        onchange={(event) => void onDeckFileSelected(event)}
        aria-hidden="true"
        tabindex="-1"
      />
    </div>
    {#if deckPreview}
      <div class="deck-preview-panel" aria-live="polite">
        <p class="deck-preview-summary">
          {#if deckPreview.summary.ready}
            All {deckPreview.summary.resolved_count} card name(s) resolved. You can import this deck.
          {:else}
            {deckPreview.summary.resolved_count} resolved,
            {deckPreview.summary.unknown_count} unknown,
            {deckPreview.summary.ambiguous_count} ambiguous — fix names before importing.
          {/if}
        </p>
        <div class="deck-preview-table-wrap">
          <table class="deck-preview-table">
            <thead>
              <tr>
                <th scope="col">Line</th>
                <th scope="col">Input</th>
                <th scope="col">Qty</th>
                <th scope="col">Status</th>
                <th scope="col">Resolved name</th>
              </tr>
            </thead>
            <tbody>
              {#each deckPreview.commanders as line}
                <tr class:deck-preview-row-error={line.status !== "resolved"}>
                  <td>—</td>
                  <td>{line.input_name}</td>
                  <td>—</td>
                  <td>
                    <span class="deck-preview-status" data-status={line.status}>
                      {previewStatusLabel(line.status)}
                    </span>
                  </td>
                  <td>{line.name ?? "—"}</td>
                </tr>
              {/each}
              {#each deckPreview.maindeck as line}
                <tr class:deck-preview-row-error={line.status !== "resolved"}>
                  <td>{line.line_number ?? "—"}</td>
                  <td>{line.input_name}</td>
                  <td>{line.quantity ?? "—"}</td>
                  <td>
                    <span class="deck-preview-status" data-status={line.status}>
                      {previewStatusLabel(line.status)}
                    </span>
                  </td>
                  <td>{line.name ?? "—"}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/if}
    {#if deckImportError}
      <p class="deck-import-error" role="alert">{deckImportError}</p>
    {/if}
  </section>
{/if}

{#if meta.db_ready && libraryReady && !latestDeckId}
  <section class="future-section">
    <p class="future-label">Library</p>
    <p class="library-hint">Your generated decks will appear in the saved library.</p>
  </section>
{/if}

{#if meta.db_ready}
  <section class="card-data-section">
    {#if refreshConfirmOpen}
      <div
        id="refresh-confirm-panel"
        class="refresh-confirm"
        role="region"
        aria-labelledby="refresh-confirm-title"
      >
        <h2 id="refresh-confirm-title" class="refresh-confirm-title">Refresh card data?</h2>
        <p class="refresh-confirm-copy">{REFRESH_CONFIRM_MESSAGE}</p>
        <div class="refresh-confirm-actions">
          <button class="btn btn-back" type="button" onclick={cancelRefreshConfirm}>
            Cancel
          </button>
          <button class="btn btn-primary" type="button" onclick={() => void confirmRefresh()}>
            Refresh now
          </button>
        </div>
      </div>
    {:else}
      <button
        class="btn-text"
        type="button"
        disabled={importing}
        aria-controls="refresh-confirm-panel"
        onclick={openRefreshConfirm}
      >
        Refresh card data
      </button>
      <p class="card-data-hint">
        Re-download Scryfall oracle bulk and rebuild the database when you want a newer snapshot.
      </p>
    {/if}
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

  .deck-import-section {
    margin-top: 8px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .deck-import-copy {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.45;
    margin: 0;
  }

  .deck-import-copy code {
    font-size: 12px;
  }

  .deck-import-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .deck-import-field-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
  }

  .deck-import-textarea {
    width: 100%;
    min-height: 140px;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg);
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    line-height: 1.45;
    resize: vertical;
  }

  .deck-import-textarea:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .deck-import-hint {
    margin: 0;
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .deck-import-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .deck-import-actions .btn {
    width: 100%;
  }

  .deck-import-file {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .deck-preview-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg-subtle, #f8fafc);
  }

  .deck-preview-summary {
    margin: 0;
    font-size: 13px;
    line-height: 1.45;
    color: var(--text-muted);
  }

  .deck-preview-table-wrap {
    overflow-x: auto;
  }

  .deck-preview-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .deck-preview-table th,
  .deck-preview-table td {
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
  }

  .deck-preview-table th {
    font-weight: 600;
    color: var(--text-muted);
  }

  .deck-preview-row-error {
    background: rgba(185, 28, 28, 0.06);
  }

  .deck-preview-status[data-status="resolved"] {
    color: var(--green-700, #15803d);
    font-weight: 600;
  }

  .deck-preview-status[data-status="unknown"],
  .deck-preview-status[data-status="ambiguous"] {
    color: var(--red-700, #b91c1c);
    font-weight: 600;
  }

  .deck-import-error {
    margin: 0;
    font-size: 12px;
    color: var(--red-700, #b91c1c);
  }

  .btn-hint {
    font-size: 12px;
    color: var(--disabled-text);
    text-align: center;
    line-height: 1.4;
    margin-top: -4px;
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

  .card-data-section {
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  }

  .btn-text {
    background: none;
    border: none;
    padding: 0;
    min-height: var(--touch-min);
    font-size: 13px;
    font-weight: 600;
    color: var(--blue-700);
    text-align: left;
    cursor: pointer;
  }

  .btn-text:disabled {
    color: var(--disabled-text);
    cursor: not-allowed;
  }

  .card-data-hint {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.45;
  }

  .refresh-confirm {
    margin-top: 8px;
    padding: 14px;
    border-radius: 10px;
    border: 1px solid var(--warn-700);
    background: var(--warn-100);
  }

  .refresh-confirm-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--warn-700);
    margin-bottom: 8px;
    line-height: 1.3;
  }

  .refresh-confirm-copy {
    font-size: 13px;
    line-height: 1.45;
    color: var(--warn-700);
    margin-bottom: 12px;
  }

  .refresh-confirm-actions {
    display: flex;
    gap: 10px;
  }

  .refresh-confirm-actions .btn {
    flex: 1;
    min-height: 40px;
  }
</style>
