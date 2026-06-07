<script lang="ts">
  interface Props {
    title: string;
    description: string;
    checked: boolean;
    ontoggle: (checked: boolean) => void;
    id?: string;
  }

  let { title, description, checked, ontoggle, id }: Props = $props();
</script>

<label class="toggle-row">
  <span class="toggle-copy">
    <strong>{title}</strong>
    <span>{description}</span>
  </span>
  <input
    class="toggle-input"
    type="checkbox"
    {id}
    {checked}
    onchange={(e) => ontoggle(e.currentTarget.checked)}
  />
  <span class="toggle-switch" aria-hidden="true"></span>
</label>
