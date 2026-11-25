// Split card: coloured panel on the left, form on the right.
function ring(cx, cy, r, seed) {
  const pts = [];
  for (let i = 0; i <= 120; i++) {
    const t = (i / 120) * Math.PI * 2;
    const wob = 1 + 0.1 * Math.sin(3 * t + seed) + 0.06 * Math.sin(5 * t + seed * 1.7) + 0.035 * Math.sin(8 * t + seed * 0.6);
    pts.push(`${(cx + Math.cos(t) * r * wob * 1.15).toFixed(1)},${(cy + Math.sin(t) * r * wob).toFixed(1)}`);
  }
  return `M${pts.join("L")}Z`;
}

const CLUSTERS = [
  { cx: 120, cy: 470, n: 13, step: 26, seed: 0.4 },
  { cx: 330, cy: 150, n: 8, step: 22, seed: 2.1 },
  { cx: 300, cy: 560, n: 6, step: 20, seed: 4.0 },
];
const PATHS = CLUSTERS.flatMap((c) =>
  Array.from({ length: c.n }, (_, i) => ring(c.cx, c.cy, 14 + i * c.step, c.seed + i * 0.18))
);

function ContourArt() {
  return (
    <svg className="auth-contours" viewBox="0 0 420 640" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {PATHS.map((d, i) => <path key={i} d={d} />)}
    </svg>
  );
}

export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth-wrap">
      <div className="auth-split">
        <aside className="auth-art" aria-hidden="true">
          <ContourArt />
          <h2 className="auth-tagline">Multi-agent stock research</h2>
          <div className="auth-art-foot">
            <span className="auth-bar" />
            <span>EquityLens</span>
          </div>
        </aside>

        <section className="auth-panel">
          <h1 className="auth-title">{title}</h1>
          <p className="auth-sub">{subtitle}</p>
          {children}
          <p className="auth-foot">{footer}</p>
        </section>
      </div>
    </div>
  );
}
