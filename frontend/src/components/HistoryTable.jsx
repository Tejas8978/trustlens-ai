import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Clock, Trash2, RefreshCw, Filter } from 'lucide-react';
import './HistoryTable.css';

const API = import.meta.env.VITE_API_URL || '';

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
};

export default function HistoryTable() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState('');

  async function fetchLogs() {
    setLoading(true);
    setError('');
    try {
      const params = filter ? { scan_type: filter } : {};
      const res = await axios.get(`${API}/api/history/`, { params });
      setLogs(res.data);
    } catch (err) {
      setError('Could not load history. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchLogs(); }, [filter]);

  async function deleteScan(id) {
    try {
      await axios.delete(`${API}/api/history/${id}`);
      setLogs(logs.filter(l => l.id !== id));
    } catch (e) {
      console.error('Delete failed');
    }
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleString();
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
          </select>
        </div>
        <button
          id="refresh-history-btn"
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          onClick={fetchLogs}
        >
          <RefreshCw size={14} /> Refresh
        </button>
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
            <p>No scans yet. Analyze something to see results here.</p>
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
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={log.id}>
                  <td className="font-mono text-xs" style={{ color: 'var(--text-dim)' }}>
                    {log.id}
                  </td>
                  <td>
                    <span className="type-badge">
                      {TYPE_ICONS[log.scan_type]} {log.scan_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="font-mono text-xs" style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {log.filename || '—'}
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
                    <button
                      className="btn btn-danger delete-btn"
                      onClick={() => deleteScan(log.id)}
                      title="Delete scan"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
