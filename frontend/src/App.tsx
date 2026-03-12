import { Suspense, lazy, useDeferredValue, useState, useTransition } from 'react';
import Papa from 'papaparse';
import { useQuery } from '@tanstack/react-query';

import './App.css';
import { MetricCard } from './components/MetricCard';
import { ToggleFilterGroup } from './components/ToggleFilterGroup';
import {
  analyzePortfolio,
  fetchCurrencyCatalog,
  fetchHealth,
  fetchMarketMonitor,
  fetchPortfolioTemplate,
} from './lib/api';
import { formatCurrency, formatLongDate, formatPercent, formatRate } from './lib/format';
import {
  buildScenarioDraft,
  filterPortfolioRows,
  normalizePortfolioRows,
  scenarioDraftToPayload,
  uniqueAssetClasses,
  uniqueBooks,
} from './lib/portfolio';
import type { Frequency, PositionInput, ScenarioDraftRow, ScenarioPresetOption } from './types';

const OverviewTab = lazy(async () => import('./features/OverviewTab').then((module) => ({ default: module.OverviewTab })));
const PortfolioRiskTab = lazy(async () =>
  import('./features/PortfolioRiskTab').then((module) => ({ default: module.PortfolioRiskTab })),
);
const StressTestTab = lazy(async () =>
  import('./features/StressTestTab').then((module) => ({ default: module.StressTestTab })),
);
const DataApiTab = lazy(async () => import('./features/DataApiTab').then((module) => ({ default: module.DataApiTab })));

type TabId = 'overview' | 'risk' | 'stress' | 'data';

const DEFAULT_MARKET_CURRENCIES = ['USD', 'GBP', 'CHF', 'JPY', 'AUD', 'CAD'];

const TAB_CONFIG: Array<{ id: TabId; label: string; eyebrow: string; description: string }> = [
  {
    id: 'overview',
    label: 'Overview',
    eyebrow: 'Live picture',
    description: 'Start with the market pulse, the biggest exposure, and the pair that deserves attention first.',
  },
  {
    id: 'risk',
    label: 'Portfolio Risk',
    eyebrow: 'Concentration',
    description: 'Narrow the book, then inspect exposure, volatility, and the positions driving the current footprint.',
  },
  {
    id: 'stress',
    label: 'Stress Test',
    eyebrow: 'Scenario work',
    description: 'Run deliberate shocks and compare which currencies swing the portfolio hardest under pressure.',
  },
  {
    id: 'data',
    label: 'Data & API',
    eyebrow: 'Reference',
    description: 'Check freshness, sample inputs, and the payload contract behind the frontend.',
  },
];

const SCENARIO_PRESETS: Array<ScenarioPresetOption & { shocks: Record<string, number> }> = [
  {
    id: 'broad-eur-rally',
    label: 'EUR +3% broad',
    description: 'Moderate broad strengthening across the main non-EUR currencies.',
    shocks: { USD: 3, GBP: 2, CHF: 1, JPY: 2, AUD: 4, CAD: 3 },
  },
  {
    id: 'usd-squeeze',
    label: 'EUR +5% vs USD',
    description: 'Single-pair squeeze to see how much of the book is really USD-led.',
    shocks: { USD: 5 },
  },
  {
    id: 'commodity-reversal',
    label: 'EUR -4% vs AUD/CAD',
    description: 'Commodity bloc reversal with EUR weakness against higher-beta currencies.',
    shocks: { AUD: -4, CAD: -4 },
  },
];

function buildFilterSelection(
  positions: PositionInput[],
  selectedBooks: string[],
  selectedAssetClasses: string[],
) {
  const bookOptions = uniqueBooks(positions);
  const assetOptions = uniqueAssetClasses(positions);

  return {
    bookOptions,
    assetOptions,
    filtered: filterPortfolioRows(positions, selectedBooks, selectedAssetClasses),
  };
}

function toggleSelection(current: string[], option: string) {
  return current.includes(option) ? current.filter((item) => item !== option) : [...current, option];
}

function summarizeSelection(selected: string[], total: number) {
  if (total === 0) {
    return 'No options available';
  }
  if (selected.length === 0) {
    return 'No filter applied';
  }
  if (selected.length === total) {
    return 'All active';
  }
  return `${selected.length}/${total} active`;
}

function buildScenarioPresetDraft(
  rows: ScenarioDraftRow[],
  preset: Record<string, number>,
): ScenarioDraftRow[] {
  return rows.map((row) => ({
    ...row,
    shockPct: preset[row.currency] !== undefined ? String(preset[row.currency]) : '',
  }));
}

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [focusCurrency, setFocusCurrency] = useState('USD');
  const [marketCurrencies, setMarketCurrencies] = useState<string[]>(DEFAULT_MARKET_CURRENCIES);
  const [frequency, setFrequency] = useState<Frequency>('D');
  const [lookbackDays, setLookbackDays] = useState(180);
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);
  const [rollingWindow, setRollingWindow] = useState(20);
  const [portfolioRows, setPortfolioRows] = useState<PositionInput[]>([]);
  const [portfolioSource, setPortfolioSource] = useState('Waiting for a sample or upload');
  const [uploadStatus, setUploadStatus] = useState('No custom file loaded.');
  const [riskBooks, setRiskBooks] = useState<string[]>([]);
  const [riskAssetClasses, setRiskAssetClasses] = useState<string[]>([]);
  const [stressBooks, setStressBooks] = useState<string[]>([]);
  const [stressAssetClasses, setStressAssetClasses] = useState<string[]>([]);
  const [draftScenarioRows, setDraftScenarioRows] = useState<ScenarioDraftRow[]>([]);
  const [committedScenarioShocks, setCommittedScenarioShocks] = useState<Record<string, number>>({});
  const [isPending, startTransition] = useTransition();

  const deferredPortfolioRows = useDeferredValue(portfolioRows);

  const healthQuery = useQuery({ queryKey: ['health'], queryFn: fetchHealth });
  const currencyQuery = useQuery({ queryKey: ['currencies'], queryFn: fetchCurrencyCatalog });
  const templateQuery = useQuery({ queryKey: ['portfolio-template'], queryFn: fetchPortfolioTemplate });

  function applyPortfolioRows(rows: PositionInput[], source: string) {
    const books = uniqueBooks(rows);
    const assetClasses = uniqueAssetClasses(rows);
    setPortfolioRows(rows);
    setPortfolioSource(source);
    setRiskBooks(books);
    setRiskAssetClasses(assetClasses);
    setStressBooks(books);
    setStressAssetClasses(assetClasses);
    setDraftScenarioRows(buildScenarioDraft(rows));
    setCommittedScenarioShocks({});
  }

  const fetchedCurrencyOptions = (currencyQuery.data ?? []).map((row) => row.symbol).filter((symbol) => symbol !== 'EUR');
  const currencyOptions = fetchedCurrencyOptions.length > 0 ? fetchedCurrencyOptions : DEFAULT_MARKET_CURRENCIES;
  const effectiveFocusCurrency = currencyOptions.includes(focusCurrency) ? focusCurrency : (currencyOptions[0] ?? 'USD');
  const effectiveMarketCurrencies = (() => {
    const next = marketCurrencies.filter((currency) => currencyOptions.includes(currency));
    return next.length > 0 ? next : DEFAULT_MARKET_CURRENCIES.filter((currency) => currencyOptions.includes(currency));
  })();

  const riskSelection = buildFilterSelection(deferredPortfolioRows, riskBooks, riskAssetClasses);
  const stressSelection = buildFilterSelection(deferredPortfolioRows, stressBooks, stressAssetClasses);
  const syncedScenarioDraftRows = (() => {
    const baseRows = buildScenarioDraft(stressSelection.filtered);
    const draftMap = new Map(draftScenarioRows.map((row) => [row.currency, row.shockPct]));
    return baseRows.map((row) => ({ currency: row.currency, shockPct: draftMap.get(row.currency) ?? '' }));
  })();

  const marketQuery = useQuery({
    queryKey: ['market-monitor', effectiveFocusCurrency, effectiveMarketCurrencies.join(','), lookbackDays, frequency],
    enabled: effectiveMarketCurrencies.length > 0,
    queryFn: () =>
      fetchMarketMonitor({
        focusCurrency: effectiveFocusCurrency,
        currencies: effectiveMarketCurrencies,
        lookbackDays,
        frequency,
      }),
  });

  const overviewAnalysisQuery = useQuery({
    queryKey: ['portfolio-analysis', 'overview', deferredPortfolioRows, lookbackDays, confidenceLevel, rollingWindow, frequency],
    enabled: deferredPortfolioRows.length > 0,
    queryFn: () =>
      analyzePortfolio({
        positions: deferredPortfolioRows,
        lookbackDays,
        confidenceLevel,
        rollingWindow,
        frequency,
      }),
  });

  const riskAnalysisQuery = useQuery({
    queryKey: ['portfolio-analysis', 'risk', riskSelection.filtered, lookbackDays, confidenceLevel, rollingWindow, frequency],
    enabled: activeTab === 'risk' && riskSelection.filtered.length > 0,
    queryFn: () =>
      analyzePortfolio({
        positions: riskSelection.filtered,
        lookbackDays,
        confidenceLevel,
        rollingWindow,
        frequency,
      }),
  });

  const stressAnalysisQuery = useQuery({
    queryKey: [
      'portfolio-analysis',
      'stress',
      stressSelection.filtered,
      lookbackDays,
      confidenceLevel,
      rollingWindow,
      frequency,
      committedScenarioShocks,
    ],
    enabled: activeTab === 'stress' && stressSelection.filtered.length > 0,
    queryFn: () =>
      analyzePortfolio({
        positions: stressSelection.filtered,
        lookbackDays,
        confidenceLevel,
        rollingWindow,
        frequency,
        scenarioShocks: committedScenarioShocks,
      }),
  });

  const coreError = healthQuery.error || currencyQuery.error || marketQuery.error;

  function handleLoadSample() {
    if (!templateQuery.data) {
      return;
    }
    startTransition(() => {
      applyPortfolioRows(templateQuery.data.sample, 'Sample portfolio from API');
      setUploadStatus(`Loaded ${templateQuery.data.sample.length} rows from the sample template.`);
    });
  }

  function handleDownloadTemplate() {
    if (!templateQuery.data) {
      return;
    }
    const csv = Papa.unparse(templateQuery.data.sample);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'sample_portfolio.csv';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function handleUpload(file: File | null) {
    if (!file) {
      return;
    }
    Papa.parse<Record<string, unknown>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        try {
          const rows = normalizePortfolioRows(results.data as Array<Record<string, unknown>>);
          startTransition(() => {
            applyPortfolioRows(rows, file.name);
            setUploadStatus(`Loaded ${rows.length} rows from ${file.name}.`);
          });
        } catch (error) {
          setUploadStatus(error instanceof Error ? error.message : 'Unable to parse the uploaded file.');
        }
      },
      error: (error) => setUploadStatus(error.message),
    });
  }

  function handleApplyScenarioPreset(presetId: string) {
    const preset = SCENARIO_PRESETS.find((entry) => entry.id === presetId);
    if (!preset) {
      return;
    }

    const nextDraft = buildScenarioPresetDraft(syncedScenarioDraftRows, preset.shocks);
    startTransition(() => {
      setDraftScenarioRows(nextDraft);
      setCommittedScenarioShocks(scenarioDraftToPayload(nextDraft));
    });
  }

  if (coreError instanceof Error) {
    return <div className="app-state">{coreError.message}</div>;
  }

  const health = healthQuery.data;
  const market = marketQuery.data;
  const overviewAnalysis = overviewAnalysisQuery.data;
  const portfolioLoaded = deferredPortfolioRows.length > 0;
  const activeTabConfig = TAB_CONFIG.find((tab) => tab.id === activeTab) ?? TAB_CONFIG[0];
  const topExposure = overviewAnalysis?.currency_exposure.find((row) => row.currency !== 'EUR');
  const activeShockCount = Object.keys(committedScenarioShocks).length;
  const worstScenario =
    overviewAnalysis?.scenario_analysis
      .slice()
      .sort((left, right) => left.scenario_pnl_eur - right.scenario_pnl_eur)
      .find((row) => row.scenario_pnl_eur !== 0) ?? overviewAnalysis?.scenario_analysis[0];

  const tabMeta: Record<TabId, string> = {
    overview: `Focus EUR/${effectiveFocusCurrency}`,
    risk: `${riskSelection.filtered.length} rows in scope`,
    stress: activeShockCount === 0 ? 'No live shocks' : `${activeShockCount} live shocks`,
    data: `${currencyOptions.length} supported currencies`,
  };

  const railSignals = [
    {
      label: 'Current view',
      value: activeTabConfig.label,
      detail: activeTabConfig.eyebrow,
    },
    {
      label: 'Portfolio load',
      value: deferredPortfolioRows.length.toLocaleString('en-US'),
      detail: portfolioSource,
    },
    {
      label: 'Priority watch',
      value: portfolioLoaded ? topExposure?.currency ?? 'EUR only' : 'Load sample',
      detail: topExposure
        ? formatCurrency(topExposure.value_eur, { compact: true })
        : portfolioLoaded
          ? 'No non-EUR exposure'
          : 'Upload a portfolio or load the sample book',
    },
    {
      label: 'Scenario state',
      value: activeShockCount.toLocaleString('en-US'),
      detail: activeShockCount === 0 ? 'No committed shocks' : 'Committed shocks ready',
    },
  ];

  return (
    <div className="app-shell">
      <aside className="control-rail">
        <section className="rail-panel">
          <span className="rail-panel__eyebrow">Mission control</span>
          <h2>Command rail</h2>
          <p>Stage the live EUR view, load a portfolio when you need risk, then narrow the slice before committing scenarios.</p>
          <div className="rail-signal-list">
            {railSignals.map((signal) => (
              <article key={signal.label} className="rail-signal">
                <span>{signal.label}</span>
                <strong>{signal.value}</strong>
                <p>{signal.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <label className="control-group">
          <span className="control-group__label">Focus currency</span>
          <select value={effectiveFocusCurrency} onChange={(event) => setFocusCurrency(event.target.value)}>
            {currencyOptions.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </label>

        <section className="control-group">
          <span className="control-group__label">Portfolio file</span>
          <input type="file" accept=".csv" onChange={(event) => handleUpload(event.target.files?.[0] ?? null)} />
          <div className="button-row">
            <button type="button" onClick={handleLoadSample}>
              Load sample
            </button>
            <button type="button" className="button-secondary" onClick={handleDownloadTemplate}>
              Download template
            </button>
          </div>
          <div className="status-card">
            <span>Source</span>
            <strong>{portfolioSource}</strong>
            <p>{uploadStatus}</p>
          </div>
        </section>

        {(activeTab === 'risk' || activeTab === 'stress') && (
          <section className="rail-panel rail-panel--compact">
            <span className="rail-panel__eyebrow">Scope filters</span>
            <h3>{activeTab === 'risk' ? 'Risk slice' : 'Stress slice'}</h3>
            <ToggleFilterGroup
              label="Books"
              options={activeTab === 'risk' ? riskSelection.bookOptions : stressSelection.bookOptions}
              selected={activeTab === 'risk' ? riskBooks : stressBooks}
              summary={summarizeSelection(
                activeTab === 'risk' ? riskBooks : stressBooks,
                activeTab === 'risk' ? riskSelection.bookOptions.length : stressSelection.bookOptions.length,
              )}
              onSelectAll={() =>
                activeTab === 'risk'
                  ? setRiskBooks(riskSelection.bookOptions)
                  : setStressBooks(stressSelection.bookOptions)
              }
              onToggle={(option) =>
                activeTab === 'risk'
                  ? setRiskBooks((current) => toggleSelection(current, option))
                  : setStressBooks((current) => toggleSelection(current, option))
              }
            />
            <ToggleFilterGroup
              label="Asset classes"
              options={activeTab === 'risk' ? riskSelection.assetOptions : stressSelection.assetOptions}
              selected={activeTab === 'risk' ? riskAssetClasses : stressAssetClasses}
              summary={summarizeSelection(
                activeTab === 'risk' ? riskAssetClasses : stressAssetClasses,
                activeTab === 'risk' ? riskSelection.assetOptions.length : stressSelection.assetOptions.length,
              )}
              onSelectAll={() =>
                activeTab === 'risk'
                  ? setRiskAssetClasses(riskSelection.assetOptions)
                  : setStressAssetClasses(stressSelection.assetOptions)
              }
              onToggle={(option) =>
                activeTab === 'risk'
                  ? setRiskAssetClasses((current) => toggleSelection(current, option))
                  : setStressAssetClasses((current) => toggleSelection(current, option))
              }
            />
          </section>
        )}

        <details className="rail-expander">
          <summary>
            <div>
              <span className="rail-panel__eyebrow">Advanced settings</span>
              <strong>Market window and model controls</strong>
            </div>
            <span>{lookbackDays}d / {Math.round(confidenceLevel * 100)}% / {rollingWindow}</span>
          </summary>
          <div className="rail-expander__body">
            <ToggleFilterGroup
              label="Snapshot currencies"
              options={currencyOptions}
              selected={effectiveMarketCurrencies}
              summary={`${effectiveMarketCurrencies.length}/${currencyOptions.length || 0} active`}
              onSelectAll={() => setMarketCurrencies(currencyOptions)}
              onToggle={(option) =>
                setMarketCurrencies((current) => {
                  const next = toggleSelection(current, option);
                  return next.length === 0 ? current : next;
                })
              }
            />

            <label className="control-group">
              <span className="control-group__label">Frequency</span>
              <select value={frequency} onChange={(event) => setFrequency(event.target.value as Frequency)}>
                <option value="D">Daily</option>
                <option value="M">Monthly</option>
                <option value="Q">Quarterly</option>
                <option value="A">Annual</option>
              </select>
            </label>

            <label className="control-group">
              <span className="control-group__label">Lookback window</span>
              <input
                type="range"
                min="30"
                max="365"
                step="30"
                value={lookbackDays}
                onChange={(event) => setLookbackDays(Number(event.target.value))}
              />
              <strong>{lookbackDays} days</strong>
            </label>

            <label className="control-group">
              <span className="control-group__label">VaR confidence</span>
              <input
                type="range"
                min="0.8"
                max="0.99"
                step="0.01"
                value={confidenceLevel}
                onChange={(event) => setConfidenceLevel(Number(event.target.value))}
              />
              <strong>{Math.round(confidenceLevel * 100)}%</strong>
            </label>

            <label className="control-group">
              <span className="control-group__label">Rolling window</span>
              <input
                type="range"
                min="5"
                max="60"
                step="1"
                value={rollingWindow}
                onChange={(event) => setRollingWindow(Number(event.target.value))}
              />
              <strong>{rollingWindow} periods</strong>
            </label>
          </div>
        </details>
      </aside>

      <main className="workspace">
        <header className="hero-panel">
          <div className="hero-panel__status">
            <span>ECB reference rates</span>
            <span>API {health?.status ?? 'starting'}</span>
            <span>{health ? formatLongDate(health.date) : 'Connecting to backend'}</span>
          </div>
          <div className="hero-panel__grid">
            <div className="hero-panel__brief">
              <p className="hero-panel__eyebrow">EUR FX operating picture</p>
              <h1>Capital Risk Intelligence</h1>
              <p className="hero-panel__copy">{activeTabConfig.description}</p>
              <div className="hero-panel__coords">
                <span>Sector // EUR/{effectiveFocusCurrency}</span>
                <span>Window // {lookbackDays}D</span>
                <span>Cadence // {frequency}</span>
              </div>
              <div className="hero-panel__signalbar">
                <article className="hero-signal">
                  <span>Primary watch</span>
                  <strong>{portfolioLoaded ? topExposure?.currency ?? 'EUR only' : 'Load book'}</strong>
                  <p>
                    {topExposure
                      ? formatCurrency(topExposure.value_eur)
                      : portfolioLoaded
                        ? 'No non-EUR exposure in scope'
                        : 'Use the sample book or upload a CSV to compute exposure'}
                  </p>
                </article>
                <article className="hero-signal">
                  <span>Market regime</span>
                  <strong>{market ? formatPercent(market.summary.annualized_volatility, 1) : 'Loading...'}</strong>
                  <p>
                    {market
                      ? `${formatPercent(market.summary.max_drawdown, 1)} max drawdown over the selected window`
                      : 'Fetching the live EUR market snapshot'}
                  </p>
                </article>
                <article className="hero-signal">
                  <span>Scenario watch</span>
                  <strong>{portfolioLoaded ? worstScenario?.currency ?? 'Flat' : 'Pending'}</strong>
                  <p>
                    {portfolioLoaded && worstScenario
                      ? formatCurrency(worstScenario.scenario_pnl_eur, { signed: true })
                      : 'Scenario sensitivity appears after a portfolio is loaded'}
                  </p>
                </article>
              </div>
            </div>
            <div className="hero-panel__metrics">
              <MetricCard
                label="Largest FX exposure"
                value={portfolioLoaded ? topExposure?.currency ?? 'EUR only' : 'No portfolio'}
                detail={
                  topExposure
                    ? formatCurrency(topExposure.value_eur)
                    : portfolioLoaded
                      ? 'No non-EUR positions'
                      : 'Load sample or upload CSV'
                }
              />
              <MetricCard
                label="Rates as of"
                value={market ? formatLongDate(market.latest_snapshot[0]?.rate_date ?? health?.date ?? '') : 'Loading...'}
                detail={market ? `EUR/${effectiveFocusCurrency} at ${formatRate(market.summary.latest_rate)}` : 'Fetching ECB snapshot'}
              />
              <MetricCard
                label="Portfolio rows"
                value={deferredPortfolioRows.length.toLocaleString('en-US')}
                detail={portfolioSource}
              />
              <MetricCard
                label="Non-EUR share"
                value={
                  overviewAnalysis
                    ? formatPercent(overviewAnalysis.summary.non_eur_share, 1)
                    : portfolioLoaded
                      ? 'Calculating...'
                      : 'Pending'
                }
                detail={
                  overviewAnalysis
                    ? formatCurrency(overviewAnalysis.summary.portfolio_value_eur, { compact: true })
                    : portfolioLoaded
                      ? 'Computing portfolio summary'
                      : 'Requires a loaded portfolio'
                }
              />
            </div>
          </div>
        </header>

        <nav className="tab-strip">
          {TAB_CONFIG.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`tab-strip__button ${activeTab === tab.id ? 'tab-strip__button--active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-strip__eyebrow">{tab.eyebrow}</span>
              <strong className="tab-strip__title">{tab.label}</strong>
              <span className="tab-strip__detail">{tab.description}</span>
              <span className="tab-strip__meta">{tabMeta[tab.id]}</span>
            </button>
          ))}
        </nav>

        {isPending ? <div className="inline-status" role="status">Refreshing the current view...</div> : null}

        <Suspense fallback={<div className="app-state">Loading the view...</div>}>
          {activeTab === 'overview' ? (
            <OverviewTab
              focusCurrency={effectiveFocusCurrency}
              market={market}
              analysis={overviewAnalysis}
              marketLoading={marketQuery.isLoading}
              analysisLoading={overviewAnalysisQuery.isLoading}
              portfolioLoaded={portfolioLoaded}
            />
          ) : null}

          {activeTab === 'risk' ? (
            !portfolioLoaded ? (
              <div className="app-state">Load the sample portfolio or upload a CSV to start portfolio risk analysis.</div>
            ) : riskSelection.filtered.length === 0 ? (
              <div className="app-state">No positions match the current risk filters.</div>
            ) : riskAnalysisQuery.data ? (
              <PortfolioRiskTab analysis={riskAnalysisQuery.data} />
            ) : (
              <div className="app-state">Building the filtered risk view...</div>
            )
          ) : null}

          {activeTab === 'stress' ? (
            !portfolioLoaded ? (
              <div className="app-state">Load the sample portfolio or upload a CSV to start scenario analysis.</div>
            ) : stressSelection.filtered.length === 0 ? (
              <div className="app-state">No positions match the current stress-test filters.</div>
            ) : stressAnalysisQuery.data ? (
              <StressTestTab
                analysis={stressAnalysisQuery.data}
                draftRows={syncedScenarioDraftRows}
                presets={SCENARIO_PRESETS.map(({ id, label, description }) => ({ id, label, description }))}
                appliedShockCount={activeShockCount}
                onApplyPreset={handleApplyScenarioPreset}
                onChangeDraft={(currency, value) =>
                  setDraftScenarioRows(
                    syncedScenarioDraftRows.map((row) =>
                      row.currency === currency ? { ...row, shockPct: value } : row,
                    ),
                  )
                }
                onApplyScenario={() =>
                  startTransition(() => {
                    setCommittedScenarioShocks(scenarioDraftToPayload(syncedScenarioDraftRows));
                  })
                }
                onResetScenario={() =>
                  startTransition(() => {
                    setDraftScenarioRows(buildScenarioDraft(stressSelection.filtered));
                    setCommittedScenarioShocks({});
                  })
                }
              />
            ) : (
              <div className="app-state">Building the stress view...</div>
            )
          ) : null}

          {activeTab === 'data' ? (
            health && templateQuery.data && market ? (
              <DataApiTab
                health={health}
                template={templateQuery.data}
                currencyCatalog={currencyQuery.data ?? []}
                market={market}
                lookbackDays={lookbackDays}
                frequency={frequency}
              />
            ) : (
              <div className="app-state">Loading reference data...</div>
            )
          ) : null}
        </Suspense>
      </main>
    </div>
  );
}

export default App;
