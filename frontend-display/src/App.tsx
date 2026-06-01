import * as echarts from 'echarts'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
} from 'lightweight-charts'
import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

type Point = {
  timestamp: string
  value: number
}

type Candle = {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

type TradeMarker = {
  timestamp: string
  side: string
  price: number
}

type SnapshotPayload = {
  title: string
  strategy_id: string
  strategy_version: string
  backtest_config: Record<string, unknown>
  metrics: {
    cumulative_return?: number
    max_drawdown?: number
    win_rate?: number
    trade_count?: number
    profit_loss_ratio?: number
    bar_count?: number
  }
  result_payload: {
    equity_curve?: Point[]
    benchmark_curve?: Point[]
    drawdown_curve?: Point[]
    candles?: Candle[]
    trade_markers?: TradeMarker[]
    position_curve?: Point[]
    trade_table?: Array<Record<string, unknown>>
    risk_disclosure?: string
  }
  generated_at: string
  publisher: string
  risk_disclosure?: string
}

type PublicSnapshot = {
  id: number
  title: string
  version: number
  payload: SnapshotPayload
  published_at: string | null
}

function getShareToken(): string {
  const params = new URLSearchParams(window.location.search)
  const queryToken = params.get('token')
  if (queryToken) {
    return queryToken
  }
  const pathParts = window.location.pathname.split('/').filter(Boolean)
  return pathParts[pathParts.length - 1] ?? ''
}

function formatPercent(value?: number): string {
  if (typeof value !== 'number') {
    return '-'
  }
  return `${(value * 100).toFixed(2)}%`
}

function formatNumber(value?: number): string {
  if (typeof value !== 'number') {
    return '-'
  }
  return String(value)
}

function latestValue(points: Point[] = []): number | undefined {
  return points[points.length - 1]?.value
}

function chartTime(timestamp: string): Time {
  const parsed = Date.parse(timestamp)
  return Math.floor((Number.isNaN(parsed) ? Date.now() : parsed) / 1000) as Time
}

function formatTradeValue(value: unknown): string {
  if (typeof value === 'number') {
    return value.toLocaleString(undefined, { maximumFractionDigits: 4 })
  }
  return typeof value === 'string' ? value : '-'
}

function CurveChart({
  equityCurve,
  benchmarkCurve,
  drawdownCurve,
}: {
  equityCurve: Point[]
  benchmarkCurve: Point[]
  drawdownCurve: Point[]
}) {
  const chartRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!chartRef.current) {
      return
    }

    const chart = echarts.init(chartRef.current, undefined, { renderer: 'canvas' })
    chart.setOption({
      animationDuration: 500,
      color: ['#0f766e', '#64748b', '#dc2626'],
      tooltip: { trigger: 'axis' },
      legend: { top: 0, right: 8, textStyle: { color: '#475569' } },
      grid: { left: 46, right: 28, top: 42, bottom: 34 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: equityCurve.map((point) => point.timestamp),
        axisLabel: { color: '#64748b' },
        axisLine: { lineStyle: { color: '#d7dee8' } },
      },
      yAxis: [
        {
          type: 'value',
          scale: true,
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e7edf5' } },
        },
        {
          type: 'value',
          axisLabel: { color: '#64748b', formatter: (value: number) => `${(value * 100).toFixed(0)}%` },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: 'Strategy Equity',
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 3 },
          areaStyle: { opacity: 0.08 },
          data: equityCurve.map((point) => point.value),
        },
        {
          name: 'Benchmark',
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, type: 'dashed' },
          data: benchmarkCurve.map((point) => point.value),
        },
        {
          name: 'Drawdown',
          type: 'line',
          yAxisIndex: 1,
          symbol: 'none',
          lineStyle: { width: 2 },
          areaStyle: { opacity: 0.1 },
          data: drawdownCurve.map((point) => point.value),
        },
      ],
    })

    const resize = () => chart.resize()
    window.addEventListener('resize', resize)
    return () => {
      window.removeEventListener('resize', resize)
      chart.dispose()
    }
  }, [benchmarkCurve, drawdownCurve, equityCurve])

  return <div className="echart-canvas" ref={chartRef} />
}

function PositionChart({ points }: { points: Point[] }) {
  const chartRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!chartRef.current) {
      return
    }

    const chart = echarts.init(chartRef.current, undefined, { renderer: 'canvas' })
    chart.setOption({
      animationDuration: 450,
      color: ['#2563eb'],
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 16, top: 18, bottom: 30 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: points.map((point) => point.timestamp),
        axisLabel: { color: '#64748b' },
        axisLine: { lineStyle: { color: '#d7dee8' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#64748b', formatter: (value: number) => `${value}%` },
        splitLine: { lineStyle: { color: '#e7edf5' } },
      },
      series: [
        {
          name: 'Position',
          type: 'line',
          step: 'middle',
          symbol: 'none',
          areaStyle: { opacity: 0.12 },
          lineStyle: { width: 3 },
          data: points.map((point) => point.value),
        },
      ],
    })

    const resize = () => chart.resize()
    window.addEventListener('resize', resize)
    return () => {
      window.removeEventListener('resize', resize)
      chart.dispose()
    }
  }, [points])

  return <div className="position-echart" ref={chartRef} />
}

function CandleChart({ candles, markers }: { candles: Candle[]; markers: TradeMarker[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!containerRef.current) {
      return
    }

    const chart: IChartApi = createChart(containerRef.current, {
      autoSize: true,
      height: 330,
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#475569',
      },
      grid: {
        vertLines: { color: '#eef2f7' },
        horzLines: { color: '#eef2f7' },
      },
      rightPriceScale: { borderColor: '#d7dee8' },
      timeScale: { borderColor: '#d7dee8' },
      crosshair: { mode: 1 },
    })
    const series: ISeriesApi<'Candlestick'> = chart.addSeries(CandlestickSeries, {
      upColor: '#dc2626',
      downColor: '#16a34a',
      borderUpColor: '#dc2626',
      borderDownColor: '#16a34a',
      wickUpColor: '#dc2626',
      wickDownColor: '#16a34a',
    })

    series.setData(
      candles.map((candle) => ({
        time: chartTime(candle.timestamp),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      })),
    )

    createSeriesMarkers(
      series,
      markers.map(
        (marker): SeriesMarker<Time> => ({
          time: chartTime(marker.timestamp),
          position: marker.side === 'buy' ? 'belowBar' : 'aboveBar',
          color: marker.side === 'buy' ? '#16a34a' : '#dc2626',
          shape: marker.side === 'buy' ? 'arrowUp' : 'arrowDown',
          text: `${marker.side.toUpperCase()} ${marker.price}`,
        }),
      ),
    )
    chart.timeScale().fitContent()

    return () => {
      chart.remove()
    }
  }, [candles, markers])

  return <div className="candle-chart" ref={containerRef} />
}

function App() {
  const token = useMemo(() => getShareToken(), [])
  const [snapshot, setSnapshot] = useState<PublicSnapshot | null>(null)
  const [loading, setLoading] = useState(() => Boolean(token))
  const [error, setError] = useState(() => (token ? '' : 'Missing share token.'))

  useEffect(() => {
    if (!token) {
      return
    }

    fetch(`${API_BASE_URL}/public/snapshots/${token}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Snapshot request failed: ${response.status}`)
        }
        return response.json() as Promise<PublicSnapshot>
      })
      .then(setSnapshot)
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : 'Snapshot request failed.')
      })
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return <main className="state-page">Loading published strategy snapshot...</main>
  }

  if (error || !snapshot) {
    return (
      <main className="state-page">
        <h1>Snapshot unavailable</h1>
        <p>{error || 'The report link is invalid or has been revoked.'}</p>
      </main>
    )
  }

  const payload = snapshot.payload
  const result = payload.result_payload
  const metrics = payload.metrics
  const equityCurve = result.equity_curve ?? []
  const benchmarkCurve = result.benchmark_curve ?? []
  const drawdownCurve = result.drawdown_curve ?? []
  const positionCurve = result.position_curve ?? []
  const candles = result.candles ?? []
  const trades = result.trade_table ?? []
  const markers = result.trade_markers ?? []

  const metricCards = [
    { label: 'Cumulative Return', value: formatPercent(metrics.cumulative_return) },
    { label: 'Max Drawdown', value: formatPercent(metrics.max_drawdown) },
    { label: 'Win Rate', value: formatPercent(metrics.win_rate) },
    { label: 'Trade Count', value: formatNumber(metrics.trade_count) },
    { label: 'Profit/Loss Ratio', value: formatNumber(metrics.profit_loss_ratio) },
    { label: 'Bar Count', value: formatNumber(metrics.bar_count) },
  ]

  return (
    <main className="report-page">
      <section className="report-hero">
        <div>
          <span className="eyebrow">Published Strategy Snapshot</span>
          <h1>{snapshot.title}</h1>
          <p>
            This read-only report is generated from an immutable backend snapshot. It presents reviewed backtest
            results only and does not connect to live trading.
          </p>
        </div>
        <dl className="snapshot-meta">
          <div>
            <dt>Strategy</dt>
            <dd>{payload.strategy_id}</dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>v{snapshot.version}</dd>
          </div>
          <div>
            <dt>Frequency</dt>
            <dd>{String(payload.backtest_config.frequency ?? '-')}</dd>
          </div>
          <div>
            <dt>Published At</dt>
            <dd>{snapshot.published_at ? new Date(snapshot.published_at).toLocaleString() : '-'}</dd>
          </div>
        </dl>
      </section>

      <section className="metric-strip">
        {metricCards.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="chart-grid">
        <article className="panel wide">
          <header>
            <h2>Equity, Benchmark and Drawdown</h2>
            <span>Latest equity {latestValue(equityCurve)?.toFixed(2) ?? '-'}</span>
          </header>
          <CurveChart equityCurve={equityCurve} benchmarkCurve={benchmarkCurve} drawdownCurve={drawdownCurve} />
        </article>

        <article className="panel">
          <header>
            <h2>Drawdown</h2>
            <span>Risk observation</span>
          </header>
          <div className="risk-stat">
            <strong>{formatPercent(metrics.max_drawdown)}</strong>
            <span>Worst observed decline in the published snapshot</span>
          </div>
        </article>

        <article className="panel">
          <header>
            <h2>Position Curve</h2>
            <span>Backend snapshot values</span>
          </header>
          <PositionChart points={positionCurve} />
        </article>

        <article className="panel wide">
          <header>
            <h2>Candles and Trade Markers</h2>
            <span>{markers.length} markers</span>
          </header>
          <CandleChart candles={candles} markers={markers} />
        </article>
      </section>

      <section className="panel trade-panel">
        <header>
          <h2>Trade Details</h2>
          <span>Simulated trades saved in the immutable snapshot</span>
        </header>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Side</th>
              <th>Price</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, index) => (
              <tr key={index}>
                <td>{formatTradeValue(trade.timestamp)}</td>
                <td>{formatTradeValue(trade.side)}</td>
                <td>{formatTradeValue(trade.price)}</td>
                <td>{formatTradeValue(trade.change_percent)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="risk-note">
        <h2>Strategy Description and Risk Disclosure</h2>
        <p>
          {payload.risk_disclosure ??
            result.risk_disclosure ??
            'Backtest results are simulated and do not represent real-money trading.'}
        </p>
      </section>
    </main>
  )
}

export default App
