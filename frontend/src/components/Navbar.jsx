import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Zap, Clock, User, LogOut, Key, Menu, X, Settings } from 'lucide-react';
import BackendModal from './BackendModal';
import './Navbar.css';

export default function Navbar() {
  const loc = useLocation();
  const [user, setUser] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    const handleOpenSettings = () => setShowSettings(true);
    window.addEventListener('open_backend_modal', handleOpenSettings);
    return () => window.removeEventListener('open_backend_modal', handleOpenSettings);
  }, []);

  useEffect(() => {
    const loadUser = () => {
      try {
        const raw = localStorage.getItem('trustlens_user');
        if (raw) setUser(JSON.parse(raw));
        else setUser(null);
      } catch {
        setUser(null);
      }
    };
    loadUser();

    window.addEventListener('authChange', loadUser);
    window.addEventListener('storage', loadUser);
    return () => {
      window.removeEventListener('authChange', loadUser);
      window.removeEventListener('storage', loadUser);
    };
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [loc.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('trustlens_user');
    setUser(null);
    window.dispatchEvent(new Event('authChange'));
    setMobileMenuOpen(false);
  };

  const active = (path) => loc.pathname === path ? 'nav-link active' : 'nav-link';
  const mobileActive = (path) => loc.pathname === path ? 'mobile-nav-link active' : 'mobile-nav-link';

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="nav-brand" onClick={() => setMobileMenuOpen(false)}>
          <div className="brand-icon">
            <Shield size={20} />
          </div>
          <span className="brand-text">
            Trust<span className="text-neon-cyan">Lens</span>
            <span className="brand-ai"> AI</span>
          </span>
        </Link>

        {/* Desktop Navigation Links */}
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

        {/* Desktop Action Buttons */}
        <div className="nav-actions">
          <button
            type="button"
            className="nav-settings-btn"
            onClick={() => setShowSettings(true)}
            title="Configure Backend Connection"
            id="nav-settings-btn"
          >
            <Settings size={15} />
          </button>

          {user ? (
            <div className="nav-user-badge">
              <div className="user-avatar-circle">
                <User size={13} className="text-neon-cyan" />
              </div>
              <div className="user-meta-info">
                <span className="user-name-text">{user.name || 'Operative'}</span>
                <span className="user-status-text">
                  <span className="user-status-dot" /> ACTIVE
                </span>
              </div>
              <button 
                type="button" 
                onClick={handleLogout} 
                className="nav-logout-btn" 
                title="Disconnect session"
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <Link to="/login" className="nav-login-link" id="nav-login-btn">
              <Key size={14} />
              <span>Log In</span>
            </Link>
          )}

          <Link to="/analyze" className="btn btn-primary nav-cta" id="nav-scan-btn">
            <Shield size={14} />
            <span>Start Scan</span>
          </Link>

          {/* Mobile Hamburger Button */}
          <button
            type="button"
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(prev => !prev)}
            aria-label="Toggle mobile navigation menu"
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Animated Dropdown Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer">
          <div className="mobile-nav-links">
            <Link to="/" className={mobileActive('/')} onClick={() => setMobileMenuOpen(false)}>
              <Zap size={18} className="text-neon-cyan" />
              <span>Home Overview</span>
            </Link>
            <Link to="/analyze" className={mobileActive('/analyze')} onClick={() => setMobileMenuOpen(false)}>
              <Shield size={18} className="text-neon-cyan" />
              <span>Forensic Scanner</span>
            </Link>
            <Link to="/history" className={mobileActive('/history')} onClick={() => setMobileMenuOpen(false)}>
              <Clock size={18} className="text-neon-cyan" />
              <span>Scan Telemetry</span>
            </Link>
            <Link to="/login" className={mobileActive('/login')} onClick={() => setMobileMenuOpen(false)}>
              <Key size={18} className="text-neon-magenta" />
              <span>{user ? 'Operative Terminal' : 'Sign In / Register'}</span>
            </Link>
            <button
              type="button"
              className="mobile-settings-btn"
              onClick={() => {
                setShowSettings(true);
                setMobileMenuOpen(false);
              }}
            >
              <Settings size={18} className="text-neon-cyan" />
              <span>Backend Connection</span>
            </button>
          </div>

          <div className="mobile-drawer-footer">
            {user ? (
              <div className="mobile-user-row">
                <div className="mobile-user-details">
                  <User size={16} className="text-neon-cyan" />
                  <span className="mobile-user-name">{user.name}</span>
                  <span className="mobile-user-pill">ACTIVE</span>
                </div>
                <button type="button" onClick={handleLogout} className="mobile-logout-btn">
                  <LogOut size={14} /> Sign Out
                </button>
              </div>
            ) : (
              <Link to="/login" className="mobile-signin-btn" onClick={() => setMobileMenuOpen(false)}>
                Operative Sign In
              </Link>
            )}
            <Link to="/analyze" className="btn btn-primary mobile-scan-cta" onClick={() => setMobileMenuOpen(false)}>
              Start Threat Scan
            </Link>
          </div>
        </div>
      )}

      {/* Global Backend Gateway Settings Modal */}
      <BackendModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </nav>
  );
}



