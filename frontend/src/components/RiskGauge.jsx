import { useEffect, useRef, useState } from 'react';
import './RiskGauge.css';

const VERDICT_META = {
  SAFE:      { label: 'SAFE',      color: '#00FF88', glow: 'rgba(0,255,136,0.35)',  icon: '✓', cls: 'gauge-safe' },
  SUSPICIOUS:{ label: 'SUSPICIOUS',color: '#FFD600', glow: 'rgba(255,214,0,0.35)',  icon: '⚠', cls: 'gauge-warn' },
  HIGH_RISK: { label: 'HIGH RISK', color: '#FF2052', glow: 'rgba(255,32,82,0.45)',  icon: '✕', cls: 'gauge-danger' },
};

// SVG arc helper
function describeArc(cx, cy, r, startDeg, endDeg) {
  const toRad = d => (d * Math.PI) / 180;
  const x1 = cx + r * Math.cos(toRad(startDeg));
  const y1 = cy + r * Math.sin(toRad(startDeg));
  const x2 = cx + r * Math.cos(toRad(endDeg));
  const y2 = cy + r * Math.sin(toRad(endDeg));
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
}

export default function RiskGauge({ score = 0, verdict = 'SAFE' }) {
  const [displayScore, setDisplayScore] = useState(0);
  const animRef = useRef(null);
  const meta = VERDICT_META[verdict] || VERDICT_META.SAFE;

  // Animate score counter from 0 → target
  useEffect(() => {
    let start = null;
    const duration = 1400;
    const from = 0;
    const to = score;

    cancelAnimationFrame(animRef.current);

    function step(ts) {
      if (!start) start = ts;
      const elapsed = ts - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(from + (to - from) * eased));
      if (progress < 1) animRef.current = requestAnimationFrame(step);
    }

    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [score]);

  // SVG dimensions
  const SIZE   = 200;
  const CX     = 100;
  const CY     = 108;
  const R      = 78;
  const START  = 150;   // degrees — bottom-left
  const RANGE  = 240;   // degrees of arc span

  const trackEnd  = START + RANGE;
  const fillFrac  = Math.min(displayScore / 100, 1);
  const fillEnd   = START + RANGE * fillFrac;

  // Circumference of a circle at radius R — used for the ring glow
  const C = 2 * Math.PI * R;
  const fillDash = (fillFrac * C * (RANGE / 360)).toFixed(2);
  const gapDash  = C.toFixed(2);

  return (
    <div className={`risk-gauge-wrapper ${meta.cls}`}>
      {/* Outer glow ring (animated pulse) */}
      <div className="gauge-glow-ring" style={{ '--glow-color': meta.glow, '--arc-color': meta.color }} />

      <svg
        className="risk-gauge-svg"
        viewBox={`0 0 ${SIZE} ${SIZE + 10}`}
        width={SIZE}
        height={SIZE + 10}
        aria-label={`Risk score: ${score}% — ${meta.label}`}
      >
        <defs>
          <linearGradient id={`arcGrad-${verdict}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor={meta.color} stopOpacity="0.6" />
            <stop offset="100%" stopColor={meta.color} stopOpacity="1" />
          </linearGradient>
          <filter id="arcGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Track arc */}
        <path
          d={describeArc(CX, CY, R, START, trackEnd)}
          fill="none"
          stroke="rgba(0,245,255,0.07)"
          strokeWidth="14"
          strokeLinecap="round"
        />

        {/* Zone tints: safe / warn / danger */}
        <path d={describeArc(CX, CY, R, START, START + RANGE * 0.40)} fill="none" stroke="rgba(0,255,136,0.12)"  strokeWidth="14" />
        <path d={describeArc(CX, CY, R, START + RANGE * 0.40, START + RANGE * 0.70)} fill="none" stroke="rgba(255,214,0,0.12)"  strokeWidth="14" />
        <path d={describeArc(CX, CY, R, START + RANGE * 0.70, trackEnd)}              fill="none" stroke="rgba(255,32,82,0.12)"   strokeWidth="14" />

        {/* Filled arc */}
        {fillFrac > 0 && (
          <path
            d={describeArc(CX, CY, R, START, fillEnd)}
            fill="none"
            stroke={`url(#arcGrad-${verdict})`}
            strokeWidth="14"
            strokeLinecap="round"
            filter="url(#arcGlow)"
            className="gauge-fill-arc"
          />
        )}

        {/* Needle dot at arc tip */}
        {fillFrac > 0 && (
          <>
            <circle
              cx={CX + R * Math.cos((fillEnd * Math.PI) / 180)}
              cy={CY + R * Math.sin((fillEnd * Math.PI) / 180)}
              r="9"
              fill={meta.color}
              filter="url(#arcGlow)"
              className="gauge-needle-dot"
            />
            <circle
              cx={CX + R * Math.cos((fillEnd * Math.PI) / 180)}
              cy={CY + R * Math.sin((fillEnd * Math.PI) / 180)}
              r="4"
              fill="white"
              opacity="0.8"
            />
          </>
        )}

        {/* Center score */}
        <text
          x={CX} y={CY - 8}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="38"
          fontWeight="800"
          fontFamily="'Space Grotesk', sans-serif"
          fill={meta.color}
          className="gauge-score-text"
        >
          {displayScore}
        </text>
        <text
          x={CX} y={CY + 22}
          textAnchor="middle"
          fontSize="10"
          fontWeight="600"
          fontFamily="'Space Mono', monospace"
          fill="rgba(232,244,255,0.45)"
          letterSpacing="2"
        >
          RISK SCORE
        </text>

        {/* Zone labels */}
        <text x={CX - 44} y={CY + R + 18} textAnchor="middle" fontSize="9" fontFamily="'Space Mono', monospace" fill="rgba(0,255,136,0.55)">SAFE</text>
        <text x={CX + 44} y={CY + R + 18} textAnchor="middle" fontSize="9" fontFamily="'Space Mono', monospace" fill="rgba(255,32,82,0.55)">DANGER</text>
      </svg>

      {/* Verdict badge */}
      <div className={`gauge-verdict-badge ${meta.cls}`}>
        <span className="gauge-verdict-icon">{meta.icon}</span>
        <span className="gauge-verdict-label">{meta.label}</span>
        <span className="gauge-verdict-dot" />
      </div>
    </div>
  );
}
