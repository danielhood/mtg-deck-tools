<script lang="ts">
  import { parseManaCostSymbols, symbolSvgUrl } from "../lib/mana-cost";

  interface Props {
    cost?: string;
  }

  let { cost = "" }: Props = $props();

  const symbols = $derived(parseManaCostSymbols(cost));
</script>

{#if !symbols.length}
  <span class="mana-cost-empty">—</span>
{:else}
  <span class="mana-cost" aria-label={cost} role="img">
    {#each symbols as symbol, index (symbol.raw + index)}
      <img
        class="mana-symbol"
        src={symbolSvgUrl(symbol.key)}
        alt=""
        aria-hidden="true"
        loading="lazy"
        decoding="async"
      />
    {/each}
  </span>
{/if}

<style>
  .mana-cost {
    display: inline-flex;
    align-items: center;
    gap: 1px;
    vertical-align: middle;
  }

  .mana-symbol {
    height: 14px;
    width: auto;
    display: block;
  }

  .mana-cost-empty {
    color: inherit;
  }
</style>
