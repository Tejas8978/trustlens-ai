import { useState } from 'react';
import HistoryTable from '../components/HistoryTable';
import LoginLogsTable from '../components/LoginLogsTable';
import { Clock, Shield, Key } from 'lucide-react';
import './History.css';

export default function History() {
  const [activeTab, setActiveTab] = useState('scans'); // 'scans' | 'logins'

  return (
    <div className="history-page">
      <div className="history-header">
        <p className="history-eyebrow">
          {activeTab === 'scans' ? (
            <>
              <Clock size={14} /> Scan Forensics Database
            </>
          ) : (
            <>
              <Key size={14} /> Operative Telemetry & Access Feed
            </>
          )}
        </p>

        <h1>
          {activeTab === 'scans' ? (
            <>
              Scan <span className="text-gradient">History</span>
            </>
          ) : (
            <>
              Operative <span className="text-gradient">Access Logs</span>
            </>
          )}
        </h1>

        <p className="history-desc">
          {activeTab === 'scans'
            ? 'All previous deepfake and malicious scam analyses are securely stored in MongoDB. Filter by media type, view verdicts, and manage scan logs.'
            : 'Live authentication feed fed into MongoDB collections (`login_logs` and `users`). Inspect operative logins, clearance levels, client IPs, and auth protocols.'}
        </p>

        {/* Tab Switcher */}
        <div className="history-tab-track">
          <button
            type="button"
            className={`history-tab-btn ${activeTab === 'scans' ? 'active' : ''}`}
            onClick={() => setActiveTab('scans')}
          >
            <Shield size={14} />
            <span>Threat Scans</span>
          </button>
          <button
            type="button"
            className={`history-tab-btn ${activeTab === 'logins' ? 'active' : ''}`}
            onClick={() => setActiveTab('logins')}
          >
            <Key size={14} />
            <span>MongoDB Login Feed</span>
          </button>
        </div>
      </div>

      <div className="history-content container">
        {activeTab === 'scans' ? <HistoryTable /> : <LoginLogsTable />}
      </div>
    </div>
  );
}
