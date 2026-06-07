<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";
  import type { WizardMeta } from "../lib/api";
  import { formatColors } from "../lib/format";

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

  const COLOR_ORDER = ["W", "U", "B", "R", "G"] as const;

  $effect(() => {
    saveDraft(draft);
  });

  function isPipChecked(id: string): boolean {
    return draft.colorFilter === "selected" && draft.colors.includes(id);
  }

  function togglePip(id: string, checked: boolean): void {
    const colors = new Set(draft.colors);
    if (checked) {
      colors.add(id);
      draft = {
        ...draft,
        colorFilter: "selected",
        colors: COLOR_ORDER.filter((c) => colors.has(c)),
      };
      return;
    }

    colors.delete(id);
    const next = COLOR_ORDER.filter((c) => colors.has(c));
    draft = {
      ...draft,
      colorFilter: next.length ? "selected" : "any",
      colors: next,
    };
  }

  function setColorlessOnly(enabled: boolean): void {
    draft = enabled
      ? { ...draft, colorFilter: "colorless", colors: [] }
      : { ...draft, colorFilter: "any", colors: [] };
  }

  function summary(): string {
    if (draft.colorFilter === "colorless") return "Colorless only";
    if (draft.colorFilter === "any" || !draft.colors.length) return "Any (no color filter)";
    return formatColors(draft.colors);
  }
</script>

<WizardChrome step={4} backRoute="/build/3" nextRoute="/build/5" dbReady={meta.db_ready}>
  <WizardIntro
    title="Colors"
    lead="Choose colors that should be present in the commander's identity."
  />

  <section class="wizard-section" aria-label="Color identity">
    <div class="color-grid" role="group" aria-label="Colored commander identity">
      {#each PIPS as pip (pip.id)}
        <label class="color-option color-{pip.id.toLowerCase()}">
          <input
            type="checkbox"
            name="color"
            value={pip.id}
            checked={isPipChecked(pip.id)}
            onchange={(e) => togglePip(pip.id, e.currentTarget.checked)}
          />
          <span class="pip-slot">
            <span class="mana-pip" aria-hidden="true">{pip.id}</span>
          </span>
          <span class="color-label">{pip.label}</span>
        </label>
      {/each}
    </div>

    <div class="colorless-row">
      <button
        type="button"
        class="colorless-option"
        class:is-selected={draft.colorFilter === "colorless"}
        aria-pressed={draft.colorFilter === "colorless"}
        onclick={() => setColorlessOnly(draft.colorFilter !== "colorless")}
      >
        <span class="colorless-pip-slot">
          <span class="mana-pip-colorless" aria-hidden="true">∅</span>
        </span>
        <span class="colorless-copy">
          <strong>Colorless only</strong>
          <span>Commanders with empty color identity (void) — excludes all colored picks.</span>
        </span>
      </button>
    </div>

    <div class="selection-summary" aria-live="polite">
      <h3>Selected identity</h3>
      <p>{summary()}</p>
    </div>
  </section>
</WizardChrome>
