import { DataTable } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { SectionTitle } from '../components/SectionTitle';
import { formatLongDate, formatRate } from '../lib/format';
import type { CurrencyCatalogRow, Frequency, HealthResponse, MarketMonitorResponse, PortfolioTemplateResponse } from '../types';

type DataApiTabProps = {
  health: HealthResponse;
  template: PortfolioTemplateResponse;
  currencyCatalog: CurrencyCatalogRow[];
  market: MarketMonitorResponse;
  lookbackDays: number;
  frequency: Frequency;
};

export function DataApiTab({ health, template, currencyCatalog, market, lookbackDays, frequency }: DataApiTabProps) {
  return (
    <div className="page-grid">
      <SectionTitle
        eyebrow="Reference layer"
        command="fx.reference --inspect feed --show routes"
        title="Data & API"
        description="Source freshness, sample inputs, and the API contract that powers the web app."
      />

      <div className="brief-grid">
        <article className="brief-card">
          <span className="brief-card__label">Source</span>
          <strong>ECB via Euro Rates API</strong>
          <p>{health.status === 'ok' ? 'The backend is healthy and serving the latest upstream context.' : 'Backend status requires attention.'}</p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Coverage</span>
          <strong>{currencyCatalog.length.toLocaleString('en-US')} currencies</strong>
          <p>{market.latest_snapshot.length.toLocaleString('en-US')} currencies are in the active live snapshot.</p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Client mode</span>
          <strong>{lookbackDays}d / {frequency}</strong>
          <p>The frontend is currently requesting a {lookbackDays}-day window at {frequency} frequency.</p>
        </article>
      </div>

      <div className="metric-grid">
        <MetricCard label="Rates as of" value={formatLongDate(market.latest_snapshot[0]?.rate_date ?? health.date)} />
        <MetricCard label="Snapshot currencies" value={market.latest_snapshot.length.toLocaleString('en-US')} />
        <MetricCard label="Supported currencies" value={currencyCatalog.length.toLocaleString('en-US')} />
        <MetricCard label="Lookback / frequency" value={`${lookbackDays}d / ${frequency}`} />
      </div>

      <div className="split-grid">
        <section className="panel">
          <div className="panel__header">
            <h3>Latest ECB snapshot</h3>
            <span>{health.source}</span>
          </div>
          <DataTable
            columns={[
              { key: 'currency', label: 'Currency' },
              { key: 'rate', label: 'Rate', align: 'right' },
              { key: 'date', label: 'Date', align: 'right' },
            ]}
            rows={market.latest_snapshot.map((row) => ({
              currency: row.target_currency,
              rate: formatRate(row.exchange_rate),
              date: row.rate_date,
            }))}
          />
        </section>

        <section className="panel">
          <div className="panel__header">
            <h3>API routes</h3>
            <span>FastAPI backend</span>
          </div>
          <DataTable
            columns={[
              { key: 'method', label: 'Method' },
              { key: 'path', label: 'Path' },
              { key: 'purpose', label: 'Purpose' },
            ]}
            rows={[
              { method: 'GET', path: '/health', purpose: 'Service health and source metadata' },
              { method: 'GET', path: '/currencies', purpose: 'Supported ECB currency catalog' },
              { method: 'GET', path: '/rates/latest', purpose: 'Current EUR exchange rates' },
              { method: 'GET', path: '/rates/history', purpose: 'Historical EUR FX series' },
              { method: 'GET', path: '/market-monitor', purpose: 'Market dashboard payload' },
              { method: 'POST', path: '/portfolio/analyze', purpose: 'Portfolio FX risk analysis' },
            ]}
          />
        </section>
      </div>

      <section className="panel">
        <div className="panel__header">
          <h3>Sample portfolio contract</h3>
          <span>{template.columns.join(', ')}</span>
        </div>
        <DataTable
          columns={template.columns.map((column) => ({ key: column, label: column }))}
          rows={template.sample.slice(0, 3).map((row) => ({
            position_id: row.position_id,
            position_name: row.position_name,
            asset_class: row.asset_class,
            book: row.book,
            currency: row.currency,
            market_value_local: row.market_value_local.toLocaleString('en-US'),
          }))}
        />
      </section>
    </div>
  );
}
