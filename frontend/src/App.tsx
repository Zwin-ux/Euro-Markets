import { Suspense, lazy, useDeferredValue, useEffect, useRef, useState, useTransition } from 'react';
import Papa from 'papaparse';
import { useQuery } from '@tanstack/react-query';

import './App.css';
import { MetricCard } from './components/MetricCard';
import { ToggleFilterGroup } from './components/ToggleFilterGroup';
import { fetchCurrencyCatalog, fetchHealth, fetchMarketMonitor, fetchPortfolioTemplate, analyzePortfolio } from './lib/api';
import { formatCurrency, formatLongDate, formatPercent } from './lib/format';
import {
  buildScenarioDraft,
  filterPortfolioRows,
  normalizePortfolioRows,
  scenarioDraftToPayload,
  uniqueAssetClasses,
  uniqueBooks,
} from './lib/portfolio';
import type { Frequency, PositionInput, ScenarioDraftRow } from './types';
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

function buildFilterSelection(
  positions: PositionInput[],
  selectedBooks: string[],
  selectedAssetClasses: string[],
) {
  const bookOptions = uniqueBooks(positions);
  const assetOptions = uniqueAssetClasses(positions);

  if ((bookOptions.length > 0 && selectedBooks.length === 0) || (assetOptions.length > 0 && selectedAssetClasses.length === 0)) {
    return { bookOptions, assetOptions, filtered: [] as PositionInput[] };
  }

  return {
    bookOptions,
    assetOptions,
    filtered: filterPortfolioRows(positions, selectedBooks, selectedAssetClasses),
  };
}

function toggleSelection(current: string[], option: string) {
  return current.includes(option) ? current.filter((item) => item !== option) : [...current, option];
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
  const hasSeededTemplate = useRef(false);

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

  useEffect(() => {
    if (templateQuery.data && portfolioRows.length === 0 && !hasSeededTemplate.current) {
      hasSeededTemplate.current = true;
      startTransition(() => {
        applyPortfolioRows(templateQuery.data.sample, 'Sample portfolio from API');
      });
    }
  }, [templateQuery.data, portfolioRows.length]);

  const currencyOptions = (currencyQuery.data ?? []).map((row) => row.symbol).filter((symbol) => symbol !== 'EUR');
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
    enabled: currencyOptions.length > 0 && effectiveMarketCurrencies.length > 0,
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

  const baseError =
    healthQuery.error || currencyQuery.error || templateQuery.error || marketQuery.error || overviewAnalysisQuery.error;

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

  if (baseError instanceof Error) {
    return <div className="app-state">{baseError.message}</div>;
  }

  if (!healthQuery.data || !templateQuery.data || !marketQuery.data || !overviewAnalysisQuery.data) {
    return <div className="app-state">Loading the operating picture...</div>;
  }

  return (
    <div className="app-shell">
      <aside className="control-rail">
        <section className="rail-panel">
          <span className="rail-panel__eyebrow">Core inputs</span>
          <h2>Control rail</h2>
          <p>Change the focus pair, load a book, and only adjust model inputs when you actually need to.</p>
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
              onToggle={(option) =>
                activeTab === 'risk'
                  ? setRiskAssetClasses((current) => toggleSelection(current, option))
                  : setStressAssetClasses((current) => toggleSelection(current, option))
              }
            />
          </section>
        )}

        <section className="rail-panel rail-panel--compact">
          <span className="rail-panel__eyebrow">Advanced settings</span>
            <ToggleFilterGroup
              label="Snapshot currencies"
              options={currencyOptions}
              selected={effectiveMarketCurrencies}
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
            <input type="range" min="30" max="365" step="30" value={lookbackDays} onChange={(event) => setLookbackDays(Number(event.target.value))} />
            <strong>{lookbackDays} days</strong>
          </label>

          <label className="control-group">
            <span className="control-group__label">VaR confidence</span>
            <input type="range" min="0.8" max="0.99" step="0.01" value={confidenceLevel} onChange={(event) => setConfidenceLevel(Number(event.target.value))} />
            <strong>{Math.round(confidenceLevel * 100)}%</strong>
          </label>

          <label className="control-group">
            <span className="control-group__label">Rolling window</span>
            <input type="range" min="5" max="60" step="1" value={rollingWindow} onChange={(event) => setRollingWindow(Number(event.target.value))} />
            <strong>{rollingWindow} periods</strong>
          </label>
        </section>
      </aside>

      <main className="workspace">
        <header className="hero-panel">
          <div className="hero-panel__status">
            <span>ECB reference rates</span>
            <span>API {healthQuery.data.status}</span>
            <span>{formatLongDate(healthQuery.data.date)}</span>
          </div>
          <div className="hero-panel__grid">
            <div>
              <p className="hero-panel__eyebrow">EUR risk command view</p>
              <h1>Capital Risk Intelligence</h1>
              <p className="hero-panel__copy">
                A browser-native control room for EUR exchange-rate monitoring, portfolio concentration, and scenario work.
              </p>
            </div>
            <div className="hero-panel__metrics">
              <MetricCard label="Largest FX exposure" value={overviewAnalysisQuery.data.currency_exposure.find((row) => row.currency !== 'EUR')?.currency ?? 'EUR only'} detail={formatCurrency(overviewAnalysisQuery.data.currency_exposure.find((row) => row.currency !== 'EUR')?.value_eur ?? 0)} />
              <MetricCard label="Rates as of" value={formatLongDate(marketQuery.data.latest_snapshot[0]?.rate_date ?? healthQuery.data.date)} detail={`EUR/${effectiveFocusCurrency} in focus`} />
              <MetricCard label="Portfolio rows" value={deferredPortfolioRows.length.toLocaleString('en-US')} detail={portfolioSource} />
              <MetricCard label="Non-EUR share" value={formatPercent(overviewAnalysisQuery.data.summary.non_eur_share, 1)} detail={formatCurrency(overviewAnalysisQuery.data.summary.portfolio_value_eur, { compact: true })} />
            </div>
          </div>
        </header>

        <nav className="tab-strip">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'risk', label: 'Portfolio Risk' },
            { id: 'stress', label: 'Stress Test' },
            { id: 'data', label: 'Data & API' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`tab-strip__button ${activeTab === tab.id ? 'tab-strip__button--active' : ''}`}
              onClick={() => setActiveTab(tab.id as TabId)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {isPending ? <div className="inline-status">Refreshing the view...</div> : null}

        <Suspense fallback={<div className="app-state">Loading the view...</div>}>
          {activeTab === 'overview' ? (
            <OverviewTab focusCurrency={effectiveFocusCurrency} market={marketQuery.data} analysis={overviewAnalysisQuery.data} />
          ) : null}

          {activeTab === 'risk' ? (
            riskSelection.filtered.length === 0 ? (
              <div className="app-state">No positions match the current risk filters.</div>
            ) : riskAnalysisQuery.data ? (
              <PortfolioRiskTab analysis={riskAnalysisQuery.data} />
            ) : (
              <div className="app-state">Building the filtered risk view...</div>
            )
          ) : null}

          {activeTab === 'stress' ? (
            stressSelection.filtered.length === 0 ? (
              <div className="app-state">No positions match the current stress-test filters.</div>
            ) : stressAnalysisQuery.data ? (
              <StressTestTab
                analysis={stressAnalysisQuery.data}
                draftRows={syncedScenarioDraftRows}
                appliedShockCount={Object.keys(committedScenarioShocks).length}
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
            <DataApiTab
              health={healthQuery.data}
              template={templateQuery.data}
              currencyCatalog={currencyQuery.data ?? []}
              market={marketQuery.data}
              lookbackDays={lookbackDays}
              frequency={frequency}
            />
          ) : null}
        </Suspense>
      </main>
    </div>
  );
}

export default App;
