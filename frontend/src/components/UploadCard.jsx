import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, Image, Volume2, Video, MessageSquare, Mail, Globe, X, FileText, Loader, AlertTriangle, RotateCw, Settings, Sparkles } from 'lucide-react';
import { getApiUrl } from '../api/config';
import './UploadCard.css';

function formatErrorMessage(msg) {
  if (!msg) return 'Analysis failed. Please try again.';
  if (typeof msg === 'string') return msg.trim();
  if (Array.isArray(msg)) return msg.map(formatErrorMessage).join('\n');
  if (typeof msg === 'object') {
    if (msg.detail) return formatErrorMessage(msg.detail);
    if (msg.message) return formatErrorMessage(msg.message);
    return Object.entries(msg)
      .filter(([, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${key}: ${formatErrorMessage(value)}`)
      .join('\n');
  }
  return String(msg);
}

// Wake up the Render backend before analysis (free tier sleeps after inactivity)
// Render cold starts can take up to 60s — retry for 15×4s = 60s
async function wakeUpBackend(retries = 15, delayMs = 4000) {
  const API = getApiUrl();
  for (let i = 0; i < retries; i++) {
    try {
      const resp = await axios.get(`${API}/health`, { timeout: 10000 });
      if (resp.status === 200) return true;
    } catch (_err) {
      // Still sleeping — wait and retry
    }
    if (i < retries - 1) await new Promise(r => setTimeout(r, delayMs));
  }
  return false;
}

const TABS = [
  { id: 'image', label: 'Image', icon: <Image size={16} />, accept: 'image/*', endpoint: '/api/analyze/image' },
  { id: 'audio', label: 'Audio', icon: <Volume2 size={16} />, accept: 'audio/*', endpoint: '/api/analyze/audio' },
  { id: 'video', label: 'Video', icon: <Video size={16} />, accept: 'video/*', endpoint: '/api/analyze/video' },
  { id: 'url',   label: 'URL',   icon: <Globe size={16} />, accept: null, endpoint: '/api/analyze/text' },
  { id: 'sms',   label: 'SMS',   icon: <MessageSquare size={16} />, accept: null, endpoint: '/api/analyze/text' },
  { id: 'email', label: 'Email', icon: <Mail size={16} />, accept: null, endpoint: '/api/analyze/text' },
];

const DEMO_SAMPLES = {
  image: [
    { label: 'Synthetic Face Sample', path: '/sample-deepfake.jpg', filename: 'synthetic-portrait-sample.jpg' },
  ],
  url: [
    { label: 'Phishing Credential Harvester', text: 'http://secure-wellsfargo-verify.account-update.xyz/login' },
    { label: 'Homoglyph Spoofing Domain', text: 'https://pаypal.com/auth-token/check?session=expired' },
  ],
  sms: [
    { label: 'Package Delivery Scam', text: 'USPS Notice: Your parcel #9400111 has an incomplete address and cannot be delivered. Update card details within 12h: http://usps-redelivery-card.top' },
    { label: 'Urgent Bank Alert Fraud', text: 'URGENT CHASE ALERT: Unauthorized withdrawal of $1,420 detected. If this was NOT you, immediately verify your PIN at https://chase-security-verify.biz/portal' },
  ],
  email: [
    { label: 'Payroll Direct Deposit Phish', text: 'Subject: Urgent: Direct Deposit Payment Update Required\n\nDear Employee,\n\nOur payroll system detected a processing failure for your upcoming paycheck. Please review and update your banking credentials immediately via our secured corporate HR portal: http://hr-employee-portal-secure.info/update\n\nFailure to update within 24 hours will delay payment.\n\nRegards,\nCorporate Payroll Security' },
    { label: 'Account Suspension Warning', text: 'Subject: Storage Limit Exceeded - Account Suspension Warning\n\nYour cloud storage account has exceeded allocated quotas. All stored documents will be purged within 48 hours unless you verify ownership: http://account-storage-resolver.cloud/renew' },
  ],
};

export default function UploadCard({ onResult, onLoading }) {
  const [activeTab, setActiveTab] = useState('image');
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState('');
  const [warming, setWarming] = useState(false);
  const [loadingSample, setLoadingSample] = useState(false);
  const fileRef = useRef(null);

  const tab = TABS.find(t => t.id === activeTab);
  const isText = activeTab === 'sms' || activeTab === 'email' || activeTab === 'url';

  async function loadSample(sample) {
    setError('');
    if (sample.path) {
      setLoadingSample(true);
      try {
        const resp = await fetch(sample.path);
        const blob = await resp.blob();
        const testFile = new File([blob], sample.filename, { type: blob.type || 'image/jpeg' });
        setFile(testFile);
      } catch (err) {
        console.error('Failed to load sample:', err);
      } finally {
        setLoadingSample(false);
      }
    } else if (sample.text) {
      setText(sample.text);
    }
  }

  function handleFile(f) {
    setFile(f);
    setError('');
  }

  function onDrop(e) {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }

  async function handleAnalyze() {
    setError('');

    if (isText && !text.trim()) {
      setError(activeTab === 'url' ? 'Please enter a URL to inspect.' : 'Please paste content to analyze.');
      return;
    }
    if (!isText && !file) {
      setError('Please select a file to analyze.');
      return;
    }

    const API = getApiUrl();

    // Check if backend is reachable — if not, try to wake it up (Render free tier)
    if (API) {
      try {
        await axios.get(`${API}/health`, { timeout: 5000 });
      } catch (_err) {
        // Backend might be sleeping — show warm-up message and retry
        setWarming(true);
        onLoading(false);
        const alive = await wakeUpBackend();
        setWarming(false);
        if (!alive) {
          setError({
            isGateway: true,
            status: 'Render Cold Start Timeout',
            message: 'Backend server did not respond within 60s. Render free instances sleep after inactivity, or the configured URL might be incorrect.',
            targetUrl: API,
          });
          return;
        }
      }
    }

    onLoading(true);
    try {
      let res;
      if (isText) {
        const form = new FormData();
        form.append('text', text);
        form.append('mode', activeTab);
        res = await axios.post(`${API}/api/analyze/text`, form, { timeout: 60000 });
      } else {
        const form = new FormData();
        form.append('file', file);
        // Do NOT set Content-Type manually — axios must set it with the correct boundary
        res = await axios.post(`${API}${tab.endpoint}`, form, { timeout: 60000 });
      }
      
      const payload = {
        ...res.data,
        previewUrl: (!isText && file && file.type?.startsWith('image/')) ? URL.createObjectURL(file) : null,
      };
      onResult(payload);
    } catch (err) {
      const status = err.response?.status;
      if (!status || status === 502 || status === 503 || status === 404 || err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED') {
        const isLocal = !API || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'));
        setError({
          isGateway: true,
          status: status ? `HTTP ${status}` : 'Connection Refused / Network Error',
          message: isLocal && !API
            ? 'Cannot connect to local backend on port 8000. Please start your server (run start-backend.ps1).'
            : 'Backend returned a gateway or network error. If hosted on Render, the server may be waking up (wait 30–50s), or your Render service URL may have changed.',
          targetUrl: API || 'http://localhost:8000',
        });
      } else if (status === 413) {
        setError('File is too large. Please upload a smaller file.');
      } else if (status === 422) {
        setError('Invalid file or input format. Please check what you uploaded.');
      } else {
        const msg = err.response?.data?.detail || err.response?.data || err.message || 'Analysis failed. Please try again.';
        setError(formatErrorMessage(msg));
      }
    } finally {
      onLoading(false);
    }
  }

  return (
    <div className="upload-card glass-card">
      {/* Tab Bar */}
      <div className="tab-bar upload-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => { setActiveTab(t.id); setFile(null); setText(''); setError(''); }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      <div className="upload-body">
        {DEMO_SAMPLES[activeTab] && (
          <div className="sample-presets-bar">
            <span className="sample-presets-label">
              <Sparkles size={13} className="text-neon-cyan" /> Try a sample:
            </span>
            <div className="sample-presets-buttons">
              {DEMO_SAMPLES[activeTab].map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="sample-preset-btn"
                  onClick={() => loadSample(s)}
                  disabled={loadingSample}
                >
                  {loadingSample && s.path ? 'Loading…' : s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {isText ? (
          <div className="text-input-area">
            <label className="input-label">
              {activeTab === 'url' ? '🌐 Inspect Website URL or Link' : activeTab === 'sms' ? '📱 Paste SMS / Text Message' : '📧 Paste Email Content'}
            </label>
            <textarea
              id={`${activeTab}-input`}
              className="cyber-input"
              rows={activeTab === 'url' ? 4 : 8}
              placeholder={
                activeTab === 'url'
                  ? 'https://example-secure-bank-login.com/account/verify...'
                  : activeTab === 'sms'
                  ? 'Paste the suspicious SMS message here...'
                  : 'Paste the email body or subject + body here...'
              }
              value={text}
              onChange={e => setText(e.target.value)}
            />
            <p className="input-hint">
              {activeTab === 'url'
                ? 'Analyzes domain homoglyphs, brand spoofing, raw IP hosts, suspicious TLDs, and cloaking'
                : text.length > 0 ? `${text.length} characters` : 'Tip: include the full message for best accuracy'}
            </p>
          </div>
        ) : (
          <div
            id={`${activeTab}-dropzone`}
            className={`upload-zone ${drag ? 'drag-over' : ''}`}
            onDragOver={e => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
          >
            <input
              ref={fileRef}
              type="file"
              accept={tab.accept}
              style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files?.[0])}
            />
            {file ? (
              <div className="file-selected">
                <div className="file-icon">
                  <FileText size={32} />
                </div>
                <p className="file-name">{file.name}</p>
                <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
                <button
                  className="btn btn-secondary file-clear"
                  onClick={e => { e.stopPropagation(); setFile(null); }}
                >
                  <X size={14} /> Remove
                </button>
              </div>
            ) : (
              <div className="upload-placeholder">
                <div className="upload-icon animate-float">
                  {tab.icon}
                </div>
                <p className="upload-main-text">
                  Drop your {tab.label.toLowerCase()} file here
                </p>
                <p className="upload-sub-text">or click to browse</p>
                <div className="upload-formats">
                  {activeTab === 'image' && 'JPG, PNG, WEBP, BMP'}
                  {activeTab === 'audio' && 'MP3, WAV, FLAC, OGG'}
                  {activeTab === 'video' && 'MP4, MOV, AVI, WEBM'}
                </div>
              </div>
            )}
          </div>
        )}

        {warming && (
          <div className="upload-warming">
            <Loader size={14} className="spin-icon" />
            ⏳ Backend is warming up (Render free tier cold start)… please wait ~30s
          </div>
        )}

        {error && (
          typeof error === 'object' && error.isGateway ? (
            <div className="upload-error upload-error-gateway">
              <div className="gateway-error-top">
                <AlertTriangle size={18} className="gateway-error-icon" />
                <span>Backend Gateway / Connection Error ({error.status})</span>
              </div>
              <p className="gateway-error-desc">{error.message}</p>
              <div className="gateway-meta-row">
                <span className="gateway-target-label">Target URL:</span>
                <code className="gateway-target-code">{error.targetUrl}</code>
              </div>
              <div className="gateway-actions-row">
                <button
                  type="button"
                  className="btn btn-secondary gateway-btn"
                  onClick={() => window.dispatchEvent(new CustomEvent('open_backend_modal'))}
                >
                  <Settings size={14} /> Configure Backend URL
                </button>
                <button
                  type="button"
                  className="btn btn-primary gateway-btn"
                  onClick={handleAnalyze}
                >
                  <RotateCw size={14} /> Retry Analysis
                </button>
              </div>
            </div>
          ) : (
            <div className="upload-error">
              ⚠ {typeof error === 'string' ? error : (error.message || JSON.stringify(error))}
            </div>
          )
        )}

        <button
          id="analyze-btn"
          className="btn btn-primary analyze-btn"
          onClick={handleAnalyze}
          disabled={(!isText && !file) || (isText && !text.trim())}
        >
          <Upload size={16} />
          Analyze Now
        </button>
      </div>
    </div>
  );
}
