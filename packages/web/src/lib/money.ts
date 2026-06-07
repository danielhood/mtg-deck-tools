/** Money input helpers — parity with build-step-05-budget wireframe script. */

const COMMITTED_MONEY_PATTERN = /^\d+(\.\d{1,2})?$/;

export function formatAmount(amount: number | null): string {
  if (amount === null) return "";
  const fixed = amount.toFixed(2);
  const [whole, frac] = fixed.split(".");
  if (frac === "00") return whole;
  return `${whole}.${frac}`;
}

export function formatUsd(amount: number | null): string {
  if (amount === null) return "";
  return `$${formatAmount(amount)}`;
}

export function sanitizeMoneyEntry(text: string): string {
  let raw = text.replace(/^\$/, "").replace(/[^\d.]/g, "");
  const dotIndex = raw.indexOf(".");
  if (dotIndex === -1) return raw;
  const whole = raw.slice(0, dotIndex);
  const frac = raw.slice(dotIndex + 1).replace(/\./g, "").slice(0, 2);
  return `${whole}.${frac}`;
}

export type MoneyParseResult = { value: number | null; valid: boolean };

export function parseOptionalMoney(text: string, { strict = false } = {}): MoneyParseResult {
  const trimmed = text.trim();
  if (!trimmed) return { value: null, valid: true };

  const normalized = trimmed.replace(/^\$/, "");
  if (strict && !COMMITTED_MONEY_PATTERN.test(normalized)) {
    return { value: null, valid: false };
  }
  if (!strict && !/^\d*\.?\d{0,2}$/.test(normalized)) {
    return { value: null, valid: false };
  }
  if (normalized.endsWith(".")) {
    return { value: null, valid: !strict };
  }

  const num = Number.parseFloat(normalized);
  if (!Number.isFinite(num) || num < 0) {
    return { value: null, valid: false };
  }
  return { value: Math.round(num * 100) / 100, valid: true };
}

export function parseBudgetMoney(text: string, { strict = false } = {}): MoneyParseResult {
  const trimmed = text.trim();
  if (!trimmed) return { value: null, valid: false };

  const normalized = trimmed.replace(/^\$/, "");
  if (strict && !COMMITTED_MONEY_PATTERN.test(normalized)) {
    return { value: null, valid: false };
  }
  if (!strict && !/^\d*\.?\d{0,2}$/.test(normalized)) {
    return { value: null, valid: false };
  }
  if (normalized.endsWith(".")) {
    return { value: null, valid: !strict };
  }

  const num = Number.parseFloat(normalized);
  if (!Number.isFinite(num) || num <= 0) {
    return { value: null, valid: false };
  }
  return { value: Math.round(num * 100) / 100, valid: true };
}

export function stepOptional(
  current: number | null,
  step: number,
  direction: "more" | "less",
): number | null {
  if (direction === "more") {
    if (current === null) return step;
    return Math.round((current + step) * 100) / 100;
  }
  if (current === null) return null;
  const next = Math.round((current - step) * 100) / 100;
  return next < step ? null : next;
}

export const BUDGET_STEP = 10;
export const BUDGET_MIN = 10;
export const MIN_CARD_STEP = 1;
export const MAX_CARD_STEP = 5;
