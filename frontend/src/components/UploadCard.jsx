import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, Image, Volume2, Video, MessageSquare, Mail, X, FileText, Loader } from 'lucide-react';
import './UploadCard.css';

function getApiUrl() {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return '';
  }
  const stored = localStorage.getItem('VITE_API_URL');
  if (stored) return stored.replace(/\/$/, '');
  
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/$/, '');
  
  return 'https://trustlens-backend.onrender.com';
}

const API = getApiUrl();

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
async function wakeUpBackend(retries = 8, delayMs = 3500) {
  for (let i = 0; i < retries; i++) {
    try {
      const resp = await axios.get(`${API}/health`, { timeout: 8000 });
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
  { id: 'sms',   label: 'SMS',   icon: <MessageSquare size={16} />, accept: null, endpoint: '/api/analyze/text' },
  { id: 'email', label: 'Email', icon: <Mail size={16} />, accept: null, endpoint: '/api/analyze/text' },
];

export default function UploadCard({ onResult, onLoading }) {
  const [activeTab, setActiveTab] = useState('image');
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState('');
  const [warming, setWarming] = useState(false);
  const fileRef = useRef(null);

  const tab = TABS.find(t => t.id === activeTab);
  const isText = activeTab === 'sms' || activeTab === 'email';

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
      setError('Please paste a message to analyze.');
      return;
    }
    if (!isText && !file) {
      setError('Please select a file to analyze.');
      return;
    }

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
          setError(
            'The backend server is unavailable. If deployed on Render free tier, it may have been ' +
            'shut down. Visit your Render dashboard to restart it, or wait 60s and try again.'
          );
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
      onResult(res.data);
    } catch (err) {
      const status = err.response?.status;
      if (!status || status === 502 || status === 503 || err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED') {
        if (!API) {
          setError(
            'Cannot connect to the local backend server. Please make sure the backend is running ' +
            'on port 8000 (run start-backend.ps1).'
          );
        } else {
          setError(
            'Backend returned a gateway error (502/503). The server may be restarting — ' +
            'wait 30 seconds and try again. Or update the backend URL using the settings cog at the top.'
          );
        }
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
        {isText ? (
          <div className="text-input-area">
            <label className="input-label">
              {activeTab === 'sms' ? '📱 Paste SMS / Text Message' : '📧 Paste Email Content'}
            </label>
            <textarea
              id={`${activeTab}-input`}
              className="cyber-input"
              rows={8}
              placeholder={
                activeTab === 'sms'
                  ? 'Paste the suspicious SMS message here...'
                  : 'Paste the email body or subject + body here...'
              }
              value={text}
              onChange={e => setText(e.target.value)}
            />
            <p className="input-hint">
              {text.length > 0 ? `${text.length} characters` : 'Tip: include the full message for best accuracy'}
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
          <div className="upload-error">
            ⚠ {error}
          </div>
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
