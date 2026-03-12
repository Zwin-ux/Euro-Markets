export function formatCurrency(value: number, options?: { signed?: boolean; compact?: boolean }): string {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: options?.compact ? 1 : 0,
    notation: options?.compact ? 'compact' : 'standard',
  });
  const rendered = formatter.format(Math.abs(value));
  if (options?.signed) {
    return `${value >= 0 ? '+' : '-'}${rendered}`;
  }
  return value < 0 ? `-${rendered}` : rendered;
}

export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(date);
}

export function formatLongDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
}

export function formatRate(value: number): string {
  return value.toFixed(4);
}
