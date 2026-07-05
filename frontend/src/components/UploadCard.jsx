import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, Image, Volume2, Video, MessageSquare, Mail, X, FileText } from 'lucide-react';
import './UploadCard.css';

const API = '';

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

    onLoading(true);
    try {
      let res;
      if (isText) {
        const form = new FormData();
        form.append('text', text);
        form.append('mode', activeTab);
        res = await axios.post(`${API}/api/analyze/text`, form);
      } else {
        const form = new FormData();
        form.append('file', file);
        res = await axios.post(`${API}${tab.endpoint}`, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      onResult(res.data);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Analysis failed. Is the backend running?';
      setError(msg);
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
