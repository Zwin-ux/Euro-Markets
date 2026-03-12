import type {
  CurrencyCatalogRow,
  HealthResponse,
  MarketMonitorResponse,
  PortfolioAnalysisResponse,
  PortfolioTemplateResponse,
  PositionInput,
  Frequency,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

type MarketMonitorParams = {
  focusCurrency: string;
  currencies: string[];
  lookbackDays: number;
  frequency: Frequency;
};

type PortfolioAnalysisParams = {
  positions: PositionInput[];
  lookbackDays: number;
  confidenceLevel: number;
  rollingWindow: number;
  frequency: Frequency;
  scenarioShocks?: Record<string, number>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      // Ignore JSON parse failures on error payloads.
    }
    throw new Error(detail || 'Request failed');
  }

  return (await response.json()) as T;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function fetchCurrencyCatalog(): Promise<CurrencyCatalogRow[]> {
  const response = await request<{ currencies: CurrencyCatalogRow[] }>('/currencies');
  return response.currencies;
}

export async function fetchPortfolioTemplate(): Promise<PortfolioTemplateResponse> {
  return request<PortfolioTemplateResponse>('/portfolio/template');
}

export async function fetchMarketMonitor(params: MarketMonitorParams): Promise<MarketMonitorResponse> {
  const searchParams = new URLSearchParams({
    focus_currency: params.focusCurrency,
    currencies: params.currencies.join(','),
    lookback_days: String(params.lookbackDays),
    frequency: params.frequency,
  });
  return request<MarketMonitorResponse>(`/market-monitor?${searchParams.toString()}`);
}

export async function analyzePortfolio(params: PortfolioAnalysisParams): Promise<PortfolioAnalysisResponse> {
  return request<PortfolioAnalysisResponse>('/portfolio/analyze', {
    method: 'POST',
    body: JSON.stringify({
      positions: params.positions,
      lookback_days: params.lookbackDays,
      confidence_level: params.confidenceLevel,
      rolling_window: params.rollingWindow,
      frequency: params.frequency,
      scenario_shocks: params.scenarioShocks ?? {},
    }),
  });
}
