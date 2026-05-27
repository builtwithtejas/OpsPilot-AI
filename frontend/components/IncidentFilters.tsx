"use client";

import { Download, RefreshCw } from "lucide-react";

const SEVERITIES = ["All", "Critical", "High", "Medium", "Low"];
const STATUSES = ["All", "Open", "In Progress", "Resolved", "Closed"];

interface Props {
  severityFilter: string;
  setSeverityFilter: (s: string) => void;
  statusFilter: string;
  setStatusFilter: (s: string) => void;
  total: number;
  filtered: number;
  onExportCSV: () => void;
  onRefresh: () => void;
}

export default function IncidentFilters({ severityFilter, setSeverityFilter, statusFilter, setStatusFilter, total, filtered, onExportCSV, onRefresh }: Props) {
  const btnBase: React.CSSProperties = {
    padding: "6px 14px", borderRadius: "999px", fontSize: "13px", fontWeight: 600,
    cursor: "pointer", border: "1px solid var(--border)", transition: "all 0.15s",
  };

  function FilterGroup({ label, options, value, onChange }: { label: string; options: string[]; value: string; onChange: (v: string) => void }) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
        <span style={{ fontSize: "12px", color: "var(--text-tertiary)", marginRight: "2px" }}>{label}:</span>
        {options.map(opt => (
          <button key={opt} onClick={() => onChange(opt)} style={{
            ...btnBase,
            background: value === opt ? "rgba(57,255,136,0.12)" : "var(--input-bg)",
            color: value === opt ? "var(--accent)" : "var(--text-secondary)",
            borderColor: value === opt ? "var(--accent)" : "var(--border)",
          }}>{opt}</button>
        ))}
      </div>
    );
  }

  return (
    <div style={{
      display: "flex", flexWrap: "wrap", gap: "16px", alignItems: "center",
      justifyContent: "space-between", marginBottom: "20px",
      padding: "16px 20px", background: "var(--card-bg)", borderRadius: "16px",
      border: "1px solid var(--border)", backdropFilter: "blur(12px)",
    }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "16px", alignItems: "center" }}>
        <FilterGroup label="Severity" options={SEVERITIES} value={severityFilter} onChange={setSeverityFilter} />
        <FilterGroup label="Status" options={STATUSES} value={statusFilter} onChange={setStatusFilter} />
      </div>

      <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
        <span style={{ fontSize: "13px", color: "var(--text-tertiary)" }}>
          {filtered === total ? `${total} incidents` : `${filtered} of ${total}`}
        </span>
        <button onClick={onRefresh} className="glow-button"
          style={{ ...btnBase, background: "var(--input-bg)", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
          <RefreshCw size={13} /> Refresh
        </button>
        <button onClick={onExportCSV} className="glow-button"
          style={{ ...btnBase, background: "rgba(57,255,136,0.1)", color: "var(--accent)", borderColor: "var(--accent)", display: "flex", alignItems: "center", gap: "6px" }}>
          <Download size={13} /> Export CSV
        </button>
      </div>
    </div>
  );
}
