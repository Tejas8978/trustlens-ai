import { useState, useEffect } from 'react';
import { Settings, CheckCircle2, AlertTriangle, XCircle, RotateCcw, X, ExternalLink, Activity, Server } from 'lucide-react';
import { getApiUrl, setApiUrl, resetApiUrl, testApiUrl, DEFAULT_FALLBACK_URL } from '../api/config';
import './BackendModal.css';

export default function BackendModal({ isOpen, onClose }) {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('idle'); // 'idle' | 'testing' | 'success' | 'warning' | 'error'
  const [statusMsg, setStatusMsg] = useState('');
  const [latency, setLatency] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setUrl(getApiUrl());
      setStatus('idle');
      setStatusMsg('');
      setLatency(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  async function handleTest(testTarget) {
    const target = (testTarget !== undefined ? testTarget : url).trim();
    setStatus('testing');
    setStatusMsg('Pinging backend endpoint...');
    setLatency(null);

    const result = await testApiUrl(target);
    setLatency(result.latency);

    if (result.ok) {
      const dbInfo = result.data?.database ? ` · Database: ${result.data.database.toUpperCase()}` : '';
      setStatus('success');
      setStatusMsg(`Connected successfully! Server is live and healthy (${result.latency}ms${dbInfo}).`);
    } else if (result.status === 502 || result.status === 503 || result.timeout) {
      setStatus('warning');
      setStatusMsg(
        'Render container is spinning up (free tier cold start). Please wait 30 seconds and test again.'
      );
    } else if (result.status === 404 && result.noServer) {
      setStatus('error');
      setStatusMsg(
        'Render edge reported "no-server" (404). This service name does not exist on Render. Please check your Render dashboard URL.'
      );
    } else {
      setStatus('error');
      setStatusMsg(result.error || 'Connection failed. Verify the URL and ensure the server is active.');
    }
  }

  function handleSave() {
    setApiUrl(url.trim());
    onClose();
  }

  function handleReset() {
    resetApiUrl();
    setUrl(getApiUrl());
    setStatus('idle');
    setStatusMsg('');
  }

  function handleApplyPreset(presetUrl) {
    setUrl(presetUrl);
    handleTest(presetUrl);
  }

  return (
    <div className="backend-modal-overlay" onClick={onClose}>
      <div className="backend-modal-card glass-card" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="backend-modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge">
              <Server size={18} className="text-neon-cyan" />
            </div>
            <div>
              <h3 className="modal-title">Backend Connection Settings</h3>
              <p className="modal-subtitle">Configure TrustLens AI API Gateway</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="backend-modal-body">
          <div className="input-group">
            <label className="input-field-label">
              <span>Backend API URL</span>
              <span className="label-badge">CORS Enabled</span>
            </label>
            <div className="url-input-wrapper">
              <input
                type="text"
                className="cyber-input url-input"
                value={url}
                onChange={e => {
                  setUrl(e.target.value);
                  setStatus('idle');
                }}
                placeholder="https://your-service.onrender.com"
                spellCheck="false"
              />
              <button
                type="button"
                className="btn btn-secondary test-btn"
                onClick={() => handleTest()}
                disabled={status === 'testing'}
              >
                <Activity size={14} className={status === 'testing' ? 'spin-icon' : ''} />
                {status === 'testing' ? 'Pinging...' : 'Test Ping'}
              </button>
            </div>
          </div>

          {/* Test Status Banner */}
          {status !== 'idle' && (
            <div className={`status-banner status-${status}`}>
              <div className="status-banner-icon">
                {status === 'testing' && <Activity size={16} className="spin-icon" />}
                {status === 'success' && <CheckCircle2 size={16} />}
                {status === 'warning' && <AlertTriangle size={16} />}
                {status === 'error' && <XCircle size={16} />}
              </div>
              <div className="status-banner-text">
                <p className="status-msg">{statusMsg}</p>
                {latency && <span className="latency-tag">⚡ {latency}ms</span>}
              </div>
            </div>
          )}

          {/* Quick Presets */}
          <div className="presets-section">
            <span className="presets-label">Quick Presets:</span>
            <div className="presets-grid">
              <button
                type="button"
                className="preset-chip"
                onClick={() => handleApplyPreset('https://trustlens-backend.onrender.com')}
              >
                Render: trustlens-backend
              </button>
              <button
                type="button"
                className="preset-chip"
                onClick={() => handleApplyPreset('http://localhost:8000')}
              >
                Local Dev: localhost:8000
              </button>
              <button
                type="button"
                className="preset-chip"
                onClick={() => handleApplyPreset('')}
              >
                Vite Proxy / Same Origin
              </button>
            </div>
          </div>

          {/* Helper Guide */}
          <div className="render-help-box">
            <div className="help-box-header">
              <ExternalLink size={14} className="text-neon-cyan" />
              <span>How to find your active Render URL</span>
            </div>
            <ol className="help-steps">
              <li>Open your <strong>Render Dashboard</strong> at <a href="https://dashboard.render.com" target="_blank" rel="noreferrer">dashboard.render.com</a></li>
              <li>Click your <strong>trustlens-backend</strong> web service.</li>
              <li>Check the service status: if it says <em>Sleeping</em>, making a request will wake it in ~30–50s.</li>
              <li>Copy the HTTPS link located directly below the service name (e.g., <code>https://trustlens-backend-xxxx.onrender.com</code>) and paste it above.</li>
            </ol>
          </div>
        </div>

        {/* Footer */}
        <div className="backend-modal-footer">
          <button type="button" className="btn btn-secondary reset-btn" onClick={handleReset}>
            <RotateCcw size={14} /> Reset
          </button>
          <div className="footer-actions">
            <button type="button" className="btn btn-secondary cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="button" className="btn btn-primary save-btn" onClick={handleSave}>
              Save & Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
