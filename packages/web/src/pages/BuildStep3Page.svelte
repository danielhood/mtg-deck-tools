<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import { postSynergyContext, type ActivatedProfile, type WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, toDeckCriteria, type WizardDraft } from "../lib/criteria";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let profiles = $state<ActivatedProfile[]>([]);

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    postSynergyContext(toDeckCriteria(draft))
      .then((ctx) => {
        profiles = ctx.activated_profiles;
      })
      .catch(() => {
        profiles = [];
      });
  });

  function setFocus(profileId: string, level: string | null): void {
    const focus = { ...draft.mechanic_focus };
    if (!level) delete focus[profileId];
    else focus[profileId] = level;
    draft = { ...draft, mechanic_focus: focus };
  }

  function currentIndex(profile: ActivatedProfile): number {
    const idx = profile.focus_options.findIndex((opt) => opt.value === (draft.mechanic_focus[profile.profile_id] ?? null));
    return idx >= 0 ? idx : 0;
  }

  function stepFocus(profile: ActivatedProfile, delta: number): void {
    const idx = currentIndex(profile);
    const next = profile.focus_options[Math.min(Math.max(idx + delta, 0), profile.focus_options.length - 1)];
    setFocus(profile.profile_id, next.value);
  }
</script>

<WizardChrome step={3} backRoute="/build/2" nextRoute="/build/4" dbReady={meta.db_ready}>
  <h2 class="section-title">Synergy &amp; dependencies</h2>
  <p class="section-lead">Optional strictness toggles and per-mechanic focus levels.</p>

  <div class="toggle-row">
    <label for="strict-deps">Block picks with no valid targets</label>
    <input
      id="strict-deps"
      type="checkbox"
      checked={draft.strict_dependencies}
      onchange={(e) => (draft = { ...draft, strict_dependencies: e.currentTarget.checked })}
    />
  </div>
  <div class="toggle-row">
    <label for="repair-deps">Fix gaps after build</label>
    <input
      id="repair-deps"
      type="checkbox"
      checked={draft.repair_dependencies}
      onchange={(e) => (draft = { ...draft, repair_dependencies: e.currentTarget.checked })}
    />
  </div>

  {#if profiles.length}
    <div class="focus-list">
      {#each profiles as profile (profile.profile_id)}
        {@const idx = currentIndex(profile)}
        {@const option = profile.focus_options[idx]}
        <div class="focus-row">
          <div>
            <div class="field-label">{profile.prompt_label}</div>
            <div class="focus-level">{option.label}</div>
            <div class="dot-meter" aria-hidden="true">
              {#each Array(5) as _, dotIndex}
                <span class:filled={dotIndex < option.dots}></span>
              {/each}
            </div>
          </div>
          <div class="stepper">
            <button type="button" onclick={() => stepFocus(profile, -1)} aria-label="Lower focus">−</button>
            <button type="button" onclick={() => stepFocus(profile, 1)} aria-label="Raise focus">+</button>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="empty-panel">
      No activated synergy profiles yet. Adjust themes or included mechanics on earlier steps.
    </div>
  {/if}
</WizardChrome>

<style>
  .focus-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .focus-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
  }

  .focus-level {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
  }

  .dot-meter {
    display: flex;
    gap: 4px;
    margin-top: 6px;
  }

  .dot-meter span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--border);
  }

  .dot-meter span.filled {
    background: var(--blue-700);
  }

  .stepper {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stepper button {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg);
    font-size: 22px;
    cursor: pointer;
  }

  .empty-panel {
    padding: 16px;
    border: 1px dashed var(--border);
    border-radius: 10px;
    font-size: 13px;
    color: var(--text-muted);
  }
</style>
