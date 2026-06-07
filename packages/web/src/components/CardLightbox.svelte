<script lang="ts">
  interface Props {
    open: boolean;
    name: string;
    imageUri: string | null;
    subtitle?: string | null;
    onclose: () => void;
  }

  let { open, name, imageUri, subtitle = null, onclose }: Props = $props();
</script>

{#if open}
  <div class="card-lightbox" role="dialog" aria-modal="true" aria-label={name}>
    <button type="button" class="card-lightbox-backdrop" aria-label="Close" onclick={onclose}></button>
    <div class="card-lightbox-panel">
      <button type="button" class="card-lightbox-close" onclick={onclose}>×</button>
      {#if imageUri}
        <img src={imageUri} alt={name} />
      {:else}
        <div class="card-lightbox-placeholder">No image available</div>
      {/if}
      <p class="card-lightbox-title">{name}</p>
      {#if subtitle}
        <p class="card-lightbox-subtitle">{subtitle}</p>
      {/if}
    </div>
  </div>
{/if}
