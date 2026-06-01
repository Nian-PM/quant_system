const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

export type StrategyTemplate = {
  strategy_id: string
  display_name: string
  description: string
  version: string
  supported_scopes: string[]
  supported_frequencies: string[]
  parameters: StrategyParameter[]
  output_contract: string[]
}

export type StrategyParameter = {
  name: string
  label: string
  type: 'number' | 'integer' | 'boolean' | 'select'
  default: number | boolean | string
  description: string
  min_value: number | null
  max_value: number | null
  options: string[]
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export type UserProfile = {
  id: number
  username: string
}

export type OperationLog = {
  id: number
  actor: string
  action: string
  target_type: string
  target_id: string
  detail: Record<string, unknown>
  created_at: string
}

export type Instrument = {
  id: number
  symbol: string
  exchange: string
  name: string
  asset_type: string
  created_at: string
}

export type InstrumentInput = {
  symbol: string
  exchange: string
  name: string
  asset_type: string
}

export type PortfolioPosition = {
  instrument: Instrument
  weight: number
}

export type Portfolio = {
  id: number
  name: string
  description: string
  positions: PortfolioPosition[]
  created_at: string
}

export type PortfolioInput = {
  name: string
  description: string
  positions: Array<{ instrument_id: number; weight: number }>
}

export type DataImportTask = {
  id: number
  source: string
  status: string
  message: string
  rows_imported: number
  rows_updated: number
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export type Bar = {
  id: number
  instrument_id: number
  frequency: string
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  source: string
  data_version: string
}

export type CsvImportInput = {
  instrument_id: number
  frequency: string
  source: string
  csv_text: string
}

export type StrategyParameterSet = {
  id: number
  strategy_id: string
  name: string
  parameters: Record<string, number | boolean | string>
  created_at: string
}

export type StrategyParameterSetInput = {
  strategy_id: string
  name: string
  parameters: Record<string, number | boolean | string>
}

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }

  return response.json()
}

export async function fetchStrategies(): Promise<StrategyTemplate[]> {
  return requestJson<StrategyTemplate[]>('/strategies')
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  return requestJson<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function fetchProfile(token: string): Promise<UserProfile> {
  return requestJson<UserProfile>('/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function fetchOperationLogs(token: string): Promise<OperationLog[]> {
  return requestJson<OperationLog[]>('/operation-logs', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function fetchInstruments(token: string): Promise<Instrument[]> {
  return requestJson<Instrument[]>('/instruments', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function createInstrument(token: string, input: InstrumentInput): Promise<Instrument> {
  return requestJson<Instrument>('/instruments', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  })
}

export async function fetchPortfolios(token: string): Promise<Portfolio[]> {
  return requestJson<Portfolio[]>('/portfolios', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function createPortfolio(token: string, input: PortfolioInput): Promise<Portfolio> {
  return requestJson<Portfolio>('/portfolios', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  })
}

export async function importCsvMarketData(token: string, input: CsvImportInput): Promise<DataImportTask> {
  return requestJson<DataImportTask>('/market-data/import-csv', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  })
}

export async function fetchMarketBars(
  token: string,
  instrumentId: number,
  frequency = '5m',
): Promise<Bar[]> {
  const params = new URLSearchParams({
    instrument_id: String(instrumentId),
    frequency,
    limit: '20',
  })
  return requestJson<Bar[]>(`/market-data/bars?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function fetchDataImportTasks(token: string): Promise<DataImportTask[]> {
  return requestJson<DataImportTask[]>('/market-data/import-tasks', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function fetchStrategyParameterSets(token: string): Promise<StrategyParameterSet[]> {
  return requestJson<StrategyParameterSet[]>('/strategy-parameter-sets', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export async function createStrategyParameterSet(
  token: string,
  input: StrategyParameterSetInput,
): Promise<StrategyParameterSet> {
  return requestJson<StrategyParameterSet>('/strategy-parameter-sets', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  })
}
