"use client";

import { useState } from "react";
import { RotateCcw, ExternalLink } from "lucide-react";
import type { WorkflowRun } from "@/types";
import { conclusionColor } from "@/utils/formatters";
import { triggerWorkflowRerun } from "@/lib/api";

interface Props { workflows: WorkflowRun[]; }

export default function WorkflowList({ workflows }: Props) {
  const [rerunning, setRerunning] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleRerun(url: string) {
    setRerunning(url);
    setMessage(null);
    try {
      const res = await triggerWorkflowRerun(url);
      setMessage(res.message);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Rerun failed");
    } finally {
      setRerunning(null);
      setTimeout(() => setMessage(null), 4000);
    }
  }

  if (workflows.length === 0) {
    return <div style={{ color: "var(--text-tertiary)", fontSize: "14px" }}>No workflow data available.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      {message && (
        <div style={{ padding: "10px 16px", borderRadius: "10px", background: "rgba(57,255,136,0.1)", border: "1px solid rgba(57,255,136,0.3)", color: "#33ff88", fontSize: "13px", fontFamily: "monospace" }}>
          {message}
        </div>
      )}

      {workflows.map((wf, index) => (
        <div key={index} className="hover-card" style={{
          background: "var(--card-bg)", padding: "16px 18px", borderRadius: "12px",
          border: "1px solid var(--border)", display: "flex", justifyContent: "space-between",
          alignItems: "center", gap: "12px",
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: "var(--accent)", fontWeight: 700, marginBottom: "3px", fontSize: "14px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {wf.workflow}
            </div>
            <div style={{ color: "var(--text-tertiary)", fontSize: "12px" }}>
              {wf.branch} · {wf.actor} · #{wf.run_number}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ color: conclusionColor(wf.conclusion), fontWeight: 700, fontSize: "13px", textTransform: "capitalize" }}>
                {wf.conclusion ?? wf.status}
              </div>
              <div style={{ color: "var(--text-tertiary)", fontSize: "11px" }}>{wf.commit}</div>
            </div>

            {wf.conclusion === "failure" && (
              <button onClick={() => void handleRerun(wf.url)} disabled={rerunning === wf.url}
                title="Re-run this workflow" className="glow-button"
                style={{ padding: "6px 10px", borderRadius: "8px", background: "rgba(255,77,77,0.1)", border: "1px solid rgba(255,77,77,0.3)", color: "#ff4d4d", cursor: "pointer", display: "flex", alignItems: "center", gap: "5px", fontSize: "12px", fontWeight: 600 }}>
                <RotateCcw size={12} className={rerunning === wf.url ? "spin" : ""} />
                {rerunning === wf.url ? "..." : "Rerun"}
              </button>
            )}

            <a href={wf.url} target="_blank" rel="noopener noreferrer"
              style={{ padding: "6px 8px", borderRadius: "8px", background: "var(--input-bg)", border: "1px solid var(--border)", color: "var(--text-secondary)", display: "flex", alignItems: "center" }}>
              <ExternalLink size={12} />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
