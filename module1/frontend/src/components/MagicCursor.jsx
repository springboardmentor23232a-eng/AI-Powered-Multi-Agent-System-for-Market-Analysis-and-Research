import { useEffect, useRef, useState } from "react";

// "Magic cursor": a dot + a lagging ring that grows over clickable things, plus a short sparkle trail.
// Desktop only ((hover:hover) and (pointer:fine)), never with prefers-reduced-motion, and the user can switch it off.
const LINK = "a,button,[role=tab],[role=button],select,label,summary";
const TEXT = "input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]),textarea,[contenteditable=true]";
const KEY = "magicCursor";

function eligible() {
  return typeof window !== "undefined" && window.matchMedia("(hover: hover) and (pointer: fine)").matches
    && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
function savedOn() {
  try { return localStorage.getItem(KEY) !== "off"; } catch { return true; }
}

export default function MagicCursor() {
  const [ok] = useState(eligible);
  const [on, setOn] = useState(savedOn);
  const dot = useRef(null), ring = useRef(null), canvas = useRef(null);

  useEffect(() => {
    if (!ok || !on) return;
    document.body.classList.add("magic-cursor");
    const ctx = canvas.current.getContext("2d");
    const m = { x: -100, y: -100, rx: -100, ry: -100, lastX: -100, lastY: -100, seen: false };
    let particles = [], raf = 0, w = 0, h = 0;

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth; h = window.innerHeight;
      canvas.current.width = w * dpr; canvas.current.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function ringState(t) {
      const r = ring.current; if (!r) return;
      const el = t instanceof Element ? t : null;
      r.classList.toggle("is-text", !!el?.closest(TEXT));
      r.classList.toggle("is-link", !!el && !el.closest(TEXT) && !!el.closest(LINK));
    }
    function onMove(e) {
      m.x = e.clientX; m.y = e.clientY;
      if (!m.seen) { m.seen = true; m.rx = m.x; m.ry = m.y; m.lastX = m.x; m.lastY = m.y; dot.current.classList.remove("is-hidden"); ring.current.classList.remove("is-hidden"); }
      const dx = m.x - m.lastX, dy = m.y - m.lastY;
      if (dx * dx + dy * dy > 144) { // emit a sparkle every ~12px of travel
        m.lastX = m.x; m.lastY = m.y;
        const dark = document.documentElement.classList.contains("dark");
        const hues = dark ? [215, 265, 190] : [225, 265, 195];
        particles.push({ x: m.x, y: m.y, vx: (Math.random() - .5) * 1.2, vy: (Math.random() - .5) * 1.2 - .2,
                         r: 1.5 + Math.random() * 2.2, life: 1, hue: hues[(Math.random() * 3) | 0], dark });
        if (particles.length > 60) particles.shift();
      }
    }
    const onOver = (e) => ringState(e.target);
    const onDown = () => ring.current?.classList.add("is-down");
    const onUp = () => ring.current?.classList.remove("is-down");
    const onLeave = () => { dot.current?.classList.add("is-hidden"); ring.current?.classList.add("is-hidden"); m.seen = false; };

    function frame() {
      m.rx += (m.x - m.rx) * 0.18; m.ry += (m.y - m.ry) * 0.18;
      dot.current.style.transform = `translate3d(${m.x}px,${m.y}px,0)`;
      ring.current.style.transform = `translate3d(${m.rx}px,${m.ry}px,0)`;
      ctx.clearRect(0, 0, w, h);
      particles = particles.filter((p) => p.life > 0.02);
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy; p.life *= 0.93;
        ctx.globalAlpha = p.life * 0.8;
        ctx.fillStyle = `hsl(${p.hue} ${p.dark ? 90 : 75}% ${p.dark ? 72 : 52}%)`;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (0.5 + p.life * 0.5), 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    }
    const onVis = () => { cancelAnimationFrame(raf); if (!document.hidden) raf = requestAnimationFrame(frame); };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMove, { passive: true });
    document.addEventListener("mouseover", onOver, { passive: true });
    window.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    document.documentElement.addEventListener("mouseleave", onLeave);
    document.addEventListener("visibilitychange", onVis);
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      document.body.classList.remove("magic-cursor");
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseover", onOver);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      document.documentElement.removeEventListener("mouseleave", onLeave);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [ok, on]);

  if (!ok) return null;
  const flip = () => setOn((v) => { const n = !v; try { localStorage.setItem(KEY, n ? "on" : "off"); } catch { /* ignore */ } return n; });
  return (
    <>
      {on && (
        <div aria-hidden="true">
          <canvas ref={canvas} className="cursor-canvas" />
          <div ref={ring} className="cursor-ring is-hidden" />
          <div ref={dot} className="cursor-dot is-hidden" />
        </div>
      )}
      <button type="button" onClick={flip} aria-pressed={on} title={on ? "Turn off the magic cursor" : "Turn on the magic cursor"}
              className="cursor-toggle btn-ghost !rounded-full !px-3 !py-1 text-xs shadow-md">
        ✨ cursor {on ? "on" : "off"}
      </button>
    </>
  );
}
