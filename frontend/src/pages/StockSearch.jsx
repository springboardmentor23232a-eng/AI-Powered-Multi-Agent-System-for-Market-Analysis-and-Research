import { useEffect, useState } from 'react';
import { ArrowUpRight, BookmarkPlus, LoaderCircle, Search, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const markets = ['NSE', 'BSE', 'NASDAQ', 'NYSE'];
const periods = ['1 Month', '3 Months', '6 Months', '1 Year', '5 Years'];
const money = (value, currency = '') => value == null ? 'Live quote unavailable' : `${currency ? `${currency} ` : ''}${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

export default function StockSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [market, setMarket] = useState('NASDAQ');
  const [period, setPeriod] = useState('1 Year');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  useEffect(() => {
    api.get('/preferences').then(({ data }) => {
      setMarket(data.default_market);
      setPeriod(data.default_analysis_period);
    }).catch((error) => {
      setMessage(error.response?.data?.detail || 'Unable to load your saved research preferences.');
    });
  }, []);

  const search = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setMessage('');
    try {
      const { data } = await api.get('/stocks/search', { params: { q: query.trim(), market } });
      setResults(data.results || []);
      if (!data.results?.length) setMessage('No matching listings were returned. Try a ticker symbol or another market.');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Stock search is temporarily unavailable.');
    } finally {
      setLoading(false);
    }
  };

  const add = async (stock) => {
    try {
      await api.post('/watchlist', { company_name: stock.company_name, ticker: stock.ticker, market, provider_symbol: stock.provider_symbol });
      setMessage(`${stock.ticker} added to your watchlist.`);
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Could not save this stock.');
    }
  };

  const research = async (stock) => {
    try {
      const { data } = await api.post('/research/start', { company_name: stock.company_name, ticker: stock.ticker, market, analysis_period: period });
      navigate('/history', { state: { created: data.id } });
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Could not create research task.');
    }
  };

  const showAnalytics = async (stock) => {
    setAnalyticsLoading(true);
    setAnalytics({ stock });
    try {
      const { data } = await api.get('/stocks/analytics', { params: { ticker: stock.ticker, market, period } });
      setAnalytics({ stock, data });
    } catch (error) {
      setAnalytics({ stock, error: error.response?.data?.detail || 'Analytics are temporarily unavailable.' });
    } finally {
      setAnalyticsLoading(false);
    }
  };

  return (
    <>
      <div className="page-heading"><div><div className="eyebrow">DISCOVER COMPANIES</div><h1>Stock search</h1><p>Find listed companies and add them to your research workspace.</p></div></div>
      <section className="surface-card search-panel">
        <div className="search-panel-title"><div className="stat-icon violet"><Search size={19}/></div><div><h3>Find a company</h3><p>Search by company name or ticker symbol.</p></div></div>
        <form className="stock-search-form" onSubmit={search}>
          <div className="search-input-wrap"><Search size={18}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try Apple, AAPL, Reliance…"/></div>
          <select value={market} onChange={(event) => { setMarket(event.target.value); setResults([]); }}>{markets.map((item) => <option key={item}>{item}</option>)}</select>
          <select value={period} onChange={(event) => setPeriod(event.target.value)}>{periods.map((item) => <option key={item}>{item}</option>)}</select>
          <button className="primary-btn" disabled={loading || !query.trim()}>{loading ? <LoaderCircle className="spin" size={17}/> : <Search size={17}/>} Search</button>
        </form>
        <div className="provider-note">Listings, prices, and analytics come from Yahoo Finance when available. Missing provider values are shown as unavailable.</div>
      </section>
      {message && <div className={`alert ${message.includes('added') ? 'success' : 'info'}`}>{message}</div>}
      <div className="section-title results-title"><div><h2>Search results</h2><p>{results.length ? `${results.length} matching listings` : 'Companies matching your query will appear here.'}</p></div></div>
      {results.length > 0 ? <div className="results-grid">{results.map((stock, index) => <article className="result-card" key={`${stock.ticker}-${index}`}>
        <div className="result-top"><div className="ticker-avatar large">{stock.ticker.slice(0, 2)}</div><span className="market-tag">{stock.market}</span></div>
        <h3>{stock.company_name}</h3>
        <p>{stock.ticker} · {money(stock.price, stock.currency)}{stock.change_percent == null ? '' : ` · ${Number(stock.change_percent).toFixed(2)}%`}</p>
        <div className="result-actions"><button className="subtle-btn" onClick={() => add(stock)}><BookmarkPlus size={15}/> Watchlist</button><button className="subtle-btn" onClick={() => showAnalytics(stock)}>Analytics</button><button className="primary-btn compact" onClick={() => research(stock)}>Research <ArrowUpRight size={15}/></button></div>
      </article>)}</div> : <div className="search-empty"><div className="empty-icon"><Search size={23}/></div><b>Ready when you are</b><p>Enter a company name or symbol to discover matching listings.</p></div>}
      {analytics && <div className="modal-backdrop" onClick={() => setAnalytics(null)}><div className="report-modal analytics-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setAnalytics(null)}><X size={20}/></button><div className="eyebrow">MARKET ANALYTICS</div><h2>{analytics.stock.company_name}</h2><p className="provider-note">{analytics.stock.ticker} · {market} · {period}</p>{analyticsLoading ? <div className="empty-state"><LoaderCircle className="spin" size={24}/><p>Loading provider analytics…</p></div> : analytics.error ? <div className="alert info">{analytics.error}</div> : <div className="analytics-grid">{[['Period high', analytics.data.period_high], ['Period low', analytics.data.period_low], ['Horizon return', analytics.data.horizon_return], ['Max drawdown', analytics.data.maximum_drawdown], ['Annualized volatility', analytics.data.annualized_volatility], ['RSI 14', analytics.data.rsi_14], ['SMA 50', analytics.data.sma_50], ['SMA 200', analytics.data.sma_200], ['MACD', analytics.data.macd]].map(([label, value]) => <div className="analytics-metric" key={label}><span>{label}</span><b>{value == null ? 'Unavailable' : `${Number(value).toFixed(2)}${label.includes('return') || label.includes('drawdown') || label.includes('volatility') ? '%' : ''}`}</b></div>)}</div>}</div></div>}
    </>
  );
}
