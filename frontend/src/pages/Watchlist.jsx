import { useEffect, useState } from 'react';
import { ArrowUpRight, Bookmark, Search, Trash2, LoaderCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Watchlist() {
  const [items, setItems] = useState([]);
  const [quotes, setQuotes] = useState({});
  const [preference, setPreference] = useState({ default_analysis_period: '1 Year' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [{ data: stocks }, { data: preferences }] = await Promise.all([api.get('/watchlist'), api.get('/preferences')]);
      setItems(stocks);
      setPreference(preferences);
      const quoteResults = await Promise.all(stocks.map(async (stock) => {
        try {
          const { data } = await api.get('/stocks/quote', { params: { ticker: stock.ticker, market: stock.market } });
          return [stock.id, data];
        } catch {
          return [stock.id, null];
        }
      }));
      setQuotes(Object.fromEntries(quoteResults));
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load your watchlist.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    setBusy(String(id));
    try {
      await api.delete(`/watchlist/${id}`);
      setItems((current) => current.filter((item) => item.id !== id));
      setQuotes((current) => { const next = { ...current }; delete next[id]; return next; });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to remove stock.');
    } finally {
      setBusy('');
    }
  };

  const research = async (stock) => {
    setBusy(`research-${stock.id}`);
    try {
      const { data } = await api.post('/research/start', {
        company_name: stock.company_name,
        ticker: stock.ticker,
        market: stock.market,
        analysis_period: preference.default_analysis_period,
      });
      navigate('/history', { state: { created: data.id } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to start research.');
    } finally {
      setBusy('');
    }
  };

  return (
    <>
      <div className="page-heading"><div><div className="eyebrow">YOUR SHORTLIST</div><h1>Watchlist</h1><p>Companies you have saved for quick access and future research.</p></div><Link to="/search" className="primary-btn compact"><Search size={16}/> Find stocks</Link></div>
      {error && <div className="alert info">{error}</div>}
      <div className="section-title"><div><h2>Saved companies</h2><p>{items.length} {items.length === 1 ? 'stock' : 'stocks'} saved to your account.</p></div></div>
      {loading ? <div className="search-empty"><LoaderCircle className="spin" size={24}/><p>Loading your saved companies…</p></div> : items.length === 0 ? <div className="search-empty"><div className="empty-icon"><Bookmark size={23}/></div><b>Your watchlist is waiting</b><p>Search for a company and save it here for easy access.</p><Link to="/search" className="subtle-btn">Search stocks <ArrowUpRight size={15}/></Link></div> : <div className="watch-grid">{items.map((stock) => { const quote = quotes[stock.id]; return <article className="watch-card" key={stock.id}><div className="watch-card-top"><div className="ticker-avatar large">{stock.ticker.slice(0, 2)}</div><button className="icon-button danger" title="Remove stock" onClick={() => remove(stock.id)} disabled={busy === String(stock.id)}>{busy === String(stock.id) ? <LoaderCircle className="spin" size={16}/> : <Trash2 size={16}/>}</button></div><h3>{stock.company_name}</h3><div className="watch-meta"><b>{stock.ticker}</b><span>{stock.market}</span></div><div className="watch-quote">{quote?.price == null ? 'Live quote unavailable' : `${quote.currency || ''} ${Number(quote.price).toLocaleString(undefined, { maximumFractionDigits: 2 })}`} {quote?.change_percent != null && <em className={quote.change_percent < 0 ? 'negative' : ''}>{Number(quote.change_percent).toFixed(2)}%</em>}</div><div className="watch-date">Saved {new Date(stock.created_at).toLocaleDateString()}</div><button className="subtle-btn full" onClick={() => research(stock)} disabled={busy === `research-${stock.id}`}>{busy === `research-${stock.id}` ? <LoaderCircle className="spin" size={15}/> : <ArrowUpRight size={15}/>} Start research</button></article>; })}</div>}
    </>
  );
}
