<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import type { WizardMeta } from "../lib/api";
  import { formatColors } from "../lib/format";
  import { loadDraft, saveDraft, type ColorFilter, type WizardDraft } from "../lib/criteria";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());

  const PIPS = [
    { id: "W", label: "White" },
    { id: "U", label: "Blue" },
    { id: "B", label: "Black" },
    { id: "R", label: "Red" },
    { id: "G", label: "Green" },
  ] as const;

  $effect(() => {
    saveDraft(draft);
  });

  function setColorFilter(mode: ColorFilter): void {
    if (mode === "colorless") {
      draft = { ...draft, colorFilter: "colorless", colors: [] };
      return;
    }
    if (mode === "any") {
      draft = { ...draft, colorFilter: "any", colors: [] };
      return;
    }
    draft = { ...draft, colorFilter: "selected" };
  }

  function togglePip(id: string): void {
    const colors = new Set(draft.colors);
    if (colors.has(id)) colors.delete(id);
    else colors.add(id);
    draft = {
      ...draft,
      colorFilter: "selected",
      colors: [...colors].sort(),
    };
  }

  function summary(): string {
    if (draft.colorFilter === "colorless") return "Colorless commanders only";
    if (draft.colorFilter === "any") return "Any commander colors";
    return formatColors(draft.colors);
  }
</script>

<WizardChrome step={4} backRoute="/build/3" nextRoute="/build/5" dbReady={meta.db_ready}>
  <h2 class="section-title">Colors</h2>
  <p class="section-lead">Pick commander color identity constraints.</p>

  <div class="pip-grid">
    {#each PIPS as pip (pip.id)}
      <button
        type="button"
        class="pip"
        class:selected={draft.colorFilter === "selected" && draft.colors.includes(pip.id)}
        disabled={draft.colorFilter === "colorless"}
        onclick={() => togglePip(pip.id)}
        aria-label={pip.label}
      >
        {pip.id}
      </button>
    {/each}
  </div>

  <button
    type="button"
    class="void-btn"
    class:selected={draft.colorFilter === "colorless"}
    onclick={() => setColorFilter(draft.colorFilter === "colorless" ? "any" : "colorless")}
  >
    Colorless (void)
  </button>

  <button type="button" class="linkish" onclick={() => setColorFilter("any")}>Clear to any colors</button>

  <div class="summary-box"><strong>Selection:</strong> {summary()}</div>
</WizardChrome>

<style>
  .pip-grid {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .pip {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    border: 2px solid var(--border);
    background: var(--bg);
    font-weight: 700;
    cursor: pointer;
  }

  .pip.selected {
    background: #facc15;
    border-color: #ca8a04;
  }

  .pip:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .void-btn {
    min-height: var(--touch-min);
    border-radius: 10px;
    border: 1px dashed var(--border);
    background: var(--surface);
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
  }

  .void-btn.selected {
    border-color: var(--blue-700);
    background: var(--blue-100);
  }

  .linkish {
    border: none;
    background: none;
    color: var(--blue-700);
    font-size: 12px;
    cursor: pointer;
    text-align: left;
    padding: 0;
  }
</style>
