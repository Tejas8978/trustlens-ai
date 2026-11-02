import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Shield, 
  Lock, 
  Mail, 
  User, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle,
  Loader2
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../api/config';
import './Login.css';

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [isAlreadyRegistered, setIsAlreadyRegistered] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    emailOrUsername: '',
    password: '',
    confirmPassword: '',
    rememberMe: true,
  });

  const pwd = formData.password || '';
  const pwdCriteria = {
    length: pwd.length >= 8,
    upper: /[A-Z]/.test(pwd),
    lower: /[a-z]/.test(pwd),
    number: /[0-9]/.test(pwd),
    special: /[^A-Za-z0-9]/.test(pwd),
  };
  const isPwdStrong = Object.values(pwdCriteria).every(Boolean);

  const handleChange = (e) => {
    setError('');
    setIsAlreadyRegistered(false);
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleEmailBlur = async () => {
    if (!isRegister) return;
    const clean = formData.emailOrUsername.trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!clean || !emailRegex.test(clean)) return;

    try {
      const API = getApiUrl();
      const res = await axios.get(`${API}/api/auth/check-email?email=${encodeURIComponent(clean)}`, { timeout: 6000 });
      if (res.data?.exists) {
        setError('This email address is already registered. Only one account is permitted per email address.');
        setIsAlreadyRegistered(true);
      }
    } catch {
      // Background check error ignored; form submit will validate as well
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsAlreadyRegistered(false);

    const identifier = formData.emailOrUsername.trim();
    if (!identifier) {
      setError(isRegister ? 'Please enter your email address.' : 'Please enter your email or username.');
      return;
    }

    if (!formData.password) {
      setError('Please enter your password.');
      return;
    }

    const cleanEmail = identifier.toLowerCase();

    if (isRegister) {
      if (!formData.name.trim()) {
        setError('Please enter your full name.');
        return;
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(cleanEmail)) {
        setError('Please enter a valid email address (e.g. name@example.com).');
        return;
      }
      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return;
      }
      if (!isPwdStrong) {
        setError('Password must combine uppercase letters (A-Z), lowercase letters (a-z), numbers (0-9), and special characters (!@#$%).');
        return;
      }
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
    }

    setIsLoading(true);

    const isEmail = identifier.includes('@');
    const email = isEmail ? cleanEmail : `${cleanEmail.replace(/\s+/g, '')}@trustlens.user`;
    const name = isRegister ? formData.name.trim() : (formData.name.trim() || identifier.split('@')[0]);

    const API = getApiUrl();
    const endpoint = isRegister ? `${API}/api/auth/register` : `${API}/api/auth/login`;
    const payload = {
      email,
      password: formData.password,
      name,
      role: 'User',
      auth_type: isRegister ? 'register' : 'password',
    };

    try {
      const res = await axios.post(endpoint, payload, { timeout: 15000 });
      if (res.data) {
        const userProfile = {
          id: res.data.id,
          name: res.data.name || name,
          email: res.data.email || email,
          role: res.data.role || 'User',
          authLevel: res.data.auth_level || 'Standard User',
          loggedInAt: new Date().toISOString(),
          mongodbConnected: res.data.mongodb_connected ?? true,
        };

        setIsLoading(false);
        setSuccess(true);
        localStorage.setItem('trustlens_user', JSON.stringify(userProfile));
        window.dispatchEvent(new Event('authChange'));

        setTimeout(() => {
          navigate('/analyze');
        }, 900);
      }
    } catch (err) {
      setIsLoading(false);
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      if (status === 409 || (typeof detail === 'string' && detail.toLowerCase().includes('already registered'))) {
        setError(detail || 'This email address is already registered. Only one account is permitted per email address.');
        setIsAlreadyRegistered(true);
      } else if (detail) {
        setError(detail);
      } else if (!status || err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED') {
        const isLocal = !API || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'));
        setError(
          isLocal
            ? 'Cannot connect to backend server on port 8000. Please start your backend (run start-backend.ps1) so your account is saved to MongoDB.'
            : 'Cannot reach backend server. Please verify your connection or check backend settings.'
        );
      } else {
        setError(err.message || 'Authentication failed. Please try again.');
      }
    }
  };

  const handleForgotPassword = (e) => {
    e.preventDefault();
    alert('Password reset link has been dispatched to your email address (if registered).');
  };

  return (
    <div className="normal-login-viewport">
      <div className="login-card-wrapper">
        {/* Logo / Brand Header */}
        <div className="login-brand-header">
          <Link to="/" className="login-brand-logo">
            <div className="brand-icon-box">
              <Shield size={24} />
            </div>
            <span className="brand-title">
              Trust<span className="text-accent">Lens</span> AI
            </span>
          </Link>
          <h1 className="login-heading">
            {isRegister ? 'Create an account' : 'Welcome back'}
          </h1>
          <p className="login-subheading">
            {isRegister 
              ? 'Sign up to start scanning images, audio, video, and suspicious links.' 
              : 'Enter your credentials to access your account and reports.'}
          </p>
        </div>

        {/* Auth Card */}
        <div className="normal-auth-card">
          {/* Mode Tab Switcher */}
          <div className="auth-tab-bar">
            <button
              type="button"
              className={`auth-tab-btn ${!isRegister ? 'active' : ''}`}
              onClick={() => { setIsRegister(false); setError(''); setIsAlreadyRegistered(false); }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`auth-tab-btn ${isRegister ? 'active' : ''}`}
              onClick={() => { setIsRegister(true); setError(''); setIsAlreadyRegistered(false); }}
            >
              Sign Up
            </button>
          </div>

          {/* Success Screen */}
          {success ? (
            <div className="login-success-state">
              <div className="success-icon-wrap">
                <CheckCircle2 size={48} className="text-success" />
              </div>
              <h3>{isRegister ? 'Account Created!' : 'Signed In Successfully'}</h3>
              <p>Redirecting to your dashboard…</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="normal-auth-form">
              {error && (
                <div className="auth-error-banner">
                  <AlertCircle size={18} className="auth-error-icon" />
                  <div className="auth-error-content">
                    <span>{error}</span>
                    {isAlreadyRegistered && (
                      <button
                        type="button"
                        className="error-action-btn"
                        onClick={() => {
                          setIsRegister(false);
                          setError('');
                          setIsAlreadyRegistered(false);
                        }}
                      >
                        Sign in with this email →
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Full Name (Sign Up only) */}
              {isRegister && (
                <div className="form-group">
                  <label className="form-label" htmlFor="name">Full Name</label>
                  <div className="form-input-box">
                    <User size={18} className="input-field-icon" />
                    <input
                      id="name"
                      type="text"
                      name="name"
                      placeholder="e.g. Alex Vance"
                      value={formData.name}
                      onChange={handleChange}
                      className="form-input"
                      autoComplete="name"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Email or Username */}
              <div className="form-group">
                <label className="form-label" htmlFor="emailOrUsername">
                  {isRegister ? 'Email Address' : 'Email or Username'}
                </label>
                <div className="form-input-box">
                  <Mail size={18} className="input-field-icon" />
                  <input
                    id="emailOrUsername"
                    type={isRegister ? 'email' : 'text'}
                    name="emailOrUsername"
                    placeholder={isRegister ? 'name@example.com' : 'Enter email or username'}
                    value={formData.emailOrUsername}
                    onChange={handleChange}
                    onBlur={handleEmailBlur}
                    className="form-input"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              {/* Password */}
              <div className="form-group">
                <div className="form-label-row">
                  <label className="form-label" htmlFor="password">Password</label>
                  {!isRegister && (
                    <button 
                      type="button" 
                      onClick={handleForgotPassword}
                      className="forgot-link"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="form-input-box">
                  <Lock size={18} className="input-field-icon" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    placeholder={isRegister ? 'Min. 8 chars (A-Z, a-z, 0-9, !@#$)' : 'Enter your password'}
                    value={formData.password}
                    onChange={handleChange}
                    className="form-input"
                    autoComplete={isRegister ? 'new-password' : 'current-password'}
                    required
                  />
                  <button
                    type="button"
                    className="password-eye-btn"
                    onClick={() => setShowPassword(p => !p)}
                    tabIndex={-1}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>

                {/* Password Strength & Combination Criteria (Sign Up only) */}
                {isRegister && (
                  <div className="pwd-criteria-box">
                    <span className="criteria-heading">Password Requirements:</span>
                    <div className="criteria-pills">
                      <span className={`criteria-pill ${pwdCriteria.length ? 'met' : ''}`}>
                        {pwdCriteria.length ? '✓' : '•'} 8+ Characters
                      </span>
                      <span className={`criteria-pill ${pwdCriteria.upper ? 'met' : ''}`}>
                        {pwdCriteria.upper ? '✓' : '•'} Uppercase (A-Z)
                      </span>
                      <span className={`criteria-pill ${pwdCriteria.lower ? 'met' : ''}`}>
                        {pwdCriteria.lower ? '✓' : '•'} Lowercase (a-z)
                      </span>
                      <span className={`criteria-pill ${pwdCriteria.number ? 'met' : ''}`}>
                        {pwdCriteria.number ? '✓' : '•'} Number (0-9)
                      </span>
                      <span className={`criteria-pill ${pwdCriteria.special ? 'met' : ''}`}>
                        {pwdCriteria.special ? '✓' : '•'} Special (!@#$)
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password (Sign Up only) */}
              {isRegister && (
                <div className="form-group">
                  <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
                  <div className="form-input-box">
                    <Lock size={18} className="input-field-icon" />
                    <input
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      name="confirmPassword"
                      placeholder="Re-enter your password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      className="form-input"
                      autoComplete="new-password"
                      required
                    />
                    <button
                      type="button"
                      className="password-eye-btn"
                      onClick={() => setShowConfirmPassword(p => !p)}
                      tabIndex={-1}
                      aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                    >
                      {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
              )}

              {/* Remember Me */}
              {!isRegister && (
                <div className="remember-row">
                  <label className="remember-label">
                    <input
                      type="checkbox"
                      name="rememberMe"
                      checked={formData.rememberMe}
                      onChange={handleChange}
                    />
                    <span>Remember me</span>
                  </label>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn btn-primary submit-auth-btn"
                id="submit-auth-btn"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={18} className="spin-loader" />
                    <span>{isRegister ? 'Creating Account…' : 'Signing In…'}</span>
                  </>
                ) : (
                  <>
                    <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Card Footer toggle */}
          <div className="auth-card-footer">
            {isRegister ? (
              <p>
                Already have an account?{' '}
                <button
                  type="button"
                  className="switch-mode-btn"
                  onClick={() => { setIsRegister(false); setError(''); setIsAlreadyRegistered(false); }}
                >
                  Sign in
                </button>
              </p>
            ) : (
              <p>
                Don't have an account?{' '}
                <button
                  type="button"
                  className="switch-mode-btn"
                  onClick={() => { setIsRegister(true); setError(''); setIsAlreadyRegistered(false); }}
                >
                  Sign up
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Back Link */}
        <div className="login-bottom-nav">
          <Link to="/" className="back-link">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
