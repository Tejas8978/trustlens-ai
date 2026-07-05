import React, { useState } from 'react';
import UploadCard from '../components/UploadCard';
import ResultPanel from '../components/ResultPanel';
import { Shield, Loader } from 'lucide-react';
import './Analyze.css';

export default function Analyze() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="analyze-page">
      <div className="analyze-header">
        <p className="analyze-eyebrow">
          <Shield size={14} /> Real-Time Threat Detection
        </p>
        <h1 className="analyze-title">
          Analyze <span className="text-gradient">Your Content</span>
        </h1>
        <p className="analyze-desc">
          Upload an image, audio, video or paste a message. TrustLens AI will
          scan it instantly and return an explainable risk report.
        </p>
      </div>

      <div className="analyze-layout">
        {/* Left: Upload */}
        <div className="analyze-left">
          <UploadCard onResult={setResult} onLoading={setLoading} />
        </div>

        {/* Right: Result */}
        <div className="analyze-right">
          {loading ? (
            <div className="scan-loading glass-card">
              <div className="scan-animation">
                <div className="scan-ring" />
                <div className="scan-ring scan-ring-2" />
                <div className="scan-ring scan-ring-3" />
                <Shield size={32} style={{ color: 'var(--cyan)' }} />
              </div>
              <h3>Analyzing...</h3>
              <p>Running deepfake detection algorithms</p>
              <div className="scan-steps">
                {['Loading file', 'Extracting features', 'Running analysis', 'Computing score'].map((s, i) => (
                  <div key={i} className="scan-step">
                    <div className="scan-step-dot" style={{ animationDelay: `${i * 0.4}s` }} />
                    {s}
                  </div>
                ))}
              </div>
            </div>
          ) : result ? (
            <ResultPanel result={result} />
          ) : (
            <div className="analyze-placeholder glass-card">
              <div className="placeholder-icon">
                <Shield size={48} />
              </div>
              <h3>Ready to Scan</h3>
              <p>Select a file type, upload your content, and click <strong>Analyze Now</strong> to see the risk report here.</p>
              <div className="placeholder-tips">
                <p className="tip">💡 Try pasting a suspicious SMS or email for instant scam detection</p>
                <p className="tip">💡 Upload any photo to check for AI generation artifacts</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
