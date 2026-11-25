import { MARKETS } from "../constants";

export default function EmptyState({ onPick }) {
  return (
    <section className="panel empty-state">
      <h2>Pick a stock to see its data</h2>
      <p>Search above, or open an example from each exchange.</p>
      <div className="market-tiles">
        {MARKETS.map((m) => (
          <button key={m.id} className="tile" onClick={() => onPick({ ticker: m.example, market: m.id })}>
            <strong>{m.id}</strong>
            <span>{m.full}</span>
            <span>Try {m.example}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
