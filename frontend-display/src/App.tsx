import './App.css'

const metrics = [
  { label: '累计收益', value: '+28.6%' },
  { label: '年化收益', value: '+13.4%' },
  { label: '最大回撤', value: '-7.8%' },
  { label: '胜率', value: '61.2%' },
  { label: '交易次数', value: '84' },
  { label: '盈亏比', value: '1.72' },
]

const trades = [
  ['2025-11-12 10:35', '买入', '600519.SH', '低位网格触发', '10%'],
  ['2025-12-03 14:20', '卖出', '600519.SH', '高位网格触发', '10%'],
  ['2026-01-16 11:05', '买入', '600519.SH', '均线过滤通过', '10%'],
  ['2026-03-22 13:45', '卖出', '600519.SH', '滚动T止盈', '10%'],
]

function App() {
  return (
    <main className="report-page">
      <section className="report-hero">
        <div>
          <span className="eyebrow">Published Strategy Snapshot</span>
          <h1>Rolling T / Grid Strategy Report</h1>
          <p>
            固定股票策略快照。所有图表来自后台审核后的静态回测结果，客户页面不连接实时交易。
          </p>
        </div>
        <dl className="snapshot-meta">
          <div>
            <dt>标的</dt>
            <dd>600519.SH</dd>
          </div>
          <div>
            <dt>周期</dt>
            <dd>5分钟</dd>
          </div>
          <div>
            <dt>区间</dt>
            <dd>2024-06-01 至 2026-05-31</dd>
          </div>
          <div>
            <dt>生成时间</dt>
            <dd>2026-06-01 11:30</dd>
          </div>
        </dl>
      </section>

      <section className="metric-strip">
        {metrics.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="chart-grid">
        <article className="panel wide">
          <header>
            <h2>策略收益 vs 基准收益</h2>
            <span>权益曲线</span>
          </header>
          <div className="line-chart">
            <svg viewBox="0 0 760 260" role="img" aria-label="strategy equity curve">
              <polyline className="benchmark-line" points="0,210 100,205 200,182 300,176 400,160 500,138 620,128 760,118" />
              <polyline className="strategy-line" points="0,218 80,190 160,198 250,150 340,156 430,112 530,96 650,72 760,54" />
            </svg>
          </div>
        </article>

        <article className="panel">
          <header>
            <h2>回撤曲线</h2>
            <span>风险观察</span>
          </header>
          <div className="drawdown-bars">
            {[12, 30, 18, 42, 24, 50, 28, 20, 36, 16, 24, 10].map((height, index) => (
              <i key={index} style={{ height: `${height}%` }} />
            ))}
          </div>
        </article>

        <article className="panel">
          <header>
            <h2>仓位变化</h2>
            <span>底仓 + 交易仓</span>
          </header>
          <div className="position-steps">
            {[50, 60, 50, 40, 50, 60, 50, 40, 50].map((value, index) => (
              <i key={index} style={{ height: `${value}%` }} />
            ))}
          </div>
        </article>

        <article className="panel wide">
          <header>
            <h2>K线与买卖点</h2>
            <span>示意占位，后续接 Lightweight Charts</span>
          </header>
          <div className="candles">
            {Array.from({ length: 34 }).map((_, index) => (
              <i
                key={index}
                className={index % 3 === 0 ? 'down' : 'up'}
                style={{ height: `${36 + ((index * 17) % 96)}px` }}
              />
            ))}
            <b className="buy-marker">B</b>
            <b className="sell-marker">S</b>
          </div>
        </article>
      </section>

      <section className="panel trade-panel">
        <header>
          <h2>交易明细</h2>
          <span>后台发布快照中的模拟成交记录</span>
        </header>
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>方向</th>
              <th>标的</th>
              <th>原因</th>
              <th>仓位变化</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={trade.join('-')}>
                {trade.map((cell) => (
                  <td key={cell}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="risk-note">
        <h2>策略说明与风险提示</h2>
        <p>
          本页面展示的是历史回测快照，不代表未来收益。策略参数、手续费、滑点、数据源和回测区间都会影响结果。
          V1 不包含真实下单能力，所有结果仅用于策略研究和客户演示。
        </p>
      </section>
    </main>
  )
}

export default App
