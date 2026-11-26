import React, { useState, useEffect, useCallback } from 'react';
import {
  LayoutGrid,
  Star,
  Clock,
  Trash2,
  TrendingUp,
  FolderPlus,
  FileText,
  Sparkles,
  ExternalLink,
  X,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Calendar,
  Globe,
  Loader2,
  SlidersHorizontal,
  Check,
  Activity,
  Download,
  FileDown,
  Database
} from 'lucide-react';
import Navbar from '../components/Navbar';
import StockSearch from '../components/StockSearch';
import AgentCard from '../components/AgentCard';
import StockAnalyticsHub from '../components/StockAnalyticsHub';
import StructuredReportViewer from '../components/StructuredReportViewer';
import FundamentalAnalysisModal from '../components/FundamentalAnalysisModal';
import { jsPDF } from 'jspdf';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/api';

export const Dashboard = () => {
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState([]);
  const [recentResearch, setRecentResearch] = useState([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);
  const [loadingResearch, setLoadingResearch] = useState(false);

  // User Preferences State
  const [preferences, setPreferences] = useState({
    preferred_market: 'NSE',
    preferred_period: '6 Months',
  });
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [prefSavedMessage, setPrefSavedMessage] = useState('');

  // Modal states
  const [isResearchModalOpen, setIsResearchModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isFundamentalModalOpen, setIsFundamentalModalOpen] = useState(false);
  const [fundamentalTicker, setFundamentalTicker] = useState('INFY.NS');
  const [selectedTask, setSelectedTask] = useState(null);
  const [activeReport, setActiveReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [launchingResearch, setLaunchingResearch] = useState(false);

  const handleDownloadPDF = () => {
    if (!activeReport) return;
    try {
      const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: 'a4'
      });

      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 44;
      const contentWidth = pageWidth - margin * 2;
      const bulletIndent = 16;
      const textPaddingRight = 12;
      const bulletTextWidth = contentWidth - bulletIndent - textPaddingRight;
      let y = margin;

      // Robust sanitizer for typography, currency symbols, and emojis
      const cleanText = (str) => {
        if (!str) return '';
        return str
          .replace(/\[COMING SOON\]/gi, '')
          // Currency symbol normalization for Helvetica PDF fonts
          .replace(/₹/g, 'Rs. ')
          .replace(/\u20B9/g, 'Rs. ')
          .replace(/INR\s*\([¹₹]\)/gi, 'INR (Rs.)')
          .replace(/\(¹\)/g, '(Rs.)')
          .replace(/¹/g, 'Rs. ')
          // Keep bracket content clean
          .replace(/\[([^\]]+)\]/g, '$1')
          // Strip emojis & unicode symbols
          .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{2300}-\u{23FF}\u{2B50}\u{FE0F}]/gu, '')
          .replace(/[🟢📰🛡️⚖️📈🤖⚠️💡▸•►✓✔✕]/gu, '')
          .replace(/\*\*(.*?)\*\*/g, '$1')
          .replace(/\*(.*?)\*/g, '$1')
          .replace(/_{1,2}(.*?)_{1,2}/g, '$1')
          .replace(/`{1,3}(.*?)`{1,3}/g, '$1')
          .replace(/Rs\.\s*Rs\./g, 'Rs.')
          .replace(/[ \t]+/g, ' ')
          .trim();
      };

      const checkPageBreak = (neededHeight) => {
        if (y + neededHeight > pageHeight - margin - 25) {
          doc.addPage();
          y = margin;
          renderHeader();
        }
      };

      const renderHeader = () => {
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(140, 150, 160);
        doc.text(`AI-Powered Multi-Agent Research Analyst | ${selectedTask?.ticker || 'Stock'} Research Report`, margin, 25);
      };

      // Header Banner Box
      doc.setFillColor(15, 23, 42);
      doc.roundedRect(margin, y, contentWidth, 70, 3, 3, 'F');

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(255, 255, 255);
      doc.text(`${selectedTask?.ticker || 'EQUITY'} - Research Report`, margin + 14, y + 26);

      doc.setFontSize(9.5);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(56, 189, 248);
      doc.text(`${cleanText(selectedTask?.company_name)} | Market: ${selectedTask?.market || 'NSE'} | Horizon: ${selectedTask?.requested_period || '6 Months'}`, margin + 14, y + 43);

      doc.setFontSize(8);
      doc.setTextColor(148, 163, 184);
      const genDate = new Date(activeReport?.created_at || selectedTask?.created_at || Date.now()).toLocaleString();
      doc.text(`Report Generated: ${genDate} | Data Source: yfinance Market Data Feed`, margin + 14, y + 58);

      y += 84;

      // Executive Summary
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(16, 185, 129);
      doc.text('EXECUTIVE SYNTHESIS', margin, y);
      y += 14;

      doc.setFontSize(8.5);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(51, 65, 85);

      const rawSummary = cleanText(
        (activeReport.summary || '')
          .replace(/Currency Notice.*?\./gi, '')
          .replace(/All valuation multiples and metrics for .*? are denominated in .*?\./gi, '')
      );

      const summaryLines = doc.splitTextToSize(rawSummary, contentWidth - textPaddingRight);
      checkPageBreak(summaryLines.length * 12 + 10);
      doc.text(summaryLines, margin, y);
      y += summaryLines.length * 12 + 16;

      // Detailed Sections
      const content = activeReport.report_content || '';
      const rawSections = content.split(/(?=### \d+\.)/);

      rawSections.forEach((sec) => {
        const trimmed = sec.trim();
        if (!trimmed) return;

        const lines = trimmed.split('\n');
        const headerLine = lines[0] || '';
        const bodyLines = lines.slice(1);

        const cleanHeading = cleanText(headerLine.replace(/^###\s+/, ''));
        if (!cleanHeading) return;

        checkPageBreak(45);
        doc.setFillColor(241, 245, 249);
        doc.roundedRect(margin, y, contentWidth, 18, 2, 2, 'F');
        doc.setFontSize(9.5);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(15, 23, 42);
        doc.text(cleanHeading, margin + 8, y + 12.5);
        y += 33; // Clear 15 pt separation between heading box and first bullet point

        bodyLines.forEach((bLine) => {
          const bTrim = bLine.trim();
          if (!bTrim) return;

          // Suppress duplicate currency notices
          if (bTrim.toLowerCase().includes('currency notice')) return;

          let isBullet = bTrim.startsWith('- ') || bTrim.startsWith('* ');
          let cleanedLine = cleanText(bTrim.replace(/^[-*]\s+/, ''));
          if (!cleanedLine) return;

          const textX = isBullet ? margin + bulletIndent : margin + 4;
          const availableWidth = isBullet ? bulletTextWidth : (contentWidth - textPaddingRight);
          const splitLines = doc.splitTextToSize(cleanedLine, availableWidth);

          checkPageBreak(splitLines.length * 12 + 4);

          if (isBullet) {
            // Draw clean, perfectly vertically centered emerald bullet dot
            doc.setFillColor(16, 185, 129);
            doc.circle(margin + 6, y - 2.8, 1.8, 'F');
          }

          // Check if line has a bold key: value label
          const colonIdx = cleanedLine.indexOf(':');
          if (isBullet && colonIdx > 0 && colonIdx < 35) {
            const label = cleanedLine.slice(0, colonIdx + 1);
            const val = cleanedLine.slice(colonIdx + 1).trim();

            doc.setFontSize(8.5);
            doc.setFont('helvetica', 'bold');
            const labelWidth = doc.getTextWidth(label + ' ');

            if (splitLines.length === 1) {
              doc.setTextColor(30, 41, 59);
              doc.text(label, textX, y);
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(51, 65, 85);
              doc.text(val, textX + labelWidth, y);
              y += 12 + 3.5;
            } else {
              // Multi-line bullet: bold label followed by value wrapped with clean hanging indent
              const firstLineRemainingWidth = availableWidth - labelWidth;
              const valWords = val.split(' ');
              let line1 = '';
              let wIdx = 0;
              doc.setFont('helvetica', 'normal');
              while (wIdx < valWords.length) {
                const test = line1 ? line1 + ' ' + valWords[wIdx] : valWords[wIdx];
                if (doc.getTextWidth(test) <= firstLineRemainingWidth) {
                  line1 = test;
                  wIdx++;
                } else {
                  break;
                }
              }
              const remText = valWords.slice(wIdx).join(' ');
              const remLines = remText ? doc.splitTextToSize(remText, availableWidth) : [];

              checkPageBreak((remLines.length + 1) * 12 + 4);

              // Print Line 1: Bold label + first line of val
              doc.setFont('helvetica', 'bold');
              doc.setTextColor(30, 41, 59);
              doc.text(label, textX, y);

              doc.setFont('helvetica', 'normal');
              doc.setTextColor(51, 65, 85);
              if (line1) {
                doc.text(line1, textX + labelWidth, y);
              }

              // Print Remaining lines: Clean hanging indent under textX
              remLines.forEach((rLine, rIdx) => {
                doc.text(rLine, textX, y + (rIdx + 1) * 12);
              });

              y += (remLines.length + 1) * 12 + 3.5;
            }
          } else {
            // Multi-line non-bullet or unstructured text
            doc.setFontSize(8.5);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(51, 65, 85);
            doc.text(splitLines, textX, y);
            y += splitLines.length * 12 + 3.5;
          }
        });

        y += 14; // Clean separation between sections
      });

      // Limitations & Disclaimer Box
      if (activeReport.limitations) {
        checkPageBreak(45);
        doc.setFillColor(254, 243, 199);
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(180, 83, 9);
        doc.text('DISCLAIMER & LIMITATIONS', margin, y);
        y += 13;

        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(120, 53, 15);
        const limClean = cleanText(activeReport.limitations);
        const limLines = doc.splitTextToSize(limClean, contentWidth - textPaddingRight);
        checkPageBreak(limLines.length * 11 + 10);
        doc.text(limLines, margin, y);
        y += limLines.length * 11 + 14;
      }

      // Page Numbers and Footer
      const totalPages = doc.internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(7.5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(148, 163, 184);
        doc.text(`Page ${i} of ${totalPages}`, pageWidth - margin - 45, pageHeight - 15);
        doc.text('Confidential - For Research & Educational Purposes Only', margin, pageHeight - 15);
      }

      doc.save(`${selectedTask?.ticker || 'Stock'}_Research_Report.pdf`);
    } catch (err) {
      console.error('Failed to generate PDF:', err);
      window.print();
    }
  };

  const handleDownloadMarkdown = () => {
    if (!activeReport) return;
    const reportDate = new Date(activeReport?.created_at || selectedTask?.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    const mdText = `# Research Report: ${selectedTask?.ticker} - ${selectedTask?.company_name}
Report Generated Date: ${reportDate}
Data Source: yfinance API
Data Retrieval Timestamp: ${new Date(selectedTask?.created_at).toLocaleString()}
Market Exchange: ${selectedTask?.market} | Horizon: ${selectedTask?.requested_period}

## Executive Summary
${activeReport.summary}

## Detailed Findings
${activeReport.report_content}

## Limitations & Disclaimer
${activeReport.limitations}
`;
    const blob = new Blob([mdText], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${selectedTask?.ticker || 'Stock'}_Research_Report.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Market Analytics Hub State (Appears only when user searches or selects a stock)
  const [analyticsTicker, setAnalyticsTicker] = useState(null);

  const handleSelectStockForAnalytics = (selectedTicker) => {
    setAnalyticsTicker(selectedTicker);
    // Smooth scroll down to the analytics hub
    setTimeout(() => {
      const el = document.getElementById('analytics-hub');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const handleQuickAddWatchlist = async (tickerToAdd) => {
    try {
      await dashboardService.addToWatchlist(tickerToAdd);
      fetchWatchlist();
    } catch (e) {
      console.error('Failed to add to watchlist:', e);
    }
  };

  // USD currency confirmation modal (for watchlist, preference, analytics)
  const [usdConfirm, setUsdConfirm] = useState({ open: false, stock: null, type: null, targetMarket: null });

  // Form state for new research
  const [researchForm, setResearchForm] = useState({
    ticker: '',
    company_name: '',
    market: 'NSE',
    requested_period: '6 Months',
  });

  const fetchWatchlist = useCallback(async () => {
    try {
      setLoadingWatchlist(true);
      const data = await dashboardService.getWatchlist();
      setWatchlist(data || []);
    } catch (err) {
      console.error('Error fetching watchlist:', err);
    } finally {
      setLoadingWatchlist(false);
    }
  }, []);

  const fetchRecentResearch = useCallback(async () => {
    try {
      setLoadingResearch(true);
      const data = await dashboardService.getRecentResearch();
      setRecentResearch(data || []);
    } catch (err) {
      console.error('Error fetching recent research:', err);
    } finally {
      setLoadingResearch(false);
    }
  }, []);

  const fetchPreferences = useCallback(async () => {
    try {
      const data = await dashboardService.getPreferences();
      if (data) {
        setPreferences({
          preferred_market: data.preferred_market || 'NSE',
          preferred_period: data.preferred_period || '6 Months',
        });
      }
    } catch (err) {
      console.error('Failed to load user preferences:', err);
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
    fetchRecentResearch();
    fetchPreferences();
  }, [fetchWatchlist, fetchRecentResearch, fetchPreferences]);

  const handleSavePreferences = async (e) => {
    if (e) e.preventDefault();
    try {
      setSavingPreferences(true);
      await dashboardService.updatePreferences(preferences);
      setPrefSavedMessage('Preferences saved to database!');
      setTimeout(() => setPrefSavedMessage(''), 2500);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleRemoveFromWatchlist = async (savedStockId) => {
    try {
      await dashboardService.removeFromWatchlist(savedStockId);
      setWatchlist((prev) => prev.filter((item) => item.saved_stock_id !== savedStockId));
    } catch (err) {
      console.error('Failed to remove stock:', err);
    }
  };

  const openResearchModal = (ticker, companyName = '', market = '') => {
    let detectedMarket = preferences.preferred_market;
    if (market) {
      if (market.includes('NSE') || market.includes('India')) detectedMarket = 'NSE';
      else if (market.includes('BSE')) detectedMarket = 'BSE';
      else if (market.includes('NASDAQ')) detectedMarket = 'NASDAQ';
      else if (market.includes('NYSE') || market.includes('United States')) detectedMarket = 'NYSE';
    }

    setResearchForm({
      ticker: ticker,
      company_name: companyName,
      market: detectedMarket,
      requested_period: preferences.preferred_period || '6 Months',
    });
    setIsResearchModalOpen(true);
  };

  const handleLaunchResearch = async (e) => {
    e.preventDefault();
    if (!researchForm.ticker) return;

    try {
      setLaunchingResearch(true);
      await dashboardService.createResearchTask(researchForm);
      await fetchRecentResearch();
      setIsResearchModalOpen(false);
    } catch (err) {
      console.error('Failed to launch research:', err);
    } finally {
      setLaunchingResearch(false);
    }
  };

  const handleOpenReport = async (task) => {
    try {
      setSelectedTask(task);
      setLoadingReport(true);
      setIsReportModalOpen(true);
      const reportData = await dashboardService.getResearchReport(task.task_id);
      setActiveReport(reportData);
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleDeleteResearch = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this research report?')) {
      return;
    }
    try {
      await dashboardService.deleteResearch(taskId);
      setRecentResearch((prev) => prev.filter((t) => t.task_id !== taskId));
      if (selectedTask?.task_id === taskId) {
        setIsReportModalOpen(false);
        setActiveReport(null);
        setSelectedTask(null);
      }
    } catch (err) {
      console.error('Failed to delete research report:', err);
    }
  };

  const isUSMarket = (market) => market === 'NASDAQ' || market === 'NYSE';

  const displayName = user?.full_name || 'Stock Researcher';

  return (
    <div className="min-h-screen bg-[#05080a] text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-7">

        {/* Welcome Section */}
        <section className="relative flex items-center min-h-[135px] sm:min-h-[155px] px-3 sm:px-6 py-4 overflow-hidden rounded-2xl">
          {/* Left Text */}
          <div className="relative z-10 max-w-xl">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight drop-shadow-md">
              Welcome back, <span className="text-white">{displayName}</span>!
            </h1>
            <p className="mt-1.5 text-sm sm:text-base text-slate-300/90 font-normal drop-shadow-sm">
              Your stock research workspace.
            </p>
          </div>

          {/* Globe & Candlesticks graphic */}
          <div className="absolute inset-0 w-full h-full pointer-events-none select-none overflow-hidden flex justify-end items-center">
            <div className="relative w-full h-full flex justify-end">
              <img
                src="/images/dashboard-globe.png"
                alt="Digital Financial Globe and Market Growth"
                className="w-full sm:w-[92%] lg:w-[85%] h-full object-cover object-right opacity-85 sm:opacity-90"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#05080a] via-[#05080a]/60 to-transparent pointer-events-none" />
            </div>
          </div>
        </section>

        {/* Section: User Preferences Control Bar */}
        <section className="bg-[#0b0f15] border border-[#1c2533] rounded-2xl p-4 sm:p-5 shadow-sm">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">

            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                <SlidersHorizontal className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Research Preferences</h3>
                <p className="text-xs text-slate-400">Save default market exchange and historical analysis horizon</p>
              </div>
            </div>

            <div className="flex items-center flex-wrap gap-3 w-full md:w-auto">
              {/* Market Preference Dropdown */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-400 font-medium">Market:</span>
                <select
                  value={preferences.preferred_market}
                  onChange={(e) => {
                    const newMarket = e.target.value;
                    if (newMarket === 'NASDAQ' || newMarket === 'NYSE') {
                      setUsdConfirm({
                        open: true,
                        type: 'preference',
                        targetMarket: newMarket,
                        stock: null,
                      });
                    } else {
                      setPreferences({ ...preferences, preferred_market: newMarket });
                    }
                  }}
                  className="px-3 py-1.5 bg-[#111620] border border-[#1e293b] rounded-lg text-xs font-semibold text-white focus:outline-none focus:border-emerald-500 transition-colors"
                >
                  <option value="NSE">NSE (India)</option>
                  <option value="BSE">BSE (India)</option>
                  <option value="NASDAQ">NASDAQ (US)</option>
                  <option value="NYSE">NYSE (US)</option>
                </select>
              </div>

              {/* Analysis Period Dropdown */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-400 font-medium">Period:</span>
                <select
                  value={preferences.preferred_period}
                  onChange={(e) => setPreferences({ ...preferences, preferred_period: e.target.value })}
                  className="px-3 py-1.5 bg-[#111620] border border-[#1e293b] rounded-lg text-xs font-semibold text-white focus:outline-none focus:border-emerald-500 transition-colors"
                >
                  <option value="1 Month">1 Month</option>
                  <option value="3 Months">3 Months</option>
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="5 Years">5 Years</option>
                </select>
              </div>

              {/* Save Preferences Button */}
              <button
                type="button"
                onClick={handleSavePreferences}
                disabled={savingPreferences}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-60 shrink-0"
              >
                {savingPreferences ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                <span>Save</span>
              </button>

              {prefSavedMessage && (
                <span className="text-xs text-emerald-400 font-medium animate-fade-in">
                  ✓ {prefSavedMessage}
                </span>
              )}
            </div>

          </div>
        </section>

        {/* Stock Search Section */}
        <section>
          <StockSearch
            onWatchlistUpdated={fetchWatchlist}
            onStartResearch={openResearchModal}
            onSelectStock={handleSelectStockForAnalytics}
          />
        </section>

        {/* Module 2: Market Analytics & Financial Intelligence Hub */}
        {analyticsTicker && (
          <section id="analytics-hub" className="animate-fade-in">
            <StockAnalyticsHub
              ticker={analyticsTicker}
              initialPeriod={preferences.preferred_period}
              onClose={() => setAnalyticsTicker(null)}
              onAddToWatchlist={handleQuickAddWatchlist}
              onOpenResearch={openResearchModal}
              onOpenFundamental={(t) => {
                setFundamentalTicker(t);
                setIsFundamentalModalOpen(true);
              }}
            />
          </section>
        )}

        {/* Research Agents Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <LayoutGrid className="w-5 h-5 text-white" />
            <h2 className="text-xl font-bold text-white tracking-tight">Research Agents</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AgentCard
              title="Fundamental Analysis Agent"
              description="Analyzes company revenue, earnings, profitability, debt, financial ratios, peer benchmarks, and data audits."
              iconType="fundamental"
              status="active"
              onClick={() => {
                const defaultTicker = analyticsTicker || (preferences.preferred_market === 'NASDAQ' || preferences.preferred_market === 'NYSE' ? 'AAPL' : 'INFY.NS');
                setFundamentalTicker(defaultTicker);
                setIsFundamentalModalOpen(true);
              }}
            />
            <AgentCard
              title="Technical Analysis Agent"
              description="Examines historical stock prices, market trends, SMA, EMA, RSI, and MACD."
              iconType="technical"
            />
            <AgentCard
              title="News and Sentiment Analysis Agent"
              description="Analyzes financial news, company announcements, and market sentiment."
              iconType="news"
            />
            <AgentCard
              title="Risk Analysis Agent"
              description="Evaluates financial risks, market volatility, maximum drawdown, and conflicting findings."
              iconType="risk"
            />
          </div>
        </section>

        {/* Bottom Dual Panels: My Watchlist & Recent Research */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Left Panel: My Watchlist */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">My Watchlist</h2>
            </div>

            <div className="bg-[#0b0f15] border border-[#1c2533] rounded-2xl p-5 min-h-[220px] flex flex-col justify-center shadow-sm">
              {watchlist.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-center text-slate-400 py-6">
                  <div className="w-12 h-12 rounded-xl bg-[#121924] border border-[#1c2533] flex items-center justify-center mb-3 text-slate-400">
                    <FolderPlus className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <p className="text-sm font-medium text-slate-400">
                    Your manually saved stocks will appear here.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-[#18212e] w-full">
                  {watchlist.map((stock) => (
                    <div key={stock.saved_stock_id} className="flex items-center justify-between py-3 px-1 gap-2">
                      {/* Left: ticker + enriched market info (Clickable to open Market Analytics & Financial Intelligence) */}
                      <div
                        onClick={() => {
                          if (stock.is_us_market) {
                            setUsdConfirm({ open: true, stock, type: 'analytics' });
                          } else {
                            handleSelectStockForAnalytics(stock.ticker);
                          }
                        }}
                        className="flex flex-col min-w-0 cursor-pointer group"
                        title="Click to view Market Analytics & Financial Intelligence"
                      >
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-white text-sm tracking-wide group-hover:text-emerald-400 transition-colors">
                            {stock.ticker}
                          </span>
                          {/* Currency badge */}
                          {stock.is_us_market ? (
                            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-950/60 text-amber-400 border border-amber-500/40">$ USD</span>
                          ) : (
                            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">₹ INR</span>
                          )}
                          {stock.exchange && (
                            <span className="text-[10px] text-slate-500 font-medium">{stock.exchange}</span>
                          )}
                        </div>
                        {stock.company_name && (
                          <span className="text-[11px] text-slate-400 truncate max-w-[180px] mt-0.5 group-hover:text-slate-200 transition-colors">
                            {stock.company_name}
                          </span>
                        )}
                        <div className="flex items-center gap-2 mt-0.5">
                          {stock.current_price != null && (
                            <span className="text-xs font-semibold text-slate-200">
                              {stock.currency_symbol || (stock.is_us_market ? '$' : '₹')}{Number(stock.current_price).toFixed(2)}
                            </span>
                          )}
                          {stock.change_percent != null && (
                            <span className={`text-[10px] font-semibold ${stock.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {stock.change_percent >= 0 ? '+' : ''}{Number(stock.change_percent).toFixed(2)}%
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {/* Analyze — USD confirmation for US stocks */}
                        <button
                          onClick={() => {
                            if (stock.is_us_market) {
                              setUsdConfirm({ open: true, stock, type: 'research' });
                            } else {
                              openResearchModal(stock.ticker, stock.company_name, stock.exchange || '');
                            }
                          }}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/30 transition-all"
                          title="Start research for this saved stock"
                        >
                          <Sparkles className="w-3 h-3 text-emerald-400" />
                          <span>Analyze</span>
                        </button>

                        {/* Remove */}
                        <button
                          onClick={() => handleRemoveFromWatchlist(stock.saved_stock_id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                          title="Remove from watchlist"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel: Recent Research */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-200" />
              <h2 className="text-lg font-bold text-white tracking-tight">Recent Research</h2>
            </div>

            <div className="bg-[#0b0f15] border border-[#1c2533] rounded-2xl p-5 min-h-[220px] flex flex-col justify-center shadow-sm">
              {recentResearch.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-center text-slate-400 py-6">
                  <div className="w-12 h-12 rounded-xl bg-[#121924] border border-[#1c2533] flex items-center justify-center mb-3 text-slate-400">
                    <FileText className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <p className="text-sm font-medium text-slate-400">
                    Your previous research records will appear here.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-[#18212e] w-full">
                  {recentResearch.map((task) => (
                    <div key={task.task_id} className="flex items-center justify-between py-3 px-1 gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-white text-sm">{task.ticker}</span>
                          <span className="text-xs text-slate-400 truncate">
                            {task.company_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                          <span className="font-medium text-slate-300">{task.market}</span>
                          <span>•</span>
                          <span>{task.requested_period}</span>
                          <span>•</span>
                          <span>{new Date(task.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0">
                        {/* Research Status Badge */}
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/70 text-emerald-400 border border-emerald-500/40 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          <span>{task.status}</span>
                        </span>

                        {/* Open report */}
                        <button
                          onClick={() => handleOpenReport(task)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#141d2a] hover:bg-[#1a2536] text-slate-200 border border-[#243347] transition-all"
                        >
                          <FileText className="w-3 h-3 text-emerald-400" />
                          <span>Report</span>
                        </button>

                        {/* Delete research report individually */}
                        <button
                          onClick={() => handleDeleteResearch(task.task_id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                          title="Delete research report"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </section>

      </main>

      {/* ── MODAL 1: USD Currency Confirmation (Preference, Watchlist, Analytics) ── */}
      {usdConfirm.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-[#0b0f15] border border-amber-500/40 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-start gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white mb-1">Currency Notice — US Dollar Market</h3>
                {usdConfirm.type === 'preference' ? (
                  <p className="text-sm text-slate-300 leading-relaxed">
                    You have selected <span className="font-semibold text-amber-300">{usdConfirm.targetMarket} (US Market)</span> as your market preference. All stock valuations, historical prices, and analytics will be quoted in <span className="font-bold text-white">US Dollars (USD $)</span>.
                  </p>
                ) : (
                  <p className="text-sm text-slate-300 leading-relaxed">
                    <span className="font-semibold text-amber-300">{usdConfirm.stock?.ticker}</span> is listed on a{' '}
                    <span className="font-semibold text-amber-300">US Exchange ({usdConfirm.stock?.exchange || 'NASDAQ/NYSE'})</span>.
                    All prices and financial data are quoted in{' '}
                    <span className="font-bold text-white">US Dollars (USD $)</span>.
                  </p>
                )}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/20 text-xs text-amber-300/90 mb-5">
              💡 If you are based in India, note that returns and metrics will be affected by USD/INR foreign exchange fluctuations.
            </div>
            <div className="flex items-center gap-3 justify-end">
              <button
                type="button"
                onClick={() => setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null })}
                className="px-4 py-2 rounded-lg border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  if (usdConfirm.type === 'preference') {
                    setPreferences((prev) => ({ ...prev, preferred_market: usdConfirm.targetMarket }));
                    setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null });
                  } else if (usdConfirm.type === 'analytics') {
                    const t = usdConfirm.stock?.ticker;
                    setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null });
                    if (t) handleSelectStockForAnalytics(t);
                  } else {
                    const s = usdConfirm.stock;
                    setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null });
                    if (s) openResearchModal(s.ticker, s.company_name, s.exchange || 'NASDAQ');
                  }
                }}
                className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-all shadow-md"
              >
                Yes, Proceed in USD ($)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL 2: Launch Stock Research Task ── */}
      {isResearchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-[#0b0f15] border border-[#1c2533] rounded-3xl p-6 sm:p-7 shadow-2xl relative">

            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Start Research Task</h3>
                  <p className="text-xs text-slate-400">Configure parameters for Multi-Agent analysis</p>
                </div>
              </div>
              <button
                onClick={() => setIsResearchModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleLaunchResearch} className="space-y-4">
              {/* Selected Stock Info */}
              <div className="p-3 rounded-xl bg-[#101722] border border-[#1c2533] flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400">Target Asset</span>
                  <div className="font-bold text-white text-base">{researchForm.ticker}</div>
                </div>
                {researchForm.company_name && (
                  <span className="text-xs text-slate-300 max-w-[200px] truncate text-right">
                    {researchForm.company_name}
                  </span>
                )}
              </div>

              {/* Market Selection */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-slate-400" />
                  <span>Market / Exchange</span>
                </label>
                <select
                  value={researchForm.market}
                  onChange={(e) => setResearchForm({ ...researchForm, market: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="NSE">NSE – National Stock Exchange of India</option>
                  <option value="BSE">BSE – BSE Ltd., India</option>
                  <option value="NASDAQ">NASDAQ – US Stock Exchange</option>
                  <option value="NYSE">NYSE – New York Stock Exchange</option>
                </select>
              </div>

              {/* USD Currency Notice — shown when NASDAQ or NYSE is selected */}
              {isUSMarket(researchForm.market) && (
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/30 border border-amber-500/30">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-300 leading-relaxed">
                    <span className="font-semibold text-amber-200">Currency Notice:</span> This stock is on a US exchange ({researchForm.market}).
                    All prices and financial data are quoted in <span className="font-bold text-white">US Dollars (USD $)</span>.
                  </p>
                </div>
              )}

              {/* Analysis Period */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>Analysis Period</span>
                </label>
                <select
                  value={researchForm.requested_period}
                  onChange={(e) => setResearchForm({ ...researchForm, requested_period: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="1 Month">1 Month</option>
                  <option value="3 Months">3 Months</option>
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="5 Years">5 Years</option>
                </select>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsResearchModalOpen(false)}
                  className="px-4 py-2.5 rounded-lg border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={launchingResearch}
                  className="px-5 py-2.5 rounded-lg bg-[#00a86b] hover:bg-[#00ba77] text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-900/30 transition-all disabled:opacity-60"
                >
                  {launchingResearch ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Saving Task...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Launch Research Task</span>
                    </>
                  )}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

      {/* ── FULL SIZE WINDOW: View Generated Research Report ── */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#090d14] flex flex-col w-screen h-screen overflow-hidden">

          {/* Top Full-Width Navigation Bar */}
          <div className="flex items-center justify-between px-5 sm:px-8 py-3.5 border-b border-[#1c2533] bg-[#0b0f15] shrink-0">
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  setIsReportModalOpen(false);
                  setPdfNotice(false);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#141b25] hover:bg-[#1a2332] text-xs font-semibold text-slate-200 border border-[#222e40] transition-colors"
              >
                <span>← Back to Dashboard</span>
              </button>
              <div className="h-6 w-px bg-[#1c2533] mx-1" />
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                  <span>{selectedTask?.ticker}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/30">
                    Report Complete
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  {selectedTask?.company_name} • {selectedTask?.market} ({selectedTask?.requested_period})
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 flex-wrap">
              {/* Option to delete research report individually */}
              {selectedTask?.task_id && (
                <button
                  type="button"
                  onClick={() => handleDeleteResearch(selectedTask.task_id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-500/30 text-xs font-semibold transition-colors"
                  title="Delete this research report"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Delete Report</span>
                </button>
              )}

              {/* Download PDF Button */}
              <button
                type="button"
                onClick={handleDownloadPDF}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-950/40 hover:bg-red-900/50 text-xs font-semibold text-red-300 border border-red-500/30 hover:border-red-500/50 transition-colors shadow-sm"
                title="Download formatted PDF report"
              >
                <FileDown className="w-3.5 h-3.5 text-red-400" />
                <span className="hidden sm:inline">Download PDF</span>
              </button>

              {/* Download Markdown Report Button */}
              <button
                type="button"
                onClick={handleDownloadMarkdown}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-xs font-semibold text-emerald-300 border border-emerald-500/40 transition-colors shadow-sm"
                title="Download report as Markdown (.md)"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden sm:inline">Markdown</span>
              </button>
            </div>
          </div>

          {/* Full-Screen Scrollable Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-8 bg-[#090d14]">
            <div className="max-w-6xl mx-auto space-y-6 text-xs sm:text-sm">

              {/* Metadata Badges */}
              <div className="flex items-center gap-2.5 text-xs text-slate-400 flex-wrap pb-2 border-b border-[#141d2a]">
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121924] border border-[#1e293b] text-emerald-300 font-medium">
                  <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Generated: <strong className="text-white">{new Date(activeReport?.created_at || selectedTask?.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</strong></span>
                </span>
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121924] border border-[#1e293b] text-slate-300 font-medium">
                  <Database className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Source: <strong className="text-white">yfinance API</strong></span>
                </span>
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121924] border border-[#1e293b] text-slate-300 font-mono">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Retrieved: {new Date(selectedTask?.created_at).toLocaleString()}</span>
                </span>
              </div>

              {loadingReport ? (
                <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
                  <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
                  <span>Loading report from database...</span>
                </div>
              ) : activeReport ? (
                <>
                  {/* Executive Summary */}
                  <div className="p-4 sm:p-5 rounded-2xl bg-[#0c121c] border border-emerald-500/25 space-y-3 shadow-md">
                    <div className="flex items-center justify-between border-b border-[#182333] pb-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400">
                          <Sparkles className="w-3.5 h-3.5" />
                        </div>
                        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                          Executive Synthesis
                        </h4>
                      </div>
                      <div className="flex items-center gap-2">
                        {isUSMarket(selectedTask?.market) && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            USD ($)
                          </span>
                        )}
                        <span className="text-[10px] font-medium text-slate-400 bg-[#141b25] px-2 py-0.5 rounded-md border border-[#222e40]">
                          {selectedTask?.requested_period}
                        </span>
                      </div>
                    </div>

                    {/* US Currency Notice Callout */}
                    {(isUSMarket(selectedTask?.market) || activeReport.summary?.includes('Currency Notice')) && (
                      <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/25 border border-amber-500/30 text-xs text-amber-300/90 leading-relaxed">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold text-amber-200">US Market Currency Notice: </span>
                          <span>
                            All valuation multiples, historical prices, and financial metrics for {selectedTask?.ticker} are quoted in <strong className="text-white">US Dollars ($ USD)</strong>.
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Clean Synthesis Narrative */}
                    <p className="text-slate-200 text-xs sm:text-sm leading-relaxed font-normal">
                      {activeReport.summary
                        .replace(/\*\*⚠️ Currency Notice.*?\*\*\.?/gs, '')
                        .replace(/All valuation multiples and metrics for .*? are denominated in \*\*US Dollars \(\$ USD\)\*\*\.?/gs, '')
                        .replace(/\*\*/g, '')
                        .trim()}
                    </p>
                  </div>

                  {/* Multi-Agent Breakdown Rendered via StructuredReportViewer */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                        Research Findings
                      </h4>
                      <span className="text-[11px] text-slate-400">
                        AI-Powered Research Report
                      </span>
                    </div>
                    <StructuredReportViewer content={activeReport.report_content} />
                  </div>

                  {/* Limitations and Disclaimer */}
                  <div className="p-3.5 rounded-xl bg-[#141312] border border-amber-900/30 text-amber-300/80 text-xs flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-amber-300 block mb-0.5">Disclaimer & Limitations</span>
                      <p className="text-slate-400 leading-normal">
                        {activeReport.limitations}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-10 text-slate-400">
                  Could not load report content.
                </div>
              )}
            </div>
          </div>

          {/* Full-Screen Footer Bar */}
          <div className="px-6 py-3 border-t border-[#1c2533] bg-[#0b0f15] flex items-center justify-between text-xs text-slate-400 shrink-0">
            <div className="flex items-center gap-2">
              <span>Research Report • {selectedTask?.ticker}</span>
              <span>•</span>
              <span>Source: <strong className="text-white">yfinance API</strong></span>
            </div>
          </div>

        </div>
      )}

      {/* ── MODAL 4: Fundamental Analysis Agent Screen ── */}
      <FundamentalAnalysisModal
        isOpen={isFundamentalModalOpen}
        onClose={() => setIsFundamentalModalOpen(false)}
        initialTicker={fundamentalTicker || (preferences.preferred_market === 'NASDAQ' || preferences.preferred_market === 'NYSE' ? 'AAPL' : 'INFY.NS')}
        preferredMarket={preferences.preferred_market}
      />

      {/* Footer */}
      <footer className="w-full bg-[#070a0e] border-t border-[#1c2533] py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
          <div>
            <span className="font-bold text-slate-200">Multi-Agent Stock Research Analyst</span>
            <span className="mx-2 text-slate-600">|</span>
            <span>AI-Powered Stock Research and Analysis Platform.</span>
          </div>
          <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Research Smarter. Invest Better.</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
