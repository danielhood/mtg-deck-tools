<script lang="ts">
  import type { Snippet } from "svelte";
  import { navigate } from "../lib/router";

  interface Props {
    step: number;
    backRoute: string | null;
    nextRoute: string | null;
    nextLabel?: string;
    nextDisabled?: boolean;
    dbReady?: boolean;
    children: Snippet;
  }

  let {
    step,
    backRoute,
    nextRoute,
    nextLabel = "Next",
    nextDisabled = false,
    dbReady = true,
    children,
  }: Props = $props();
</script>

<div class="step-badge">Step {step} of 7</div>
{@render children()}

<div class="wizard-footer">
  <button class="btn btn-secondary" type="button" disabled={!backRoute} onclick={() => backRoute && navigate(backRoute)}>
    Back
  </button>
  <button
    class="btn btn-primary"
    type="button"
    disabled={!dbReady || !nextRoute || nextDisabled}
    onclick={() => nextRoute && !nextDisabled && navigate(nextRoute)}
  >
    {nextLabel}
  </button>
</div>
