import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Shield, 
  Lock, 
  Mail, 
  User, 
  Key, 
  Eye, 
  EyeOff, 
  Zap, 
  Fingerprint, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight,
  Terminal,
  Cpu,
  Sparkles
} from 'lucide-react';
import './Login.css';

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [biometricScanning, setBiometricScanning] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Forensic Analyst',
    rememberMe: true,
  });

  // Calculate password strength (0-100)
  const calculateStrength = (pwd) => {
    if (!pwd) return 0;
    let score = 0;
    if (pwd.length >= 6) score += 25;
    if (pwd.length >= 10) score += 25;
    if (/[A-Z]/.test(pwd)) score += 25;
    if (/[0-9!@#$%^&*]/.test(pwd)) score += 25;
    return score;
  };
  const passwordStrength = calculateStrength(formData.password);

  const handleChange = (e) => {
    setError('');
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleQuickDemo = (role, email) => {
    setError('');
    setFormData({
      name: role,
      email: email,
      password: 'CyberSecurity#2026',
      role: role,
      rememberMe: true,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) {
      setError('Please provide all authentication credentials.');
      return;
    }
    if (isRegister && !formData.name) {
      setError('Please provide operative designation name.');
      return;
    }

    setIsLoading(true);
    setError('');

    // Simulate cyber authentication handshake
    setTimeout(() => {
      setIsLoading(false);
      setSuccess(true);
      const userProfile = {
        name: formData.name || formData.email.split('@')[0],
        email: formData.email,
        role: formData.role,
        authLevel: 'LEVEL 4 // CLEARANCE GRANTED',
        loggedInAt: new Date().toISOString()
      };
      localStorage.setItem('trustlens_user', JSON.stringify(userProfile));
      window.dispatchEvent(new Event('authChange'));

      setTimeout(() => {
        navigate('/analyze');
      }, 1400);
    }, 1200);
  };

  const handleBiometricAuth = () => {
    setBiometricScanning(true);
    setError('');
    setTimeout(() => {
      setBiometricScanning(false);
      setFormData(prev => ({
        ...prev,
        email: 'operative.lead@trustlens.ai',
        password: 'BiometricVerified#2026',
        name: 'Lead Cryptanalyst',
      }));
      setSuccess(true);
      const userProfile = {
        name: 'Lead Cryptanalyst',
        email: 'operative.lead@trustlens.ai',
        role: 'Biometric Authenticated Operative',
        authLevel: 'LEVEL 5 // BIOMETRIC MASTER',
        loggedInAt: new Date().toISOString()
      };
      localStorage.setItem('trustlens_user', JSON.stringify(userProfile));
      window.dispatchEvent(new Event('authChange'));

      setTimeout(() => {
        navigate('/analyze');
      }, 1300);
    }, 1500);
  };

  return (
    <div className="login-viewport">
      {/* Dynamic Cyber Ambient Glow Background Elements */}
      <div className="cyber-ambient-orb orb-cyan" />
      <div className="cyber-ambient-orb orb-magenta" />
      <div className="cyber-ambient-orb orb-purple" />
      <div className="cyber-grid-plane" />

      <div className="login-container">
        {/* Holographic Security Scanner Emblem */}
        <div className="scanner-badge-wrapper">
          <div className="radar-ring-outer">
            <div className="radar-ring-middle">
              <div className="radar-ring-inner">
                <Shield className="scanner-shield-icon" size={32} />
              </div>
            </div>
            <div className="radar-sweep-beam" />
          </div>
          <div className="scanner-title-group">
            <div className="terminal-badge">
              <Terminal size={12} className="text-neon-cyan" />
              <span>TERMINAL ID // TL-SEC-9081</span>
              <span className="live-dot" />
            </div>
            <h1 className="cyber-title">
              Trust<span className="text-neon-cyan">Lens</span>
              <span className="brand-ai"> AI</span>
            </h1>
            <p className="cyber-subtitle">NEURAL THREAT DETECTION & BIOMETRIC AUTHENTICATION</p>
          </div>
        </div>

        {/* Main Holographic Card */}
        <div className={`login-card ${success ? 'card-success' : ''}`}>
          {/* Laser scan line sweeping the card */}
          <div className="card-scanline" />

          {/* Card corner accents */}
          <div className="corner-bracket corner-tl" />
          <div className="corner-bracket corner-tr" />
          <div className="corner-bracket corner-bl" />
          <div className="corner-bracket corner-br" />

          {success ? (
            /* Animated Success Screen */
            <div className="auth-success-screen">
              <div className="success-pulse-circle">
                <CheckCircle2 size={56} className="success-icon" />
              </div>
              <h3 className="success-heading">CLEARANCE GRANTED</h3>
              <p className="success-desc">Neural cryptographic signature verified.</p>
              <div className="success-status-box">
                <span className="status-label">ENCRYPTION:</span>
                <span className="status-val">AES-GCM-256</span>
                <span className="status-label">AUTH TOKEN:</span>
                <span className="status-val">TLS-OK-8849F</span>
              </div>
              <div className="success-loading-bar">
                <div className="loading-fill" />
              </div>
              <span className="redirecting-text">INITIALIZING FORENSIC DASHBOARD...</span>
            </div>
          ) : (
            <>
              {/* Mode Toggle Pills */}
              <div className="auth-mode-pill-track">
                <button
                  type="button"
                  className={`auth-mode-btn ${!isRegister ? 'active' : ''}`}
                  onClick={() => { setIsRegister(false); setError(''); }}
                >
                  <Key size={14} />
                  <span>Operative Sign In</span>
                </button>
                <button
                  type="button"
                  className={`auth-mode-btn ${isRegister ? 'active' : ''}`}
                  onClick={() => { setIsRegister(true); setError(''); }}
                >
                  <User size={14} />
                  <span>New Operative</span>
                </button>
              </div>

              {/* 1-Click Demo Accounts */}
              <div className="demo-accounts-bar">
                <span className="demo-label">FAST DEMO CLEARANCE:</span>
                <div className="demo-pills">
                  <button
                    type="button"
                    className="demo-pill"
                    onClick={() => handleQuickDemo('Security Analyst', 'analyst@trustlens.ai')}
                  >
                    <Zap size={12} className="text-neon-cyan" />
                    <span>Analyst</span>
                  </button>
                  <button
                    type="button"
                    className="demo-pill"
                    onClick={() => handleQuickDemo('Forensic Specialist', 'forensics@trustlens.ai')}
                  >
                    <Shield size={12} className="text-neon-magenta" />
                    <span>Forensics</span>
                  </button>
                </div>
              </div>

              {error && (
                <div className="cyber-error-alert">
                  <AlertTriangle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Login / Register Form */}
              <form onSubmit={handleSubmit} className="auth-form">
                {isRegister && (
                  <div className="input-field-group">
                    <label className="field-label">OPERATIVE DESIGNATION</label>
                    <div className="cyber-input-wrapper">
                      <User size={16} className="input-icon" />
                      <input
                        type="text"
                        name="name"
                        placeholder="e.g. Agent Alex Vance"
                        value={formData.name}
                        onChange={handleChange}
                        className="cyber-input"
                        autoComplete="name"
                      />
                    </div>
                  </div>
                )}

                <div className="input-field-group">
                  <label className="field-label">NEURAL NETWORK ID // EMAIL</label>
                  <div className="cyber-input-wrapper">
                    <Mail size={16} className="input-icon" />
                    <input
                      type="email"
                      name="email"
                      placeholder="operative@trustlens.ai"
                      value={formData.email}
                      onChange={handleChange}
                      className="cyber-input"
                      autoComplete="email"
                    />
                  </div>
                </div>

                <div className="input-field-group">
                  <div className="field-label-split">
                    <label className="field-label">CRYPTOGRAPHIC ACCESS KEY</label>
                    {!isRegister && (
                      <span className="forgot-pass-link" onClick={() => alert('Demo key hint: Use any password or click the Fast Demo pills above.')}>
                        Lost Key?
                      </span>
                    )}
                  </div>
                  <div className="cyber-input-wrapper">
                    <Lock size={16} className="input-icon" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      placeholder="••••••••••••"
                      value={formData.password}
                      onChange={handleChange}
                      className="cyber-input"
                      autoComplete={isRegister ? 'new-password' : 'current-password'}
                    />
                    <button
                      type="button"
                      className="password-toggle-btn"
                      onClick={() => setShowPassword(p => !p)}
                      title={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>

                  {/* Password Strength Meter (Shown during Register or Typing) */}
                  {isRegister && formData.password && (
                    <div className="strength-meter-wrap">
                      <div className="strength-bar-track">
                        <div
                          className={`strength-bar-fill ${
                            passwordStrength <= 25 ? 'weak' : passwordStrength <= 50 ? 'medium' : 'strong'
                          }`}
                          style={{ width: `${passwordStrength}%` }}
                        />
                      </div>
                      <span className="strength-text">
                        CYBER DEFENSE: {passwordStrength <= 25 ? 'LOW' : passwordStrength <= 50 ? 'STANDARD' : 'MAXIMUM'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Form Options */}
                <div className="form-options-row">
                  <label className="cyber-checkbox-label">
                    <input
                      type="checkbox"
                      name="rememberMe"
                      checked={formData.rememberMe}
                      onChange={handleChange}
                    />
                    <span className="checkbox-custom" />
                    <span>Maintain terminal session</span>
                  </label>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading || biometricScanning}
                  className="cyber-submit-btn"
                  id="auth-submit-btn"
                >
                  <div className="btn-sheen" />
                  {isLoading ? (
                    <div className="btn-loading-state">
                      <Cpu size={18} className="spinner-icon" />
                      <span>AUTHENTICATING NEURAL SIGNATURE...</span>
                    </div>
                  ) : (
                    <div className="btn-normal-state">
                      <span>{isRegister ? 'INITIALIZE CLEARANCE' : 'AUTHENTICATE ACCESS'}</span>
                      <ArrowRight size={16} className="btn-arrow" />
                    </div>
                  )}
                </button>

                {/* Biometric Scan Alternative */}
                <div className="biometric-divider">
                  <span>OR BYPASS VIA BIOMETRIC TELEMETRY</span>
                </div>

                <button
                  type="button"
                  disabled={biometricScanning || isLoading}
                  onClick={handleBiometricAuth}
                  className={`biometric-btn ${biometricScanning ? 'scanning' : ''}`}
                >
                  <Fingerprint size={20} className="bio-icon" />
                  <span>
                    {biometricScanning ? 'SCANNING RETINAL & DERMAL PRINT...' : 'Simulate Biometric Scan'}
                  </span>
                  {biometricScanning && <div className="bio-laser-sweep" />}
                </button>
              </form>

              {/* Card Footer Security Stats */}
              <div className="card-security-footer">
                <div className="sec-item">
                  <Shield size={12} className="text-neon-cyan" />
                  <span>ZERO-TRUST GATEWAY</span>
                </div>
                <div className="sec-item">
                  <Sparkles size={12} className="text-neon-magenta" />
                  <span>SOC-2 TYPE II CERTIFIED</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer Return Home Link */}
        <div className="login-footer-links">
          <Link to="/" className="back-home-link">
            ← Return to TrustLens AI Public Terminal
          </Link>
        </div>
      </div>
    </div>
  );
}
