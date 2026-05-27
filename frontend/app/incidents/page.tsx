"use client";

import { useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import IncidentCard from "@/components/IncidentCard";
import IncidentFilters from "@/components/IncidentFilters";
import { useIncidents } from "@/hooks/useIncidents";
import { useSearch } from "@/hooks/useSearch";
import { exportIncidentsCSV } from "@/utils/formatters";
import { downloadIncidentPdf } from "@/lib/api";
import { FileText, ChevronLeft, ChevronRight } from "lucide-react";
import type { IncidentStatus } from "@/types";

const PAGE_SIZE = 10;

const SEED_INCIDENTS = [
  { title: "Build failure in CI pipeline",    severity: "Critical" as const, status: "Open" as const,        description: "npm build failed due to missing dependency react-dom@18.3.0 in package-lock.json.",                  remediation: "1. Run npm install\n2. Commit updated package-lock.json\n3. Re-trigger pipeline",    confidence: 94 },
  { title: "Docker image push timeout",       severity: "High" as const,     status: "In Progress" as const, description: "Docker push to registry exceeded 5 minute timeout. Registry returned 503 Service Unavailable.", remediation: "1. Check registry status\n2. Retry with --timeout\n3. Switch to backup registry",     confidence: 88 },
  { title: "Unit test coverage below 80%",    severity: "Medium" as const,   status: "Open" as const,        description: "Test coverage dropped to 67%, below the required 80% threshold in jest.config.js.",               remediation: "1. Run: npm test -- --coverage\n2. Add tests for uncovered modules",                   confidence: 76 },
  { title: "Security scan: 2 high CVEs",      severity: "High" as const,     status: "Open" as const,        description: "Trivy detected CVE-2024-29041 in express@4.18.2 and CVE-2024-28863 in tar@6.1.11.",             remediation: "1. Update express to >=4.19.2\n2. Update tar to >=6.2.1\n3. npm audit fix",          confidence: 97 },
  { title: "Deployment rollback triggered",   severity: "Low" as const,      status: "Resolved" as const,    description: "Canary deployment showed 2% error rate increase, automatic rollback triggered.",                   remediation: "Investigate error logs from canary pods before re-deploying.",                         confidence: 82 },
];

export default function IncidentsPage() {
  const { incidents, loading, error, refresh, updateStatus, remove } = useIncidents();
  const { query, setQuery, severityFilter, setSeverityFilter, statusFilter, setStatusFilter, filtered } = useSearch(incidents);
  const [page, setPage] = useState(1);

  const paginated = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  const summaryStats = useMemo(() => ({
    open:     incidents.filter(i => i.status === "Open").length,
    critical: incidents.filter(i => i.severity === "Critical").length,
    resolved: incidents.filter(i => i.status === "Resolved" || i.status === "Closed").length,
  }), [incidents]);

  async function seedDemoData() {
    const BASE    = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";
    const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";
    for (const inc of SEED_INCIDENTS) {
      try {
        await fetch(`${BASE}/incidents/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
          body: JSON.stringify(inc),
        });
      } catch { /* skip */ }
    }
    void refresh();
  }

  return (
    <AppShell onRefresh={refresh}>
      {/* Header */}
      <div className="fade-up" style={{ marginBottom: "28px", display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>Incidents</h1>
          <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>All AI-detected CI/CD incidents</p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          {incidents.length === 0 && !loading && (
            <button onClick={() => void seedDemoData()} className="glow-button" style={{ padding: "10px 18px", borderRadius: "12px", background: "rgba(255,179,71,0.1)", border: "1px solid #ffb347", color: "#ffb347", fontWeight: 600, cursor: "pointer", fontSize: "14px" }}>
              Load Demo Data
            </button>
          )}
          <button onClick={() => void downloadIncidentPdf(incidents, null)} className="glow-button"
            style={{ padding: "10px 18px", borderRadius: "12px", background: "linear-gradient(to right,#33ff88,#00c3ff)", border: "none", color: "black", fontWeight: 700, cursor: "pointer", fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
            <FileText size={15} /> Export PDF
          </button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: "14px", marginBottom: "24px" }}>
        {[
          { label: "Total",    value: incidents.length,        color: "#00c3ff" },
          { label: "Open",     value: summaryStats.open,       color: "#ff4d4d" },
          { label: "Critical", value: summaryStats.critical,   color: "#ff7a00" },
          { label: "Resolved", value: summaryStats.resolved,   color: "#33ff88" },
        ].map(s => (
          <div key={s.label} className="hover-card" style={{ background: "var(--card-bg)", border: `1px solid ${s.color}33`, borderRadius: "16px", padding: "16px", backdropFilter: "blur(12px)" }}>
            <div style={{ color: "var(--text-tertiary)", fontSize: "13px", marginBottom: "4px" }}>{s.label}</div>
            <div style={{ color: s.color, fontSize: "30px", fontWeight: 700 }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <IncidentFilters
        severityFilter={severityFilter} setSeverityFilter={v => { setSeverityFilter(v); setPage(1); }}
        statusFilter={statusFilter}     setStatusFilter={v => { setStatusFilter(v); setPage(1); }}
        total={incidents.length} filtered={filtered.length}
        onExportCSV={() => exportIncidentsCSV(filtered)}
        onRefresh={refresh}
      />

      {/* List */}
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: "90px" }} />)}
        </div>
      ) : error ? (
        <div style={{ color: "#ff4d4d", fontFamily: "monospace", padding: "20px" }}>⚠ {error}</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-tertiary)" }}>
          <div style={{ fontSize: "48px", marginBottom: "12px" }}>🎉</div>
          <div style={{ fontSize: "18px", fontWeight: 600, marginBottom: "6px" }}>No incidents found</div>
          <div style={{ fontSize: "14px" }}>{incidents.length > 0 ? "Try changing your filters" : "Upload a log file to detect your first incident"}</div>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
            {paginated.map(incident => (
              <IncidentCard key={incident.id} incident={incident} onStatusChange={updateStatus} onDelete={remove} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "12px" }}>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "10px", padding: "8px 14px", cursor: page === 1 ? "not-allowed" : "pointer", color: "var(--text-secondary)", display: "flex", alignItems: "center", opacity: page === 1 ? 0.4 : 1 }}>
                <ChevronLeft size={16} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                <button key={p} onClick={() => setPage(p)}
                  style={{ background: p === page ? "rgba(57,255,136,0.12)" : "var(--input-bg)", border: `1px solid ${p === page ? "var(--accent)" : "var(--border)"}`, borderRadius: "10px", padding: "8px 14px", cursor: "pointer", color: p === page ? "var(--accent)" : "var(--text-secondary)", fontWeight: p === page ? 700 : 400, minWidth: "40px" }}>
                  {p}
                </button>
              ))}
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "10px", padding: "8px 14px", cursor: page === totalPages ? "not-allowed" : "pointer", color: "var(--text-secondary)", display: "flex", alignItems: "center", opacity: page === totalPages ? 0.4 : 1 }}>
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
