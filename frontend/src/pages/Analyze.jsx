import { useState, useEffect } from 'react';
import UploadCard from '../components/UploadCard';
import ResultPanel from '../components/ResultPanel';
import { Shield } from 'lucide-react';
import './Analyze.css';

const SCAN_STEPS = [
  'Initializing scan engine…',
  'Loading & decoding content…',
  'Extracting forensic features…',
  'Running detection algorithms…',
  'Applying risk model…',
  'Generating report…',
];

function RadarLoader() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep(s => Math.min(s + 1, SCAN_STEPS.length - 1));
    }, 900);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="scan-loading glass-card">
      {/* Radar animation */}
      <div className="radar-container">
        <div className="radar-ring radar-ring-1" />
        <div className="radar-ring radar-ring-2" />
        <div className="radar-ring radar-ring-3" />
        <div className="radar-sweep" />
        <div className="radar-center">
          <Shield size={28} />
        </div>
        {/* Blip dots */}
        <div className="radar-blip blip-1" />
        <div className="radar-blip blip-2" />
        <div className="radar-blip blip-3" />
      </div>

      <h3 className="scan-title">Scanning Content</h3>
      <p className="scan-subtitle">TrustLens AI is analyzing for threats</p>

      {/* Step list */}
      <div className="scan-steps">
        {SCAN_STEPS.map((s, i) => (
          <div
            key={i}
            className={`scan-step ${i < activeStep ? 'step-done' : i === activeStep ? 'step-active' : 'step-pending'}`}
          >
            <span className="step-indicator">
              {i < activeStep  ? '✓' :
               i === activeStep ? <span className="step-spinner" /> :
               '○'}
            </span>
            <span className="step-label">{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Analyze() {
  const [result,  setResult]  = useState(null);
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
            <RadarLoader />
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
