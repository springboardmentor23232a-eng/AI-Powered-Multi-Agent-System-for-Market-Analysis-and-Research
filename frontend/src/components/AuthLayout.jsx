export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-xl text-white">📈</div>
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        </div>
        <div className="card">{children}</div>
        <p className="mt-4 text-center text-sm text-slate-600">{footer}</p>
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
