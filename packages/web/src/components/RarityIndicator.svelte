<script lang="ts">
  import { formatRarityLabel, rarityCssClass } from "../lib/rarity";

  interface Props {
    rarity: string | null | undefined;
  }

  let { rarity }: Props = $props();

  const label = $derived(formatRarityLabel(rarity));
  const gemClass = $derived(rarityCssClass(rarity));
</script>

{#if label}
  <span class="rarity-indicator">
    <span class="rarity-gem {gemClass}" aria-hidden="true"></span>
    <span class="rarity-label">{label}</span>
  </span>
{/if}
