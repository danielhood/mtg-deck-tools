<script lang="ts">
  interface Props {
    title: string;
    lead: string;
  }

  let { title, lead }: Props = $props();
</script>

<section class="wizard-intro">
  <h1>{title}</h1>
  <p>{lead}</p>
</section>
