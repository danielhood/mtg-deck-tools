<script lang="ts">
  interface Props {
    label: string;
    inputId: string;
    text: string;
    placeholder?: string;
    stepHint: string;
    showClear?: boolean;
    invalid?: boolean;
    lessDisabled?: boolean;
    ontextinput: (text: string) => void;
    onblur: () => void;
    onless: () => void;
    onmore: () => void;
    onclear?: () => void;
  }

  let {
    label,
    inputId,
    text,
    placeholder = "",
    stepHint,
    showClear = false,
    invalid = false,
    lessDisabled = false,
    ontextinput,
    onblur,
    onless,
    onmore,
    onclear,
  }: Props = $props();

  const hasValue = $derived(text.trim().length > 0);
</script>

<div class="price-stepper-row">
  <div class="price-cell">
    <label class="price-cell-label" for={inputId}>{label}</label>
    <div class="money-field" class:has-value={hasValue} class:is-invalid={invalid}>
      <span class="money-prefix" aria-hidden="true">$</span>
      <input
        class="money-input"
        id={inputId}
        type="text"
        inputmode="decimal"
        autocomplete="off"
        {placeholder}
        value={text}
        oninput={(e) => ontextinput(e.currentTarget.value)}
        onblur={onblur}
        aria-label={label}
      />
      {#if showClear && onclear}
        <button class="money-clear" type="button" aria-label={`Clear ${label}`} onclick={onclear}>
          ×
        </button>
      {/if}
    </div>
  </div>
  <div class="stepper-controls">
    <div class="stepper-btns">
      <button
        class="step-btn step-less"
        type="button"
        aria-label={`Decrease ${label}`}
        disabled={lessDisabled}
        onclick={onless}
      >
        <span class="step-mark">−</span>
      </button>
      <button class="step-btn step-more" type="button" aria-label={`Increase ${label}`} onclick={onmore}>
        <span class="step-mark">+</span>
      </button>
    </div>
    <span class="stepper-step-hint">{stepHint}</span>
  </div>
</div>
