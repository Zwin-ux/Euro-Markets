import { DataTable } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { SectionTitle } from '../components/SectionTitle';
import { TimeSeriesChart } from '../components/TimeSeriesChart';
import { ValueBarChart } from '../components/ValueBarChart';
import { formatCurrency, formatLongDate, formatPercent, formatRate } from '../lib/format';
import type { MarketMonitorResponse, PortfolioAnalysisResponse } from '../types';

type OverviewTabProps = {
  focusCurrency: string;
  market?: MarketMonitorResponse;
  analysis?: PortfolioAnalysisResponse;
  marketLoading: boolean;
  analysisLoading: boolean;
  portfolioLoaded: boolean;
};

export function OverviewTab({
  focusCurrency,
  market,
  analysis,
  marketLoading,
  analysisLoading,
  portfolioLoaded,
}: OverviewTabProps) {
  const topExposure = analysis?.currency_exposure.find((row) => row.currency !== 'EUR');
  const worstScenario =
    analysis?.scenario_analysis
      .slice()
      .sort((left, right) => left.scenario_pnl_eur - right.scenario_pnl_eur)
      .find((row) => row.scenario_pnl_eur !== 0) ?? analysis?.scenario_analysis[0];

  return (
    <div className="page-grid">
      <SectionTitle
        eyebrow="Operator view"
        command="fx.overview --focus live --uplink ecb"
        title="Overview"
        description="Start with the live market picture. Portfolio analysis only spins up after you load a sample book or upload a CSV."
      />

      <div className="brief-grid">
        <article className="brief-card">
          <span className="brief-card__label">Monitor next</span>
          <strong>{portfolioLoaded ? topExposure?.currency ?? 'EUR only' : 'Load a portfolio'}</strong>
          <p>
            {topExposure
              ? `${formatCurrency(topExposure.value_eur)} currently sits at the top of the exposure stack.`
              : portfolioLoaded
                ? 'The current slice is fully EUR-denominated.'
                : 'Use the sample book or upload a CSV to compute the first risk view.'}
          </p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Market regime</span>
          <strong>{market ? formatPercent(market.summary.annualized_volatility, 1) : 'Loading...'}</strong>
          <p>
            {market
              ? `${formatPercent(market.summary.max_drawdown, 1)} drawdown on the focus pair over the selected window.`
              : 'Fetching the live EUR cross and volatility snapshot.'}
          </p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Shock sensitivity</span>
          <strong>{portfolioLoaded ? worstScenario?.currency ?? 'Flat' : 'Pending'}</strong>
          <p>
            {portfolioLoaded && worstScenario
              ? `${formatCurrency(worstScenario.scenario_pnl_eur, { signed: true })} under the simple scenario deck.`
              : 'Scenario sensitivity appears after a portfolio is loaded.'}
          </p>
        </article>
      </div>

      <div className="metric-grid metric-grid--five">
        <MetricCard
          label={`EUR/${focusCurrency}`}
          value={market ? formatRate(market.summary.latest_rate) : 'Loading...'}
          detail={market ? formatPercent(market.summary.period_return) : 'Requesting market monitor payload'}
        />
        <MetricCard
          label="Portfolio value"
          value={
            analysis
              ? formatCurrency(analysis.summary.portfolio_value_eur)
              : portfolioLoaded
                ? 'Calculating...'
                : 'No portfolio'
          }
          detail={
            analysis
              ? `${analysis.summary.position_count.toLocaleString('en-US')} positions in scope`
              : portfolioLoaded
                ? 'Portfolio analytics are still running'
                : 'Load sample or upload a CSV'
          }
        />
        <MetricCard
          label="1D FX P&L"
          value={
            analysis
              ? formatCurrency(analysis.summary.fx_pnl_1d_eur, { signed: true })
              : portfolioLoaded
                ? 'Calculating...'
                : 'Pending'
          }
          tone={analysis ? (analysis.summary.fx_pnl_1d_eur < 0 ? 'danger' : 'positive') : 'default'}
        />
        <MetricCard
          label="Largest FX exposure"
          value={portfolioLoaded ? topExposure?.currency ?? 'EUR only' : 'Pending'}
          detail={
            topExposure
              ? formatCurrency(topExposure.value_eur)
              : portfolioLoaded
                ? 'No non-EUR positions'
                : 'No risk model run yet'
          }
        />
        <MetricCard
          label="Rates as of"
          value={market ? formatLongDate(market.latest_snapshot[0]?.rate_date ?? '') : 'Loading...'}
          detail={marketLoading ? 'Fetching current snapshot' : 'ECB-backed market feed'}
        />
      </div>

      {analysis ? (
        <TimeSeriesChart
          title="Portfolio value path"
          data={analysis.portfolio_value_history}
          xKey="rate_date"
          series={[{ key: 'portfolio_value_eur', label: 'Portfolio value', color: '#7AF0A2', valueType: 'currency' }]}
        />
      ) : (
        <section className="panel">
          <div className="panel__header">
            <h3>Portfolio analysis</h3>
            <span>{analysisLoading ? 'Running model' : 'Not started'}</span>
          </div>
          <div className="panel-empty">
            {portfolioLoaded
              ? 'Portfolio analytics are loading in the background.'
              : 'Load the sample portfolio or upload a CSV to unlock exposure, P&L, VaR, and scenario metrics.'}
          </div>
        </section>
      )}

      <div className="split-grid">
        {analysis ? (
          <ValueBarChart
            title="Largest non-EUR exposures"
            data={analysis.currency_exposure.filter((row) => row.currency !== 'EUR').slice(0, 8)}
            xKey="currency"
            yKey="value_eur"
          />
        ) : (
          <section className="panel">
            <div className="panel__header">
              <h3>Exposure view</h3>
              <span>{portfolioLoaded ? 'Waiting on analysis' : 'Load a portfolio'}</span>
            </div>
            <div className="panel-empty">
              Exposure ranking appears here once a portfolio has been analyzed.
            </div>
          </section>
        )}

        {market ? (
          <TimeSeriesChart
            title={`EUR/${focusCurrency} rate history`}
            data={market.history}
            xKey="rate_date"
            series={[{ key: 'exchange_rate', label: 'Rate', color: '#F5C56B' }]}
          />
        ) : (
          <section className="panel">
            <div className="panel__header">
              <h3>Market history</h3>
              <span>{marketLoading ? 'Loading' : 'Waiting'}</span>
            </div>
            <div className="panel-empty">Fetching the historical EUR/{focusCurrency} series.</div>
          </section>
        )}
      </div>

      {market ? (
        <section className="panel">
          <div className="panel__header">
            <h3>Latest ECB snapshot</h3>
            <span>{formatLongDate(market.latest_snapshot[0]?.rate_date ?? '')}</span>
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
      ) : (
        <div className="app-state">Loading the live ECB snapshot...</div>
      )}
    </div>
  );
}
