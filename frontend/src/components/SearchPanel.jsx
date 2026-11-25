import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { MARKETS, PERIODS, POPULAR } from "../constants";
import { marketFromTicker } from "../format";
import Icon from "./Icon";

export default function SearchPanel({ prefs, saved, active, onView, onResearch, onAddWatch, inputRef }) {
  const [q, setQ] = useState(active?.ticker ?? "");
  const [market, setMarket] = useState(active?.market ?? prefs.market);
  const [period, setPeriod] = useState(prefs.analysis_period);
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const reqId = useRef(0);
  const touched = useRef(false); // true only while the user is typing; programmatic text never searches
  const prevPrefs = useRef(`${prefs.market}|${prefs.analysis_period}`);
  const boxRef = useRef(null);

  useEffect(() => {
    const key = `${prefs.market}|${prefs.analysis_period}`;
    if (prevPrefs.current === key) return;
    prevPrefs.current = key;
    setMarket(prefs.market);
    setPeriod(prefs.analysis_period);
  }, [prefs.market, prefs.analysis_period]);

  useEffect(() => {
    if (!touched.current) return;
    const term = q.trim();
    if (term.length < 2) {
      setResults([]);
      setErr("");
      return;
    }
    const id = ++reqId.current;
    const t = setTimeout(async () => {
      setBusy(true);
      setErr("");
      try {
        const data = await api(`/stocks/search?q=${encodeURIComponent(term)}`);
        if (id === reqId.current && touched.current) {
          setResults(data);
          setOpen(true);
        }
      } catch (e) {
        if (id === reqId.current && touched.current) {
          setErr(e.message);
          setOpen(true);
        }
      } finally {
        if (id === reqId.current) setBusy(false);
      }
    }, 350);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    const close = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const ticker = q.trim().toUpperCase();
  const isSaved = (t) => saved.some((s) => s.ticker === t);

  const pick = (item) => {
    touched.current = false;
    reqId.current++;
    setQ(item.ticker);
    setMarket(item.market);
    setOpen(false);
    onView(item);
  };
  const submit = (e) => {
    e.preventDefault();
    if (!ticker) return;
    setOpen(false);
    onView({ ticker, market });
  };
  const chip = (t) => {
    const m = marketFromTicker(t);
    touched.current = false;
    reqId.current++;
    setQ(t);
    setMarket(m);
    onView({ ticker: t, market: m });
  };

  return (
    <div className="panel" id="search">
      <form className="search-row" onSubmit={submit}>
        <div className="search-box" ref={boxRef}>
          <Icon name="search" className="search-icon" />
          <input
            ref={inputRef}
            className="input search-input"
            value={q}
            onChange={(e) => {
              touched.current = true;
              setQ(e.target.value);
            }}
            onFocus={() => (results.length || err) && setOpen(true)}
            placeholder="Company name or ticker, for example Infosys or INFY.NS"
            aria-label="Search stocks"
            autoComplete="off"
          />
          {open && (
            <div className="dropdown" role="listbox">
              {busy && <div className="dd-empty">Searching…</div>}
              {!busy && err && <div className="dd-empty">{err}</div>}
              {!busy && !err && results.length === 0 && (
                <div className="dd-empty">No matches. Try the exact ticker, for example TCS.NS.</div>
              )}
              {results.map((r) => (
                <div key={`${r.ticker}-${r.market}`} className="dd-row" onClick={() => pick(r)}>
                  <span className="ticker">{r.ticker}</span>
                  <span className="badge">{r.market}</span>
                  <span className="dd-main dd-name">{r.company_name}</span>
                  <button
                    type="button"
                    className="icon-btn"
                    title={isSaved(r.ticker) ? "In watchlist" : "Add to watchlist"}
                    aria-label="Add to watchlist"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!isSaved(r.ticker)) onAddWatch(r);
                    }}
                  >
                    <Icon name={isSaved(r.ticker) ? "check" : "bookmark"} />
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpen(false);
                      onResearch({ ...r, analysis_period: period });
                    }}
                  >
                    Research
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <label className="field-inline">
          Market
          <select className="select" value={market} onChange={(e) => setMarket(e.target.value)}>
            {MARKETS.map((m) => <option key={m.id} value={m.id}>{m.id}</option>)}
          </select>
        </label>
        <label className="field-inline">
          Period
          <select className="select" value={period} onChange={(e) => setPeriod(e.target.value)}>
            {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </label>
        <button
          type="button"
          className="btn btn-primary"
          disabled={!ticker}
          onClick={() => onResearch({ ticker, market, analysis_period: period })}
        >
          <Icon name="trend" /> Research
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={!ticker}
          onClick={() => onAddWatch({ ticker, market })}
        >
          <Icon name="bookmark" /> Watchlist
        </button>
      </form>

      <div className="chips">
        <span className="chips-label">Popular</span>
        {POPULAR.map((t) => (
          <button key={t} className="chip" onClick={() => chip(t)}>{t}</button>
        ))}
      </div>
      <p className="hint">Press Enter to view market data. Research runs the full workflow and saves a report.</p>
    </div>
  );
}
