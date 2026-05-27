"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import type { Incident } from "@/types";
import { severityColor, timeAgo } from "@/utils/formatters";

interface Props { incident: Incident; allIncidents: Incident[]; }

export default function SimilarIncidents({ incident, allIncidents }: Props) {
  const router = useRouter();

  const similar = useMemo(() => {
    const words = incident.title.toLowerCase().split(" ").filter(w => w.length > 4);
    return allIncidents
      .filter(i => i.id !== incident.id)
      .map(i => {
        const score =
          (i.severity === incident.severity ? 2 : 0) +
          words.filter(w => i.title.toLowerCase().includes(w) || i.description.toLowerCase().includes(w)).length;
        return { ...i, score };
      })
      .filter(i => i.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }, [incident, allIncidents]);

  if (similar.length === 0) {
    return <div style={{ color: "var(--text-tertiary)", fontSize: "14px" }}>No similar incidents found.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      {similar.map(inc => {
        const color = severityColor(inc.severity);
        return (
          <button key={inc.id} onClick={() => router.push(`/incidents/${inc.id}`)}
            className="hover-card"
            style={{ background: "var(--input-bg)", border: `1px solid ${color}33`, borderLeft: `3px solid ${color}`, borderRadius: "12px", padding: "12px 16px", cursor: "pointer", textAlign: "left", width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>#{inc.id} — {inc.title}</div>
                <div style={{ fontSize: "11px", color: "var(--text-tertiary)", marginTop: "2px" }}>{inc.severity} · {timeAgo(inc.created_at)}</div>
              </div>
              <span style={{ fontSize: "12px", color, fontWeight: 600, flexShrink: 0 }}>{inc.confidence}%</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
