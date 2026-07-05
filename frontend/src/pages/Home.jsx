import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Image, Volume2, Video, MessageSquare, Mail, ArrowRight, Zap } from 'lucide-react';
import './Home.css';

const FEATURES = [
  {
    icon: <Image size={24} />,
    title: 'Image Deepfake',
    desc: 'Error Level Analysis, EXIF metadata inspection, color distribution fingerprinting.',
    color: 'var(--cyan)',
    glow: 'var(--cyan-glow)',
    border: 'var(--cyan-border)',
  },
  {
    icon: <Volume2 size={24} />,
    title: 'Audio Deepfake',
    desc: 'Spectral flatness, MFCC consistency, pitch monotonicity, silence pattern analysis.',
    color: 'var(--purple)',
    glow: 'var(--purple-glow)',
    border: 'rgba(123,47,255,0.3)',
  },
  {
    icon: <Video size={24} />,
    title: 'Video Deepfake',
    desc: 'Frame-by-frame ELA sampling, temporal inconsistency detection, artifact scoring.',
    color: 'var(--magenta)',
    glow: 'var(--magenta-glow)',
    border: 'rgba(255,0,110,0.3)',
  },
  {
    icon: <MessageSquare size={24} />,
    title: 'Scam SMS',
    desc: 'Urgency phrases, reward lures, threat language, brand impersonation detection.',
    color: 'var(--yellow)',
    glow: 'rgba(255,214,0,0.1)',
    border: 'rgba(255,214,0,0.3)',
  },
  {
    icon: <Mail size={24} />,
    title: 'Email Phishing',
    desc: 'URL risk scoring, credential harvesting patterns, spoofing signatures.',
    color: 'var(--green)',
    glow: 'var(--green-glow)',
    border: 'rgba(0,255,136,0.3)',
  },
  {
    icon: <Zap size={24} />,
    title: 'Explainable AI',
    desc: 'Every score is broken down into evidence cards with per-factor contribution.',
    color: 'var(--orange)',
    glow: 'rgba(255,107,0,0.1)',
    border: 'rgba(255,107,0,0.3)',
  },
];

const STATS = [
  { value: '5', label: 'Detection Modes' },
  { value: '0', label: 'API Keys Needed' },
  { value: '100%', label: 'Local & Private' },
  { value: '∞', label: 'Explainable Results' },
];

export default function Home() {
  return (
    <div className="home-page">
      {/* Hero */}
      <section className="hero">
        <div className="hero-badge animate-fadeInUp">
          <Shield size={14} /> AI-Powered Threat Detection
        </div>
        <h1 className="hero-title animate-fadeInUp" style={{ animationDelay: '0.1s' }}>
          <span className="text-gradient">TrustLens AI</span>
          <br />
          <span className="hero-subtitle-line">See Through the Fake</span>
        </h1>
        <p className="hero-description animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
          Upload any image, audio, video, SMS or email and receive an instant deepfake
          probability score, scam risk analysis, and actionable safety recommendations —
          all powered by explainable AI running entirely on your machine.
        </p>
        <div className="hero-ctas animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
          <Link to="/analyze" id="hero-analyze-btn" className="btn btn-primary hero-cta-main">
            Start Analyzing <ArrowRight size={18} />
          </Link>
          <Link to="/history" className="btn btn-secondary">
            View History
          </Link>
        </div>

        {/* Stats */}
        <div className="stats-row animate-fadeInUp" style={{ animationDelay: '0.4s' }}>
          {STATS.map((s, i) => (
            <div key={i} className="stat-card">
              <span className="stat-value text-neon-cyan">{s.value}</span>
              <span className="stat-desc">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Scan Types */}
      <section className="features-section container">
        <div className="section-header">
          <p className="section-eyebrow">Detection Capabilities</p>
          <h2>What Can TrustLens Detect?</h2>
          <p className="section-desc">
            Six AI-powered detection modules working in concert to identify threats across all media types.
          </p>
        </div>
        <div className="features-grid">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="feature-card glass-card animate-fadeInUp"
              style={{ animationDelay: `${i * 0.08}s` }}
            >
              <div
                className="feature-icon"
                style={{ color: f.color, background: f.glow, border: `1px solid ${f.border}` }}
              >
                {f.icon}
              </div>
              <h3 className="feature-title" style={{ color: f.color }}>{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Banner */}
      <section className="cta-banner">
        <div className="cta-banner-inner glass-card">
          <div className="cta-glow" />
          <h2>Ready to Protect Yourself?</h2>
          <p>Analyze your first file in seconds — no signup, no API key, no data sent to the cloud.</p>
          <Link to="/analyze" id="cta-banner-btn" className="btn btn-primary">
            Launch Scanner <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
