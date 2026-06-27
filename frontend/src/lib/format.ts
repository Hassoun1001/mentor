export function formatNumber(value: string | number, fractionDigits = 2): string {
  const n = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString(undefined, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatMoney(amount: string | number, currency: string): string {
  const n = typeof amount === 'string' ? Number(amount) : amount;
  if (!Number.isFinite(n)) return '—';
  try {
    return n.toLocaleString(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    });
  } catch {
    return `${formatNumber(n, 2)} ${currency}`;
  }
}

export function formatPercent(value: string | number, fractionDigits = 2): string {
  const n = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(n)) return '—';
  return `${n.toFixed(fractionDigits)}%`;
}

export function formatLots(value: string | number): string {
  return formatNumber(value, 2);
}
