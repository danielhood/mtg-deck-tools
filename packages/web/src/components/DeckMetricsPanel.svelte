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
  const blurb = $derived(curveBlurb(activeHistogram));
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
      <p class="metrics-blurb">{blurb}</p>

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
