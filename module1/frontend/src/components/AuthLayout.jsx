import AuthAnimation from "./AuthAnimation.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* animated brand panel - desktop only */}
      <aside className="relative hidden overflow-hidden lg:block">
        <AuthAnimation />
        <div className="relative z-10 flex h-full flex-col justify-between p-10 text-white">
          <div className="flex items-center gap-2 text-lg font-semibold"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15 backdrop-blur">📈</span>Stock Research Analyst</div>
          <div className="mb-40 max-w-md">
            <h2 className="reveal text-3xl font-semibold leading-tight" style={{ "--i": 1 }}>Research stocks with a team of AI agents.</h2>
            <ul className="mt-4 space-y-2 text-sm text-blue-100">
              <li className="reveal" style={{ "--i": 3 }}>• Prices, profiles and financials for NSE, BSE, NASDAQ and NYSE</li>
              <li className="reveal" style={{ "--i": 4 }}>• Every data source and retrieval time recorded</li>
              <li className="reveal" style={{ "--i": 5 }}>• Your watchlist and research history, private to you</li>
            </ul>
          </div>
          <p className="text-xs text-blue-200/70">Animation is illustrative, not real market data.</p>
        </div>
      </aside>

      <div className="relative flex items-center justify-center px-4 py-10">
        <ThemeToggle className="absolute right-4 top-4" />
        <div className="w-full max-w-md">
          <div className="reveal mb-6 text-center" style={{ "--i": 0 }}>
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-xl text-white lg:hidden">📈</div>
            <h1 className="text-2xl font-semibold">{title}</h1>
            <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
          </div>
          <div className="card reveal" style={{ "--i": 1 }}>{children}</div>
          <p className="reveal mt-4 text-center text-sm text-slate-600" style={{ "--i": 2 }}>{footer}</p>
        </div>
      </div>
    </div>
  );
}

export function Alert({ kind = "error", children }) {
  const styles = kind === "error" ? "border-red-200 bg-red-50 text-red-700" : kind === "success" ? "border-green-200 bg-green-50 text-green-700" : "border-amber-200 bg-amber-50 text-amber-800";
  return <div role="alert" className={`rounded-lg border px-3 py-2 text-sm ${styles}`}>{children}</div>;
}

export function Field({ label, error, ...props }) {
  return (
    <div>
      <label className="label" htmlFor={props.name}>{label}</label>
      <input id={props.name} className={`input ${error ? "border-red-400" : ""}`} {...props} />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
