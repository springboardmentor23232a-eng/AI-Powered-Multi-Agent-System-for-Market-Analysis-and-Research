import { useState, useEffect, useCallback } from 'react';
import { 
  registerUser, loginUser, getMyProfile, 
  getPreferences, updatePreferences, 
  getWatchlist, saveStock, deleteStock, 
  runResearch, getResearchHistory 
} from './services/api';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [isLoginView, setIsLoginView] = useState(true);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');

  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState({ preferred_market: 'NASDAQ', preferred_period: '1 Year' });
  const [watchlist, setWatchlist] = useState([]);
  const [newTicker, setNewTicker] = useState('');
  const [researchHistory, setResearchHistory] = useState([]);
  const [researchTicker, setResearchTicker] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogout = useCallback(() => {
    setToken('');
    localStorage.removeItem('token');
    setProfile(null);
  }, []);

  const fetchDashboardData = useCallback(async () => {
    try {
      const profRes = await getMyProfile();
      setProfile(profRes.data);
      const prefRes = await getPreferences();
      setPreferences(prefRes.data);
      const watchRes = await getWatchlist();
      setWatchlist(watchRes.data);
      const histRes = await getResearchHistory();
      setResearchHistory(histRes.data);
    } catch (err) {
      console.error(err);
      handleLogout();
    }
  }, [handleLogout]);

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      //eslint-disable-next-line react-hooks/set-state-in-effect
      fetchDashboardData();
    } else {
      localStorage.removeItem('token');
    }
  }, [token, fetchDashboardData]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isLoginView) {
        const res = await loginUser({ email, password });
        setToken(res.data.access_token);
      } else {
        await registerUser({ full_name: fullName, email, password });
        alert('Registration successful! Please log in.');
        setIsLoginView(true);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    }
  };

  const handleUpdatePrefs = async (e) => {
    e.preventDefault();
    try {
      const res = await updatePreferences(preferences);
      setPreferences(res.data);
      alert('Preferences updated successfully!');
    } catch {
      alert('Failed to update preferences');
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    if (!newTicker) return;
    try {
      await saveStock(newTicker);
      setNewTicker('');
      const watchRes = await getWatchlist();
      setWatchlist(watchRes.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save stock');
    }
  };

  const handleDeleteStock = async (id) => {
    try {
      await deleteStock(id);
      setWatchlist(watchlist.filter(item => item.saved_stock_id !== id));
    } catch {
      alert('Failed to remove stock');
    }
  };

  const handleRunResearch = async (e) => {
    e.preventDefault();
    if (!researchTicker) return;
    setLoading(true);
    try {
      await runResearch({ ticker: researchTicker });
      setResearchTicker('');
      const histRes = await getResearchHistory();
      setResearchHistory(histRes.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Research task failed');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="auth-container" style={{ padding: '40px', maxWidth: '400px', margin: 'auto', fontFamily: 'Arial' }}>
        <h2>{isLoginView ? 'Login to Stock Research' : 'Register Account'}</h2>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {!isLoginView && (
            <input 
              type="text" placeholder="Full Name" value={fullName} 
              onChange={(e) => setFullName(e.target.value)} required 
              style={{ padding: '10px' }}
            />
          )}
          <input 
            type="email" placeholder="Email Address" value={email} 
            onChange={(e) => setEmail(e.target.value)} required 
            style={{ padding: '10px' }}
          />
          <input 
            type="password" placeholder="Password" value={password} 
            onChange={(e) => setPassword(e.target.value)} required 
            style={{ padding: '10px' }}
          />
          <button type="submit" style={{ padding: '10px', background: '#007BFF', color: 'white', border: 'none', cursor: 'pointer' }}>
            {isLoginView ? 'Login' : 'Register'}
          </button>
        </form>
        <p style={{ marginTop: '15px', cursor: 'pointer', color: '#007BFF' }} onClick={() => setIsLoginView(!isLoginView)}>
          {isLoginView ? "Don't have an account? Register" : "Already have an account? Login"}
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard" style={{ padding: '30px', fontFamily: 'Arial', maxWidth: '1000px', margin: 'auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #ddd', paddingBottom: '15px' }}>
        <h1>📊 Stock Research Dashboard</h1>
        <div>
          <span style={{ marginRight: '15px' }}>Welcome, <b>{profile?.full_name}</b></span>
          <button onClick={handleLogout} style={{ padding: '8px 15px', background: '#dc3545', color: 'white', border: 'none', cursor: 'pointer' }}>Logout</button>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginTop: '20px' }}>
        <section style={{ background: '#f9f9f9', padding: '20px', borderRadius: '8px' }}>
          <h3>⚙️ User Preferences</h3>
          <form onSubmit={handleUpdatePrefs} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label>Preferred Market:</label>
            <select 
              value={preferences.preferred_market} 
              onChange={(e) => setPreferences({...preferences, preferred_market: e.target.value})}
              style={{ padding: '8px' }}
            >
              <option value="NASDAQ">NASDAQ</option>
              <option value="NYSE">NYSE</option>
              <option value="NSE">NSE</option>
              <option value="BSE">BSE</option>
            </select>

            <label>Analysis Period:</label>
            <select 
              value={preferences.preferred_period} 
              onChange={(e) => setPreferences({...preferences, preferred_period: e.target.value})}
              style={{ padding: '8px' }}
            >
              <option value="1 Month">1 Month</option>
              <option value="3 Months">3 Months</option>
              <option value="6 Months">6 Months</option>
              <option value="1 Year">1 Year</option>
              <option value="5 Years">5 Years</option>
            </select>
            <button type="submit" style={{ marginTop: '10px', padding: '8px', background: '#28a745', color: 'white', border: 'none', cursor: 'pointer' }}>Save Preferences</button>
          </form>
        </section>

        <section style={{ background: '#f9f9f9', padding: '20px', borderRadius: '8px' }}>
          <h3>⭐ My Watchlist</h3>
          <form onSubmit={handleAddStock} style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <input 
              type="text" placeholder="Enter Ticker (e.g. AAPL, RELIANCE)" 
              value={newTicker} onChange={(e) => setNewTicker(e.target.value)} 
              style={{ padding: '8px', flex: 1 }}
            />
            <button type="submit" style={{ padding: '8px 15px', background: '#007BFF', color: 'white', border: 'none', cursor: 'pointer' }}>Add</button>
          </form>
          <ul style={{ listStyle: 'none', padding: 0, maxHeight: '150px', overflowY: 'auto' }}>
            {watchlist.map(stock => (
              <li key={stock.saved_stock_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'white', marginBottom: '5px', borderRadius: '4px' }}>
                <span>{stock.ticker}</span>
                <button onClick={() => handleDeleteStock(stock.saved_stock_id)} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '2px 8px', cursor: 'pointer' }}>Remove</button>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section style={{ background: '#f9f9f9', padding: '20px', borderRadius: '8px', marginTop: '30px' }}>
        <h3>🔍 Run Stock Research</h3>
        <form onSubmit={handleRunResearch} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
          <input 
            type="text" placeholder="Ticker Symbol (e.g., TSLA, TCS)" 
            value={researchTicker} onChange={(e) => setResearchTicker(e.target.value)} 
            style={{ padding: '10px', flex: 1 }} required
          />
          <button type="submit" disabled={loading} style={{ padding: '10px 20px', background: '#ffc107', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
            {loading ? 'Running Research...' : 'Generate Report'}
          </button>
        </form>

        <h3>📜 Research History</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', maxHeight: '300px', overflowY: 'auto' }}>
          {researchHistory.map(task => (
            <div key={task.task_id} style={{ background: 'white', padding: '15px', borderRadius: '6px', borderLeft: '5px solid #007BFF' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <b>{task.company_name} ({task.ticker})</b>
                <span style={{ color: task.status === 'Completed' ? 'green' : 'red' }}>{task.status}</span>
              </div>
              <p style={{ margin: '5px 0', fontSize: '14px', color: '#555' }}>Market: {task.market} | Period: {task.analysis_period}</p>
              <pre style={{ background: '#f4f4f4', padding: '10px', borderRadius: '4px', whiteSpace: 'pre-wrap', fontSize: '13px' }}>{task.report_summary}</pre>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;