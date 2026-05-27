"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2, ChevronDown, ChevronUp, Copy, CheckCheck, MessageSquare, ExternalLink } from "lucide-react";
import type { Incident, IncidentStatus } from "@/types";
import { severityColor, statusColor, timeAgo } from "@/utils/formatters";
import ChatPanel from "@/components/ChatPanel";

const STATUSES: IncidentStatus[] = ["Open", "In Progress", "Resolved", "Closed"];

interface Props {
  incident: Incident;
  onStatusChange: (id: number, status: IncidentStatus) => void;
  onDelete: (id: number) => void;
}

export default function IncidentCard({ incident, onStatusChange, onDelete }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const router = useRouter();

  function copyAsMarkdown() {
    const md = `## [${incident.severity}] ${incident.title}\n\n**Status:** ${incident.status}  \n**Confidence:** ${incident.confidence}%  \n**Created:** ${new Date(incident.created_at).toLocaleString()}\n\n### Description\n${incident.description}\n\n### Remediation\n${incident.remediation}`;
    void navigator.clipboard.writeText(md).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  }

  const sColor  = severityColor(incident.severity);
  const stColor = statusColor(incident.status);

  return (
    <>
      <div className="hover-card" style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderLeft: `3px solid ${sColor}`, borderRadius: "16px", padding: "18px 20px", backdropFilter: "blur(12px)" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "12px", justifyContent: "space-between" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "6px" }}>
              <span className="badge" style={{ background: `${sColor}18`, color: sColor, border: `1px solid ${sColor}44` }}>{incident.severity}</span>
              <span className="badge" style={{ background: `${stColor}18`, color: stColor, border: `1px solid ${stColor}44` }}>{incident.status}</span>
              <span style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>#{incident.id}</span>
              <span style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>{timeAgo(incident.created_at)}</span>
            </div>
            <div style={{ fontWeight: 600, fontSize: "15px", color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {incident.title}
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: "6px", flexShrink: 0, flexWrap: "wrap" }}>
            <select value={incident.status} onChange={e => onStatusChange(incident.id, e.target.value as IncidentStatus)}
              style={{ background: "var(--input-bg)", border: "1px solid var(--border)", color: "var(--text-primary)", borderRadius: "8px", padding: "6px 8px", fontSize: "12px", cursor: "pointer", outline: "none" }}>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>

            <button onClick={() => router.push(`/incidents/${incident.id}`)} title="View detail" style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px 8px", cursor: "pointer", color: "var(--text-secondary)", display: "flex", alignItems: "center" }}>
              <ExternalLink size={13} />
            </button>

            <button onClick={() => setChatOpen(o => !o)} title="AI Chat" style={{ background: chatOpen ? "rgba(57,255,136,0.1)" : "var(--input-bg)", border: `1px solid ${chatOpen ? "var(--accent)" : "var(--border)"}`, borderRadius: "8px", padding: "6px 8px", cursor: "pointer", color: chatOpen ? "var(--accent)" : "var(--text-secondary)", display: "flex", alignItems: "center" }}>
              <MessageSquare size={13} />
            </button>

            <button onClick={copyAsMarkdown} title="Copy as Markdown" style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px 8px", cursor: "pointer", color: "var(--text-secondary)", display: "flex", alignItems: "center" }}>
              {copied ? <CheckCheck size={13} color="#33ff88" /> : <Copy size={13} />}
            </button>

            <button onClick={() => setExpanded(e => !e)} title="Expand" style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px 8px", cursor: "pointer", color: "var(--text-secondary)", display: "flex", alignItems: "center" }}>
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>

            <button onClick={() => onDelete(incident.id)} title="Delete" style={{ background: "rgba(255,77,77,0.08)", border: "1px solid rgba(255,77,77,0.2)", borderRadius: "8px", padding: "6px 8px", cursor: "pointer", color: "#ff4d4d", display: "flex", alignItems: "center" }}>
              <Trash2 size={13} />
            </button>
          </div>
        </div>

        {/* Confidence bar */}
        <div style={{ marginTop: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-tertiary)", marginBottom: "4px" }}>
            <span>AI Confidence</span><span>{incident.confidence}%</span>
          </div>
          <div className="progress-bar" style={{ height: "5px" }}><div className="progress-fill" style={{ width: `${incident.confidence}%` }} /></div>
        </div>

        {/* Expanded detail */}
        {expanded && (
          <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginBottom: "4px" }}>Description</div>
              <div style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.6 }}>{incident.description}</div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginBottom: "4px" }}>Remediation</div>
              <div style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.6, whiteSpace: "pre-line" }}>{incident.remediation}</div>
            </div>
          </div>
        )}
      </div>

      {chatOpen && <ChatPanel incidentId={incident.id} incidentTitle={incident.title} onClose={() => setChatOpen(false)} />}
    </>
  );
}
