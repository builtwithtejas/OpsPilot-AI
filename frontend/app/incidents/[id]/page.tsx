"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import ChatPanel from "@/components/ChatPanel";
import SimilarIncidents from "@/components/SimilarIncidents";
import { severityColor, statusColor, timeAgo } from "@/utils/formatters";
import { MessageSquare, ArrowLeft, Clock, Link2 } from "lucide-react";
import type { Incident, IncidentStatus } from "@/types";
import { updateIncidentStatus, fetchIncidents } from "@/lib/api";

const BASE    = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";
const STATUSES: IncidentStatus[] = ["Open", "In Progress", "Resolved", "Closed"];

interface AuditEntry { id: number; action: string; detail: string; actor: string; created_at: string; }

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [allIncidents, setAllIncidents] = useState<Incident[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [incRes, auditRes, allInc] = await Promise.all([
          fetch(`${BASE}/incidents/${id}`, { headers: { "X-API-Key": API_KEY } }),
          fetch(`${BASE}/incidents/${id}/audit`, { headers: { "X-API-Key": API_KEY } }),
          fetchIncidents(),
        ]);
        if (!incRes.ok) { router.push("/incidents"); return; }
        setIncident(await incRes.json());
        if (auditRes.ok) setAudit(await auditRes.json());
        setAllIncidents(allInc);
      } finally { setLoading(false); }
    }
    void load();
  }, [id, router]);

  async function changeStatus(status: IncidentStatus) {
    if (!incident) return;
    const updated = await updateIncidentStatus(incident.id, status);
    setIncident(updated);
    const res = await fetch(`${BASE}/incidents/${id}/audit`, { headers: { "X-API-Key": API_KEY } });
    if (res.ok) setAudit(await res.json());
  }

  function copyLink() {
    void navigator.clipboard.writeText(window.location.href).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  }

  const ACTION_COLORS: Record<string, string> = { created: "#33ff88", status_changed: "#00c3ff", deleted: "#ff4d4d", severity_changed: "#ffb347" };

  if (loading) return <AppShell><div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>{[80,300,200,150].map((h,i) => <div key={i} className="skeleton" style={{ height: `${h}px`, borderRadius: "16px" }} />)}</div></AppShell>;
  if (!incident) return null;

  const sColor  = severityColor(incident.severity);
  const stColor = statusColor(incident.status);

  return (
    <AppShell>
      <div className="fade-up" style={{ marginBottom: "24px" }}>
        <button onClick={() => router.back()} style={{ background: "none", border: "none", color: "var(--text-tertiary)", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px", fontSize: "14px", marginBottom: "16px", padding: 0 }}>
          <ArrowLeft size={15} /> Back to Incidents
        </button>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div style={{ display: "flex", gap: "8px", marginBottom: "8px", flexWrap: "wrap", alignItems: "center" }}>
              <span className="badge" style={{ background: `${sColor}18`, color: sColor, border: `1px solid ${sColor}44` }}>{incident.severity}</span>
              <span className="badge" style={{ background: `${stColor}18`, color: stColor, border: `1px solid ${stColor}44` }}>{incident.status}</span>
              <span style={{ fontSize: "13px", color: "var(--text-tertiary)" }}>#{incident.id} · {timeAgo(incident.created_at)}</span>
            </div>
            <h1 style={{ fontSize: "clamp(20px,3vw,32px)", fontWeight: 700, color: "var(--text-primary)" }}>{incident.title}</h1>
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button onClick={copyLink} className="glow-button"
              style={{ padding: "8px 14px", borderRadius: "10px", background: "var(--input-bg)", border: "1px solid var(--border)", color: copied ? "var(--accent)" : "var(--text-secondary)", cursor: "pointer", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px" }}>
              <Link2 size={14} /> {copied ? "Copied!" : "Share link"}
            </button>
            <select value={incident.status} onChange={e => void changeStatus(e.target.value as IncidentStatus)}
              style={{ background: "var(--input-bg)", border: "1px solid var(--border)", color: "var(--text-primary)", borderRadius: "10px", padding: "8px 12px", fontSize: "13px", cursor: "pointer", outline: "none" }}>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button onClick={() => setChatOpen(o => !o)} className="glow-button"
              style={{ padding: "8px 16px", borderRadius: "10px", background: chatOpen ? "rgba(57,255,136,0.15)" : "var(--input-bg)", border: `1px solid ${chatOpen ? "var(--accent)" : "var(--border)"}`, color: chatOpen ? "var(--accent)" : "var(--text-primary)", cursor: "pointer", fontWeight: 600, fontSize: "13px", display: "flex", alignItems: "center", gap: "8px" }}>
              <MessageSquare size={14} /> AI Chat
            </button>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "14px", marginBottom: "20px" }}>
        {[
          { label: "Confidence", value: `${incident.confidence}%`, color: "#00c3ff" },
          { label: "Created",    value: new Date(incident.created_at).toLocaleDateString(), color: "var(--text-secondary)" },
          { label: "Updated",    value: new Date(incident.updated_at).toLocaleDateString(), color: "var(--text-secondary)" },
        ].map(s => (
          <div key={s.label} style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "14px", padding: "16px", backdropFilter: "blur(12px)" }}>
            <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginBottom: "4px" }}>{s.label}</div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Confidence bar */}
      <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "16px", padding: "20px", marginBottom: "16px", backdropFilter: "blur(12px)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", color: "var(--text-tertiary)", marginBottom: "10px" }}>
          <span>AI Confidence</span><span>{incident.confidence}%</span>
        </div>
        <div className="progress-bar"><div className="progress-fill" style={{ width: `${incident.confidence}%` }} /></div>
      </div>

      {/* Description + Remediation */}
      {[{ label: "Description", value: incident.description }, { label: "Remediation", value: incident.remediation }].map(s => (
        <div key={s.label} style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "16px", padding: "20px", marginBottom: "16px", backdropFilter: "blur(12px)" }}>
          <div style={{ fontSize: "13px", color: "var(--text-tertiary)", marginBottom: "10px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>{s.label}</div>
          <div style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-line" }}>{s.value}</div>
        </div>
      ))}

      {/* Similar incidents + Audit log side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
        <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "16px", padding: "20px", backdropFilter: "blur(12px)" }}>
          <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "16px" }}>Similar Incidents</div>
          <SimilarIncidents incident={incident} allIncidents={allIncidents} />
        </div>

        <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "16px", padding: "20px", backdropFilter: "blur(12px)" }}>
          <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Clock size={15} color="var(--accent)" /> Activity Timeline
          </div>
          {audit.length === 0 ? (
            <div style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>No activity yet.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column" }}>
              {audit.map((entry, i) => {
                const color = ACTION_COLORS[entry.action] ?? "#888";
                return (
                  <div key={entry.id} style={{ display: "flex", gap: "12px", alignItems: "flex-start", paddingBottom: "14px", position: "relative" }}>
                    {i < audit.length - 1 && <div style={{ position: "absolute", left: "7px", top: "18px", width: "2px", height: "calc(100% - 4px)", background: "var(--border)" }} />}
                    <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: color, flexShrink: 0, marginTop: "2px", zIndex: 1 }} />
                    <div>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", textTransform: "capitalize" }}>{entry.action.replace("_", " ")}</div>
                      {entry.detail && <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginTop: "2px" }}>{entry.detail}</div>}
                      <div style={{ fontSize: "11px", color: "var(--text-tertiary)", marginTop: "3px" }}>{timeAgo(entry.created_at)} · {entry.actor}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {chatOpen && <ChatPanel incidentId={incident.id} incidentTitle={incident.title} onClose={() => setChatOpen(false)} />}
    </AppShell>
  );
}
