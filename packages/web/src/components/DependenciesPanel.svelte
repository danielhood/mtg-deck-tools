<script lang="ts">
  import {
    getSwapPlaybooks,
    type SwapStrategy,
  } from "../lib/api";
  import {
    buildDetailBlocks,
    issueDeficit,
    issueSwapOracleIds,
    SWAP_PLAYBOOK_RULES,
    type DependencyIssueRow,
    type IssueSwapCard,
    type ParsedDependencyReport,
  } from "../lib/dependency-report";

  interface Props {
    report: ParsedDependencyReport;
    cards?: IssueSwapCard[];
    swapBusy?: boolean;
    swappingIssueKey?: string | null;
    fixingIssueKey?: string | null;
    onShowInDeck?: (oracleId: string, cardName: string | null) => void;
    onSwapAll?: (oracleIds: string[], issueKey: string) => void;
    onFixIssue?: (
      oracleIds: string[],
      issue: DependencyIssueRow,
      strategyId: string | null,
    ) => void;
    onQuickFix?: (
      oracleIds: string[],
      issue: DependencyIssueRow,
      strategyId: string | null,
    ) => void;
  }

  let {
    report,
    cards = [],
    swapBusy = false,
    swappingIssueKey = null,
    fixingIssueKey = null,
    onShowInDeck,
    onSwapAll,
    onFixIssue,
    onQuickFix,
  }: Props = $props();

  let open = $state(false);
  let playbooks = $state<Record<string, SwapStrategy[]>>({});
  let selectedStrategy = $state<Record<string, string | null>>({});

  $effect(() => {
    open = report.defaultOpen;
  });

  function statusLabel(status: DependencyIssueRow["status"]): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  function showInDeckLabel(issue: DependencyIssueRow): string {
    const name = issue.card_name?.trim();
    return name ? `Show in deck — ${name}` : "Show in deck";
  }

  function issueKey(issue: DependencyIssueRow): string {
    return `${issue.rule_id}:${issue.message}`;
  }

  function swapTargets(issue: DependencyIssueRow): string[] {
    return issueSwapOracleIds(issue, cards, strategyForIssue(issue));
  }

  async function ensurePlaybooks(issue: DependencyIssueRow): Promise<void> {
    const key = issueKey(issue);
    if (playbooks[key]) return;
    if (!SWAP_PLAYBOOK_RULES.has(issue.rule_id)) return;
    try {
      const response = await getSwapPlaybooks(issue.rule_id, issueDeficit(issue) ?? undefined);
      playbooks = { ...playbooks, [key]: response.strategies };
      if (!selectedStrategy[key]) {
        const defaultStrategy = response.strategies.find((row) => row.default);
        selectedStrategy = {
          ...selectedStrategy,
          [key]: defaultStrategy?.id ?? response.strategies[0]?.id ?? null,
        };
      }
    } catch {
      playbooks = { ...playbooks, [key]: [] };
    }
  }

  function pickStrategy(issue: DependencyIssueRow, strategyId: string): void {
    selectedStrategy = { ...selectedStrategy, [issueKey(issue)]: strategyId };
  }

  function strategyForIssue(issue: DependencyIssueRow): string | null {
    return selectedStrategy[issueKey(issue)] ?? null;
  }

  async function ensurePlaybooks(issue: DependencyIssueRow): Promise<void> {
    const key = issueKey(issue);
    if (playbooks[key]) return;
    if (!SWAP_PLAYBOOK_RULES.has(issue.rule_id)) return;
    try {
      const response = await getSwapPlaybooks(issue.rule_id, issueDeficit(issue) ?? undefined);
      playbooks = { ...playbooks, [key]: response.strategies };
      if (!selectedStrategy[key]) {
        const defaultStrategy = response.strategies.find((row) => row.default);
        selectedStrategy = {
          ...selectedStrategy,
          [key]: defaultStrategy?.id ?? response.strategies[0]?.id ?? null,
        };
      }
    } catch {
      playbooks = { ...playbooks, [key]: [] };
    }
  }

  function pickStrategy(issue: DependencyIssueRow, strategyId: string): void {
    selectedStrategy = { ...selectedStrategy, [issueKey(issue)]: strategyId };
  }

  function strategyForIssue(issue: DependencyIssueRow): string | null {
    return selectedStrategy[issueKey(issue)] ?? null;
  }
</script>

<details
  class="deps-panel"
  class:deps-panel--pass={report.summaryTone === "pass"}
  class:deps-panel--warn={report.summaryTone === "warn"}
  class:deps-panel--fail={report.hasFail}
  aria-label="Dependencies"
  bind:open
>
  <summary>
    <span>Dependencies</span>
    {#if report.summaryHint}
      <span
        class="deps-summary-hint"
        class:deps-summary-ok={report.summaryTone === "pass"}
        class:deps-summary-warn={report.summaryTone === "warn"}
      >
        {report.summaryHint}
      </span>
    {/if}
  </summary>

  <div class="deps-body">
    {#if !report.hasReport}
      <p class="deps-empty" role="status">No dependency report in this deck.</p>
    {:else}
      {#if report.profiles.length}
        <p class="deps-section-title">Profiles</p>
        {#each report.profiles as profile (profile.profile_id)}
          <div class="deps-profile-row">
            <div class="deps-profile-head">
              <span class="deps-profile-name">{profile.label}</span>
              <span class="deps-status-pill deps-status-{profile.status}">
                {statusLabel(profile.status)}
              </span>
            </div>
            {#if Object.keys(profile.counts).length}
              <div class="deps-count-chips">
                {#each Object.entries(profile.counts) as [key, count] (key)}
                  <span class="deps-count-chip">{key}: {count}</span>
                {/each}
              </div>
            {/if}
            {#if profile.messages.length}
              <ul class="deps-profile-messages">
                {#each profile.messages as message, index (index)}
                  <li>{message}</li>
                {/each}
              </ul>
            {/if}
          </div>
        {/each}
      {/if}

      {#if report.issues.length}
        <p class="deps-section-title" class:deps-section-title-spaced={report.profiles.length}>
          Issues
        </p>
        {#each report.issues as issue (issue.rule_id + issue.message)}
          {@const key = issueKey(issue)}
          {@const targets = swapTargets(issue)}
          {@const deficit = issueDeficit(issue)}
          <details
            class="deps-issue-row deps-issue-{issue.status}"
            ontoggle={(event) => {
              if (event.currentTarget.open) void ensurePlaybooks(issue);
            }}
          >
            <summary class="deps-issue-head">
              <span>{issue.rule_label}</span>
              <span class="deps-issue-chevron" aria-hidden="true"></span>
            </summary>
            <div class="deps-issue-body">
              <p class="deps-issue-message">{issue.message}</p>
              <p class="deps-issue-meta">
                {#if issue.profile_label}
                  Profile: {issue.profile_label} · Status: {statusLabel(issue.status)}
                  {#if deficit}
                    · Deficit: {deficit}
                  {/if}
                {:else}
                  Status: {statusLabel(issue.status)}
                  {#if deficit}
                    · Deficit: {deficit}
                  {/if}
                {/if}
              </p>
              {#each buildDetailBlocks(issue.detail) as block, index (`${issue.rule_id}-${index}`)}
                <div class="deps-detail-block">
                  <div class="deps-detail-label">{block.label}</div>
                  {#if block.kind === "list" && block.items}
                    <ul class="deps-detail-list">
                      {#each block.items as item (item)}
                        <li>{item}</li>
                      {/each}
                    </ul>
                  {:else if block.kind === "scalar" && block.text != null}
                    <p class="deps-detail-scalar">{block.text}</p>
                  {:else if block.kind === "json" && block.json}
                    <pre class="deps-detail-json">{block.json}</pre>
                  {/if}
                </div>
              {/each}

              {#if SWAP_PLAYBOOK_RULES.has(issue.rule_id) && playbooks[key]?.length}
                <p class="deps-strategy-label">How do you want to fix this?</p>
                <div class="chips" role="group" aria-label="Resolution strategies">
                  {#each playbooks[key] as strategy (strategy.id)}
                    <button
                      type="button"
                      class="chip"
                      class:active={strategyForIssue(issue) === strategy.id}
                      onclick={() => pickStrategy(issue, strategy.id)}
                    >
                      {strategy.label}
                    </button>
                  {/each}
                </div>
              {/if}

              <div class="deps-action-row">
                {#if onFixIssue && SWAP_PLAYBOOK_RULES.has(issue.rule_id) && targets.length}
                  <button
                    type="button"
                    class="deps-btn-fix"
                    disabled={swapBusy}
                    onclick={() => onFixIssue(targets, issue, strategyForIssue(issue))}
                  >
                    {swapBusy && fixingIssueKey === key ? "Opening…" : "Fix issue…"}
                  </button>
                  {#if onQuickFix}
                    <button
                      type="button"
                      class="deps-btn-quick-fix"
                      disabled={swapBusy}
                      onclick={() => onQuickFix(targets, issue, strategyForIssue(issue))}
                    >
                      Quick fix
                      <span class="proto-badge">Prototype</span>
                    </button>
                  {/if}
                {/if}
                {#if issue.card_oracle_id && onShowInDeck}
                  <button
                    type="button"
                    class="deps-link-btn deps-link-btn-inline"
                    onclick={() => onShowInDeck(issue.card_oracle_id!, issue.card_name)}
                  >
                    {showInDeckLabel(issue)}
                  </button>
                {/if}
                {#if onSwapAll && targets.length}
                  <button
                    type="button"
                    class="deps-link-btn deps-link-btn-inline"
                    disabled={swapBusy}
                    onclick={() => onSwapAll(targets, key)}
                  >
                    {swapBusy && swappingIssueKey === key ? "Swapping…" : "Swap All"}
                  </button>
                {/if}
              </div>
            </div>
          </details>
        {/each}
      {/if}
    {/if}
  </div>
</details>
