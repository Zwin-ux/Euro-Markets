import { DataTable } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { SectionTitle } from '../components/SectionTitle';
import { TimeSeriesChart } from '../components/TimeSeriesChart';
import { ValueBarChart } from '../components/ValueBarChart';
import { formatCurrency, formatLongDate, formatPercent, formatRate } from '../lib/format';
import type { MarketMonitorResponse, PortfolioAnalysisResponse } from '../types';

type OverviewTabProps = {
  focusCurrency: string;
  market: MarketMonitorResponse;
  analysis: PortfolioAnalysisResponse;
};

export function OverviewTab({ focusCurrency, market, analysis }: OverviewTabProps) {
  const topExposure = analysis.currency_exposure.find((row) => row.currency !== 'EUR');
  const worstScenario =
    analysis.scenario_analysis
      .slice()
      .sort((left, right) => left.scenario_pnl_eur - right.scenario_pnl_eur)
      .find((row) => row.scenario_pnl_eur !== 0) ?? analysis.scenario_analysis[0];

  return (
    <div className="page-grid">
      <SectionTitle
        eyebrow="Operator view"
        title="Overview"
        description="Start with the high-level risk picture, then drill into the cross and exposure that deserve attention first."
      />

      <div className="brief-grid">
        <article className="brief-card">
          <span className="brief-card__label">Monitor next</span>
          <strong>{topExposure?.currency ?? 'EUR only'}</strong>
          <p>
            {topExposure
              ? `${formatCurrency(topExposure.value_eur)} currently sits at the top of the exposure stack.`
              : 'The current slice is fully EUR-denominated.'}
          </p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Market regime</span>
          <strong>{formatPercent(market.summary.annualized_volatility, 1)}</strong>
          <p>{formatPercent(market.summary.max_drawdown, 1)} drawdown on the focus pair over the selected window.</p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Shock sensitivity</span>
          <strong>{worstScenario?.currency ?? 'Flat'}</strong>
          <p>
            {worstScenario
              ? `${formatCurrency(worstScenario.scenario_pnl_eur, { signed: true })} under the simple scenario deck.`
              : 'No scenario sensitivity available.'}
          </p>
        </article>
      </div>

      <div className="metric-grid metric-grid--five">
        <MetricCard label="Portfolio value" value={formatCurrency(analysis.summary.portfolio_value_eur)} />
        <MetricCard
          label="1D FX P&L"
          value={formatCurrency(analysis.summary.fx_pnl_1d_eur, { signed: true })}
          tone={analysis.summary.fx_pnl_1d_eur < 0 ? 'danger' : 'positive'}
        />
        <MetricCard
          label={`${Math.round(analysis.summary.confidence_level * 100)}% 1D VaR`}
          value={formatCurrency(analysis.summary.historical_var_1d_eur)}
          tone="warning"
        />
        <MetricCard
          label="Largest FX exposure"
          value={topExposure?.currency ?? 'EUR only'}
          detail={topExposure ? formatCurrency(topExposure.value_eur) : 'No non-EUR positions'}
        />
        <MetricCard
          label={`EUR/${focusCurrency}`}
          value={formatRate(market.summary.latest_rate)}
          detail={formatPercent(market.summary.period_return)}
        />
      </div>

      <TimeSeriesChart
        title="Portfolio value path"
        data={analysis.portfolio_value_history}
        xKey="rate_date"
        series={[{ key: 'portfolio_value_eur', label: 'Portfolio value', color: '#7AF0A2', valueType: 'currency' }]}
      />

      <div className="split-grid">
        <ValueBarChart
          title="Largest non-EUR exposures"
          data={analysis.currency_exposure.filter((row) => row.currency !== 'EUR').slice(0, 8)}
          xKey="currency"
          yKey="value_eur"
        />
        <TimeSeriesChart
          title={`EUR/${focusCurrency} rate history`}
          data={market.history}
          xKey="rate_date"
          series={[{ key: 'exchange_rate', label: 'Rate', color: '#F5C56B' }]}
        />
      </div>

      <section className="panel">
        <div className="panel__header">
          <h3>Latest ECB snapshot</h3>
          <span>{formatLongDate(market.latest_snapshot[0]?.rate_date ?? analysis.summary.latest_rate_date)}</span>
        </div>
        <DataTable
          columns={[
            { key: 'currency', label: 'Currency' },
            { key: 'rate', label: 'Rate', align: 'right' },
            { key: 'date', label: 'Date', align: 'right' },
          ]}
          rows={market.latest_snapshot.slice(0, 8).map((row) => ({
            currency: row.target_currency,
            rate: formatRate(row.exchange_rate),
            date: row.rate_date,
          }))}
        />
      </section>
    </div>
  );
}
