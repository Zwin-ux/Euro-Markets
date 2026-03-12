import type {
  CurrencyCatalogRow,
  HealthResponse,
  MarketMonitorResponse,
  PortfolioAnalysisResponse,
  PortfolioTemplateResponse,
  PositionInput,
  Frequency,
} from '../types';

const REQUEST_TIMEOUT_MS = 15_000;

function inferRailwayApiBaseUrl(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const host = window.location.host;
  if (host.includes('capital-risk-dashboard') && host.includes('.up.railway.app')) {
    return `${window.location.protocol}//${host.replace('capital-risk-dashboard', 'capital-risk-api')}`;
  }

  return null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? inferRailwayApiBaseUrl() ?? '/api';

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
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`The API request timed out. Current API base: ${API_BASE_URL}`);
    }
    throw new Error(`The dashboard could not reach the API. Current API base: ${API_BASE_URL}`);
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      // Ignore JSON parse failures on error payloads.
    }
    throw new Error(detail || `API request failed (${response.status}) for ${path}`);
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
