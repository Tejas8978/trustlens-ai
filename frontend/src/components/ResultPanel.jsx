import { useState } from 'react';
import RiskGauge from './RiskGauge';
import ExplainCard from './ExplainCard';
import {
  Shield,
  ChevronDown,
  Copy,
  Check,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  Printer,
  Download,
  Layers,
  Eye,
  Sliders,
  FileCheck,
} from 'lucide-react';
import './ResultPanel.css';

const TYPE_LABELS = {
  image: '🖼  Image Deepfake Detection',
  audio: '🎵  Audio Deepfake Detection',
  video: '🎬  Video Deepfake Detection',
  url:   '🌐  Phishing URL & Link Inspector',
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
  const [visualMode, setVisualMode] = useState('split'); // 'split' | 'ela' | 'original'
  const [sliderPos, setSliderPos]   = useState(50);

  if (!result) return null;

  const vc = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.SAFE;
  const hasEla = Boolean(result.visual_artifact);
  const hasOriginal = Boolean(result.previewUrl);

  function copyPrompt() {
    navigator.clipboard.writeText(result.ai_builder_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handlePrint() {
    window.print();
  }

  function handleDownloadJSON() {
    const reportData = {
      platform: 'TrustLens AI Forensic Auditor',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      report_id: `TL-${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
      scan_type: result.scan_type,
      filename: result.filename || 'n/a',
      risk_score: result.risk_score,
      verdict: result.verdict,
      summary: result.summary,
      evidence: result.evidence,
      recommendations: result.recommendations,
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trustlens-forensic-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
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

      {/* ── Action Toolbar: Export Audit Report & JSON ───── */}
      <div className="report-action-bar">
        <div className="report-badge-id">
          <FileCheck size={14} className="text-neon-cyan" />
          <span>Forensic Audit Verified</span>
        </div>
        <div className="report-action-buttons">
          <button
            id="print-report-btn"
            className="btn btn-secondary action-btn-sm"
            onClick={handlePrint}
            title="Print or export as PDF"
          >
            <Printer size={14} /> Print / PDF
          </button>
          <button
            id="download-json-btn"
            className="btn btn-secondary action-btn-sm"
            onClick={handleDownloadJSON}
            title="Download audit JSON file"
          >
            <Download size={14} /> JSON Audit
          </button>
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

      {/* ── Visual Forensics Inspector (ELA Heatmap) ─────── */}
      {hasEla && (
        <div className="glass-card visual-forensics-card result-section" style={{ animationDelay: '0.08s' }}>
          <div className="visual-forensics-header">
            <div className="flex items-center gap-2">
              <Layers size={18} className="text-neon-cyan" />
              <h3 className="visual-title">Visual Forensics: Error Level Analysis (ELA)</h3>
            </div>
            <div className="visual-controls">
              {hasOriginal && (
                <button
                  className={`btn-view-toggle ${visualMode === 'split' ? 'active' : ''}`}
                  onClick={() => setVisualMode('split')}
                >
                  <Sliders size={13} /> Split Slider
                </button>
              )}
              <button
                className={`btn-view-toggle ${visualMode === 'ela' ? 'active' : ''}`}
                onClick={() => setVisualMode('ela')}
              >
                <Eye size={13} /> ELA Heatmap
              </button>
              {hasOriginal && (
                <button
                  className={`btn-view-toggle ${visualMode === 'original' ? 'active' : ''}`}
                  onClick={() => setVisualMode('original')}
                >
                  Original
                </button>
              )}
            </div>
          </div>

          <p className="visual-explanation">
            Error Level Analysis highlights compression inconsistencies. Brighter regions or high-contrast noise boundaries indicate pixel tampering, spliced objects, or AI diffusion synthesis.
          </p>

          <div className="visual-viewer-container">
            {visualMode === 'split' && hasOriginal ? (
              <div className="split-slider-wrapper">
                <div className="split-image-container">
                  {/* Under layer: ELA Heatmap */}
                  <img
                    src={result.visual_artifact}
                    alt="ELA Heatmap"
                    className="split-img ela-layer"
                  />
                  {/* Top layer: Original image clipped by slider */}
                  <div
                    className="split-original-clipped"
                    style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
                  >
                    <img
                      src={result.previewUrl}
                      alt="Original Content"
                      className="split-img original-layer"
                    />
                  </div>
                  {/* Divider line */}
                  <div className="split-divider" style={{ left: `${sliderPos}%` }}>
                    <div className="split-handle">⇄</div>
                  </div>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={sliderPos}
                  onChange={e => setSliderPos(Number(e.target.value))}
                  className="split-range-input"
                  aria-label="Drag to compare original and ELA forensic heatmap"
                />
                <div className="split-labels">
                  <span>← Original Image ({sliderPos}%)</span>
                  <span>ELA Heatmap ({100 - sliderPos}%) →</span>
                </div>
              </div>
            ) : visualMode === 'original' && hasOriginal ? (
              <div className="single-img-view">
                <img src={result.previewUrl} alt="Original Image" className="single-inspect-img" />
                <span className="img-overlay-tag">Original Image</span>
              </div>
            ) : (
              <div className="single-img-view">
                <img src={result.visual_artifact} alt="Error Level Analysis" className="single-inspect-img" />
                <span className="img-overlay-tag ela-tag">ELA Heatmap (Manipulated Artifacts)</span>
              </div>
            )}
          </div>
        </div>
      )}

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
      <div className="glass-card prompt-card result-section no-print" style={{ animationDelay: '0.3s' }}>
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

