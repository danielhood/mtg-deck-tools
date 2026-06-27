<script lang="ts">
  import {
    CMC_BUCKETS,
    curveBlurb,
    formatMetricsSummary,
    histogramForView,
    maxHistogramCount,
    sumHistogram,
    type CurveView,
    type DeckMetrics,
  } from "../lib/deck-metrics";

  interface Props {
    metrics: DeckMetrics;
  }

  let { metrics }: Props = $props();

  let open = $state(true);
  let curveView = $state<CurveView>("nonlands");

  const activeHistogram = $derived(histogramForView(metrics, curveView));
  const chartMax = $derived(maxHistogramCount(activeHistogram));
  const chartTotal = $derived(sumHistogram(activeHistogram));
  const curveNote = $derived(curveBlurb(activeHistogram, curveView, metrics.curve_advisories));
  const summary = $derived(formatMetricsSummary(metrics));
  const creatureTotal = $derived(sumHistogram(metrics.creature_cmc_histogram));
</script>

<details class="metrics-panel" aria-label="Deck metrics" bind:open>
  <summary>
    <span>Deck metrics</span>
    <span class="metrics-summary-hint">
      {curveView === "creatures" ? `${chartTotal} creatures` : `${chartTotal} nonlands`}
    </span>
  </summary>

  <div class="metrics-body">
    <div class="metrics-filters" role="group" aria-label="Curve view">
      <button
        type="button"
        class="metrics-chip"
        class:active={curveView === "nonlands"}
        onclick={() => (curveView = "nonlands")}
      >
        All nonlands
      </button>
      <button
        type="button"
        class="metrics-chip"
        class:active={curveView === "creatures"}
        disabled={creatureTotal === 0}
        onclick={() => (curveView = "creatures")}
      >
        Creatures only
      </button>
    </div>

    {#if chartTotal === 0}
      <p class="metrics-empty" role="status">No cards to chart for this view.</p>
    {:else}
      <p class="metrics-blurb" class:metrics-blurb--warn={curveNote.isWarning}>
        {#if curveNote.isWarning}
          <svg
            class="metrics-warn-icon"
            viewBox="0 0 24 24"
            width="12"
            height="12"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
          </svg>
        {/if}
        <span>{curveNote.text}</span>
      </p>

      <div
        class="metrics-chart"
        role="img"
        aria-label={`Mana curve chart, ${chartTotal} cards`}
      >
        {#each CMC_BUCKETS as bucket (bucket)}
          {@const count = activeHistogram[bucket] ?? 0}
          {@const heightPct = chartMax > 0 ? Math.round((count / chartMax) * 100) : 0}
          <div class="metrics-bar-col">
            <div class="metrics-bar-track" aria-hidden="true">
              <div
                class="metrics-bar-fill"
                class:metrics-bar-fill--zero={count === 0}
                style:height="{count > 0 ? Math.max(heightPct, 8) : 0}%"
              ></div>
            </div>
            <span class="metrics-bar-count" aria-label={`CMC ${bucket}: ${count}`}>
              {count > 0 ? count : ""}
            </span>
            <span class="metrics-bar-label">{bucket}</span>
          </div>
        {/each}
      </div>
    {/if}

    {#if summary}
      <p class="metrics-summary">{summary}</p>
    {/if}
  </div>
</details>
