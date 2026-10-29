import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { Clock, Trash2, RefreshCw, Filter, Eye, Database, X } from 'lucide-react';
import { getApiUrl } from '../api/config';
import ResultPanel from './ResultPanel';
import './HistoryTable.css';

const VERDICT_COLORS = {
  SAFE: 'var(--green)',
  SUSPICIOUS: 'var(--yellow)',
  HIGH_RISK: 'var(--red)',
};

const TYPE_ICONS = {
  image: '🖼',
  audio: '🎵',
  video: '🎬',
  sms:   '📱',
  email: '📧',
  url:   '🌐',
};

export default function HistoryTable() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState('');
  const [dbStatus, setDbStatus] = useState('checking'); // 'connected' | 'disconnected' | 'checking'
  const [selectedScan, setSelectedScan] = useState(null);
  const [inspectLoading, setInspectLoading] = useState(false);
  const [inspectError, setInspectError] = useState('');

  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const stored = localStorage.getItem('trustlens_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const handleAuthChange = () => {
      try {
        const stored = localStorage.getItem('trustlens_user');
        setCurrentUser(stored ? JSON.parse(stored) : null);
      } catch {
        setCurrentUser(null);
      }
    };
    window.addEventListener('authChange', handleAuthChange);
    window.addEventListener('storage', handleAuthChange);
    return () => {
      window.removeEventListener('authChange', handleAuthChange);
      window.removeEventListener('storage', handleAuthChange);
    };
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    const API = getApiUrl();
    const userEmail = currentUser?.email || '';

    try {
      // Check backend & DB status
      try {
        const healthRes = await axios.get(`${API}/health`, { timeout: 8000 });
        setDbStatus(healthRes.data?.database || 'connected');
      } catch {
        setDbStatus('disconnected');
      }

      // Filter by the logged-in user's email so new accounts start completely fresh
      const params = {
        ...(filter ? { scan_type: filter } : {}),
        user_email: userEmail || 'guest',
      };
      const res = await axios.get(`${API}/api/history/`, { params, timeout: 60000 });
      setLogs(res.data);
    } catch (_err) {
      if (!API) {
        setError('Could not connect to the local backend. Please make sure uvicorn is running on port 8000.');
      } else {
        setError('Could not load history. Backend may be waking up (Render free instances take ~30-50s) or check backend deployment status.');
      }
    } finally {
      setLoading(false);
    }
  }, [filter, currentUser]);

  useEffect(() => {
    let ignore = false;
    const API = getApiUrl();
    const userEmail = currentUser?.email || '';

    async function loadData() {
      try {
        try {
          const healthRes = await axios.get(`${API}/health`, { timeout: 8000 });
          if (!ignore) setDbStatus(healthRes.data?.database || 'connected');
        } catch {
          if (!ignore) setDbStatus('disconnected');
        }

        const params = {
          ...(filter ? { scan_type: filter } : {}),
          user_email: userEmail || 'guest',
        };
        const res = await axios.get(`${API}/api/history/`, { params, timeout: 60000 });
        if (!ignore) {
          setLogs(res.data);
          setError('');
        }
      } catch (_err) {
        if (!ignore) {
          if (!API) {
            setError('Could not connect to the local backend. Please make sure uvicorn is running on port 8000.');
          } else {
            setError('Could not load history. Backend may be waking up (Render free instances take ~30-50s) or check backend deployment status.');
          }
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, [filter, currentUser]);

  async function deleteScan(id, e) {
    if (e) e.stopPropagation();
    const API = getApiUrl();
    const userEmail = currentUser?.email || '';
    try {
      await axios.delete(`${API}/api/history/${id}`, {
        params: { user_email: userEmail }
      });
      setLogs(prev => prev.filter(l => l.id !== id));
      if (selectedScan && selectedScan.id === id) {
        setSelectedScan(null);
      }
    } catch (err) {
      console.error('Delete failed', err);
      setError('Failed to delete this scan. Refresh the page and try again.');
    }
  }

  async function clearAllHistory() {
    const userEmail = currentUser?.email || '';
    const confirmMsg = userEmail
      ? `Are you sure you want to purge all scan history for your account (${userEmail})?`
      : 'Are you sure you want to purge all guest scan history?';
    if (!window.confirm(confirmMsg)) {
      return;
    }
    const API = getApiUrl();
    try {
      await axios.delete(`${API}/api/history/`, {
        params: { user_email: userEmail }
      });
      setLogs([]);
      setSelectedScan(null);
    } catch (err) {
      console.error('Clear all failed', err);
      setError('Failed to clear scan history.');
    }
  }

  async function inspectScan(id) {
    setInspectLoading(true);
    setInspectError('');
    const API = getApiUrl();
    try {
      const res = await axios.get(`${API}/api/history/${id}`, { timeout: 15000 });
      setSelectedScan(res.data);
    } catch (err) {
      console.error('Inspect failed', err);
      // Fallback: build view from log item in table if available
      const fallback = logs.find(l => l.id === id);
      if (fallback) {
        setSelectedScan({
          ...fallback,
          evidence: fallback.evidence || [],
          recommendations: fallback.recommendations || ['No recorded recommendations.'],
        });
      } else {
        setInspectError('Could not retrieve full forensic breakdown for this scan.');
      }
    } finally {
      setInspectLoading(false);
    }
  }

  function formatDate(iso) {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return String(iso);
    }
  }

  return (
    <div className="history-wrapper">
      {/* Controls */}
      <div className="history-controls">
        <div className="filter-row">
          <Filter size={14} style={{ color: 'var(--text-muted)' }} />
          <select
            id="history-filter"
            className="filter-select"
            value={filter}
            onChange={e => setFilter(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="image">Image</option>
            <option value="audio">Audio</option>
            <option value="video">Video</option>
            <option value="sms">SMS</option>
            <option value="email">Email</option>
            <option value="url">URL</option>
          </select>

          {/* Database Connection Status Badge */}
          <div className={`db-status-pill ${dbStatus}`}>
            <Database size={12} />
            <span>MongoDB: {dbStatus.toUpperCase()}</span>
          </div>

          {/* Account Scope Badge */}
          <div className="account-scope-pill" style={{
            fontSize: '0.78rem',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            background: 'rgba(0, 245, 255, 0.08)',
            border: '1px solid rgba(0, 245, 255, 0.22)',
            color: 'var(--cyan)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span>Account: <strong>{currentUser?.email || 'Guest'}</strong></span>
          </div>
        </div>

        <div className="action-buttons-row">
          {logs.length > 0 && (
            <button
              id="clear-all-history-btn"
              className="btn btn-danger-outline"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              onClick={clearAllHistory}
              title="Purge all scan history"
            >
              <Trash2 size={13} /> Clear All
            </button>
          )}

          <button
            id="refresh-history-btn"
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
            onClick={fetchLogs}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        {['SAFE', 'SUSPICIOUS', 'HIGH_RISK'].map(v => {
          const count = logs.filter(l => l.verdict === v).length;
          return (
            <div key={v} className="stat-item">
              <span className="stat-count" style={{ color: VERDICT_COLORS[v] }}>{count}</span>
              <span className="stat-label">{v.replace('_', ' ')}</span>
            </div>
          );
        })}
        <div className="stat-item">
          <span className="stat-count" style={{ color: 'var(--cyan)' }}>{logs.length}</span>
          <span className="stat-label">TOTAL SCANS</span>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card table-container">
        {loading ? (
          <div className="table-loading">
            <div className="spinner" />
            <p>Loading scan history...</p>
          </div>
        ) : error ? (
          <div className="table-error">{error}</div>
        ) : logs.length === 0 ? (
          <div className="table-empty">
            <Clock size={40} style={{ color: 'var(--text-dim)' }} />
            <p>
              {currentUser?.email
                ? `No scans yet for ${currentUser.email}. Scans you analyze while logged into this account will appear here.`
                : 'No guest scans yet. Log in to an account to save your scan reports.'}
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Type</th>
                <th>File / Content</th>
                <th>Risk Score</th>
                <th>Verdict</th>
                <th>Scanned At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr
                  key={log.id}
                  className="history-row-clickable"
                  onClick={() => inspectScan(log.id)}
                  title="Click to view detailed forensic report"
                >
                  <td className="font-mono text-xs" style={{ color: 'var(--text-dim)' }}>
                    {log.id ? `${log.id.slice(0, 8)}...` : '—'}
                  </td>
                  <td>
                    <span className="type-badge">
                      {TYPE_ICONS[log.scan_type] || '🔍'} {log.scan_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="font-mono text-xs" style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {log.filename || log.summary || '—'}
                  </td>
                  <td>
                    <div className="score-cell">
                      <span className="score-num" style={{ color: log.risk_score >= 70 ? 'var(--red)' : log.risk_score >= 40 ? 'var(--yellow)' : 'var(--green)' }}>
                        {log.risk_score}
                      </span>
                      <div className="score-bar-track" style={{ flex: 1, maxWidth: 80 }}>
                        <div
                          className="score-bar-fill"
                          style={{
                            width: `${log.risk_score}%`,
                            background: log.risk_score >= 70 ? 'var(--red)' : log.risk_score >= 40 ? 'var(--yellow)' : 'var(--green)',
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`verdict-badge verdict-${log.verdict}`}>
                      {log.verdict.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {formatDate(log.created_at)}
                  </td>
                  <td>
                    <div className="row-action-buttons">
                      <button
                        className="btn btn-secondary-icon"
                        onClick={(e) => { e.stopPropagation(); inspectScan(log.id); }}
                        title="Inspect Scan Details"
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        className="btn btn-danger delete-btn"
                        onClick={(e) => deleteScan(log.id, e)}
                        title="Delete scan"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Inspect Modal Drawer */}
      {(selectedScan || inspectLoading || inspectError) && (
        <div className="scan-modal-overlay" onClick={() => setSelectedScan(null)}>
          <div className="scan-modal-card glass-card" onClick={e => e.stopPropagation()}>
            <div className="scan-modal-header">
              <div className="modal-title-box">
                <span className="modal-title-tag">FORENSIC REPORT</span>
                <h3 className="modal-title-text">
                  {selectedScan?.filename || `${selectedScan?.scan_type?.toUpperCase()} Analysis`}
                </h3>
              </div>
              <button
                type="button"
                className="scan-modal-close"
                onClick={() => { setSelectedScan(null); setInspectError(''); }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="scan-modal-body">
              {inspectLoading ? (
                <div className="table-loading">
                  <div className="spinner" />
                  <p>Retrieving forensic evidence record...</p>
                </div>
              ) : inspectError ? (
                <div className="table-error">{inspectError}</div>
              ) : selectedScan ? (
                <ResultPanel result={selectedScan} />
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
