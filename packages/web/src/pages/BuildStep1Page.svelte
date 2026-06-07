<script lang="ts">
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import {
    getSlotTemplateDefaults,
    getThemes,
    type SlotTemplateDefaults,
    type ThemeChoice,
    type WizardMeta,
  } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";
  import { chunk, formatSlotLabel, formatTagLabel } from "../lib/format";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let themes = $state<ThemeChoice[]>([]);
  let slots = $state<SlotTemplateDefaults | null>(null);
  let loading = $state(true);
  let error = $state("");
  let reload = $state(0);

  const themeRows = $derived(chunk(themes, 3));

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    loading = true;
    error = "";
    void reload;
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
      })
      .finally(() => {
        loading = false;
      });
  });

  function toggleTheme(id: string, checked: boolean): void {
    const selected = new Set(draft.themes);
    if (checked) selected.add(id);
    else selected.delete(id);
    draft = { ...draft, themes: [...selected].sort() };
  }
</script>

<WizardChrome step={1} backRoute="/" nextRoute="/build/2" dbReady={meta.db_ready}>
  <WizardIntro
    title="Themes & slot template"
    lead="Pick archetype tags for synergy cards and confirm deck slot counts."
  />

  {#if error}
    <ErrorState message={error} onretry={() => (reload += 1)} />
  {:else if loading}
    <LoadingState message="Loading themes and slot template…" />
  {/if}

  <section class="wizard-section" aria-labelledby="themes-heading">
    <SectionHeader
      id="themes-heading"
      title="Deck themes"
      description="Archetype tags that steer synergy slot picks. Select none or more."
    />

    <div class="chip-stack">
      {#each loading ? [] : themeRows as row (row.map((t) => t.id).join("-"))}
        <div class="chip-row">
          {#each row as theme (theme.id)}
            <label class="chip">
              <input
                type="checkbox"
                checked={draft.themes.includes(theme.id)}
                onchange={(e) => toggleTheme(theme.id, e.currentTarget.checked)}
              />
              {formatTagLabel(theme.id)}
            </label>
          {/each}
        </div>
      {/each}
    </div>
  </section>

  {#if slots}
    <section class="wizard-section" aria-labelledby="slots-heading">
      <SectionHeader
        id="slots-heading"
        title="Slot template"
        description="How many cards per deck role."
      />

      <div class="slot-panel">
        <div class="slot-panel-header">
          <h3>Default Commander template</h3>
          <p>Standard role counts for a 100-card deck.</p>
        </div>
        <div class="slot-grid" role="table" aria-label="Default slot counts">
          <div class="slot-row" role="row">
            <span class="slot-name">Commander</span>
            <span class="slot-count">{slots.commander_slots}</span>
          </div>
          {#each slots.order as slotId (slotId)}
            <div class="slot-row" role="row">
              <span class="slot-name">{formatSlotLabel(slotId, slots.labels)}</span>
              <span class="slot-count">{slots.default[slotId]}</span>
            </div>
          {/each}
          <div class="slot-row" role="row">
            <span class="slot-name">Total deck</span>
            <span class="slot-count">{slots.deck_total}</span>
          </div>
        </div>
      </div>
    </section>
  {/if}
</WizardChrome>
