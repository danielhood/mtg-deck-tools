<script lang="ts">
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import ToggleRow from "../components/ToggleRow.svelte";
  import { postSynergyContext, type ActivatedProfile, type WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, toSynergyContextCriteria, type WizardDraft } from "../lib/criteria";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let profiles = $state<ActivatedProfile[]>([]);
  let helpOpen = $state(false);
  let loading = $state(true);
  let error = $state("");

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    const criteria = toSynergyContextCriteria(draft);
    loading = true;
    error = "";
    postSynergyContext(criteria)
      .then((ctx) => {
        profiles = ctx.activated_profiles;
      })
      .catch((err: Error) => {
        profiles = [];
        error = err.message;
      })
      .finally(() => {
        loading = false;
      });
  });

  function currentIndex(profile: ActivatedProfile): number {
    const idx = profile.focus_options.findIndex(
      (opt) => opt.value === (draft.mechanic_focus[profile.profile_id] ?? null),
    );
    return idx >= 0 ? idx : 0;
  }

  function stepFocus(profile: ActivatedProfile, delta: number): void {
    const idx = currentIndex(profile);
    const next = profile.focus_options[Math.min(Math.max(idx + delta, 0), profile.focus_options.length - 1)];
    const focus = { ...draft.mechanic_focus };
    if (!next.value) delete focus[profile.profile_id];
    else focus[profile.profile_id] = next.value;
    draft = { ...draft, mechanic_focus: focus };
  }
</script>

<WizardChrome step={3} backRoute="/build/2" nextRoute="/build/4" dbReady={meta.db_ready}>
  <WizardIntro
    title="Synergy & dependencies"
    lead="Tune how strictly cards must connect, then dial up each activated mechanic."
  />

  <section class="wizard-section" aria-labelledby="strict-heading">
    <SectionHeader id="strict-heading" title="Synergy rules" />

    <div class="toggle-list">
      <ToggleRow
        title="Strict dependencies"
        description="Block picks with no valid targets."
        checked={draft.strict_dependencies}
        ontoggle={(checked) => (draft = { ...draft, strict_dependencies: checked })}
      />
      <ToggleRow
        title="Repair dependencies"
        description="Fix gaps after build."
        checked={draft.repair_dependencies}
        ontoggle={(checked) => (draft = { ...draft, repair_dependencies: checked })}
      />
    </div>
  </section>

  <section class="wizard-section" aria-labelledby="focus-heading">
    <SectionHeader id="focus-heading" title="Mechanic focus" />

    {#if error}
      <ErrorState message={error} />
    {:else if loading}
      <LoadingState message="Loading synergy profiles…" />
    {:else if profiles.length}
      <div class="focus-help">
        <button
          class="focus-help-toggle"
          type="button"
          aria-expanded={helpOpen}
          onclick={() => (helpOpen = !helpOpen)}
        >
          What do focus levels mean?
          <span class="chevron" aria-hidden="true">{helpOpen ? "▲" : "▼"}</span>
        </button>
        <div class="focus-help-panel" class:is-open={helpOpen}>
          <dl>
            <dt>Default</dt>
            <dd>Theme/mechanic activation only — no extra weight.</dd>
            <dt>Incidental</dt>
            <dd>Splash; appears but is not the main plan.</dd>
            <dt>Supported</dt>
            <dd>Typical Commander support package.</dd>
            <dt>Focused</dt>
            <dd>Main secondary plan; higher counts.</dd>
            <dt>Engine</dt>
            <dd>Deck built around this mechanic.</dd>
          </dl>
        </div>
      </div>

      <div class="focus-controls">
        <div class="focus-legend" aria-hidden="true">
          <span class="col-profile">Profile</span>
          <span class="col-less">−</span>
          <span class="col-more">+</span>
        </div>

        <div class="focus-list" role="list" aria-label="Mechanic focus levels">
          {#each profiles as profile (profile.profile_id)}
            {@const idx = currentIndex(profile)}
            {@const option = profile.focus_options[idx]}
            <div class="focus-row" role="listitem">
              <div class="profile-cell">
                <div class="profile-head">
                  <span class="profile-name">{profile.prompt_label}</span>
                  <span class="focus-meter" aria-label={`Focus magnitude ${option.dots} of 5`}>
                    {#each Array(5) as _, dotIndex}
                      <span class="focus-dot" class:is-on={dotIndex < option.dots}></span>
                    {/each}
                  </span>
                </div>
                <span class="profile-level">{option.label}</span>
              </div>
              <button
                class="step-btn step-less"
                type="button"
                aria-label={`Decrease ${profile.prompt_label} focus`}
                disabled={idx === 0}
                onclick={() => stepFocus(profile, -1)}
              >
                <span class="step-mark">−</span>
              </button>
              <button
                class="step-btn step-more"
                type="button"
                aria-label={`Increase ${profile.prompt_label} focus`}
                disabled={idx >= profile.focus_options.length - 1}
                onclick={() => stepFocus(profile, 1)}
              >
                <span class="step-mark">+</span>
              </button>
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="empty-panel">
        No activated synergy profiles yet. Adjust
        <button type="button" class="link-btn" onclick={() => navigate("/build/1")}>themes</button>
        or
        <button type="button" class="link-btn" onclick={() => navigate("/build/2")}>
          included mechanics
        </button>
        on earlier steps.
      </div>
    {/if}
  </section>
</WizardChrome>

<style>
  .chevron {
    font-size: 10px;
    color: var(--text-muted);
  }

  .link-btn {
    border: none;
    background: none;
    color: var(--blue-700);
    font-size: inherit;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
  }
</style>
