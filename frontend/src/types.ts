export type Frequency = 'D' | 'M' | 'Q' | 'A';

export type PositionInput = {
  position_id: string;
  position_name: string;
  currency: string;
  market_value_local: number;
  asset_class: string;
  book: string;
};

export type CurrencyCatalogRow = {
  symbol: string;
  name: string;
  country?: string;
};

export type RateRow = {
  base_currency: string;
  target_currency: string;
  rate_date: string;
  exchange_rate: number;
  frequency: Frequency;
  source: string;
};

export type RollingVolatilityPoint = {
  rate_date: string;
  rolling_volatility: number;
};

export type PortfolioValuePoint = {
  rate_date: string;
  portfolio_value_eur: number;
};

export type ExposureRow = {
  currency: string;
  position_count: number;
  market_value_local: number;
  value_eur: number;
  fx_pnl_1d_eur: number;
  current_rate: number;
  portfolio_weight: number;
};

export type ScenarioRow = {
  currency: string;
  shock_pct: number;
  current_rate: number;
  stressed_rate: number;
  current_value_eur: number;
  stressed_value_eur: number;
  scenario_pnl_eur: number;
};

export type AnalyzedPosition = PositionInput & {
  current_rate: number;
  previous_rate: number;
  value_eur: number;
  previous_value_eur: number;
  fx_pnl_1d_eur: number;
  portfolio_weight: number;
};

export type CorrelationMatrix = Record<string, Record<string, number>>;

export type MarketMonitorSummary = {
  latest_rate: number;
  latest_date: string;
  period_return: number;
  annualized_volatility: number;
  max_drawdown: number;
};

export type PortfolioSummary = {
  portfolio_value_eur: number;
  fx_pnl_1d_eur: number;
  historical_var_1d_eur: number;
  historical_var_1d_pct: number;
  annualized_portfolio_volatility: number;
  non_eur_share: number;
  position_count: number;
  currency_count: number;
  latest_rate_date: string;
  scenario_total_pnl_eur: number;
  rolling_window: number;
  confidence_level: number;
};

export type MarketMonitorResponse = {
  summary: MarketMonitorSummary;
  history: RateRow[];
  latest_snapshot: RateRow[];
  rolling_volatility: RollingVolatilityPoint[];
};

export type PortfolioAnalysisResponse = {
  summary: PortfolioSummary;
  positions: AnalyzedPosition[];
  currency_exposure: ExposureRow[];
  portfolio_value_history: PortfolioValuePoint[];
  rolling_volatility: RollingVolatilityPoint[];
  scenario_analysis: ScenarioRow[];
  correlation_matrix: CorrelationMatrix;
  market_snapshot: RateRow[];
  rate_history: RateRow[];
};

export type PortfolioTemplateResponse = {
  columns: string[];
  sample: PositionInput[];
};

export type HealthResponse = {
  status: string;
  source: string;
  date: string;
};

export type ScenarioDraftRow = {
  currency: string;
  shockPct: string;
};
