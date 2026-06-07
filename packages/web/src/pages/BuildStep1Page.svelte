<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import {
    getSlotTemplateDefaults,
    getThemes,
    type SlotTemplateDefaults,
    type ThemeChoice,
    type WizardMeta,
  } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let themes = $state<ThemeChoice[]>([]);
  let slots = $state<SlotTemplateDefaults | null>(null);
  let error = $state("");

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    Promise.all([getThemes(), getSlotTemplateDefaults()])
      .then(([themeRows, slotDefaults]) => {
        themes = themeRows;
        slots = slotDefaults;
        if (!Object.keys(draft.slot_template).length) {
          draft = { ...draft, slot_template: { ...slotDefaults.default } };
        }
      })
      .catch((err: Error) => {
        error = err.message;
      });
  });

  function toggleTheme(id: string): void {
    const selected = new Set(draft.themes);
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
    draft = { ...draft, themes: [...selected].sort() };
  }
</script>

<WizardChrome step={1} backRoute="/" nextRoute="/build/2" dbReady={meta.db_ready}>
  <h2 class="section-title">Themes &amp; slot template</h2>
  <p class="section-lead">Pick archetype themes. Slot template uses project defaults for UX7c.</p>

  {#if error}
    <p class="inline-warning">{error}</p>
  {/if}

  <div class="chip-grid" role="group" aria-label="Theme selection">
    {#each themes as theme (theme.id)}
      <button
        type="button"
        class="chip"
        class:selected={draft.themes.includes(theme.id)}
        onclick={() => toggleTheme(theme.id)}
      >
        {theme.id}
      </button>
    {/each}
  </div>

  {#if slots}
    <div class="summary-box">
      <strong>Commander slots:</strong> {slots.commander_slots}<br />
      <strong>Maindeck slots:</strong> {slots.maindeck_total}<br />
      <strong>Total deck:</strong> {slots.deck_total} cards (default template)
    </div>
  {/if}
</WizardChrome>
