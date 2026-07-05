import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Zap, Clock } from 'lucide-react';
import './Navbar.css';

export default function Navbar() {
  const loc = useLocation();
  const active = (path) => loc.pathname === path ? 'nav-link active' : 'nav-link';

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

        <Link to="/analyze" className="btn btn-primary nav-cta" id="nav-scan-btn">
          Start Scan
        </Link>
      </div>
    </nav>
  );
}
