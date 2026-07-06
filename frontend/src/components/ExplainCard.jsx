import { useState } from 'react';
import { ChevronDown, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';
import './ExplainCard.css';

const SEVERITY_ICONS = {
  high: <AlertTriangle size={14} />,
  medium: <AlertCircle size={14} />,
  low: <CheckCircle size={14} />,
};

function EvidenceBar({ contribution }) {
  const pct = Math.round(contribution * 100);
  let color = '#00FF88';
  if (pct > 60) color = '#FF2052';
  else if (pct > 30) color = '#FFD600';

  return (
    <div className="evidence-bar-row">
      <div className="score-bar-track" style={{ flex: 1 }}>
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 8px ${color}` }}
        />
      </div>
      <span className="evidence-pct" style={{ color }}>{pct}%</span>
    </div>
  );
}

export default function ExplainCard({ evidence = [] }) {
  const [open, setOpen] = useState(null);

  return (
    <div className="explain-card">
      <h3 className="explain-title">
        <span className="text-neon-cyan">⬡</span> Explainable AI Evidence
      </h3>
      <p className="explain-subtitle">
        Each factor's contribution to the final risk score
      </p>
      <div className="evidence-list">
        {evidence.map((item, i) => (
          <div key={i} className="accordion-item">
            <div
              className="accordion-header"
              onClick={() => setOpen(open === i ? null : i)}
              id={`evidence-item-${i}`}
            >
              <div className="evidence-label-row">
                <span className={`severity-${item.severity}`}>
                  {SEVERITY_ICONS[item.severity]}
                </span>
                <span className="evidence-label">{item.label}</span>
              </div>
              <div className="evidence-header-right">
                <EvidenceBar contribution={item.risk_contribution} />
                <ChevronDown
                  size={16}
                  className={`chevron ${open === i ? 'open' : ''}`}
                />
              </div>
            </div>
            {open === i && (
              <div className="accordion-body evidence-detail">
                <p className="evidence-value">{item.value}</p>
                <div className="evidence-meta">
                  <span className={`verdict-badge verdict-${
                    item.severity === 'high' ? 'HIGH_RISK' :
                    item.severity === 'medium' ? 'SUSPICIOUS' : 'SAFE'
                  }`}>
                    {item.severity.toUpperCase()} SEVERITY
                  </span>
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Contribution: {Math.round(item.risk_contribution * 100)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
