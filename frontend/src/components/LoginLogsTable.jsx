import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { 
  Key, 
  RefreshCw, 
  Filter, 
  Trash2, 
  ShieldCheck, 
  Fingerprint, 
  UserCheck, 
  Database,
  Globe,
  Clock,
  Zap,
  Users
} from 'lucide-react';
import { getApiUrl } from '../api/config';
import './LoginLogsTable.css';

const AUTH_TYPE_BADGES = {
  biometric: { label: 'Biometric Scan', icon: Fingerprint, color: 'var(--cyan)' },
  password: { label: 'Crypto Key', icon: Key, color: 'var(--yellow)' },
  quick_demo: { label: 'Fast Demo', icon: Zap, color: 'var(--magenta)' },
  register: { label: 'Registration', icon: UserCheck, color: 'var(--green)' },
};

export default function LoginLogsTable() {
  const [logs, setLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState('');
  const [showUsersModal, setShowUsersModal] = useState(false);

  const fetchAuthData = useCallback(async () => {
    setLoading(true);
    setError('');
    const API = getApiUrl();
    try {
      const [logsRes, usersRes] = await Promise.allSettled([
        axios.get(`${API}/api/auth/logs?limit=100`, { timeout: 30000 }),
        axios.get(`${API}/api/auth/users?limit=50`, { timeout: 30000 }),
      ]);

      if (logsRes.status === 'fulfilled') {
        setLogs(logsRes.value.data || []);
      } else {
        throw logsRes.reason;
      }

      if (usersRes.status === 'fulfilled') {
        setUsers(usersRes.value.data || []);
      }
    } catch (_err) {
      if (!API) {
        setError('Could not connect to the local backend. Please verify your FastAPI server is active.');
      } else {
        setError('Could not load MongoDB login records. Backend may be waking up (Render takes ~30-50s) or check your connection.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAuthData();
  }, [fetchAuthData]);

  async function handleClearLogs() {
    if (!window.confirm('Are you sure you want to purge all operative login audit records from MongoDB?')) {
      return;
    }
    const API = getApiUrl();
    try {
      await axios.delete(`${API}/api/auth/logs`);
      setLogs([]);
    } catch (e) {
      console.error('Clear failed', e);
      setError('Failed to purge login telemetry. Please try again.');
    }
  }

  function formatDate(iso) {
    if (!iso) return '—';
    try {
      const date = new Date(iso);
      return date.toLocaleString();
    } catch {
      return String(iso);
    }
  }

  const filteredLogs = filter 
    ? logs.filter(l => l.auth_type === filter) 
    : logs;

  const biometricCount = logs.filter(l => l.auth_type === 'biometric').length;
  const passwordCount = logs.filter(l => l.auth_type === 'password' || l.auth_type === 'quick_demo').length;

  return (
    <div className="login-logs-wrapper">
      {/* Controls Bar */}
      <div className="login-logs-controls">
        <div className="filter-row">
          <Filter size={14} style={{ color: 'var(--text-muted)' }} />
          <select
            id="login-auth-filter"
            className="filter-select"
            value={filter}
            onChange={e => setFilter(e.target.value)}
          >
            <option value="">All Auth Protocols</option>
            <option value="password">Crypto Key (Password)</option>
            <option value="biometric">Biometric Scan</option>
            <option value="quick_demo">Fast Demo Clearance</option>
            <option value="register">Operative Registration</option>
          </select>
        </div>

        <div className="action-buttons-group">
          <button
            type="button"
            className="btn btn-secondary users-toggle-btn"
            onClick={() => setShowUsersModal(prev => !prev)}
            title="View registered operatives in MongoDB"
          >
            <Users size={14} />
            <span>{showUsersModal ? 'Hide Operatives' : `Operatives (${users.length})`}</span>
          </button>

          <button
            id="refresh-login-logs-btn"
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
            onClick={fetchAuthData}
          >
            <RefreshCw size={14} /> Refresh Feed
          </button>

          {logs.length > 0 && (
            <button
              className="btn btn-danger delete-btn"
              onClick={handleClearLogs}
              title="Purge login audit logs"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              <Trash2 size={14} /> Purge
            </button>
          )}
        </div>
      </div>

      {/* MongoDB Live Stats Ribbon */}
      <div className="login-stats-ribbon">
        <div className="stat-card">
          <div className="stat-top">
            <Database size={15} className="text-neon-cyan" />
            <span className="stat-label">TOTAL LOGINS</span>
          </div>
          <span className="stat-val text-neon-cyan">{logs.length}</span>
          <span className="stat-sub">MongoDB records</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <Users size={15} className="text-neon-magenta" />
            <span className="stat-label">OPERATIVES</span>
          </div>
          <span className="stat-val text-neon-magenta">{users.length}</span>
          <span className="stat-sub">Unique accounts</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <Fingerprint size={15} style={{ color: 'var(--cyan)' }} />
            <span className="stat-label">BIOMETRIC</span>
          </div>
          <span className="stat-val" style={{ color: 'var(--cyan)' }}>{biometricCount}</span>
          <span className="stat-sub">Neural dermal prints</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <Key size={15} style={{ color: 'var(--yellow)' }} />
            <span className="stat-label">CRYPTO KEYS</span>
          </div>
          <span className="stat-val" style={{ color: 'var(--yellow)' }}>{passwordCount}</span>
          <span className="stat-sub">Passphrase accesses</span>
        </div>
      </div>

      {/* Registered Operatives Directory Dropdown / Card List */}
      {showUsersModal && (
        <div className="users-directory-panel glass-card">
          <div className="directory-header">
            <div className="directory-title">
              <Users size={16} className="text-neon-cyan" />
              <h4>REGISTERED OPERATIVES IN MONGODB (`users` collection)</h4>
            </div>
            <span className="directory-count-tag">{users.length} ACCOUNTS</span>
          </div>
          {users.length === 0 ? (
            <p className="no-users-msg">No operatives registered yet in MongoDB. Sign in or register to feed operative data.</p>
          ) : (
            <div className="operatives-grid">
              {users.map(u => (
                <div key={u.id || u.email} className="operative-card">
                  <div className="op-avatar">
                    <UserCheck size={18} className="text-neon-cyan" />
                  </div>
                  <div className="op-details">
                    <div className="op-name-row">
                      <span className="op-name">{u.name}</span>
                      <span className="op-count-badge">{u.login_count} logins</span>
                    </div>
                    <span className="op-email">{u.email}</span>
                    <div className="op-meta-row">
                      <span className="op-role">{u.role}</span>
                      <span className="op-last">{u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Active'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Table */}
      <div className="glass-card table-container">
        {loading ? (
          <div className="table-loading">
            <div className="spinner" />
            <p>Querying MongoDB login telemetry...</p>
          </div>
        ) : error ? (
          <div className="table-error">{error}</div>
        ) : filteredLogs.length === 0 ? (
          <div className="table-empty">
            <Clock size={40} style={{ color: 'var(--text-dim)' }} />
            <p>No login events found in MongoDB. Authenticate on the Login page to generate telemetry.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Operative</th>
                <th>Email Identifier</th>
                <th>Auth Protocol</th>
                <th>Clearance Level</th>
                <th>Client IP</th>
                <th>Logged At</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map(log => {
                const badge = AUTH_TYPE_BADGES[log.auth_type] || {
                  label: log.auth_type || 'Auth',
                  icon: Key,
                  color: 'var(--text-muted)'
                };
                const Icon = badge.icon;

                return (
                  <tr key={log.id}>
                    <td className="font-mono text-xs" style={{ color: 'var(--text-dim)' }}>
                      {log.id.slice(-8)}
                    </td>
                    <td>
                      <span className="font-medium" style={{ color: 'var(--text-bright)' }}>
                        {log.name || 'Operative'}
                      </span>
                    </td>
                    <td className="font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                      {log.email}
                    </td>
                    <td>
                      <span 
                        className="auth-method-badge" 
                        style={{ 
                          borderColor: badge.color, 
                          color: badge.color,
                          background: `color-mix(in srgb, ${badge.color} 10%, transparent)`
                        }}
                      >
                        <Icon size={12} />
                        <span>{badge.label}</span>
                      </span>
                    </td>
                    <td>
                      <span className="clearance-badge font-mono">
                        {log.auth_level || 'LEVEL 4'}
                      </span>
                    </td>
                    <td className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>
                      <span className="ip-wrapper">
                        <Globe size={11} /> {log.client_ip || '127.0.0.1'}
                      </span>
                    </td>
                    <td className="text-xs" style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {formatDate(log.timestamp)}
                    </td>
                    <td>
                      <span className={`status-pill ${log.status === 'SUCCESS' ? 'status-success' : 'status-fail'}`}>
                        <ShieldCheck size={12} />
                        <span>{log.status}</span>
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
