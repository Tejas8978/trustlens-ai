import { useState } from 'react';
import RiskGauge from './RiskGauge';
import ExplainCard from './ExplainCard';
import { Shield, ChevronDown, Copy, Check, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';
import './ResultPanel.css';

const TYPE_LABELS = {
  image: '🖼  Image Deepfake Detection',
  audio: '🎵  Audio Deepfake Detection',
  video: '🎬  Video Deepfake Detection',
  sms:   '📱  SMS Scam Analysis',
  email: '📧  Email Phishing Detection',
};

const VERDICT_CONFIG = {
  SAFE: {
    icon:    <CheckCircle size={22} />,
    heading: 'Content Appears Safe',
    tagline: 'No significant threats detected. Stay vigilant.',
    cls:     'vstate-safe',
  },
  SUSPICIOUS: {
    icon:    <AlertCircle size={22} />,
    heading: 'Suspicious Activity Detected',
    tagline: 'Multiple red flags found. Treat with caution.',
    cls:     'vstate-warn',
  },
  HIGH_RISK: {
    icon:    <AlertTriangle size={22} />,
    heading: 'HIGH RISK — Likely Fraud or Deepfake',
    tagline: 'Do NOT interact with this content. Block & report immediately.',
    cls:     'vstate-danger',
  },
};

export default function ResultPanel({ result }) {
  const [promptOpen, setPromptOpen] = useState(false);
  const [copied, setCopied]         = useState(false);

  if (!result) return null;

  const vc = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.SAFE;

  function copyPrompt() {
    navigator.clipboard.writeText(result.ai_builder_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className={`result-panel animate-fadeInUp ${vc.cls}`} data-verdict={result.verdict}>

      {/* ── Verdict Banner ─────────────────────────────────── */}
      <div className="verdict-banner">
        <span className="verdict-banner-icon">{vc.icon}</span>
        <div className="verdict-banner-text">
          <strong className="verdict-banner-heading">{vc.heading}</strong>
          <span className="verdict-banner-tagline">{vc.tagline}</span>
        </div>
        <div className="verdict-banner-score">
          <span className="vb-score-num">{result.risk_score}%</span>
          <span className="vb-score-label">RISK</span>
        </div>
      </div>

      {/* ── Header: summary + gauge ─────────────────────────── */}
      <div className="result-header glass-card">
        <div className="result-header-left">
          <p className="result-type-label">
            {TYPE_LABELS[result.scan_type] || result.scan_type}
          </p>
          {result.filename && (
            <p className="result-filename">
              <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>
                {result.filename}
              </span>
            </p>
          )}
          <p className="result-summary">{result.summary}</p>
        </div>
        <div className="result-gauge">
          <RiskGauge score={result.risk_score} verdict={result.verdict} />
        </div>
      </div>

      {/* ── Evidence ────────────────────────────────────────── */}
      <div className="glass-card result-section" style={{ animationDelay: '0.1s' }}>
        <ExplainCard evidence={result.evidence} />
      </div>

      {/* ── Recommendations ────────────────────────────────── */}
      <div className="glass-card recommendations-card result-section" style={{ animationDelay: '0.2s' }}>
        <h3 className="rec-title">
          <Shield size={18} className="text-neon-cyan" /> Safety Recommendations
        </h3>
        <ul className="rec-list">
          {result.recommendations.map((r, i) => (
            <li key={i} className="rec-item" style={{ animationDelay: `${0.25 + i * 0.08}s` }}>
              <span className={`rec-dot ${
                result.verdict === 'HIGH_RISK'   ? 'dot-red'    :
                result.verdict === 'SUSPICIOUS'  ? 'dot-yellow' : 'dot-green'
              }`} />
              {r}
            </li>
          ))}
        </ul>
      </div>

      {/* ── AI Builder Prompt ──────────────────────────────── */}
      <div className="glass-card prompt-card result-section" style={{ animationDelay: '0.3s' }}>
        <div
          className="accordion-header prompt-header"
          onClick={() => setPromptOpen(!promptOpen)}
          id="ai-builder-prompt-toggle"
        >
          <div className="flex items-center gap-3">
            <span className="prompt-badge">AI</span>
            <span className="prompt-title">AI Builder Prompt</span>
            <span className="text-xs opacity-60" style={{ color: 'var(--text-muted)' }}>
              Replicate this detection with your own AI
            </span>
          </div>
          <ChevronDown size={16} className={`chevron ${promptOpen ? 'open' : ''}`} style={{ color: 'var(--text-muted)' }} />
        </div>
        {promptOpen && (
          <div className="accordion-body prompt-body">
            <pre className="prompt-text">{result.ai_builder_prompt}</pre>
            <button
              id="copy-prompt-btn"
              className="btn btn-secondary copy-btn"
              onClick={copyPrompt}
            >
              {copied ? <><Check size={14} /> Copied!</> : <><Copy size={14} /> Copy Prompt</>}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
