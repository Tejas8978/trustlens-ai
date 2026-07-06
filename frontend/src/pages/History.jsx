import HistoryTable from '../components/HistoryTable';
import { Clock } from 'lucide-react';
import './History.css';

export default function History() {
  return (
    <div className="history-page">
      <div className="history-header">
        <p className="history-eyebrow">
          <Clock size={14} /> Scan Records
        </p>
        <h1>
          Scan <span className="text-gradient">History</span>
        </h1>
        <p className="history-desc">
          All previous scans are stored locally in your SQLite database.
          Filter by type, view verdicts, and manage your scan records.
        </p>
      </div>
      <div className="history-content container">
        <HistoryTable />
      </div>
    </div>
  );
}
