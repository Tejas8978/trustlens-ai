import React, { useEffect, useRef } from 'react';
import './RiskGauge.css';

const VERDICT_LABELS = {
  SAFE: { label: 'SAFE', color: '#00FF88' },
  SUSPICIOUS: { label: 'SUSPICIOUS', color: '#FFD600' },
  HIGH_RISK: { label: 'HIGH RISK', color: '#FF2052' },
};

function getScoreColor(score) {
  if (score >= 70) return '#FF2052';
  if (score >= 40) return '#FFD600';
  return '#00FF88';
}

export default function RiskGauge({ score = 0, verdict = 'SAFE' }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const currentScore = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const SIZE = 220;
    canvas.width = SIZE;
    canvas.height = SIZE;

    const cx = SIZE / 2;
    const cy = SIZE / 2 + 20;
    const R = 80;
    const START = Math.PI;
    const END = 2 * Math.PI;

    const target = score;
    const color = getScoreColor(score);

    function drawGauge(val) {
      ctx.clearRect(0, 0, SIZE, SIZE);

      // Track
      ctx.beginPath();
      ctx.arc(cx, cy, R, START, END);
      ctx.strokeStyle = 'rgba(0,245,255,0.08)';
      ctx.lineWidth = 16;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Zone bands (subtle)
      const zones = [
        { end: 0.4, color: 'rgba(0,255,136,0.15)' },
        { end: 0.7, color: 'rgba(255,214,0,0.15)' },
        { end: 1.0, color: 'rgba(255,32,82,0.15)' },
      ];
      let prevFrac = 0;
      zones.forEach(z => {
        ctx.beginPath();
        ctx.arc(cx, cy, R, START + Math.PI * prevFrac, START + Math.PI * z.end);
        ctx.strokeStyle = z.color;
        ctx.lineWidth = 16;
        ctx.stroke();
        prevFrac = z.end;
      });

      // Fill arc
      if (val > 0) {
        const frac = val / 100;
        ctx.beginPath();
        ctx.arc(cx, cy, R, START, START + Math.PI * frac);
        ctx.strokeStyle = color;
        ctx.lineWidth = 16;
        ctx.lineCap = 'round';
        ctx.shadowBlur = 20;
        ctx.shadowColor = color;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // Needle dot
      const angle = START + Math.PI * (val / 100);
      const nx = cx + R * Math.cos(angle);
      const ny = cy + R * Math.sin(angle);
      ctx.beginPath();
      ctx.arc(nx, ny, 8, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.shadowBlur = 15;
      ctx.shadowColor = color;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Center score
      ctx.fillStyle = color;
      ctx.font = `bold 36px 'Space Grotesk', sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.shadowBlur = 10;
      ctx.shadowColor = color;
      ctx.fillText(Math.round(val), cx, cy - 10);
      ctx.shadowBlur = 0;

      ctx.fillStyle = 'rgba(232,244,255,0.5)';
      ctx.font = `500 11px 'Space Mono', monospace`;
      ctx.fillText('RISK SCORE', cx, cy + 14);
    }

    function animate() {
      const diff = target - currentScore.current;
      if (Math.abs(diff) < 0.5) {
        currentScore.current = target;
        drawGauge(target);
        return;
      }
      currentScore.current += diff * 0.06;
      drawGauge(currentScore.current);
      animRef.current = requestAnimationFrame(animate);
    }

    cancelAnimationFrame(animRef.current);
    animate();

    return () => cancelAnimationFrame(animRef.current);
  }, [score, verdict]);

  const v = VERDICT_LABELS[verdict] || VERDICT_LABELS.SAFE;

  return (
    <div className="risk-gauge-wrapper">
      <canvas ref={canvasRef} className="risk-gauge-canvas" />
      <div className={`verdict-badge verdict-${verdict} gauge-verdict`}>
        <span className="verdict-dot" />
        {v.label}
      </div>
    </div>
  );
}
