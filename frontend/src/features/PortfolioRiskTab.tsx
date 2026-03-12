import { CorrelationHeatmap } from '../components/CorrelationHeatmap';
import { DataTable } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { SectionTitle } from '../components/SectionTitle';
import { TimeSeriesChart } from '../components/TimeSeriesChart';
import { ValueBarChart } from '../components/ValueBarChart';
import { formatCurrency, formatPercent } from '../lib/format';
import type { PortfolioAnalysisResponse } from '../types';

type PortfolioRiskTabProps = {
  analysis: PortfolioAnalysisResponse;
};

export function PortfolioRiskTab({ analysis }: PortfolioRiskTabProps) {
  return (
    <div className="page-grid">
      <SectionTitle
        eyebrow="Filtered slice"
        title="Portfolio Risk"
        description="Use the filters in the control rail to narrow the portfolio. The ranked ledger below stays centered on concentration first."
      />

      <div className="metric-grid">
        <MetricCard label="Portfolio value" value={formatCurrency(analysis.summary.portfolio_value_eur)} />
        <MetricCard label="Non-EUR share" value={formatPercent(analysis.summary.non_eur_share, 1)} />
        <MetricCard
          label="Annualized volatility"
          value={formatPercent(analysis.summary.annualized_portfolio_volatility)}
        />
        <MetricCard label="Positions" value={analysis.summary.position_count.toLocaleString('en-US')} />
      </div>

      <section className="panel">
        <div className="panel__header">
          <h3>Exposure ledger</h3>
          <span>Ranked by EUR value</span>
        </div>
        <DataTable
          columns={[
            { key: 'currency', label: 'Currency' },
            { key: 'positions', label: 'Positions', align: 'right' },
            { key: 'value', label: 'Value (EUR)', align: 'right' },
            { key: 'weight', label: 'Weight', align: 'right' },
            { key: 'pnl', label: '1D FX P&L', align: 'right' },
          ]}
          rows={analysis.currency_exposure.map((row) => ({
            currency: row.currency,
            positions: row.position_count.toLocaleString('en-US'),
            value: formatCurrency(row.value_eur),
            weight: formatPercent(row.portfolio_weight, 1),
            pnl: formatCurrency(row.fx_pnl_1d_eur, { signed: true }),
          }))}
        />
      </section>

      <div className="split-grid">
        <ValueBarChart
          title="Exposure by currency"
          data={analysis.currency_exposure.filter((row) => row.currency !== 'EUR').slice(0, 8)}
          xKey="currency"
          yKey="value_eur"
        />
        <CorrelationHeatmap matrix={analysis.correlation_matrix} />
      </div>

      <TimeSeriesChart
        title="Filtered portfolio value path"
        data={analysis.portfolio_value_history}
        xKey="rate_date"
        series={[{ key: 'portfolio_value_eur', label: 'Portfolio value', color: '#7AF0A2', valueType: 'currency' }]}
      />

      <section className="panel">
        <div className="panel__header">
          <h3>Position detail</h3>
          <span>{analysis.positions.length.toLocaleString('en-US')} rows</span>
        </div>
        <DataTable
          columns={[
            { key: 'id', label: 'Position ID' },
            { key: 'name', label: 'Position Name' },
            { key: 'book', label: 'Book' },
            { key: 'asset', label: 'Asset Class' },
            { key: 'currency', label: 'Currency' },
            { key: 'value', label: 'Value (EUR)', align: 'right' },
          ]}
          rows={analysis.positions.slice(0, 14).map((row) => ({
            id: row.position_id,
            name: row.position_name,
            book: row.book || 'Unassigned',
            asset: row.asset_class || 'Unassigned',
            currency: row.currency,
            value: formatCurrency(row.value_eur),
          }))}
        />
      </section>
    </div>
  );
}
