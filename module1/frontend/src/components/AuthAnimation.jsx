import { useEffect, useRef } from "react";
import { useTheme } from "../ThemeContext.jsx";

// Looping animated candlestick chart for the sign-in / register pages (canvas, no video file needed).
// ILLUSTRATIVE only - random data, not real prices. Pauses when the tab is hidden; static if the user prefers reduced motion.
const CANDLE_W = 14, GAP = 8, STEP = CANDLE_W + GAP, SPEED = 0.35; // px per frame

function nextCandle(prev) {
  const open = prev.close;
  const close = open + (Math.random() - 0.47) * 7;
  const high = Math.max(open, close) + Math.random() * 4;
  const low = Math.min(open, close) - Math.random() * 4;
  return { open, close, high, low };
}

// Panel palette per theme (white text sits on top of it in both).
const PALETTES = {
  light: { bg: ["#2f5fe0", "#6a3fd8"], grid: "rgba(255,255,255,0.12)", up: "#86efac", down: "#fda4af", line: "#ffffff", glow: "#c7d6ff",
           orbs: ["rgba(125,211,252,0.55)", "rgba(196,181,253,0.55)", "rgba(249,168,212,0.45)"] },
  dark: { bg: ["#070d1f", "#14275f"], grid: "rgba(255,255,255,0.06)", up: "#4ade80", down: "#f87171", line: "#93c5fd", glow: "#60a5fa",
          orbs: ["rgba(59,108,240,0.45)", "rgba(139,92,246,0.4)", "rgba(34,211,238,0.3)"] },
};

export default function AuthAnimation() {
  const ref = useRef(null);
  const { theme } = useTheme();
  const themeRef = useRef(theme);
  themeRef.current = theme; // read inside the animation loop - toggling the theme does not restart it

  useEffect(() => {
    const canvas = ref.current, ctx = canvas.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0, h = 0, raf = 0, offset = 0, candles = [], t0 = 0;

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const need = Math.ceil(w / STEP) + 3;
      if (!candles.length) candles = [{ open: 100, close: 100, high: 102, low: 98 }];
      while (candles.length < need) candles.push(nextCandle(candles[candles.length - 1]));
    }

    function draw() {
      const P = PALETTES[themeRef.current] || PALETTES.dark;
      ctx.clearRect(0, 0, w, h);
      const g = ctx.createLinearGradient(0, 0, w, h);
      g.addColorStop(0, P.bg[0]); g.addColorStop(1, P.bg[1]);
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);

      // gently floating glow orbs
      const tt = (performance.now() - t0) / 1000;
      P.orbs.forEach((c, i) => {
        const r = Math.min(w, h) * (0.32 + i * 0.05);
        const x = w * (0.2 + 0.3 * i) + Math.sin(tt * (0.25 + i * 0.07) + i * 2) * w * 0.08;
        const y = h * (0.25 + 0.2 * i) + Math.cos(tt * (0.2 + i * 0.05) + i) * h * 0.06;
        const og = ctx.createRadialGradient(x, y, 0, x, y, r);
        og.addColorStop(0, c); og.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = og; ctx.fillRect(0, 0, w, h);
      });

      ctx.strokeStyle = P.grid; ctx.lineWidth = 1;
      for (let y = h * 0.1; y < h; y += h / 8) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

      const vis = candles.slice(0, Math.ceil(w / STEP) + 2);
      const lo = Math.min(...vis.map((c) => c.low)), hi = Math.max(...vis.map((c) => c.high));
      const top = h * 0.66, bottom = h * 0.96, y = (v) => bottom - ((v - lo) / (hi - lo || 1)) * (bottom - top);

      vis.forEach((c, i) => {
        const x = i * STEP - offset, up = c.close >= c.open;
        ctx.strokeStyle = ctx.fillStyle = up ? P.up : P.down;
        ctx.globalAlpha = 0.85;
        ctx.beginPath(); ctx.moveTo(x + CANDLE_W / 2, y(c.high)); ctx.lineTo(x + CANDLE_W / 2, y(c.low)); ctx.stroke();
        const yo = y(c.open), yc = y(c.close);
        ctx.fillRect(x, Math.min(yo, yc), CANDLE_W, Math.max(Math.abs(yo - yc), 1.5));
      });
      ctx.globalAlpha = 1;

      // glowing moving-average style line over the candles
      ctx.strokeStyle = P.line; ctx.lineWidth = 2.5; ctx.shadowColor = P.glow; ctx.shadowBlur = 12;
      ctx.beginPath();
      vis.forEach((c, i) => { const x = i * STEP - offset + CANDLE_W / 2, avg = (c.open + c.close) / 2; i ? ctx.lineTo(x, y(avg)) : ctx.moveTo(x, y(avg)); });
      ctx.stroke(); ctx.shadowBlur = 0; ctx.lineWidth = 1;
    }

    function frame() {
      offset += SPEED;
      if (offset >= STEP) { offset -= STEP; candles.shift(); candles.push(nextCandle(candles[candles.length - 1])); }
      draw();
      raf = requestAnimationFrame(frame);
    }
    const onVisibility = () => { cancelAnimationFrame(raf); if (!document.hidden && !reduce) raf = requestAnimationFrame(frame); };

    t0 = performance.now();
    resize(); draw();
    if (!reduce) raf = requestAnimationFrame(frame);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", onVisibility);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); document.removeEventListener("visibilitychange", onVisibility); };
  }, [theme]);

  return <canvas ref={ref} className="absolute inset-0 h-full w-full" aria-hidden="true" />;
}
