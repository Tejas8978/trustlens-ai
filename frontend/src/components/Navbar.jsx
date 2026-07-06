import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Zap, Clock, Settings, Save, X } from 'lucide-react';
import './Navbar.css';

export default function Navbar() {
  const loc = useLocation();
  const active = (path) => loc.pathname === path ? 'nav-link active' : 'nav-link';
  const [showSettings, setShowSettings] = useState(false);
  const [backendUrl, setBackendUrl] = useState(
    localStorage.getItem('VITE_API_URL') || import.meta.env.VITE_API_URL || 'https://trustlens-backend.onrender.com'
  );

  function handleSave() {
    localStorage.setItem('VITE_API_URL', backendUrl);
    setShowSettings(false);
    window.location.reload();
  }

  function handleReset() {
    localStorage.removeItem('VITE_API_URL');
    setBackendUrl(import.meta.env.VITE_API_URL || 'https://trustlens-backend.onrender.com');
    window.location.reload();
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="nav-brand">
          <div className="brand-icon">
            <Shield size={20} />
          </div>
          <span className="brand-text">
            Trust<span className="text-neon-cyan">Lens</span>
            <span className="brand-ai"> AI</span>
          </span>
        </Link>

        <div className="nav-links">
          <Link to="/" className={active('/')}>
            <Zap size={15} /> Home
          </Link>
          <Link to="/analyze" className={active('/analyze')}>
            <Shield size={15} /> Analyze
          </Link>
          <Link to="/history" className={active('/history')}>
            <Clock size={15} /> History
          </Link>
        </div>

        <div className="nav-actions" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Settings Trigger */}
          <div className="settings-container" style={{ position: 'relative' }}>
            <button
              className="btn btn-secondary btn-icon"
              onClick={() => setShowSettings(!showSettings)}
              title="Configure Backend URL"
              style={{ padding: '8px' }}
            >
              <Settings size={16} />
            </button>

            {showSettings && (
              <div className="settings-dropdown glass-card">
                <div className="settings-header">
                  <h4>⚙️ Backend Configuration</h4>
                  <button className="close-btn" onClick={() => setShowSettings(false)}>
                    <X size={14} />
                  </button>
                </div>
                <div className="settings-body">
                  <label className="settings-label">Backend API URL</label>
                  <input
                    type="text"
                    className="cyber-input"
                    value={backendUrl}
                    onChange={(e) => setBackendUrl(e.target.value)}
                    placeholder="https://your-backend.onrender.com"
                    style={{ fontSize: '0.8rem', padding: '6px var(--space-3)' }}
                  />
                  <p className="settings-hint">
                    {window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
                      ? "💡 Note: On localhost, this config is ignored to use local proxy."
                      : "Saves to your browser storage and reloads."
                    }
                  </p>
                </div>
                <div className="settings-footer">
                  <button className="btn btn-secondary text-xs" onClick={handleReset} style={{ padding: '4px 10px' }}>
                    Reset
                  </button>
                  <button className="btn btn-primary text-xs" onClick={handleSave} style={{ padding: '4px 10px' }}>
                    <Save size={12} /> Save
                  </button>
                </div>
              </div>
            )}
          </div>

          <Link to="/analyze" className="btn btn-primary nav-cta" id="nav-scan-btn">
            Start Scan
          </Link>
        </div>
      </div>
    </nav>
  );
}

