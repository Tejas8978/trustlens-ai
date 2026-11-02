import React from 'react';
import { Download, ShieldCheck, CheckCircle2, Copy, ExternalLink, X, AlertTriangle } from 'lucide-react';
import './ExtensionModal.css';

function ChromeIcon({ size = 24, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="4" />
      <line x1="21.17" y1="8" x2="12" y2="8" />
      <line x1="3.95" y1="6.06" x2="8.54" y2="14" />
      <line x1="10.88" y1="21.94" x2="15.46" y2="14" />
    </svg>
  );
}

export default function ExtensionModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="ext-modal-backdrop" onClick={onClose}>
      <div className="ext-modal glass-card" onClick={(e) => e.stopPropagation()}>
        <div className="ext-modal-header">
          <div className="ext-modal-title-group">
            <div className="ext-icon-badge">
              <Chrome size={24} className="text-neon-cyan" />
            </div>
            <div>
              <span className="ext-subtitle">REAL-TIME BROWSER SHIELD</span>
              <h3 className="ext-title">TrustLens AI Chrome Extension</h3>
            </div>
          </div>
          <button type="button" className="ext-close-btn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="ext-modal-body">
          <p className="ext-intro">
            Protect your social media feeds, emails, and browsing sessions in real-time. Automatically scans 
            images, links, and text on <strong>X/Twitter, Reddit, LinkedIn, Facebook</strong>, and web pages for deepfakes and phishing.
          </p>

          {/* Download Action Box */}
          <div className="ext-download-box">
            <div className="ext-download-info">
              <span className="ext-badge">Manifest V3 Ready</span>
              <h4>TrustLens Shield v1.0.0</h4>
              <p>Works on Google Chrome, Microsoft Edge, Brave, Opera & Chromium browsers.</p>
            </div>
            <a 
              href="/trustlens-extension.zip" 
              download="trustlens-ai-extension.zip"
              className="btn btn-primary ext-download-btn"
              id="download-extension-zip-btn"
            >
              <Download size={18} /> Download Extension (.zip)
            </a>
          </div>

          {/* 3 Step Installation Guide */}
          <div className="ext-steps-container">
            <h4 className="ext-steps-heading">
              <ShieldCheck size={16} className="text-neon-cyan" /> 3-Step Setup Instructions
            </h4>

            <div className="ext-step-card">
              <div className="step-num">1</div>
              <div className="step-content">
                <strong>Extract the Zip</strong>
                <p>Unzip the downloaded <code>trustlens-ai-extension.zip</code> file to a folder on your computer.</p>
              </div>
            </div>

            <div className="ext-step-card">
              <div className="step-num">2</div>
              <div className="step-content">
                <strong>Open Extensions & Enable Developer Mode</strong>
                <p>In your browser address bar, navigate to:</p>
                <div className="ext-code-row">
                  <code>chrome://extensions</code>
                  <button 
                    type="button" 
                    className="ext-copy-btn"
                    onClick={() => handleCopy('chrome://extensions')}
                    title="Copy to clipboard"
                  >
                    <Copy size={13} /> Copy
                  </button>
                </div>
                <p className="step-note">Toggle on <strong>Developer mode</strong> in the top-right corner of the page.</p>
              </div>
            </div>

            <div className="ext-step-card">
              <div className="step-num">3</div>
              <div className="step-content">
                <strong>Click "Load unpacked" & Select Folder</strong>
                <p>Click the <strong>Load unpacked</strong> button in the top-left, and choose the extracted extension folder.</p>
              </div>
            </div>
          </div>

          <div className="ext-features-summary">
            <div className="ext-feat-item">
              <CheckCircle2 size={15} className="text-neon-green" />
              <span>Auto-scans dynamic social feeds</span>
            </div>
            <div className="ext-feat-item">
              <CheckCircle2 size={15} className="text-neon-green" />
              <span>Flags homoglyph phishing domains</span>
            </div>
            <div className="ext-feat-item">
              <CheckCircle2 size={15} className="text-neon-green" />
              <span>Right-click context menu "Scan with TrustLens"</span>
            </div>
          </div>
        </div>

        <div className="ext-modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
