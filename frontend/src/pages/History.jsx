import { useEffect, useState } from 'react';
import { ArrowUpRight, Clock3, Search } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import api from '../services/api';

const fmt = (date) => new Date(date).toLocaleString(undefined, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

export default function History() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [report, setReport] = useState(null);
  const location = useLocation();

  useEffect(() => {
    api.get('/research/history').then(({ data }) => setItems(data)).catch((err) => setError(err.response?.data?.detail || 'Unable to load research history.'));
  }, []);

  const open = async (item) => {
    if (!item.report_available) {
      setError('A report is not available for this task yet.');
      return;
    }
    try {
      const { data } = await api.get(`/research/${item.id}/report`);
      setReport(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Report unavailable.');
    }
  };

  const filtered = items.filter((item) => (filter === 'all' || item.status === filter) && `${item.company_name} ${item.ticker}`.toLowerCase().includes(query.toLowerCase()));

  return (
    <>
      <div className="page-heading"><div><div className="eyebrow">YOUR ACTIVITY</div><h1>Research history</h1><p>Every stock research task associated with your account.</p></div></div>
      {location.state?.created && <div className="alert success">Research task created and saved. It is currently pending until the analysis workflow is connected.</div>}
      {error && <div className="alert info">{error}</div>}
      <section className="surface-card table-card"><div className="table-toolbar"><div className="search-input-wrap table-search"><Search size={17}/><input placeholder="Search company or ticker" value={query} onChange={(event) => setQuery(event.target.value)}/></div><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">All statuses</option><option value="pending">Pending</option><option value="processing">Processing</option><option value="completed">Completed</option><option value="failed">Failed</option></select></div>
        {filtered.length === 0 ? <div className="empty-state"><div className="empty-icon"><Clock3 size={22}/></div><b>No matching research</b><p>Your created research tasks will be listed here.</p></div> : <div className="table-scroll"><table><thead><tr><th>COMPANY</th><th>MARKET</th><th>ANALYSIS PERIOD</th><th>RESEARCH DATE</th><th>STATUS</th><th>REPORT</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td><div className="company-cell"><div className="ticker-avatar">{item.ticker.slice(0, 2)}</div><div><b>{item.company_name}</b><small>{item.ticker}</small></div></div></td><td>{item.market}</td><td>{item.analysis_period}</td><td>{fmt(item.created_at)}</td><td><span className={`status-pill ${item.status}`}>{item.status}</span></td><td><button className="table-action" disabled={!item.report_available} onClick={() => open(item)}>{item.report_available ? <>Open <ArrowUpRight size={14}/></> : 'Unavailable'}</button></td></tr>)}</tbody></table></div>}
      </section>
      {report && <div className="modal-backdrop" onClick={() => setReport(null)}><div className="report-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setReport(null)}>×</button><div className="eyebrow">RESEARCH REPORT</div><h2>Research report</h2><pre>{JSON.stringify(report, null, 2)}</pre></div></div>}
    </>
  );
}
