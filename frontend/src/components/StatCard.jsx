export default function StatCard({ label, value, icon: Icon, tone = 'accent', sub }) {
  const tones = {
    accent: 'text-soc-accent border-soc-accent/30',
    success: 'text-soc-green border-soc-green/30',
    warning: 'text-soc-warning border-soc-warning/30',
    danger: 'text-soc-danger border-soc-danger/30',
    muted: 'text-soc-muted border-soc-border',
  }
  return (
    <div className={`bg-soc-panel border rounded-xl p-5 ${tones[tone] ?? tones.accent}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-soc-muted">{label}</span>
        {Icon && <Icon size={20} className="opacity-70" />}
      </div>
      <div className="mt-2 text-3xl font-bold text-slate-100">{value ?? '—'}</div>
      {sub && <div className="mt-1 text-xs text-soc-muted">{sub}</div>}
    </div>
  )
}
