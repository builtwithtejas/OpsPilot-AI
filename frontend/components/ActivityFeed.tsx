"use client";

import type { Incident, WorkflowRun } from "@/types";
import { severityColor, conclusionColor, timeAgo } from "@/utils/formatters";
import { AlertTriangle, Rocket, CheckCircle, XCircle } from "lucide-react";

interface FeedItem {
  id: string;
  type: "incident" | "workflow";
  title: string;
  subtitle: string;
  color: string;
  icon: React.ReactNode;
  time: string;
}

interface Props {
  incidents: Incident[];
  workflows: WorkflowRun[];
}

export default function ActivityFeed({ incidents, workflows }: Props) {
  const items: FeedItem[] = [
    ...incidents.slice(0, 8).map(inc => ({
      id: `inc-${inc.id}`,
      type: "incident" as const,
      title: `Incident #${inc.id} — ${inc.status}`,
      subtitle: inc.title.slice(0, 60) + (inc.title.length > 60 ? "…" : ""),
      color: severityColor(inc.severity),
      icon: inc.status === "Resolved" ? <CheckCircle size={14} /> : <AlertTriangle size={14} />,
      time: inc.updated_at,
    })),
    ...workflows.slice(0, 6).map((wf, i) => ({
      id: `wf-${i}`,
      type: "workflow" as const,
      title: `${wf.workflow} — ${wf.conclusion ?? wf.status}`,
      subtitle: `${wf.branch} · ${wf.actor} · #${wf.run_number}`,
      color: conclusionColor(wf.conclusion),
      icon: wf.conclusion === "failure" ? <XCircle size={14} /> : <Rocket size={14} />,
      time: wf.created_at,
    })),
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 12);

  if (items.length === 0) {
    return <div style={{ color: "var(--text-tertiary)", fontSize: "14px", padding: "20px 0" }}>No activity yet — data will appear here as incidents and deployments are recorded.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
      {items.map((item, i) => (
        <div key={item.id} style={{ display: "flex", gap: "14px", alignItems: "flex-start", paddingBottom: "16px", position: "relative" }}>
          {i < items.length - 1 && (
            <div style={{ position: "absolute", left: "11px", top: "24px", width: "2px", height: "calc(100% - 8px)", background: "var(--border)" }} />
          )}
          <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: `${item.color}18`, border: `1.5px solid ${item.color}55`, display: "flex", alignItems: "center", justifyContent: "center", color: item.color, flexShrink: 0, zIndex: 1, marginTop: "1px" }}>
            {item.icon}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "2px" }}>{item.title}</div>
            <div style={{ fontSize: "12px", color: "var(--text-tertiary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.subtitle}</div>
            <div style={{ fontSize: "11px", color: "var(--text-tertiary)", marginTop: "3px" }}>{timeAgo(item.time)}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
