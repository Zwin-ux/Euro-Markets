import type { PositionInput, ScenarioDraftRow } from '../types';

const COLUMN_ALIASES: Record<string, keyof PositionInput> = {
  id: 'position_id',
  position: 'position_name',
  local_amount: 'market_value_local',
  market_value: 'market_value_local',
  notional_local: 'market_value_local',
  desk: 'book',
};

const REQUIRED_COLUMNS: Array<keyof PositionInput> = [
  'position_id',
  'position_name',
  'currency',
  'market_value_local',
];

export function serializePositions(positions: PositionInput[]): string {
  return JSON.stringify(positions);
}

export function uniqueBooks(positions: PositionInput[]): string[] {
  return Array.from(new Set(positions.map((position) => position.book).filter(Boolean))).sort();
}

export function uniqueAssetClasses(positions: PositionInput[]): string[] {
  return Array.from(new Set(positions.map((position) => position.asset_class).filter(Boolean))).sort();
}

export function filterPortfolioRows(
  positions: PositionInput[],
  books: string[],
  assetClasses: string[],
): PositionInput[] {
  return positions.filter((position) => {
    const bookMatch = books.length === 0 || books.includes(position.book);
    const assetMatch = assetClasses.length === 0 || assetClasses.includes(position.asset_class);
    return bookMatch && assetMatch;
  });
}

export function buildScenarioDraft(positions: PositionInput[]): ScenarioDraftRow[] {
  const currencies = Array.from(
    new Set(positions.map((position) => position.currency.toUpperCase()).filter((currency) => currency !== 'EUR')),
  ).sort();
  return currencies.map((currency) => ({ currency, shockPct: '' }));
}

export function scenarioDraftToPayload(rows: ScenarioDraftRow[]): Record<string, number> {
  return rows.reduce<Record<string, number>>((accumulator, row) => {
    const parsed = Number(row.shockPct);
    if (!Number.isNaN(parsed) && parsed !== 0) {
      accumulator[row.currency] = parsed / 100;
    }
    return accumulator;
  }, {});
}

export function normalizePortfolioRows(rawRows: Array<Record<string, unknown>>): PositionInput[] {
  if (rawRows.length === 0) {
    throw new Error('The uploaded file is empty.');
  }

  const normalized = rawRows.map((rawRow) => {
    const canonicalRow: Record<string, unknown> = {};
    Object.entries(rawRow).forEach(([key, value]) => {
      const normalizedKey = key.trim().toLowerCase().replace(/\s+/g, '_');
      const targetKey = COLUMN_ALIASES[normalizedKey] ?? normalizedKey;
      canonicalRow[targetKey] = value;
    });

    const missing = REQUIRED_COLUMNS.filter((column) => !(column in canonicalRow));
    if (missing.length > 0) {
      throw new Error(`Missing required portfolio columns: ${missing.join(', ')}`);
    }

    const marketValue = Number(canonicalRow.market_value_local);
    if (Number.isNaN(marketValue)) {
      throw new Error('Portfolio values must be numeric.');
    }

    return {
      position_id: String(canonicalRow.position_id ?? '').trim(),
      position_name: String(canonicalRow.position_name ?? canonicalRow.position_id ?? '').trim(),
      currency: String(canonicalRow.currency ?? '').trim().toUpperCase(),
      market_value_local: marketValue,
      asset_class: String(canonicalRow.asset_class ?? '').trim(),
      book: String(canonicalRow.book ?? '').trim(),
    } satisfies PositionInput;
  });

  const filtered = normalized.filter((row) => row.position_id && row.currency);
  if (filtered.length === 0) {
    throw new Error('No valid positions remain after cleaning the uploaded file.');
  }
  return filtered;
}
