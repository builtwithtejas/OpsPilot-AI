"use client";

import type { AnalyzeResult, AnalyticsData } from "@/types";
import { severityColor } from "@/utils/formatters";
import { downloadIncidentPdf } from "@/lib/api";

interface Props {
  result: AnalyzeResult | null;
  analytics: AnalyticsData | null;
  loading: boolean;
  error: string | null;
}

export default function AnalysisPanel({ result, analytics, loading, error }: Props) {
  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {[200, 80, 120].map((w, i) => <div key={i} className="skeleton" style={{ height: "20px", width: `${w}px` }} />)}
      </div>
    );
  }

  if (error) {
    return <div style={{ color: "#ff4d4d", fontFamily: "monospace", fontSize: "15px" }}>⚠ Analysis failed: {error}</div>;
  }

  if (!result) {
    return <div style={{ color: "var(--text-tertiary)", fontFamily: "monospace", fontSize: "14px" }}>Upload a log file above to see AI analysis.</div>;
  }

  const sColor = severityColor(result.severity);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div style={{ color: "var(--accent)", fontFamily: "monospace", fontSize: "15px", lineHeight: 1.7 }}>
        {result.summary}
      </div>

      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
        {[
          { label: "Severity",   value: result.severity,         color: sColor },
          { label: "Confidence", value: `${result.confidence}%`, color: "#00c3ff" },
          { label: "Status",     value: result.status,           color: "#ffb347" },
        ].map(p => (
          <div key={p.label} style={{ padding: "6px 14px", borderRadius: "999px", border: `1px solid ${p.color}55`, background: `${p.color}11`, fontSize: "13px", color: p.color, fontWeight: 600 }}>
            {p.label}: {p.value}
          </div>
        ))}
      </div>

      <div>
        <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginBottom: "6px" }}>Root cause</div>
        <div style={{ color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.6 }}>{result.root_cause}</div>
      </div>

      <div>
        <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginBottom: "6px" }}>Remediation</div>
        <div style={{ color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.6, whiteSpace: "pre-line" }}>{result.remediation}</div>
      </div>

      <div>
        <div style={{ marginBottom: "6px", color: "var(--text-tertiary)", fontSize: "12px" }}>AI Confidence — {result.confidence}%</div>
        <div className="progress-bar"><div className="progress-fill" style={{ width: `${result.confidence}%` }} /></div>
      </div>

      {analytics && (
        <button onClick={() => void downloadIncidentPdf([], analytics)} className="glow-button"
          style={{ alignSelf: "flex-start", background: "linear-gradient(to right,#33ff88,#00c3ff)", border: "none", color: "black", padding: "12px 22px", borderRadius: "12px", fontWeight: 700, cursor: "pointer", fontSize: "14px" }}>
          Download Incident PDF
        </button>
      )}
    </div>
  );
}
