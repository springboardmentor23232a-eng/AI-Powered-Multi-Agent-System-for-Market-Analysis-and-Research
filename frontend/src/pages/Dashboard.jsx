import { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, Bookmark, Clock3, Search, Sparkles, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const fmt = (date) => new Date(date).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' });

export default function Dashboard() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [watch, setWatch] = useState([]);
  const [pref, setPref] = useState({ default_market: 'NASDAQ', default_analysis_period: '1 Year' });
  const [indices, setIndices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.allSettled([
      api.get('/research/history'),
      api.get('/watchlist'),
      api.get('/preferences'),
      api.get('/stocks/indices'),
    ]).then(([historyResult, watchResult, preferenceResult, indexResult]) => {
      const failures = [];
      if (historyResult.status === 'fulfilled') setHistory(historyResult.value.data);
      else failures.push(historyResult.reason);
      if (watchResult.status === 'fulfilled') setWatch(watchResult.value.data);
      else failures.push(watchResult.reason);
      if (preferenceResult.status === 'fulfilled') setPref(preferenceResult.value.data);
      else failures.push(preferenceResult.reason);
      if (indexResult.status === 'fulfilled') setIndices(indexResult.value.data);
      else failures.push(indexResult.reason);
      if (failures.length) setError(failures[0]?.response?.data?.detail || 'Some workspace data is temporarily unavailable.');
      setLoading(false);
    });
  }, []);

  const completed = history.filter((item) => item.status === 'completed').length;

  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">YOUR WORKSPACE</div><h1>Good to see you, {user?.full_name?.split(' ')[0] || 'there'}.</h1><p>Here’s an overview of your stock research activity.</p></div>
        <Link to="/search" className="primary-btn compact"><Search size={16}/> Start research</Link>
      </div>
      {error && <div className="alert info">{error}</div>}
      {indices.length > 0 && <div className="index-tape" aria-label="Market indices">{indices.map((index) => <span key={index.symbol}><b>{index.name}</b><strong>{index.price == null ? 'Unavailable' : Number(index.price).toLocaleString(undefined, { maximumFractionDigits: 2 })}</strong><em className={index.change_percent < 0 ? 'negative' : ''}>{index.change_percent == null ? '—' : `${Number(index.change_percent).toFixed(2)}%`}</em></span>)}</div>}
      <section className="welcome-banner"><div className="banner-glow"/><div className="banner-copy"><div className="banner-kicker"><Sparkles size={14}/> RESEARCH, ORGANIZED</div><h2>Make every market question<br/>a little more <em>structured.</em></h2><p>Search a company, save it to your watchlist, and keep your research history in one place.</p><Link to="/search" className="banner-link">Explore stocks <ArrowUpRight size={16}/></Link></div><div className="banner-graphic"><div className="chart-ring ring1"/><div className="chart-ring ring2"/><div className="chart-core"><TrendingUp size={31}/></div><div className="chart-label">MARKET<br/>INTELLIGENCE</div></div></section>
      <div className="section-title"><div><h2>Workspace overview</h2><p>Your saved activity at a glance.</p></div><span className="updated-label">LIVE FROM YOUR ACCOUNT</span></div>
      <div className="stat-grid"><div className="stat-card"><div className="stat-icon violet"><Activity size={19}/></div><span>Total research</span><b>{loading ? '—' : history.length}</b><small>Research tasks created</small></div><div className="stat-card"><div className="stat-icon green"><TrendingUp size={19}/></div><span>Completed</span><b>{loading ? '—' : completed}</b><small>Reports marked completed</small></div><div className="stat-card"><div className="stat-icon amber"><Bookmark size={19}/></div><span>Saved stocks</span><b>{loading ? '—' : watch.length}</b><small>Companies in your watchlist</small></div><div className="stat-card"><div className="stat-icon blue"><Clock3 size={19}/></div><span>Default setup</span><b className="pref-value">{pref.default_market}</b><small>{pref.default_analysis_period} analysis period</small></div></div>
      <div className="dashboard-columns"><section className="surface-card"><div className="card-heading"><div><h3>Recent research</h3><p>Your latest research tasks</p></div><Link to="/history" className="text-link">View all <ArrowUpRight size={15}/></Link></div>{history.length === 0 ? <div className="empty-state"><div className="empty-icon"><Activity size={22}/></div><b>No research yet</b><p>Start by searching for a company or ticker.</p><Link to="/search" className="subtle-btn">Find a stock <ArrowUpRight size={15}/></Link></div> : <div className="recent-list">{history.slice(0, 5).map((item) => <div className="recent-row" key={item.id}><div className="ticker-avatar">{item.ticker.slice(0, 2)}</div><div className="recent-main"><b>{item.company_name}</b><span>{item.ticker} · {item.market} · {item.analysis_period}</span></div><div className="recent-meta"><span className={`status-pill ${item.status}`}>{item.status}</span><small>{fmt(item.created_at)}</small></div></div>)}</div>}</section><section className="surface-card preference-card"><div className="card-heading"><div><h3>Your preferences</h3><p>Default research configuration</p></div><Link to="/preferences" className="icon-link"><ArrowUpRight size={17}/></Link></div><div className="preference-line"><span>Preferred market</span><b>{pref.default_market}</b></div><div className="preference-line"><span>Analysis period</span><b>{pref.default_analysis_period}</b></div><div className="preference-note"><div className="note-dot"/> These defaults are applied when you create a research task.</div><Link to="/preferences" className="subtle-btn full">Manage preferences <ArrowUpRight size={15}/></Link></section></div>
    </>
  );
}
