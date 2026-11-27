/**
 * agentRegistry.js
 * Centralized declarative Agent Registry and Category Configuration for SAI ANALYSIS.
 *
 * Canonical Module Architecture:
 * - Module 1: User Authentication and Research Workspace (Platform Capability)
 * - Module 2: Stock Search, Market Data Collection and Dataset Validation
 * - Module 3: Fundamental Analysis Agent
 * - Module 4: Technical Analysis Agent (Planned)
 * - Module 5: News and Sentiment Agent (Planned)
 * - Module 6: Risk Analysis Agent (Planned)
 * - Module 7: Supervisor Agent and Multi-Agent Orchestration (Planned)
 */

import DatasetValidationDashboard from '../components/dataset/DatasetValidationDashboard';
import FundamentalAnalysisView from '../components/research/FundamentalAnalysisView';

// ── 1. Canonical Agent Categories ───────────────────────────────────────────
export const AGENT_CATEGORIES = {
  DATA_INTELLIGENCE: {
    id: 'DATA_INTELLIGENCE',
    label: 'Data Intelligence',
    description: 'Market data collection, cleaning, normalization, and multi-tier data quality validation.',
    icon: 'Database',
    displayOrder: 1,
  },
  FINANCIAL_ANALYSIS: {
    id: 'FINANCIAL_ANALYSIS',
    label: 'Financial Analysis',
    description: 'Autonomous financial statement analysis, accounting equation validation, ratio calculation, and peer comparison.',
    icon: 'TrendingUp',
    displayOrder: 2,
  },
  MARKET_ANALYSIS: {
    id: 'MARKET_ANALYSIS',
    label: 'Market Analysis',
    description: 'Algorithmic technical indicators, momentum oscillators, moving averages, and chart pattern recognition.',
    icon: 'CandlestickChart',
    displayOrder: 3,
  },
  MARKET_INTELLIGENCE: {
    id: 'MARKET_INTELLIGENCE',
    label: 'Market Intelligence',
    description: 'Real-time financial news aggregation, press release extraction, and LLM-driven sentiment scoring.',
    icon: 'Newspaper',
    displayOrder: 4,
  },
  RISK_INTELLIGENCE: {
    id: 'RISK_INTELLIGENCE',
    label: 'Risk Intelligence',
    description: 'Quantitative portfolio risk modeling, Value at Risk (VaR), beta sensitivity, and macroeconomic stress testing.',
    icon: 'ShieldAlert',
    displayOrder: 5,
  },
  ORCHESTRATION: {
    id: 'ORCHESTRATION',
    label: 'Orchestration',
    description: 'Autonomous multi-agent execution routing, conflict resolution, and cross-domain insight synthesis.',
    icon: 'Cpu',
    displayOrder: 6,
  },
};

// ── 2. Platform Workspaces (Not AI Agents) ──────────────────────────────────
export const PLATFORM_WORKSPACES = {
  overview: {
    id: 'overview',
    name: 'Terminal Overview',
    description: 'Unified financial overview with active stock telemetry, KPI Bento cards, performance charts, and dual activity workspace.',
    icon: 'LayoutDashboard',
    displayOrder: 1,
  },
  watchlist: {
    id: 'watchlist',
    name: 'Saved Watchlist',
    description: 'PostgreSQL-persisted stock watchlist with single-click research execution and tracking.',
    icon: 'Bookmark',
    displayOrder: 2,
  },
  history: {
    id: 'history',
    name: 'Research Archive',
    description: 'Historical research tasks, background agent telemetry logs, and comprehensive report viewer.',
    icon: 'History',
    displayOrder: 3,
  },
};

// ── 3. Centralized AI Agent Registry ────────────────────────────────────────
export const AGENT_REGISTRY = [
  // ── DATA INTELLIGENCE (Module 2) ──
  {
    id: 'market-data-collector',
    categoryId: 'DATA_INTELLIGENCE',
    name: 'Market Data Collection Agent',
    shortName: 'Market Data',
    description: 'Extracts real-time and historical OHLCV market telemetry with exchange provider normalization and failover handling.',
    module: 'Module 2',
    status: 'planned', // Active telemetry powers Terminal Overview; standalone agent workspace planned
    icon: 'BarChart2',
    capabilities: [
      'Multi-Exchange OHLCV Ingestion (NSE, BSE, NASDAQ, NYSE)',
      'Intraday & Historical Data Retrieval',
      'Provider Failover & Rate Limit Optimization',
      'Chronological Order Verification',
    ],
    expectedInputs: ['ticker', 'market_exchange', 'timeframe_period'],
    expectedOutputs: ['ohlcv_candles', 'trading_volume', 'market_status', 'price_statistics'],
    component: null,
  },
  {
    id: 'dataset-validation-agent',
    categoryId: 'DATA_INTELLIGENCE',
    name: 'Dataset Validation Agent',
    shortName: 'Data Validation',
    description: 'Autonomous multi-tier financial data quality cleaning, statistical outlier detection, null filtering, and audit reporting.',
    module: 'Module 2',
    status: 'active',
    icon: 'Database',
    capabilities: [
      'Missing Record & Chronological Gap Detection',
      'Null, Empty & Infinite Value Elimination',
      'Statistical Outlier & Price Spike Filtering',
      'Data Quality Tier Scoring (High, Acceptable, Caveats, Low)',
      'Automated Cleaned Dataset CSV Export',
    ],
    expectedInputs: ['ticker', 'market_exchange', 'timeframe_period'],
    expectedOutputs: ['validation_report', 'cleaned_dataset', 'quality_score', 'anomaly_summary'],
    component: DatasetValidationDashboard,
  },

  // ── FINANCIAL ANALYSIS (Module 3) ──
  {
    id: 'fundamental-analysis-agent',
    categoryId: 'FINANCIAL_ANALYSIS',
    name: 'Fundamental Analysis Agent',
    shortName: 'Fundamental',
    description: 'Comprehensive 3-statement financial auditor, ratio calculation engine, multi-year historical comparison, and peer benchmarking.',
    module: 'Module 3',
    status: 'active',
    icon: 'TrendingUp',
    capabilities: [
      'Income Statement, Balance Sheet & Cash Flow Modeling',
      'Financial Ratio Calculation (P/E, Forward P/E, P/B, ROE, Margins)',
      '5-Year Historical Trend & CAGR Growth Analysis',
      'Peer Benchmarking & Median Comparison',
      'Deterministic Balance Sheet Accounting Equation Verification',
      'Cross-Currency Reporting vs Trading Variance Disclosure',
    ],
    expectedInputs: ['ticker', 'overview_data', 'financial_statements'],
    expectedOutputs: ['fundamental_analysis_report', 'valuation_ratios', 'peer_comparison', 'data_integrity_audit'],
    component: FundamentalAnalysisView,
  },

  // ── MARKET ANALYSIS (Module 4 - Planned) ──
  {
    id: 'technical-analysis-agent',
    categoryId: 'MARKET_ANALYSIS',
    name: 'Technical Analysis Agent',
    shortName: 'Technical',
    description: 'Algorithmic technical indicator computation, momentum oscillators, moving averages, and pattern recognition.',
    module: 'Module 4',
    status: 'planned',
    icon: 'CandlestickChart',
    capabilities: [
      'Simple & Exponential Moving Averages (20, 50, 200 SMA/EMA)',
      'Relative Strength Index (RSI 14) & MACD Momentum Profiling',
      'Bollinger Bands & Volatility Channel Calculation',
      'Dynamic Support, Resistance & Breakout Level Identification',
    ],
    expectedInputs: ['ticker', 'ohlcv_candles', 'timeframe_period'],
    expectedOutputs: ['technical_indicators', 'momentum_signals', 'support_resistance_levels'],
    component: null,
  },

  // ── MARKET INTELLIGENCE (Module 5 - Planned) ──
  {
    id: 'news-sentiment-agent',
    categoryId: 'MARKET_INTELLIGENCE',
    name: 'News and Sentiment Agent',
    shortName: 'News & Sentiment',
    description: 'Real-time financial news stream aggregation, press release extraction, and LLM-driven market sentiment analysis.',
    module: 'Module 5',
    status: 'planned',
    icon: 'Newspaper',
    capabilities: [
      'Multi-Source Financial News Aggregation',
      'Company Press Release & Regulatory Filing Scraping',
      'NLP-Driven Headline & Article Sentiment Scoring',
      'Key Catalysts, Rumors & Market Event Extraction',
    ],
    expectedInputs: ['ticker', 'company_name', 'news_lookback_days'],
    expectedOutputs: ['news_feed', 'sentiment_scores', 'catalyst_events', 'sentiment_trend'],
    component: null,
  },

  // ── RISK INTELLIGENCE (Module 6 - Planned) ──
  {
    id: 'risk-analysis-agent',
    categoryId: 'RISK_INTELLIGENCE',
    name: 'Risk Analysis Agent',
    shortName: 'Risk Analysis',
    description: 'Quantitative equity and portfolio risk assessment, downside volatility, Sharpe/Sortino ratios, and stress simulation.',
    module: 'Module 6',
    status: 'planned',
    icon: 'ShieldAlert',
    capabilities: [
      'Historical & Parametric Value at Risk (VaR 95% / 99%)',
      'Beta Sensitivity against Benchmark Index (Nifty 50 / S&P 500)',
      'Maximum Historical Drawdown & Downside Volatility Analysis',
      'Macroeconomic Shock & Interest Rate Stress Testing',
    ],
    expectedInputs: ['ticker', 'historical_returns', 'benchmark_returns'],
    expectedOutputs: ['var_metrics', 'beta_sensitivity', 'drawdown_profile', 'stress_test_matrix'],
    component: null,
  },

  // ── ORCHESTRATION (Module 7 - Planned) ──
  {
    id: 'supervisor-agent',
    categoryId: 'ORCHESTRATION',
    name: 'Supervisor Agent',
    shortName: 'Supervisor',
    description: 'Autonomous multi-agent coordinator that manages task routing, handles conflicting agent signals, and generates master research summaries.',
    module: 'Module 7',
    status: 'planned',
    icon: 'Cpu',
    capabilities: [
      'Autonomous Multi-Agent Task Routing & Dependency Resolution',
      'Cross-Domain Insight Synthesis & Conflict Arbitration',
      'Executive Investment Thesis & Research Summary Generation',
      'Multi-Agent System Telemetry & Pipeline Health Monitoring',
    ],
    expectedInputs: ['ticker', 'user_research_query', 'agent_outputs_bundle'],
    expectedOutputs: ['master_synthesis_report', 'agent_confidence_scores', 'consensus_signal'],
    component: null,
  },
];

// ── 4. Defensive Safe Lookup & Utility Functions ────────────────────────────

/**
 * Safely retrieve an agent by its unique identifier.
 * Returns null if not found or if agentId is invalid.
 */
export const getAgentById = (agentId) => {
  if (!agentId || typeof agentId !== 'string') return null;
  return AGENT_REGISTRY.find((agent) => agent.id === agentId) || null;
};

/**
 * Fallback category returned when an invalid or unknown categoryId is referenced.
 */
const DEFAULT_UNKNOWN_CATEGORY = Object.freeze({
  id: 'GENERAL',
  label: 'General Intelligence',
  description: 'Uncategorized or auxiliary AI analytical capabilities.',
  icon: 'Cpu',
  displayOrder: 999,
});

/**
 * Safely retrieve category metadata by its ID.
 * Returns a defensive fallback category if categoryId is invalid or unmapped.
 */
export const getCategoryById = (categoryId) => {
  if (!categoryId || typeof categoryId !== 'string') return DEFAULT_UNKNOWN_CATEGORY;
  return AGENT_CATEGORIES[categoryId] || {
    ...DEFAULT_UNKNOWN_CATEGORY,
    id: categoryId,
    label: categoryId.replace(/_/g, ' '),
  };
};

/**
 * Retrieve all agents belonging to a given category.
 * Returns an empty array if categoryId is invalid or has no registered agents.
 */
export const getAgentsByCategory = (categoryId) => {
  if (!categoryId || typeof categoryId !== 'string') return [];
  return AGENT_REGISTRY.filter((agent) => agent.categoryId === categoryId);
};

/**
 * Retrieve all categories sorted by displayOrder.
 */
export const getAllCategories = () => {
  return Object.values(AGENT_CATEGORIES).sort((a, b) => a.displayOrder - b.displayOrder);
};

/**
 * Retrieve all platform workspaces sorted by displayOrder.
 */
export const getAllPlatformWorkspaces = () => {
  return Object.values(PLATFORM_WORKSPACES).sort((a, b) => a.displayOrder - b.displayOrder);
};

/**
 * Safely retrieve a platform workspace definition by its ID.
 */
export const getWorkspaceById = (workspaceId) => {
  if (!workspaceId || typeof workspaceId !== 'string') return null;
  return PLATFORM_WORKSPACES[workspaceId] || null;
};

/**
 * Check whether a given identifier represents a platform workspace.
 */
export const isPlatformWorkspace = (id) => {
  if (!id || typeof id !== 'string') return false;
  return Object.prototype.hasOwnProperty.call(PLATFORM_WORKSPACES, id);
};

/**
 * Safely check whether an agent object or agent ID has an active, callable component.
 */
export const hasValidComponent = (agentOrId) => {
  const agent = typeof agentOrId === 'string' ? getAgentById(agentOrId) : agentOrId;
  return Boolean(agent && typeof agent.component === 'function');
};

/**
 * Safely retrieve the status ('active' or 'planned') for an agent.
 */
export const getAgentStatus = (agentOrId) => {
  const agent = typeof agentOrId === 'string' ? getAgentById(agentOrId) : agentOrId;
  if (!agent) return 'unknown';
  return agent.status === 'active' ? 'active' : 'planned';
};
