import HistoryTable from '../components/HistoryTable';
import { Clock } from 'lucide-react';
import './History.css';

export default function History() {
  return (
    <div className="history-page">
      <div className="history-header">
        <p className="history-eyebrow">
          <Clock size={14} /> Scan Forensics Database
        </p>

        <h1>
          Scan <span className="text-gradient">History</span>
        </h1>

        <p className="history-desc">
          All previous deepfake and malicious scam analyses are securely stored in MongoDB. Filter by media type, view verdicts, and manage scan logs.
        </p>
      </div>

      <div className="history-content container">
        <HistoryTable />
      </div>
    </div>
  );
}
