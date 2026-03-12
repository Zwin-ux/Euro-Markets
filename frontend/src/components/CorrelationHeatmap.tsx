import type { CorrelationMatrix } from '../types';

type CorrelationHeatmapProps = {
  matrix: CorrelationMatrix;
};

function cellColor(value: number) {
  if (value <= -0.5) {
    return 'rgba(240, 141, 106, 0.85)';
  }
  if (value < 0) {
    return 'rgba(240, 141, 106, 0.45)';
  }
  if (value < 0.5) {
    return 'rgba(122, 240, 162, 0.35)';
  }
  return 'rgba(122, 240, 162, 0.8)';
}

export function CorrelationHeatmap({ matrix }: CorrelationHeatmapProps) {
  const currencies = Object.keys(matrix);

  if (currencies.length < 2) {
    return <div className="panel-empty">Correlation needs at least two non-EUR currencies with overlapping history.</div>;
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <h3>Correlation Grid</h3>
      </div>
      <div className="heatmap-grid" style={{ gridTemplateColumns: `120px repeat(${currencies.length}, minmax(72px, 1fr))` }}>
        <div className="heatmap-grid__corner">Currency</div>
        {currencies.map((currency) => (
          <div key={`column-${currency}`} className="heatmap-grid__label">
            {currency}
          </div>
        ))}
        {currencies.map((rowCurrency) => (
          <FragmentRow
            key={rowCurrency}
            rowCurrency={rowCurrency}
            currencies={currencies}
            matrix={matrix}
          />
        ))}
      </div>
    </section>
  );
}

type FragmentRowProps = {
  rowCurrency: string;
  currencies: string[];
  matrix: CorrelationMatrix;
};

function FragmentRow({ rowCurrency, currencies, matrix }: FragmentRowProps) {
  return (
    <>
      <div className="heatmap-grid__label heatmap-grid__label--row">{rowCurrency}</div>
      {currencies.map((columnCurrency) => {
        const value = matrix[rowCurrency]?.[columnCurrency] ?? 0;
        return (
          <div
            key={`${rowCurrency}-${columnCurrency}`}
            className="heatmap-grid__cell"
            style={{ backgroundColor: cellColor(value) }}
            title={`${rowCurrency} / ${columnCurrency}: ${value.toFixed(3)}`}
          >
            {value.toFixed(2)}
          </div>
        );
      })}
    </>
  );
}
