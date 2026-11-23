import { useEffect, useState, useMemo, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowUpRight,
  BookmarkPlus,
  BookmarkCheck,
  Building2,
  Calendar,
  Clock,
  ExternalLink,
  Globe,
  Info,
  LoaderCircle,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  MapPin,
  BarChart3,
  FileSpreadsheet,
  Layers,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  FileDown,
  X,
  Check,
  ShieldAlert,
  SlidersHorizontal,
  HelpCircle,
  Activity
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import api from '../services/api';

const PERIODS = ['1 Month', '3 Months', '6 Months', '1 Year', '5 Years', 'Max'];

const formatPrice = (val, currency = '') => {
  if (val == null || isNaN(val)) return '—';
  return `${currency ? `${currency} ` : ''}${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatVolume = (val) => {
  if (val == null || isNaN(val)) return '—';
  return Number(val).toLocaleString();
};

const formatFinancialValue = (val, currency = '') => {
  if (val == null || isNaN(val)) return 'N/A';
  const num = Number(val);
  const isNegative = num < 0;
  const abs = Math.abs(num);
  const prefix = currency ? `${currency} ` : '';

  if (currency === 'INR') {
    if (abs >= 1e7) {
      return `${isNegative ? '-' : ''}${prefix}${(abs / 1e7).toFixed(2)} Cr`;
    }
    if (abs >= 1e5) {
      return `${isNegative ? '-' : ''}${prefix}${(abs / 1e5).toFixed(2)} L`;
    }
  } else {
    if (abs >= 1e12) {
      return `${isNegative ? '-' : ''}${prefix}${(abs / 1e12).toFixed(2)}T`;
    }
    if (abs >= 1e9) {
      return `${isNegative ? '-' : ''}${prefix}${(abs / 1e9).toFixed(2)}B`;
    }
    if (abs >= 1e6) {
      return `${isNegative ? '-' : ''}${prefix}${(abs / 1e6).toFixed(2)}M`;
    }
  }
  return `${isNegative ? '-' : ''}${prefix}${abs.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
};

// Custom Chart Tooltip displaying all 5 OHLCV values + Company, Ticker, Exchange, Trading Date
function CustomOHLCVTooltip({ active, payload, companyName, ticker, exchange, currency }) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-ohlcv-tooltip">
      <div className="tooltip-top-row">
        <span className="tooltip-co-name">{companyName}</span>
        <span className="tooltip-badge">{ticker} · {exchange}</span>
      </div>
      <div className="tooltip-date-row">
        <span>Trading Date:</span>
        <strong>{d.formattedDate || d.date}</strong>
      </div>
      <div className="tooltip-metrics-grid">
        <div className="tooltip-cell">
          <span className="t-label">Open:</span>
          <span className="t-val">{formatPrice(d.open, currency)}</span>
        </div>
        <div className="tooltip-cell">
          <span className="t-label">High:</span>
          <span className="t-val text-green">{formatPrice(d.high, currency)}</span>
        </div>
        <div className="tooltip-cell">
          <span className="t-label">Low:</span>
          <span className="t-val text-red">{formatPrice(d.low, currency)}</span>
        </div>
        <div className="tooltip-cell primary-cell">
          <span className="t-label">Close:</span>
          <strong className="t-val">{formatPrice(d.close, currency)}</strong>
        </div>
        <div className="tooltip-cell volume-cell">
          <span className="t-label">Volume:</span>
          <span className="t-val">{formatVolume(d.volume)}</span>
        </div>
      </div>
    </div>
  );
}

export default function StockDetail() {
  const { market, ticker } = useParams();
  const navigate = useNavigate();

  // Selected states
  const [period, setPeriod] = useState('1 Year');
  const [financialTab, setFinancialTab] = useState('income_statement'); // 'income_statement' | 'balance_sheet' | 'cash_flow'
  const [financialFreq, setFinancialFreq] = useState('annual'); // 'annual' | 'quarterly'
  const [page, setPage] = useState(1);
  const rowsPerPage = 15;

  // Data states
  const [quote, setQuote] = useState(null);
  const [profile, setProfile] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [financials, setFinancials] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);

  // Loading states
  const [loadingQuote, setLoadingQuote] = useState(true);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingFinancials, setLoadingFinancials] = useState(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  // Error states
  const [errorQuote, setErrorQuote] = useState('');
  const [errorProfile, setErrorProfile] = useState('');
  const [errorHistory, setErrorHistory] = useState('');
  const [errorFinancials, setErrorFinancials] = useState('');
  const [errorAnalytics, setErrorAnalytics] = useState('');

  // Watchlist & Research states
  const [watchlistSaved, setWatchlistSaved] = useState(false);
  const [watchlistBusy, setWatchlistBusy] = useState(false);
  const [researchBusy, setResearchBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  // Report Generation Modal State
  const [showReportModal, setShowReportModal] = useState(false);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [pdfError, setPdfError] = useState('');
  const [reportTitle, setReportTitle] = useState('');
  const [reportFreq, setReportFreq] = useState('annual');
  const [reportSections, setReportSections] = useState({
    companyInfo: true,
    marketSnapshot: true,
    technicalAnalysis: true,
    historicalOHLCV: true,
    incomeStatement: true,
    balanceSheet: true,
    cashFlowStatement: true
  });

  // 1. Fetch Quote
  const fetchQuote = async () => {
    setLoadingQuote(true);
    setErrorQuote('');
    try {
      const { data } = await api.get('/stocks/quote', { params: { ticker, market } });
      setQuote(data);
    } catch (err) {
      setErrorQuote(err.response?.data?.detail || 'Unable to load stock quote.');
    } finally {
      setLoadingQuote(false);
    }
  };

  // 2. Fetch Profile
  const fetchProfile = async () => {
    setLoadingProfile(true);
    setErrorProfile('');
    try {
      const { data } = await api.get('/stocks/profile', { params: { ticker, market } });
      setProfile(data);
    } catch (err) {
      setErrorProfile(err.response?.data?.detail || 'Unable to load company profile.');
    } finally {
      setLoadingProfile(false);
    }
  };

  // 3. Fetch History
  const fetchHistory = async () => {
    setLoadingHistory(true);
    setErrorHistory('');
    setPage(1);
    try {
      const { data } = await api.get('/stocks/history', { params: { ticker, market, period } });
      setHistoryData(data);
    } catch (err) {
      setErrorHistory(err.response?.data?.detail || 'Unable to load historical price data.');
    } finally {
      setLoadingHistory(false);
    }
  };

  // 4. Fetch Financials
  const fetchFinancials = async () => {
    setLoadingFinancials(true);
    setErrorFinancials('');
    try {
      const { data } = await api.get('/stocks/financials', { params: { ticker, market } });
      setFinancials(data);
    } catch (err) {
      setErrorFinancials(err.response?.data?.detail || 'Unable to load financial statements.');
    } finally {
      setLoadingFinancials(false);
    }
  };

  // 5. Fetch Analytics (Bullish / Bearish / Neutral)
  const fetchAnalytics = async () => {
    setLoadingAnalytics(true);
    setErrorAnalytics('');
    try {
      const { data } = await api.get('/stocks/analytics', { params: { ticker, market, period } });
      setAnalyticsData(data);
    } catch (err) {
      setErrorAnalytics(err.response?.data?.detail || 'Unable to compute market analytics.');
    } finally {
      setLoadingAnalytics(false);
    }
  };

  // Check Watchlist status
  useEffect(() => {
    api.get('/watchlist').then(({ data }) => {
      const found = (data || []).some((item) => item.ticker === ticker && item.market === market);
      setWatchlistSaved(found);
    }).catch(() => {});
  }, [ticker, market]);

  // Initial load
  useEffect(() => {
    fetchQuote();
    fetchProfile();
    fetchFinancials();
  }, [ticker, market]);

  // Period change triggers history and analytics reload
  useEffect(() => {
    fetchHistory();
    fetchAnalytics();
  }, [ticker, market, period]);

  // Sync default report title
  useEffect(() => {
    const coName = profile?.company_name || quote?.ticker || ticker;
    setReportTitle(`EquityLens Stock Research Report: ${coName} (${ticker})`);
  }, [profile, quote, ticker]);

  // Watchlist action
  const toggleWatchlist = async () => {
    if (watchlistSaved) {
      setActionMessage('This stock is already saved in your watchlist.');
      return;
    }
    setWatchlistBusy(true);
    setActionMessage('');
    try {
      await api.post('/watchlist', {
        company_name: profile?.company_name || quote?.ticker || ticker,
        ticker,
        market,
        provider_symbol: quote?.provider_symbol || profile?.provider_symbol
      });
      setWatchlistSaved(true);
      setActionMessage(`${ticker} added to your watchlist.`);
    } catch (err) {
      setActionMessage(err.response?.data?.detail || 'Could not save to watchlist.');
    } finally {
      setWatchlistBusy(false);
    }
  };

  // Start research action
  const startResearch = async () => {
    setResearchBusy(true);
    setActionMessage('');
    try {
      const { data } = await api.post('/research/start', {
        company_name: profile?.company_name || ticker,
        ticker,
        market,
        analysis_period: period
      });
      navigate('/history', { state: { created: data.id } });
    } catch (err) {
      setActionMessage(err.response?.data?.detail || 'Could not create research task.');
      setResearchBusy(false);
    }
  };

  // Pagination calculations for OHLCV
  const historyRows = historyData?.history || [];
  const totalPages = Math.max(1, Math.ceil(historyRows.length / rowsPerPage));
  const paginatedRows = useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    return historyRows.slice(start, start + rowsPerPage);
  }, [historyRows, page]);

  // Chart data (sorted ascending for chronology, validated numeric values)
  const chartData = useMemo(() => {
    if (!historyRows || !historyRows.length) return [];
    return [...historyRows]
      .reverse()
      .filter((item) => item && item.date && item.close != null && !isNaN(item.close) && Number(item.close) > 0)
      .map((item) => ({
        date: item.date,
        formattedDate: item.formatted_date || item.date,
        close: Number(item.close),
        open: item.open != null && !isNaN(item.open) ? Number(item.open) : Number(item.close),
        high: item.high != null && !isNaN(item.high) ? Number(item.high) : Number(item.close),
        low: item.low != null && !isNaN(item.low) ? Number(item.low) : Number(item.close),
        volume: item.volume != null && !isNaN(item.volume) ? Number(item.volume) : 0
      }));
  }, [historyRows]);

  // Current financial statement data
  const currentStatements = financials?.[financialFreq];
  const activeStatementData = currentStatements?.[financialTab] || { periods: [], metrics: [] };
  const currency = quote?.currency || profile?.currency || historyData?.currency || financials?.currency || '';
  const companyName = profile?.company_name || quote?.ticker || ticker;

  // Generate Professional PDF Report
  const handleGeneratePdf = () => {
    setPdfGenerating(true);
    setPdfError('');

    try {
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 14;
      let currentY = 18;

      // Header Banner
      doc.setFillColor(15, 25, 42); // #0f192a Dark Slate
      doc.rect(0, 0, pageWidth, 28, 'F');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.setTextColor(255, 255, 255);
      doc.text(reportTitle || `Stock Research Report: ${companyName} (${ticker})`, margin, 12);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(165, 180, 205);
      const generatedDateStr = new Date().toUTCString();
      doc.text(`Generated: ${generatedDateStr} | Exchange: ${market} | Provider: Yahoo Finance`, margin, 20);

      currentY = 36;

      // Section A: Company Information
      if (reportSections.companyInfo) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(30, 41, 59);
        doc.text('1. Company Information', margin, currentY);
        currentY += 4;

        const infoRows = [
          ['Company Name', companyName, 'Ticker / Symbol', `${ticker} (${quote?.provider_symbol || ticker})`],
          ['Exchange', profile?.exchange || market, 'Reporting Currency', currency || 'N/A'],
          ['Sector', profile?.sector || 'Not available', 'Industry', profile?.industry || 'Not available'],
          ['Market Cap', profile?.market_cap ? formatFinancialValue(profile.market_cap, currency) : 'Not available', 'Employees', profile?.full_time_employees ? Number(profile.full_time_employees).toLocaleString() : 'Not available'],
          ['Location', profile?.city && profile?.country ? `${profile.city}, ${profile.country}` : profile?.country || 'Not available', 'Official Website', profile?.website || 'Not available']
        ];

        autoTable(doc, {
          startY: currentY,
          head: [],
          body: infoRows,
          theme: 'grid',
          styles: { fontSize: 8, cellPadding: 2, textColor: [30, 41, 59] },
          columnStyles: {
            0: { fontStyle: 'bold', fillColor: [241, 245, 249], width: 38 },
            1: { width: 52 },
            2: { fontStyle: 'bold', fillColor: [241, 245, 249], width: 38 },
            3: { width: 54 }
          },
          margin: { left: margin, right: margin }
        });

        currentY = doc.lastAutoTable.finalY + 4;

        if (profile?.description) {
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(9);
          doc.setTextColor(51, 65, 85);
          doc.text('Business Summary:', margin, currentY);
          currentY += 4;

          doc.setFont('helvetica', 'normal');
          doc.setFontSize(8);
          doc.setTextColor(71, 85, 105);
          const splitDesc = doc.splitTextToSize(profile.description, pageWidth - margin * 2);
          // Show first 4 lines in summary to conserve space
          const snippet = splitDesc.slice(0, 6);
          doc.text(snippet, margin, currentY);
          currentY += snippet.length * 3.8 + 5;
        }
      }

      // Section B: Market Information
      if (reportSections.marketSnapshot && quote) {
        if (currentY > pageHeight - 40) { doc.addPage(); currentY = 18; }

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(30, 41, 59);
        doc.text('2. Market Information & Latest Quote', margin, currentY);
        currentY += 4;

        const quoteRows = [
          [
            'Current Price',
            formatPrice(quote.price, currency),
            'Price Change (%)',
            quote.change_percent != null ? `${quote.change_percent >= 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%` : '—'
          ],
          [
            'Previous Close',
            formatPrice(quote.previous_close, currency),
            'Market Data As Of',
            quote.as_of || historyData?.latest_trading_date || 'Latest available'
          ]
        ];

        autoTable(doc, {
          startY: currentY,
          head: [],
          body: quoteRows,
          theme: 'grid',
          styles: { fontSize: 8.5, cellPadding: 2.5, textColor: [30, 41, 59] },
          columnStyles: {
            0: { fontStyle: 'bold', fillColor: [241, 245, 249], width: 38 },
            1: { width: 52 },
            2: { fontStyle: 'bold', fillColor: [241, 245, 249], width: 38 },
            3: { width: 54 }
          },
          margin: { left: margin, right: margin }
        });

        currentY = doc.lastAutoTable.finalY + 7;
      }

      // Section E: Stock Analysis (Bullish / Bearish / Neutral)
      if (reportSections.technicalAnalysis && analyticsData) {
        if (currentY > pageHeight - 50) { doc.addPage(); currentY = 18; }

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(30, 41, 59);
        doc.text('3. Technical Market Analysis', margin, currentY);
        currentY += 5;

        // Sentiment badge bar
        const sent = analyticsData.sentiment || 'Neutral';
        let badgeColor = [245, 176, 65]; // Amber
        if (sent === 'Bullish') badgeColor = [39, 174, 96]; // Green
        if (sent === 'Bearish') badgeColor = [231, 76, 60]; // Red

        doc.setFillColor(...badgeColor);
        doc.roundedRect(margin, currentY, 35, 7, 1.5, 1.5, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(255, 255, 255);
        doc.text(sent.toUpperCase(), margin + 6, currentY + 4.8);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor(71, 85, 105);
        doc.text(`Confidence Rating: ${analyticsData.confidence || 50}% | Historical Horizon: ${period}`, margin + 40, currentY + 4.8);
        currentY += 10;

        // Analytics metrics table
        const analyticsMetrics = [
          ['RSI (14-Day)', analyticsData.rsi_14 != null ? Number(analyticsData.rsi_14).toFixed(1) : 'N/A', 'MACD', analyticsData.macd != null ? Number(analyticsData.macd).toFixed(2) : 'N/A'],
          ['50-Day Moving Average', formatPrice(analyticsData.sma_50, currency), 'MACD Signal Line', analyticsData.macd_signal != null ? Number(analyticsData.macd_signal).toFixed(2) : 'N/A'],
          ['200-Day Moving Average', formatPrice(analyticsData.sma_200, currency), 'Max Period Drawdown', analyticsData.maximum_drawdown != null ? `${Number(analyticsData.maximum_drawdown).toFixed(2)}%` : 'N/A'],
          ['Period High', formatPrice(analyticsData.period_high, currency), 'Period Low', formatPrice(analyticsData.period_low, currency)]
        ];

        autoTable(doc, {
          startY: currentY,
          head: [],
          body: analyticsMetrics,
          theme: 'grid',
          styles: { fontSize: 8, cellPadding: 2, textColor: [30, 41, 59] },
          columnStyles: {
            0: { fontStyle: 'bold', fillColor: [248, 250, 252], width: 44 },
            1: { width: 46 },
            2: { fontStyle: 'bold', fillColor: [248, 250, 252], width: 44 },
            3: { width: 48 }
          },
          margin: { left: margin, right: margin }
        });

        currentY = doc.lastAutoTable.finalY + 4;

        if (analyticsData.explanation) {
          doc.setFont('helvetica', 'italic');
          doc.setFontSize(8);
          doc.setTextColor(71, 85, 105);
          const splitExpl = doc.splitTextToSize(analyticsData.explanation, pageWidth - margin * 2);
          doc.text(splitExpl, margin, currentY);
          currentY += splitExpl.length * 3.5 + 5;
        }
      }

      // Section C: Historical OHLCV Table Summary
      if (reportSections.historicalOHLCV && historyRows.length > 0) {
        if (currentY > pageHeight - 50) { doc.addPage(); currentY = 18; }

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(30, 41, 59);
        doc.text(`4. Historical OHLCV Trading Records (${period})`, margin, currentY);
        currentY += 4;

        // Top 12 recent sessions for the PDF table
        const ohlcvSample = historyRows.slice(0, 15).map((row) => [
          row.formatted_date || row.date,
          formatPrice(row.open, currency),
          formatPrice(row.high, currency),
          formatPrice(row.low, currency),
          formatPrice(row.close, currency),
          formatVolume(row.volume)
        ]);

        autoTable(doc, {
          startY: currentY,
          head: [['Date', 'Open', 'High', 'Low', 'Close', 'Volume']],
          body: ohlcvSample,
          theme: 'striped',
          headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
          styles: { fontSize: 7.5, cellPadding: 1.8, halign: 'right' },
          columnStyles: { 0: { halign: 'left', fontStyle: 'bold' } },
          margin: { left: margin, right: margin }
        });

        currentY = doc.lastAutoTable.finalY + 7;
      }

      // Section D: Financial Statements
      const selectedFinancials = financials?.[reportFreq] || {};
      const printStatement = (title, stmtKey, sectionNum) => {
        const stmt = selectedFinancials[stmtKey];
        if (!stmt || !stmt.periods?.length || !stmt.metrics?.length) return;

        if (currentY > pageHeight - 50) { doc.addPage(); currentY = 18; }

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(30, 41, 59);
        doc.text(`${sectionNum}. ${title} (${reportFreq === 'annual' ? 'Annual' : 'Quarterly'})`, margin, currentY);
        currentY += 4;

        const tableHead = ['Metric', ...stmt.periods];
        const tableBody = stmt.metrics.slice(0, 16).map((m) => {
          return [
            m.name,
            ...stmt.periods.map((p) => {
              const val = m.values?.[p];
              return val != null ? formatFinancialValue(val, currency) : 'N/A';
            })
          ];
        });

        autoTable(doc, {
          startY: currentY,
          head: [tableHead],
          body: tableBody,
          theme: 'striped',
          headStyles: { fillColor: [51, 65, 85], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 7.5 },
          styles: { fontSize: 7, cellPadding: 1.8, halign: 'right' },
          columnStyles: { 0: { halign: 'left', fontStyle: 'bold', width: 55 } },
          margin: { left: margin, right: margin },
          showHead: 'everyPage' // Repeat headers on subsequent pages
        });

        currentY = doc.lastAutoTable.finalY + 7;
      };

      let secCounter = 5;
      if (reportSections.incomeStatement) {
        printStatement('Income Statement', 'income_statement', secCounter++);
      }
      if (reportSections.balanceSheet) {
        printStatement('Balance Sheet', 'balance_sheet', secCounter++);
      }
      if (reportSections.cashFlowStatement) {
        printStatement('Cash Flow Statement', 'cash_flow', secCounter++);
      }

      // Add Page Numbers and Legal Disclaimers in Footer on Every Page
      const totalDocPages = doc.internal.getNumberOfPages();
      for (let i = 1; i <= totalDocPages; i++) {
        doc.setPage(i);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(140, 155, 175);
        doc.setDrawColor(226, 232, 240);
        doc.line(margin, pageHeight - 12, pageWidth - margin, pageHeight - 12);

        doc.text(
          'Informational research report generated by EquityLens. Data sourced via Yahoo Finance. Not financial or investment advice.',
          margin,
          pageHeight - 7
        );
        doc.text(`Page ${i} of ${totalDocPages}`, pageWidth - margin - 18, pageHeight - 7);
      }

      // Download file
      const safeTicker = ticker.replace(/[^A-Za-z0-9]/g, '_');
      const safeDate = new Date().toISOString().split('T')[0];
      doc.save(`${safeTicker}_Stock_Research_Report_${safeDate}.pdf`);

      setShowReportModal(false);
    } catch (err) {
      console.error('PDF Generation Error:', err);
      setPdfError('Failed to generate PDF. Please ensure your browser allows downloads and try again.');
    } finally {
      setPdfGenerating(false);
    }
  };

  return (
    <div className="stock-detail-page">
      {/* Top Navigation */}
      <div className="stock-nav-bar">
        <div className="nav-left-cluster">
          <Link to="/search" className="subtle-btn">
            <ArrowLeft size={15} /> Back to Search
          </Link>
          <div className="nav-market-badge">
            Market: <strong>{market}</strong>
          </div>
        </div>

        <div className="nav-right-cluster">
          <button
            className="primary-btn compact"
            onClick={() => setShowReportModal(true)}
            title="Configure and generate downloadable PDF report"
          >
            <FileDown size={15} /> Generate Report
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className={`alert ${actionMessage.includes('added') ? 'success' : 'info'}`}>
          {actionMessage}
        </div>
      )}

      {/* 1. Stock Overview / Header */}
      <section className="surface-card stock-hero-card">
        <div className="hero-top">
          <div className="hero-identity">
            <div className="ticker-avatar large hero-avatar">
              {ticker.slice(0, 2)}
            </div>
            <div>
              <div className="hero-meta-row">
                <span className="market-tag">{market}</span>
                {profile?.exchange && (
                  <span className="exchange-pill">Exchange: {profile.exchange}</span>
                )}
                {currency && <span className="currency-pill">{currency}</span>}
              </div>
              <h1 className="hero-company-name">
                {companyName}
              </h1>
              <div className="hero-ticker-sub">
                <strong>{ticker}</strong>
                {quote?.provider_symbol && (
                  <span>Yahoo Ticker: <code>{quote.provider_symbol}</code></span>
                )}
              </div>
            </div>
          </div>

          <div className="hero-pricing">
            {loadingQuote ? (
              <div className="pricing-loading">
                <LoaderCircle className="spin" size={20} /> Loading quote…
              </div>
            ) : errorQuote ? (
              <div className="pricing-error">
                <AlertCircle size={16} /> {errorQuote}
              </div>
            ) : (
              <>
                <div className="hero-price">
                  {formatPrice(quote?.price, currency)}
                </div>
                <div className={`hero-change ${quote?.change_percent >= 0 ? 'positive' : 'negative'}`}>
                  {quote?.change_percent >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  <span>
                    {quote?.change_percent != null
                      ? `${quote.change_percent >= 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%`
                      : '—'}
                  </span>
                  {quote?.previous_close && (
                    <small className="prev-close">Prev: {formatPrice(quote.previous_close, currency)}</small>
                  )}
                </div>
              </>
            )}

            <div className="hero-actions">
              <button
                className="subtle-btn"
                onClick={toggleWatchlist}
                disabled={watchlistBusy || watchlistSaved}
              >
                {watchlistBusy ? (
                  <LoaderCircle className="spin" size={15} />
                ) : watchlistSaved ? (
                  <BookmarkCheck size={15} className="text-green" />
                ) : (
                  <BookmarkPlus size={15} />
                )}
                {watchlistSaved ? 'Saved in Watchlist' : 'Add to Watchlist'}
              </button>

              <button
                className="primary-btn compact"
                onClick={startResearch}
                disabled={researchBusy}
              >
                {researchBusy ? <LoaderCircle className="spin" size={15} /> : <ArrowUpRight size={15} />}
                Start Research
              </button>
            </div>
          </div>
        </div>

        {/* Retrieval Metadata Section */}
        <div className="data-source-strip">
          <div className="source-item">
            <Info size={14} />
            <span>Source: <strong>Yahoo Finance</strong></span>
          </div>
          <div className="source-item">
            <Clock size={14} />
            <span>
              Last retrieved:{' '}
              <strong>
                {quote?.retrieval_timestamp
                  ? new Date(quote.retrieval_timestamp).toUTCString()
                  : new Date().toUTCString()}
              </strong>
            </span>
          </div>
          <div className="source-item">
            <Calendar size={14} />
            <span>
              Market data as of:{' '}
              <strong>
                {quote?.as_of || historyData?.latest_trading_date || 'Latest available trading day'}
              </strong>
            </span>
          </div>
          <div className="source-disclaimer">
            Coverage and availability provided via Yahoo Finance. Not official real-time exchange feed data.
          </div>
        </div>
      </section>

      {/* 2. Technical Analysis & Market Sentiment Indicator */}
      <section className="surface-card section-card sentiment-card">
        <div className="section-header">
          <div>
            <div className="eyebrow">ANALYSIS & SENTIMENT</div>
            <h2>Technical Analysis Indicator</h2>
            <p>Computed directly from historical price momentum, moving averages, and technical indicators.</p>
          </div>
        </div>

        {loadingAnalytics ? (
          <div className="empty-state">
            <LoaderCircle className="spin" size={24} />
            <p>Analyzing technical market indicators…</p>
          </div>
        ) : errorAnalytics ? (
          <div className="alert info">
            <AlertCircle size={16} /> {errorAnalytics}
          </div>
        ) : (
          <div className="sentiment-body">
            <div className="sentiment-top-banner">
              <div className="sentiment-badge-wrap">
                <span className={`sentiment-status-pill ${analyticsData?.sentiment?.toLowerCase() || 'neutral'}`}>
                  {analyticsData?.sentiment === 'Bullish' && <TrendingUp size={16} />}
                  {analyticsData?.sentiment === 'Bearish' && <TrendingDown size={16} />}
                  {analyticsData?.sentiment === 'Neutral' && <Activity size={16} />}
                  <strong>{analyticsData?.sentiment || 'Neutral'}</strong>
                </span>

                <div className="confidence-meter-wrap">
                  <span className="meter-label">Signal Confidence: <strong>{analyticsData?.confidence || 50}%</strong></span>
                  <div className="meter-track">
                    <div
                      className={`meter-fill ${analyticsData?.sentiment?.toLowerCase() || 'neutral'}`}
                      style={{ width: `${analyticsData?.confidence || 50}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="analysis-timestamp-badge">
                <Clock size={13} />
                <span>As of: {analyticsData?.as_of || 'Latest session'}</span>
              </div>
            </div>

            {/* Explanation */}
            <div className="sentiment-explanation-box">
              <p>
                <strong>Technical summary:</strong> {analyticsData?.explanation || 'Mixed indicators reflecting market consolidation.'}
              </p>
            </div>

            {/* Supporting Indicator Grid */}
            <div className="analytics-indicators-grid">
              <div className="indicator-pill">
                <span className="ind-name">RSI (14-Day)</span>
                <strong className="ind-val">{analyticsData?.rsi_14 != null ? Number(analyticsData.rsi_14).toFixed(1) : 'N/A'}</strong>
              </div>
              <div className="indicator-pill">
                <span className="ind-name">50-Day SMA</span>
                <strong className="ind-val">{formatPrice(analyticsData?.sma_50, currency)}</strong>
              </div>
              <div className="indicator-pill">
                <span className="ind-name">200-Day SMA</span>
                <strong className="ind-val">{formatPrice(analyticsData?.sma_200, currency)}</strong>
              </div>
              <div className="indicator-pill">
                <span className="ind-name">MACD</span>
                <strong className="ind-val">{analyticsData?.macd != null ? Number(analyticsData.macd).toFixed(2) : 'N/A'}</strong>
              </div>
              <div className="indicator-pill">
                <span className="ind-name">Max Drawdown</span>
                <strong className="ind-val text-red">{analyticsData?.maximum_drawdown != null ? `${Number(analyticsData.maximum_drawdown).toFixed(2)}%` : 'N/A'}</strong>
              </div>
              <div className="indicator-pill">
                <span className="ind-name">Volatility (Ann.)</span>
                <strong className="ind-val">{analyticsData?.annualized_volatility != null ? `${Number(analyticsData.annualized_volatility).toFixed(2)}%` : 'N/A'}</strong>
              </div>
            </div>

            <div className="sentiment-disclaimer">
              <ShieldAlert size={13} />
              <span>{analyticsData?.disclaimer || 'Technical indicators are computed algorithmically from price metrics and do not constitute investment advice.'}</span>
            </div>
          </div>
        )}
      </section>

      {/* 3. Historical Stock Data & OHLCV Table */}
      <section className="surface-card section-card">
        <div className="section-header">
          <div>
            <div className="eyebrow">MARKET ACTIVITY</div>
            <h2>Historical Stock Price Data</h2>
            <p>
              Review open, high, low, close and volume records.
              {historyData?.latest_trading_date && (
                <span className="latest-date-tag">
                  Latest trading date: <strong>{historyData.latest_trading_date}</strong>
                </span>
              )}
            </p>
          </div>

          {/* Period Selector */}
          <div className="period-pills-wrap" role="group" aria-label="Historical period selector">
            {PERIODS.map((p) => (
              <button
                key={p}
                className={`period-pill ${period === p ? 'active' : ''}`}
                onClick={() => setPeriod(p)}
                disabled={loadingHistory && period === p}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* BSE Limitation Banner when applicable */}
        {historyData?.provider_note && (
          <div className="alert info bse-limitation-banner">
            <Info size={15} />
            <span>{historyData.provider_note}</span>
          </div>
        )}

        {/* Historical Price Chart with 5-Value OHLCV Tooltip */}
        <div className="chart-wrapper">
          {loadingHistory ? (
            <div className="chart-empty-state">
              <LoaderCircle className="spin" size={28} />
              <p>Loading {period} price history…</p>
            </div>
          ) : errorHistory ? (
            <div className="alert error">
              <AlertCircle size={16} /> {errorHistory}
              <button className="subtle-btn compact inline-retry" onClick={fetchHistory}>
                <RefreshCw size={13} /> Retry
              </button>
            </div>
          ) : chartData.length > 0 ? (
            <div className="recharts-container" style={{ width: '100%', height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8d7bff" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#8d7bff" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2d42" />
                  <XAxis
                    dataKey="formattedDate"
                    stroke="#6b7c96"
                    fontSize={11}
                    tickLine={false}
                    interval="preserveStartEnd"
                    minTickGap={35}
                  />
                  <YAxis
                    stroke="#6b7c96"
                    fontSize={11}
                    tickLine={false}
                    domain={['auto', 'auto']}
                    tickFormatter={(val) => Number(val).toFixed(1)}
                  />
                  {/* Rich 5-Value Custom Tooltip */}
                  <Tooltip
                    content={
                      <CustomOHLCVTooltip
                        companyName={companyName}
                        ticker={ticker}
                        exchange={market}
                        currency={currency}
                      />
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="close"
                    stroke="#8d7bff"
                    strokeWidth={2}
                    dot={chartData.length <= 5 ? { r: 4, fill: '#8d7bff' } : false}
                    activeDot={{ r: 6, stroke: '#8d7bff', strokeWidth: 2, fill: '#fff' }}
                    fillOpacity={1}
                    fill="url(#priceGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="chart-empty-state">
              <BarChart3 size={32} />
              <p>No historical data is currently available for this period from Yahoo Finance.</p>
            </div>
          )}
        </div>

        {/* OHLCV Table */}
        <div className="table-header-row">
          <h3>OHLCV Trading Records</h3>
          <span className="table-subtitle">
            Showing {historyRows.length} trading sessions ({period})
          </span>
        </div>

        {loadingHistory ? (
          <div className="empty-state">
            <LoaderCircle className="spin" size={24} />
            <p>Loading OHLCV table data…</p>
          </div>
        ) : errorHistory ? (
          <div className="alert info">{errorHistory}</div>
        ) : historyRows.length === 0 ? (
          <div className="empty-state">
            <p>No historical data is currently available for this period from Yahoo Finance.</p>
          </div>
        ) : (
          <>
            <div className="table-scroll">
              <table className="ohlcv-table">
                <thead>
                  <tr>
                    <th>TRADING DATE</th>
                    <th className="num-col">OPEN</th>
                    <th className="num-col">HIGH</th>
                    <th className="num-col">LOW</th>
                    <th className="num-col">CLOSE</th>
                    <th className="num-col">VOLUME</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedRows.map((row, idx) => (
                    <tr key={`${row.date}-${idx}`}>
                      <td>
                        <strong>{row.formatted_date || row.date}</strong>
                      </td>
                      <td className="num-col">{formatPrice(row.open, currency)}</td>
                      <td className="num-col text-green">{formatPrice(row.high, currency)}</td>
                      <td className="num-col text-red">{formatPrice(row.low, currency)}</td>
                      <td className="num-col font-bold">
                        {formatPrice(row.close, currency)}
                      </td>
                      <td className="num-col">{formatVolume(row.volume)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="pagination-bar">
              <div className="pagination-info">
                Showing{' '}
                <strong>
                  {Math.min(1 + (page - 1) * rowsPerPage, historyRows.length)} -{' '}
                  {Math.min(page * rowsPerPage, historyRows.length)}
                </strong>{' '}
                of <strong>{historyRows.length}</strong> records
              </div>

              <div className="pagination-actions">
                <button
                  className="subtle-btn compact"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  title="Previous Page"
                >
                  <ChevronLeft size={16} /> Prev
                </button>
                <span className="page-indicator">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="subtle-btn compact"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  title="Next Page"
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {/* 4. Company Profile and Overview */}
      <section className="surface-card section-card">
        <div className="section-header">
          <div>
            <div className="eyebrow">COMPANY PROFILE</div>
            <h2>Company Overview</h2>
            <p>Business background, sector classification, and leadership details.</p>
          </div>
        </div>

        {loadingProfile ? (
          <div className="empty-state">
            <LoaderCircle className="spin" size={24} />
            <p>Loading company overview…</p>
          </div>
        ) : errorProfile ? (
          <div className="alert info">
            {errorProfile}
            <button className="subtle-btn compact inline-retry" onClick={fetchProfile}>
              <RefreshCw size={13} /> Retry
            </button>
          </div>
        ) : (
          <div className="company-overview-body">
            {/* Description Block */}
            <div className="overview-description-block">
              <h3>About {companyName}</h3>
              <p className="overview-text">
                {profile?.description || 'Not available'}
              </p>
            </div>

            {/* Profile Metrics Grid */}
            <div className="profile-metrics-grid">
              <div className="profile-metric-cell">
                <span className="cell-label">Sector</span>
                <b className="cell-val">{profile?.sector || 'Not available'}</b>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Industry</span>
                <b className="cell-val">{profile?.industry || 'Not available'}</b>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Market Capitalization</span>
                <b className="cell-val font-accent">
                  {profile?.market_cap ? formatFinancialValue(profile.market_cap, currency) : 'Not available'}
                </b>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Full-time Employees</span>
                <b className="cell-val">
                  {profile?.full_time_employees
                    ? Number(profile.full_time_employees).toLocaleString()
                    : 'Not available'}
                </b>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Headquarters / Location</span>
                <b className="cell-val">
                  {profile?.city && profile?.country
                    ? `${profile.city}, ${profile.country}`
                    : profile?.country || profile?.city || 'Not available'}
                </b>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Official Website</span>
                <div className="cell-val">
                  {profile?.website ? (
                    <a
                      href={profile.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="external-site-link"
                    >
                      <Globe size={14} />
                      <span>{profile.website}</span>
                      <ExternalLink size={13} />
                    </a>
                  ) : (
                    <span>Not available</span>
                  )}
                </div>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Listing Exchange</span>
                <b className="cell-val">{profile?.exchange || market}</b>
              </div>

              <div className="profile-metric-cell">
                <span className="cell-label">Reporting Currency</span>
                <b className="cell-val">{profile?.currency || currency || 'Not available'}</b>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* 5. Financial Statements */}
      <section className="surface-card section-card">
        <div className="section-header">
          <div>
            <div className="eyebrow">FUNDAMENTALS</div>
            <h2>Financial Statements</h2>
            <p>Annual and quarterly reports sourced via Yahoo Finance.</p>
          </div>

          {/* Frequency Selector */}
          <div className="freq-selector-wrap">
            <button
              className={`freq-btn ${financialFreq === 'annual' ? 'active' : ''}`}
              onClick={() => setFinancialFreq('annual')}
            >
              Annual Statements
            </button>
            <button
              className={`freq-btn ${financialFreq === 'quarterly' ? 'active' : ''}`}
              onClick={() => setFinancialFreq('quarterly')}
            >
              Quarterly Statements
            </button>
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="financial-tab-bar">
          <button
            className={`financial-tab-btn ${financialTab === 'income_statement' ? 'active' : ''}`}
            onClick={() => setFinancialTab('income_statement')}
          >
            <FileSpreadsheet size={15} /> Income Statement
          </button>
          <button
            className={`financial-tab-btn ${financialTab === 'balance_sheet' ? 'active' : ''}`}
            onClick={() => setFinancialTab('balance_sheet')}
          >
            <Layers size={15} /> Balance Sheet
          </button>
          <button
            className={`financial-tab-btn ${financialTab === 'cash_flow' ? 'active' : ''}`}
            onClick={() => setFinancialTab('cash_flow')}
          >
            <BarChart3 size={15} /> Cash Flow Statement
          </button>
        </div>

        {loadingFinancials ? (
          <div className="empty-state">
            <LoaderCircle className="spin" size={24} />
            <p>Retrieving financial statement records…</p>
          </div>
        ) : errorFinancials ? (
          <div className="alert info">
            {errorFinancials}
            <button className="subtle-btn compact inline-retry" onClick={fetchFinancials}>
              <RefreshCw size={13} /> Retry
            </button>
          </div>
        ) : !activeStatementData.periods?.length || !activeStatementData.metrics?.length ? (
          <div className="empty-state">
            <AlertCircle size={24} />
            <b>Statement Unavailable</b>
            <p>
              The {financialFreq} {financialTab.replace('_', ' ')} is not available for this company from Yahoo Finance.
            </p>
          </div>
        ) : (
          <div className="financial-table-container">
            <div className="table-scroll">
              <table className="financial-data-table">
                <thead>
                  <tr>
                    <th className="metric-header-cell">FINANCIAL METRIC</th>
                    {activeStatementData.periods.map((p) => (
                      <th key={p} className="period-header-cell">
                        {p}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {activeStatementData.metrics.map((row) => (
                    <tr key={row.name}>
                      <td className="metric-name-cell">
                        <strong>{row.name}</strong>
                      </td>
                      {activeStatementData.periods.map((p) => {
                        const val = row.values?.[p];
                        const isNeg = val != null && val < 0;
                        return (
                          <td
                            key={p}
                            className={`period-val-cell ${isNeg ? 'neg-val' : ''}`}
                          >
                            {val == null ? (
                              <span className="na-tag">N/A</span>
                            ) : (
                              formatFinancialValue(val, currency)
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="table-caption-note">
              Values in {currency || 'local currency'}. Negative values are marked in parentheses or with a minus sign. Missing provider values are shown as N/A.
            </div>
          </div>
        )}
      </section>

      {/* 6. Report Configuration & PDF Export Modal */}
      {showReportModal && (
        <div className="modal-backdrop" onClick={() => !pdfGenerating && setShowReportModal(false)}>
          <div className="report-config-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="eyebrow">RESEARCH EXPORT</div>
                <h2>Configure Research Report PDF</h2>
                <p>Customize sections and settings before generating your formal research document.</p>
              </div>
              <button
                className="modal-close"
                onClick={() => setShowReportModal(false)}
                disabled={pdfGenerating}
              >
                <X size={20} />
              </button>
            </div>

            {pdfError && <div className="alert error">{pdfError}</div>}

            <div className="report-modal-body">
              {/* Section Settings */}
              <div className="report-field-group">
                <label className="field-label">Report Title</label>
                <input
                  className="report-input-text"
                  type="text"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  placeholder="Enter custom report title"
                />
              </div>

              <div className="report-field-group">
                <label className="field-label">Financial Statement Frequency</label>
                <div className="freq-selector-wrap" style={{ alignSelf: 'flex-start' }}>
                  <button
                    className={`freq-btn ${reportFreq === 'annual' ? 'active' : ''}`}
                    onClick={() => setReportFreq('annual')}
                  >
                    Annual Statements
                  </button>
                  <button
                    className={`freq-btn ${reportFreq === 'quarterly' ? 'active' : ''}`}
                    onClick={() => setReportFreq('quarterly')}
                  >
                    Quarterly Statements
                  </button>
                </div>
              </div>

              <div className="report-field-group">
                <label className="field-label">Sections to Include in Report</label>
                <div className="report-sections-grid">
                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.companyInfo}
                      onChange={(e) => setReportSections({ ...reportSections, companyInfo: e.target.checked })}
                    />
                    <span>Company Overview & Profile</span>
                  </label>

                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.marketSnapshot}
                      onChange={(e) => setReportSections({ ...reportSections, marketSnapshot: e.target.checked })}
                    />
                    <span>Market Quote & Snapshot</span>
                  </label>

                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.technicalAnalysis}
                      onChange={(e) => setReportSections({ ...reportSections, technicalAnalysis: e.target.checked })}
                    />
                    <span>Technical Market Analysis (Bullish / Bearish / Neutral)</span>
                  </label>

                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.historicalOHLCV}
                      onChange={(e) => setReportSections({ ...reportSections, historicalOHLCV: e.target.checked })}
                    />
                    <span>Historical OHLCV Price Records ({period})</span>
                  </label>

                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.incomeStatement}
                      onChange={(e) => setReportSections({ ...reportSections, incomeStatement: e.target.checked })}
                    />
                    <span>Income Statement</span>
                  </label>

                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.balanceSheet}
                      onChange={(e) => setReportSections({ ...reportSections, balanceSheet: e.target.checked })}
                    />
                    <span>Balance Sheet</span>
                  </label>

                  <label className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={reportSections.cashFlowStatement}
                      onChange={(e) => setReportSections({ ...reportSections, cashFlowStatement: e.target.checked })}
                    />
                    <span>Cash Flow Statement</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="modal-footer-actions">
              <button
                className="subtle-btn"
                onClick={() => setShowReportModal(false)}
                disabled={pdfGenerating}
              >
                Cancel
              </button>

              <button
                className="primary-btn"
                onClick={handleGeneratePdf}
                disabled={pdfGenerating || !Object.values(reportSections).some(Boolean)}
              >
                {pdfGenerating ? (
                  <>
                    <LoaderCircle className="spin" size={16} /> Generating PDF…
                  </>
                ) : (
                  <>
                    <FileDown size={16} /> Generate & Download PDF
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
