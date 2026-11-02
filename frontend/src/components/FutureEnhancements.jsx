import React, { useState } from 'react';
import { 
  Network, 
  Video, 
  Server, 
  AlertCircle, 
  Sparkles, 
  Layers, 
  CheckCircle2, 
  ArrowUpRight, 
  Cpu, 
  ShieldCheck,
  Zap,
  ChevronRight
} from 'lucide-react';
import './FutureEnhancements.css';

export default function FutureEnhancements() {
  const [activeModal, setActiveModal] = useState(null);

  const enhancements = [
    {
      id: 'extension',
      icon: <Network className="fe-icon" size={26} />,
      badgeBg: 'var(--fe-badge-teal)',
      cardTheme: 'fe-card-light',
      title: 'Browser extension',
      desc: 'A real-time Chrome / Firefox extension that automatically scans images and links while browsing social-media feeds.',
      tag: 'Chrome / Firefox V3',
      specs: [
        'MutationObserver for dynamic feed scanning (X, Instagram, LinkedIn, Reddit)',
        'Zero-latency hash matching against known scam image signatures',
        'Background WebWorker for off-thread forensic analysis',
        'In-line threat warning badges directly overlaid on suspicious media'
      ]
    },
    {
      id: 'webrtc',
      icon: <Video className="fe-icon" size={26} />,
      badgeBg: 'var(--fe-badge-mint)',
      cardTheme: 'fe-card-dark',
      title: 'Live video-call inspection',
      desc: 'WebRTC integration to analyze Zoom / Teams streams for real-time face-swap detection.',
      tag: 'WebRTC & MediaStream API',
      specs: [
        'Continuous 30fps facial landmark temporal tracking',
        'Blink-rate irregularity & gaze-shift consistency scoring',
        'Spectral audio-visual sync to catch synthetic lip sync lag',
        'Virtual camera & OBS virtual device injection interception'
      ]
    },
    {
      id: 'webhooks',
      icon: <Server className="fe-icon" size={26} />,
      badgeBg: 'var(--fe-badge-teal)',
      cardTheme: 'fe-card-light',
      title: 'Enterprise webhooks',
      desc: 'Automated ingestion pipelines for Slack and Microsoft Teams that block phishing attacks in transit.',
      tag: 'Slack & Teams Apps',
      specs: [
        'Inbound message & attachment event webhook handlers',
        'Real-time homoglyph & credential-harvesting quarantine',
        'Automated SOC alert notifications with instant forensic breakdown',
        'One-click remediation to purge malicious links across workspace'
      ]
    }
  ];

  return (
    <section className="future-enhancements-section container" id="defense-future">
      {/* Slide Header */}
      <div className="fe-header animate-fadeInUp">
        <div className="fe-eyebrow">
          <span className="fe-eyebrow-num">08</span>
          <span className="fe-eyebrow-text">DEFENSE & FUTURE</span>
        </div>
        <h2 className="fe-title">Future Enhancements</h2>
      </div>

      {/* Slide Board Container */}
      <div className="fe-board glass-card animate-fadeInUp" style={{ animationDelay: '0.15s' }}>
        {/* Row 1: Top 3 Cards */}
        <div className="fe-grid-top">
          {enhancements.map((item) => (
            <div 
              key={item.id} 
              className={`fe-card ${item.cardTheme}`}
              onClick={() => setActiveModal(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') setActiveModal(item); }}
            >
              <div className="fe-card-header">
                <div className="fe-icon-circle" style={{ background: item.badgeBg }}>
                  {item.icon}
                </div>
                <span className="fe-pill-tag">{item.tag}</span>
              </div>
              <h3 className="fe-card-title">{item.title}</h3>
              <p className="fe-card-desc">{item.desc}</p>
              
              <div className="fe-card-footer">
                <span className="fe-details-hint">
                  Explore architecture <ChevronRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Row 2: Bottom 2 Cards (Limitation & Research) */}
        <div className="fe-grid-bottom">
          {/* Card 4: Current limitation */}
          <div className="fe-card fe-card-limitation">
            <div className="fe-limitation-header">
              <span className="fe-label-limitation">Current limitation</span>
            </div>
            <p className="fe-limitation-desc">
              Aggressive re-compression by social platforms weakens EXIF tags and fine PRNU sensor noise.
            </p>
            <div className="fe-meta-note">
              <span>Photo-Response Non-Uniformity (PRNU) degradation under lossy JPEG / AVIF re-encoding</span>
            </div>
          </div>

          {/* Card 5: Research direction */}
          <div className="fe-card fe-card-dark fe-card-research">
            <div className="fe-research-header">
              <span className="fe-label-research">Research direction</span>
            </div>
            <p className="fe-research-desc">
              Video temporal 3D-CNNs (Video Swin Transformers) and live C2PA blockchain verification of media authenticity.
            </p>
            <div className="fe-research-tags">
              <span className="fe-tech-badge"><Cpu size={12} /> Video Swin Transformers</span>
              <span className="fe-tech-badge"><ShieldCheck size={12} /> C2PA Content Credentials</span>
            </div>
          </div>
        </div>
      </div>

      {/* Architecture Detail Modal */}
      {activeModal && (
        <div className="fe-modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="fe-modal glass-card" onClick={(e) => e.stopPropagation()}>
            <div className="fe-modal-header">
              <div className="fe-modal-title-group">
                <div className="fe-icon-circle" style={{ background: activeModal.badgeBg }}>
                  {activeModal.icon}
                </div>
                <div>
                  <span className="fe-eyebrow-text">TECHNICAL ARCHITECTURE SPEC</span>
                  <h3>{activeModal.title}</h3>
                </div>
              </div>
              <button 
                type="button" 
                className="fe-modal-close" 
                onClick={() => setActiveModal(null)}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="fe-modal-body">
              <p className="fe-modal-summary">{activeModal.desc}</p>
              
              <h4 className="fe-modal-section-title">
                <Zap size={16} /> Implementation Pipeline
              </h4>
              <ul className="fe-specs-list">
                {activeModal.specs.map((spec, idx) => (
                  <li key={idx}>
                    <CheckCircle2 size={16} className="text-neon-cyan" />
                    <span>{spec}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="fe-modal-footer">
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={() => setActiveModal(null)}
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
