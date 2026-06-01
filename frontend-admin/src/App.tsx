import {
  ApiOutlined,
  AreaChartOutlined,
  AuditOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  DeploymentUnitOutlined,
  FundProjectionScreenOutlined,
  LineChartOutlined,
  LinkOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
  StockOutlined,
} from '@ant-design/icons'
import {
  Alert,
  Badge,
  Button,
  Card,
  ConfigProvider,
  Form,
  Input,
  InputNumber,
  Layout,
  Menu,
  Progress,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import { useEffect, useState } from 'react'
import {
  fetchOperationLogs,
  fetchProfile,
  fetchInstruments,
  fetchDataImportTasks,
  fetchMarketBars,
  fetchPortfolios,
  fetchStrategies,
  fetchStrategyParameterSets,
  createInstrument,
  createPortfolio,
  createStrategyParameterSet,
  importCsvMarketData,
  type Bar,
  type CsvImportInput,
  type DataImportTask,
  login,
  type Instrument,
  type InstrumentInput,
  type OperationLog,
  type Portfolio,
  type StrategyParameter,
  type StrategyParameterSet,
  type StrategyTemplate,
  type UserProfile,
} from './api/client'
import './App.css'

const { Header, Sider, Content } = Layout
const { Text, Title } = Typography

const modules = [
  { key: 'portfolios', icon: <StockOutlined />, label: 'Portfolios' },
  { key: 'data', icon: <DatabaseOutlined />, label: 'Market Data' },
  { key: 'strategies', icon: <DeploymentUnitOutlined />, label: 'Strategies' },
  { key: 'backtests', icon: <BarChartOutlined />, label: 'Backtests' },
  { key: 'paper', icon: <PlayCircleOutlined />, label: 'Paper Runs' },
  { key: 'snapshots', icon: <FundProjectionScreenOutlined />, label: 'Snapshots' },
  { key: 'links', icon: <LinkOutlined />, label: 'Share Links' },
  { key: 'logs', icon: <AuditOutlined />, label: 'Logs' },
]

const tasks = [
  { key: 1, name: 'CSI 300 grid backtest', type: 'Backtest', status: 'Pending', updatedAt: '2026-06-01 10:30' },
  { key: 2, name: '600519.SH 5m data sync', type: 'Data', status: 'Succeeded', updatedAt: '2026-06-01 09:42' },
  { key: 3, name: 'rolling_t_grid paper run', type: 'Paper', status: 'Running', updatedAt: '2026-06-01 09:30' },
]

function App() {
  const [strategies, setStrategies] = useState<StrategyTemplate[]>([])
  const [instruments, setInstruments] = useState<Instrument[]>([])
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [bars, setBars] = useState<Bar[]>([])
  const [dataImportTasks, setDataImportTasks] = useState<DataImportTask[]>([])
  const [strategyParameterSets, setStrategyParameterSets] = useState<StrategyParameterSet[]>([])
  const [operationLogs, setOperationLogs] = useState<OperationLog[]>([])
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null)
  const [token, setToken] = useState(() => localStorage.getItem('quant_admin_token') ?? '')
  const [apiStatus, setApiStatus] = useState('Checking')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)
  const [instrumentForm] = Form.useForm<InstrumentInput>()
  const [portfolioForm] = Form.useForm<{ name: string; description: string; instrument_id: number; weight: number }>()
  const [marketDataForm] = Form.useForm<CsvImportInput>()
  const [strategyParameterForm] = Form.useForm<Record<string, number | boolean | string>>()
  const [instrumentSaving, setInstrumentSaving] = useState(false)
  const [portfolioSaving, setPortfolioSaving] = useState(false)
  const [marketDataImporting, setMarketDataImporting] = useState(false)
  const [strategyParameterSaving, setStrategyParameterSaving] = useState(false)
  const [marketDataError, setMarketDataError] = useState('')
  const [strategyParameterError, setStrategyParameterError] = useState('')

  const refreshAdminData = (accessToken: string) => {
    Promise.all([
      fetchStrategies(),
      fetchProfile(accessToken),
      fetchOperationLogs(accessToken),
      fetchInstruments(accessToken),
      fetchPortfolios(accessToken),
      fetchDataImportTasks(accessToken),
      fetchStrategyParameterSets(accessToken),
    ])
      .then(([
        strategyPayload,
        profilePayload,
        logPayload,
        instrumentPayload,
        portfolioPayload,
        importTaskPayload,
        strategyParameterSetPayload,
      ]) => {
        setStrategies(strategyPayload)
        setCurrentUser(profilePayload)
        setOperationLogs(logPayload)
        setInstruments(instrumentPayload)
        setPortfolios(portfolioPayload)
        setDataImportTasks(importTaskPayload)
        setStrategyParameterSets(strategyParameterSetPayload)
        setApiStatus('Connected')

        const firstInstrument = instrumentPayload[0]
        if (firstInstrument) {
          fetchMarketBars(accessToken, firstInstrument.id).then(setBars).catch(() => setBars([]))
        } else {
          setBars([])
        }
      })
      .catch(() => {
        setApiStatus('Offline')
        setCurrentUser(null)
        setOperationLogs([])
        setInstruments([])
        setPortfolios([])
        setBars([])
        setDataImportTasks([])
        setStrategyParameterSets([])
      })
  }

  useEffect(() => {
    if (token) {
      refreshAdminData(token)
    } else {
      fetchStrategies()
        .then((payload) => {
          setStrategies(payload)
          setApiStatus('Connected')
        })
        .catch(() => setApiStatus('Offline'))
    }
  }, [token])

  useEffect(() => {
    if (instruments[0] && !portfolioForm.getFieldValue('instrument_id')) {
      portfolioForm.setFieldValue('instrument_id', instruments[0].id)
    }
    if (instruments[0] && !marketDataForm.getFieldValue('instrument_id')) {
      marketDataForm.setFieldValue('instrument_id', instruments[0].id)
    }
  }, [instruments, marketDataForm, portfolioForm])

  useEffect(() => {
    const firstStrategy = strategies[0]
    if (!currentUser || !firstStrategy) {
      return
    }

    const defaultValues = Object.fromEntries(
      firstStrategy.parameters.map((parameter) => [parameter.name, parameter.default]),
    )
    strategyParameterForm.setFieldsValue({
      name: `${firstStrategy.display_name} default`,
      strategy_id: firstStrategy.strategy_id,
      ...defaultValues,
    })
  }, [currentUser, strategies, strategyParameterForm])

  const handleLogin = (values: { username: string; password: string }) => {
    setLoginLoading(true)
    setLoginError('')
    login(values.username, values.password)
      .then((payload) => {
        localStorage.setItem('quant_admin_token', payload.access_token)
        setToken(payload.access_token)
      })
      .catch(() => setLoginError('Invalid username or password. Use admin / admin for the local seed account.'))
      .finally(() => setLoginLoading(false))
  }

  const handleLogout = () => {
    localStorage.removeItem('quant_admin_token')
    setToken('')
    setCurrentUser(null)
    setOperationLogs([])
    setInstruments([])
    setPortfolios([])
  }

  const handleCreateInstrument = (values: InstrumentInput) => {
    if (!token) {
      return
    }

    setInstrumentSaving(true)
    createInstrument(token, values)
      .then(() => {
        instrumentForm.resetFields()
        refreshAdminData(token)
      })
      .finally(() => setInstrumentSaving(false))
  }

  const handleCreatePortfolio = (values: { name: string; description: string; instrument_id: number; weight: number }) => {
    if (!token) {
      return
    }

    setPortfolioSaving(true)
    createPortfolio(token, {
      name: values.name,
      description: values.description,
      positions: [{ instrument_id: Number(values.instrument_id), weight: Number(values.weight) }],
    })
      .then(() => {
        portfolioForm.resetFields()
        refreshAdminData(token)
      })
      .finally(() => setPortfolioSaving(false))
  }

  const handleImportMarketData = (values: CsvImportInput) => {
    if (!token) {
      return
    }

    setMarketDataImporting(true)
    setMarketDataError('')
    importCsvMarketData(token, {
      ...values,
      instrument_id: Number(values.instrument_id),
      frequency: values.frequency || '5m',
      source: values.source || 'csv',
    })
      .then(() => {
        const instrumentId = Number(values.instrument_id)
        return Promise.all([
          fetchMarketBars(token, instrumentId, values.frequency || '5m'),
          fetchDataImportTasks(token),
          fetchOperationLogs(token),
        ])
      })
      .then(([barPayload, importTaskPayload, logPayload]) => {
        setBars(barPayload)
        setDataImportTasks(importTaskPayload)
        setOperationLogs(logPayload)
      })
      .catch((error) => setMarketDataError(error instanceof Error ? error.message : 'CSV import failed'))
      .finally(() => setMarketDataImporting(false))
  }

  const renderStrategyParameterInput = (parameter: StrategyParameter) => {
    if (parameter.type === 'boolean') {
      return <Switch />
    }
    if (parameter.type === 'select') {
      return <Select options={parameter.options.map((option) => ({ label: option, value: option }))} />
    }
    return <InputNumber min={parameter.min_value ?? undefined} max={parameter.max_value ?? undefined} />
  }

  const handleCreateStrategyParameterSet = (values: Record<string, number | boolean | string>) => {
    if (!token || !strategies[0]) {
      return
    }

    const strategy = strategies[0]
    const parameters = Object.fromEntries(
      strategy.parameters.map((parameter) => [parameter.name, values[parameter.name] ?? parameter.default]),
    )

    setStrategyParameterSaving(true)
    setStrategyParameterError('')
    createStrategyParameterSet(token, {
      strategy_id: strategy.strategy_id,
      name: String(values.name || `${strategy.display_name} config`),
      parameters,
    })
      .then(() => Promise.all([fetchStrategyParameterSets(token), fetchOperationLogs(token)]))
      .then(([parameterSetPayload, logPayload]) => {
        setStrategyParameterSets(parameterSetPayload)
        setOperationLogs(logPayload)
      })
      .catch((error) => setStrategyParameterError(error instanceof Error ? error.message : 'Strategy config save failed'))
      .finally(() => setStrategyParameterSaving(false))
  }

  const loginPanel = (
    <main className="login-shell">
      <Card className="login-card">
        <Space orientation="vertical" size={18}>
          <div className="login-brand">
            <ApiOutlined />
            <div>
              <Title level={3}>Quant System Admin</Title>
              <Text type="secondary">Sign in to manage strategies, backtests, snapshots, and audit logs.</Text>
            </div>
          </div>
          {loginError ? <Alert type="error" showIcon message={loginError} /> : null}
          <Form
            layout="vertical"
            initialValues={{ username: 'admin', password: 'admin' }}
            onFinish={handleLogin}
          >
            <Form.Item label="Username" name="username" rules={[{ required: true }]}>
              <Input autoComplete="username" />
            </Form.Item>
            <Form.Item label="Password" name="password" rules={[{ required: true }]}>
              <Input.Password autoComplete="current-password" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loginLoading} block>
              Sign In
            </Button>
          </Form>
        </Space>
      </Card>
    </main>
  )

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#2563eb',
          borderRadius: 6,
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        },
      }}
    >
      {!currentUser ? (
        loginPanel
      ) : (
      <Layout className="admin-shell">
        <Sider width={232} className="admin-sider">
          <div className="brand">
            <ApiOutlined />
            <div>
              <strong>Quant System</strong>
              <span>Admin Console</span>
            </div>
          </div>
          <Menu mode="inline" defaultSelectedKeys={['backtests']} items={modules} />
        </Sider>
        <Layout>
          <Header className="admin-header">
            <div>
              <Title level={4}>Quant Strategy Admin</Title>
              <Text type="secondary">Research, backtest, simulate, publish, and audit rule-based strategies.</Text>
            </div>
            <Space>
              <Badge status={apiStatus === 'Connected' ? 'success' : 'processing'} text={`API ${apiStatus}`} />
              <Tag color="blue">Admin: {currentUser.username}</Tag>
              <Button type="primary" icon={<PlayCircleOutlined />}>
                New Backtest
              </Button>
              <Button onClick={handleLogout}>Sign Out</Button>
            </Space>
          </Header>
          <Content className="admin-content">
            <section className="metric-grid">
              <Card>
                <Space orientation="vertical" size={4}>
                  <Text type="secondary">Managed Instruments</Text>
                  <Title level={2}>{instruments.length}</Title>
                  <Text>{instruments[0] ? `${instruments[0].symbol}.${instruments[0].exchange}` : 'Create the first stock below'}</Text>
                </Space>
              </Card>
              <Card>
                <Space orientation="vertical" size={4}>
                  <Text type="secondary">Fixed Portfolios</Text>
                  <Title level={2}>{portfolios.length}</Title>
                  <Text>{portfolios[0]?.name ?? 'Create a basket after adding instruments'}</Text>
                </Space>
              </Card>
              <Card>
                <Space orientation="vertical" size={4}>
                  <Text type="secondary">Strategy Templates</Text>
                  <Title level={2}>{strategies.length}</Title>
                  <Text>
                    {strategyParameterSets.length
                      ? `${strategyParameterSets.length} saved parameter sets`
                      : strategies[0]?.display_name ?? 'Loading strategy registry'}
                  </Text>
                </Space>
              </Card>
              <Card>
                <Space orientation="vertical" size={4}>
                  <Text type="secondary">Published Snapshots</Text>
                  <Title level={2}>0</Title>
                  <Text>Immutable client reports</Text>
                </Space>
              </Card>
              <Card>
                <Space orientation="vertical" size={4}>
                  <Text type="secondary">Imported Bars</Text>
                  <Title level={2}>{bars.length}</Title>
                  <Text>{bars[0] ? `${bars[0].frequency} latest ${bars[bars.length - 1]?.close}` : 'Import CSV market data'}</Text>
                </Space>
              </Card>
              <Card>
                <Space orientation="vertical" size={4}>
                  <Text type="secondary">V1 Progress</Text>
                  <Progress percent={30} size="small" />
                  <Text>Admin, portfolios, and CSV data import connected</Text>
                </Space>
              </Card>
            </section>

            <section className="workspace">
              <Card title="Instrument Management">
                <Form
                  form={instrumentForm}
                  layout="inline"
                  initialValues={{ symbol: '600519', exchange: 'SH', name: 'Kweichow Moutai', asset_type: 'stock' }}
                  onFinish={handleCreateInstrument}
                  className="instrument-form"
                >
                  <Form.Item name="symbol" rules={[{ required: true }]}><Input placeholder="Symbol" /></Form.Item>
                  <Form.Item name="exchange" rules={[{ required: true }]}><Input placeholder="Exchange" /></Form.Item>
                  <Form.Item name="name" rules={[{ required: true }]}><Input placeholder="Name" /></Form.Item>
                  <Form.Item name="asset_type" rules={[{ required: true }]}><Input placeholder="Asset Type" /></Form.Item>
                  <Button type="primary" htmlType="submit" loading={instrumentSaving}>Add Instrument</Button>
                </Form>
                <Table
                  size="small"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    { title: 'Symbol', dataIndex: 'symbol', width: 110 },
                    { title: 'Exchange', dataIndex: 'exchange', width: 110 },
                    { title: 'Name', dataIndex: 'name' },
                    { title: 'Type', dataIndex: 'asset_type', width: 100 },
                  ]}
                  dataSource={instruments.map((instrument) => ({ ...instrument, key: instrument.id }))}
                />
              </Card>

              <Card title="Fixed Portfolio Management">
                <Form
                  form={portfolioForm}
                  layout="inline"
                  initialValues={{
                    name: 'Core A-share Basket',
                    description: 'Fixed demo portfolio for V1 backtests.',
                    instrument_id: instruments[0]?.id,
                    weight: 1,
                  }}
                  onFinish={handleCreatePortfolio}
                  className="instrument-form"
                >
                  <Form.Item name="name" rules={[{ required: true }]}><Input placeholder="Portfolio Name" /></Form.Item>
                  <Form.Item name="description"><Input placeholder="Description" /></Form.Item>
                  <Form.Item name="instrument_id" rules={[{ required: true }]}>
                    <Input placeholder="Instrument ID" />
                  </Form.Item>
                  <Form.Item name="weight" rules={[{ required: true }]}><Input placeholder="Weight" type="number" /></Form.Item>
                  <Button type="primary" htmlType="submit" loading={portfolioSaving} disabled={!instruments.length}>
                    Add Portfolio
                  </Button>
                </Form>
                <Table
                  size="small"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    { title: 'Portfolio', dataIndex: 'name' },
                    { title: 'Description', dataIndex: 'description' },
                    {
                      title: 'Positions',
                      dataIndex: 'positions',
                      width: 120,
                      render: (positions: Portfolio['positions']) => positions.length,
                    },
                    {
                      title: 'First Holding',
                      dataIndex: 'positions',
                      width: 160,
                      render: (positions: Portfolio['positions']) => {
                        const first = positions[0]?.instrument
                        return first ? `${first.symbol}.${first.exchange}` : '-'
                      },
                    },
                  ]}
                  dataSource={portfolios.map((portfolio) => ({ ...portfolio, key: portfolio.id }))}
                />
              </Card>

              <Card title="Market Data Management">
                {marketDataError ? <Alert type="error" showIcon message={marketDataError} className="form-alert" /> : null}
                <Form
                  form={marketDataForm}
                  layout="vertical"
                  initialValues={{
                    instrument_id: instruments[0]?.id,
                    frequency: '5m',
                    source: 'csv',
                    csv_text:
                      'timestamp,open,high,low,close,volume\n2026-01-02 09:35:00,10,10.5,9.8,10.2,1000\n2026-01-02 09:40:00,10.2,10.8,10.1,10.7,1200',
                  }}
                  onFinish={handleImportMarketData}
                >
                  <div className="market-data-grid">
                    <Form.Item name="instrument_id" label="Instrument ID" rules={[{ required: true }]}>
                      <Input placeholder="Instrument ID" />
                    </Form.Item>
                    <Form.Item name="frequency" label="Frequency" rules={[{ required: true }]}>
                      <Input placeholder="5m" />
                    </Form.Item>
                    <Form.Item name="source" label="Source" rules={[{ required: true }]}>
                      <Input placeholder="csv" />
                    </Form.Item>
                  </div>
                  <Form.Item name="csv_text" label="CSV Bars" rules={[{ required: true }]}>
                    <Input.TextArea rows={5} />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={marketDataImporting} disabled={!instruments.length}>
                    Import CSV Bars
                  </Button>
                </Form>
                <Table
                  size="small"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    {
                      title: 'Time',
                      dataIndex: 'timestamp',
                      width: 190,
                      render: (value: string) => new Date(value).toLocaleString(),
                    },
                    { title: 'Open', dataIndex: 'open', width: 90 },
                    { title: 'High', dataIndex: 'high', width: 90 },
                    { title: 'Low', dataIndex: 'low', width: 90 },
                    { title: 'Close', dataIndex: 'close', width: 90 },
                    { title: 'Volume', dataIndex: 'volume', width: 110 },
                  ]}
                  dataSource={bars.map((bar) => ({ ...bar, key: bar.id }))}
                />
              </Card>

              <Card title="Data Import Tasks">
                <Table
                  size="small"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    { title: 'Source', dataIndex: 'source', width: 90 },
                    {
                      title: 'Status',
                      dataIndex: 'status',
                      width: 110,
                      render: (status: string) => <Tag color={status === 'succeeded' ? 'green' : status === 'failed' ? 'red' : 'blue'}>{status}</Tag>,
                    },
                    { title: 'Imported', dataIndex: 'rows_imported', width: 100 },
                    { title: 'Updated', dataIndex: 'rows_updated', width: 100 },
                    { title: 'Message', dataIndex: 'message' },
                  ]}
                  dataSource={dataImportTasks.map((task) => ({ ...task, key: task.id }))}
                />
              </Card>

              <Card title="Strategy Template Management">
                {strategyParameterError ? <Alert type="error" showIcon message={strategyParameterError} className="form-alert" /> : null}
                {strategies[0] ? (
                  <>
                    <Space orientation="vertical" size={4} className="strategy-summary">
                      <Text strong>{strategies[0].display_name}</Text>
                      <Text type="secondary">{strategies[0].description}</Text>
                      <Space wrap>
                        {strategies[0].supported_frequencies.map((frequency) => (
                          <Tag color={frequency === '5m' ? 'blue' : 'default'} key={frequency}>
                            {frequency}
                          </Tag>
                        ))}
                      </Space>
                    </Space>
                    <Form
                      form={strategyParameterForm}
                      layout="vertical"
                      onFinish={handleCreateStrategyParameterSet}
                      className="strategy-parameter-form"
                    >
                      <Form.Item name="name" label="Parameter Set Name" rules={[{ required: true }]}>
                        <Input placeholder="Parameter set name" />
                      </Form.Item>
                      <div className="strategy-parameter-grid">
                        {strategies[0].parameters.map((parameter) => (
                          <Form.Item
                            key={parameter.name}
                            name={parameter.name}
                            label={parameter.label}
                            valuePropName={parameter.type === 'boolean' ? 'checked' : 'value'}
                            extra={parameter.description}
                          >
                            {renderStrategyParameterInput(parameter)}
                          </Form.Item>
                        ))}
                      </div>
                      <Button type="primary" htmlType="submit" loading={strategyParameterSaving}>
                        Save Strategy Config
                      </Button>
                    </Form>
                  </>
                ) : (
                  <Text type="secondary">Loading strategy metadata</Text>
                )}
                <Table
                  size="small"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    { title: 'Name', dataIndex: 'name' },
                    { title: 'Strategy', dataIndex: 'strategy_id', width: 150 },
                    {
                      title: 'Grid %',
                      dataIndex: 'parameters',
                      width: 100,
                      render: (parameters: StrategyParameterSet['parameters']) => parameters.grid_percent,
                    },
                    {
                      title: 'MA Filter',
                      dataIndex: 'parameters',
                      width: 110,
                      render: (parameters: StrategyParameterSet['parameters']) => (
                        <Tag color={parameters.enable_ma_filter ? 'green' : 'default'}>
                          {parameters.enable_ma_filter ? 'on' : 'off'}
                        </Tag>
                      ),
                    },
                  ]}
                  dataSource={strategyParameterSets.map((parameterSet) => ({ ...parameterSet, key: parameterSet.id }))}
                />
              </Card>

              <Card
                title={
                  <Space>
                    <LineChartOutlined />
                    V1 Main Workflow
                  </Space>
                }
              >
                <div className="pipeline">
                  {['Import Data', 'Set Strategy', 'Run Backtest', 'Review Result', 'Publish Snapshot', 'Client Report'].map(
                    (item) => (
                      <div className="pipeline-step" key={item}>
                        <SafetyCertificateOutlined />
                        <span>{item}</span>
                      </div>
                    ),
                  )}
                </div>
              </Card>

              <Card title="Recent Tasks">
                <Table
                  size="small"
                  pagination={false}
                  columns={[
                    { title: 'Task', dataIndex: 'name' },
                    { title: 'Type', dataIndex: 'type', width: 100 },
                    {
                      title: 'Status',
                      dataIndex: 'status',
                      width: 110,
                      render: (status: string) => {
                        const color = status === 'Succeeded' ? 'green' : status === 'Running' ? 'blue' : 'default'
                        return <Tag color={color}>{status}</Tag>
                      },
                    },
                    { title: 'Updated At', dataIndex: 'updatedAt', width: 180 },
                  ]}
                  dataSource={tasks}
                />
              </Card>

              <Card
                title={
                  <Space>
                    <AreaChartOutlined />
                    System Boundaries
                  </Space>
                }
              >
                <div className="boundary-list">
                  <Tag color="blue">No live trading in V1</Tag>
                  <Tag color="purple">No strategy logic in frontend</Tag>
                  <Tag color="cyan">Published snapshots are immutable</Tag>
                  <Tag color="geekblue">vn.py remains a lower-level reference</Tag>
                </div>
              </Card>

              <Card title="Operation Logs">
                <Table
                  size="small"
                  pagination={{ pageSize: 6 }}
                  columns={[
                    { title: 'Action', dataIndex: 'action' },
                    { title: 'Actor', dataIndex: 'actor', width: 110 },
                    { title: 'Target', dataIndex: 'target_type', width: 120 },
                    {
                      title: 'Created At',
                      dataIndex: 'created_at',
                      width: 210,
                      render: (value: string) => new Date(value).toLocaleString(),
                    },
                  ]}
                  dataSource={operationLogs.map((log) => ({ ...log, key: log.id }))}
                />
              </Card>
            </section>
          </Content>
        </Layout>
      </Layout>
      )}
    </ConfigProvider>
  )
}

export default App
