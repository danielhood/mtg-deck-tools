<script lang="ts">
  interface Props {
    title: string;
    description?: string;
    id?: string;
  }

  let { title, description, id }: Props = $props();
</script>

<div class="section-header">
  <h2 {id}>{title}</h2>
  {#if description}
    <p>{description}</p>
  {/if}
</div>
