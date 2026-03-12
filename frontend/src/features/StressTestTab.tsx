import type { ChangeEvent } from 'react';

import { DataTable } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { SectionTitle } from '../components/SectionTitle';
import { ValueBarChart } from '../components/ValueBarChart';
import { formatCurrency, formatPercent } from '../lib/format';
import type { PortfolioAnalysisResponse, ScenarioDraftRow, ScenarioPresetOption } from '../types';

type StressTestTabProps = {
  analysis: PortfolioAnalysisResponse;
  draftRows: ScenarioDraftRow[];
  presets: ScenarioPresetOption[];
  appliedShockCount: number;
  onApplyPreset: (presetId: string) => void;
  onChangeDraft: (currency: string, value: string) => void;
  onApplyScenario: () => void;
  onResetScenario: () => void;
};

export function StressTestTab({
  analysis,
  draftRows,
  presets,
  appliedShockCount,
  onApplyPreset,
  onChangeDraft,
  onApplyScenario,
  onResetScenario,
}: StressTestTabProps) {
  const worstRow = analysis.scenario_analysis[0];

  return (
    <div className="page-grid">
      <SectionTitle
        eyebrow="What-if analysis"
        command="fx.scenario --commit shocks --observe pnl"
        title="Stress Test"
        description="Set directional shocks and apply them deliberately. The scenario engine only reruns when you commit the draft."
      />

      <div className="brief-grid">
        <article className="brief-card">
          <span className="brief-card__label">Scenario total</span>
          <strong>{formatCurrency(analysis.summary.scenario_total_pnl_eur, { signed: true })}</strong>
          <p>Net portfolio move under the currently committed scenario.</p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Weakest currency</span>
          <strong>{worstRow?.currency ?? 'Flat'}</strong>
          <p>{worstRow ? `${formatCurrency(worstRow.scenario_pnl_eur, { signed: true })} on the worst row.` : 'No active scenario result.'}</p>
        </article>
        <article className="brief-card">
          <span className="brief-card__label">Committed shocks</span>
          <strong>{appliedShockCount.toLocaleString('en-US')}</strong>
          <p>
            {appliedShockCount === 0 || draftRows.length === 0
              ? 'Preset or manual shocks have not been committed yet.'
              : formatPercent(appliedShockCount / draftRows.length, 0)}
          </p>
        </article>
      </div>

      <div className="split-grid split-grid--narrow">
        <section className="panel">
          <div className="panel__header">
            <h3>Shock editor</h3>
            <span>Positive means EUR strengthens</span>
          </div>
          <div className="preset-strip">
            {presets.map((preset) => (
              <button key={preset.id} type="button" className="preset-card" onClick={() => onApplyPreset(preset.id)}>
                <span>{preset.label}</span>
                <strong>{preset.description}</strong>
              </button>
            ))}
          </div>
          <div className="shock-editor">
            {draftRows.map((row) => (
              <label key={row.currency} className="shock-editor__row">
                <span>{row.currency}</span>
                <input
                  type="number"
                  step="0.25"
                  value={row.shockPct}
                  onChange={(event: ChangeEvent<HTMLInputElement>) =>
                    onChangeDraft(row.currency, event.target.value)
                  }
                  placeholder="0.00"
                />
              </label>
            ))}
          </div>
          <div className="button-row">
            <button type="button" onClick={onApplyScenario}>
              Run scenario
            </button>
            <button type="button" className="button-secondary" onClick={onResetScenario}>
              Reset shocks
            </button>
          </div>
        </section>

        <section className="page-grid">
          <div className="metric-grid metric-grid--three">
            <MetricCard
              label="Scenario total"
              value={formatCurrency(analysis.summary.scenario_total_pnl_eur, { signed: true })}
              tone={analysis.summary.scenario_total_pnl_eur < 0 ? 'danger' : 'positive'}
            />
            <MetricCard
              label="Worst currency"
              value={worstRow?.currency ?? 'Flat'}
              detail={worstRow ? formatCurrency(worstRow.scenario_pnl_eur, { signed: true }) : 'No active shocks'}
              tone={worstRow && worstRow.scenario_pnl_eur < 0 ? 'danger' : 'default'}
            />
            <MetricCard
              label="Shocks applied"
              value={appliedShockCount.toLocaleString('en-US')}
              detail={appliedShockCount === 0 ? 'No committed scenario yet' : formatPercent(appliedShockCount / draftRows.length, 0)}
            />
          </div>
          <ValueBarChart
            title="Scenario P&L by currency"
            data={analysis.scenario_analysis}
            xKey="currency"
            yKey="scenario_pnl_eur"
            directional
          />
        </section>
      </div>

      <section className="panel">
        <div className="panel__header">
          <h3>Scenario ledger</h3>
          <span>{appliedShockCount === 0 ? 'Flat scenario' : `${appliedShockCount} active shocks`}</span>
        </div>
        <DataTable
          columns={[
            { key: 'currency', label: 'Currency' },
            { key: 'shock', label: 'Shock', align: 'right' },
            { key: 'baseValue', label: 'Base value', align: 'right' },
            { key: 'scenarioPnl', label: 'Scenario P&L', align: 'right' },
          ]}
          rows={analysis.scenario_analysis.map((row) => ({
            currency: row.currency,
            shock: formatPercent(row.shock_pct, 2),
            baseValue: formatCurrency(row.current_value_eur),
            scenarioPnl: formatCurrency(row.scenario_pnl_eur, { signed: true }),
          }))}
        />
      </section>
    </div>
  );
}
