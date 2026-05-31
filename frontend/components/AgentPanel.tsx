"use client";

import { useState } from "react";
import { triggerAgent, fetchFailedPipelines } from "@/lib/api";
import type { AgentRun, GitLabPipeline } from "@/types";
import { Bot, Play, CheckCircle, XCircle, Loader, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

const STEP_LABELS: Record<string, string> = {
  detect_failed_pipeline: "Detect failed pipeline",
  gather_job_logs:        "Gather job logs",
  gemini_analysis:        "Gemini AI analysis",
  record_incident:        "Record incident",
  gitlab_action:          "Create GitLab issue + MR comment",
  notify:                 "Send notifications",
};

export default function AgentPanel() {
  const [projectId, setProjectId] = useState("");
  const [pipelines, setPipelines] = useState<GitLabPipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPipelines, setLoadingPipelines] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  async function loadPipelines() {
    if (!projectId.trim()) return;
    setLoadingPipelines(true);
    setError(null);
    try {
      const data = await fetchFailedPipelines(projectId.trim());
      setPipelines(data.failed_pipelines);
      if (data.failed_pipelines.length === 0) setError("No failed pipelines found — system healthy!");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load pipelines");
    } finally {
      setLoadingPipelines(false);
    }
  }

  async function runAgent() {
    if (!projectId.trim()) return;
    setLoading(true);
    setError(null);
    setRun(null);
    try {
      const result = await triggerAgent(projectId.trim(), selectedPipeline ?? undefined);
      setRun(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Agent run failed");
    } finally {
      setLoading(false);
    }
  }

  const statusIcon = (status: string) => {
    if (status === "done")    return <CheckCircle size={15} color="#33ff88" />;
    if (status === "failed")  return <XCircle size={15} color="#ff4d4d" />;
    if (status === "running") return <Loader size={15} color="#00c3ff" className="spin" />;
    return <div style={{ width: 15, height: 15, borderRadius: "50%", background: "#333" }} />;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "16px 20px", background: "linear-gradient(135deg,rgba(57,255,136,0.08),rgba(0,195,255,0.08))", border: "1px solid rgba(57,255,136,0.2)", borderRadius: "16px" }}>
        <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "linear-gradient(135deg,#33ff88,#00c3ff)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Bot size={22} color="black" />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "16px" }}>OpsPilot Autonomous Agent</div>
          <div style={{ fontSize: "13px", color: "var(--text-tertiary)" }}>Gemini 2.5 Flash × GitLab MCP · 6-step orchestrated pipeline</div>
        </div>
      </div>

      {/* Project input */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <input
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          placeholder="GitLab project ID or namespace/project (e.g. 12345 or mygroup/myrepo)"
          style={{ flex: 1, minWidth: "260px", background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "12px", padding: "12px 16px", color: "var(--text-primary)", fontSize: "14px", outline: "none" }}
          onKeyDown={e => { if (e.key === "Enter") void loadPipelines(); }}
        />
        <button onClick={() => void loadPipelines()} disabled={!projectId.trim() || loadingPipelines}
          style={{ padding: "12px 18px", borderRadius: "12px", background: "var(--input-bg)", border: "1px solid var(--border)", color: "var(--text-secondary)", cursor: "pointer", fontWeight: 600, fontSize: "13px", whiteSpace: "nowrap" }}>
          {loadingPipelines ? "Loading…" : "Load Pipelines"}
        </button>
      </div>

      {/* Failed pipelines picker */}
      {pipelines.length > 0 && (
        <div>
          <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Select pipeline to analyse (or leave blank to auto-detect)
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <button onClick={() => setSelectedPipeline(null)}
              style={{ padding: "10px 14px", borderRadius: "10px", background: selectedPipeline === null ? "rgba(57,255,136,0.1)" : "var(--input-bg)", border: `1px solid ${selectedPipeline === null ? "var(--accent)" : "var(--border)"}`, color: "var(--text-primary)", cursor: "pointer", textAlign: "left", fontSize: "13px" }}>
              Auto-detect latest failure
            </button>
            {pipelines.map(p => (
              <button key={p.id} onClick={() => setSelectedPipeline(p.id)}
                style={{ padding: "10px 14px", borderRadius: "10px", background: selectedPipeline === p.id ? "rgba(255,77,77,0.08)" : "var(--input-bg)", border: `1px solid ${selectedPipeline === p.id ? "#ff4d4d" : "var(--border)"}`, color: "var(--text-primary)", cursor: "pointer", textAlign: "left", fontSize: "13px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Pipeline #{p.id} — {p.ref} · {p.sha}</span>
                <span style={{ color: "#ff4d4d", fontWeight: 700, fontSize: "12px" }}>{p.status}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Run button */}
      <button onClick={() => void runAgent()} disabled={!projectId.trim() || loading}
        className="glow-button"
        style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", padding: "14px 24px", borderRadius: "14px", background: loading ? "var(--input-bg)" : "linear-gradient(to right,#33ff88,#00c3ff)", border: "none", color: loading ? "var(--text-tertiary)" : "black", fontWeight: 800, fontSize: "16px", cursor: loading || !projectId.trim() ? "not-allowed" : "pointer" }}>
        {loading ? <><Loader size={18} className="spin" /> Running agent…</> : <><Play size={18} /> Run Agent</>}
      </button>

      {/* Error */}
      {error && (
        <div style={{ padding: "12px 16px", borderRadius: "12px", background: "rgba(255,77,77,0.08)", border: "1px solid rgba(255,77,77,0.3)", color: "#ff4d4d", fontSize: "14px", fontFamily: "monospace" }}>
          ⚠ {error}
        </div>
      )}

      {/* Run result */}
      {run && (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>

          {/* Status bar */}
          <div style={{ padding: "16px 20px", borderRadius: "14px", background: run.status === "completed" ? "rgba(57,255,136,0.08)" : run.status === "failed" ? "rgba(255,77,77,0.08)" : "rgba(0,195,255,0.08)", border: `1px solid ${run.status === "completed" ? "rgba(57,255,136,0.3)" : run.status === "failed" ? "rgba(255,77,77,0.3)" : "rgba(0,195,255,0.3)"}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: "15px", color: run.status === "completed" ? "#33ff88" : run.status === "failed" ? "#ff4d4d" : "#00c3ff", textTransform: "capitalize" }}>
                {run.status === "completed" ? "✓ Agent completed" : run.status === "failed" ? "✗ Agent failed" : run.status === "healthy" ? "✓ System healthy" : "Running…"}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginTop: "2px" }}>Run ID: {run.run_id}{run.incident_id ? ` · Incident #${run.incident_id}` : ""}</div>
            </div>
            {run.gitlab_issue_url && (
              <a href={run.gitlab_issue_url} target="_blank" rel="noopener noreferrer"
                style={{ display: "flex", alignItems: "center", gap: "6px", padding: "8px 14px", borderRadius: "10px", background: "rgba(57,255,136,0.1)", border: "1px solid var(--accent)", color: "var(--accent)", textDecoration: "none", fontWeight: 600, fontSize: "13px" }}>
                <ExternalLink size={13} /> View GitLab Issue
              </a>
            )}
          </div>

          {/* Steps */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {run.steps.map((step, i) => (
              <div key={i}>
                <button onClick={() => setExpanded(expanded === step.name ? null : step.name)}
                  style={{ width: "100%", display: "flex", alignItems: "center", gap: "10px", padding: "12px 16px", borderRadius: "12px", background: "var(--card-bg)", border: "1px solid var(--border)", cursor: "pointer", textAlign: "left" }}>
                  {statusIcon(step.status)}
                  <span style={{ flex: 1, fontSize: "14px", fontWeight: 500, color: "var(--text-primary)" }}>{STEP_LABELS[step.name] ?? step.name}</span>
                  <span style={{ fontSize: "12px", color: step.status === "done" ? "#33ff88" : step.status === "failed" ? "#ff4d4d" : "var(--text-tertiary)", textTransform: "capitalize" }}>{step.status}</span>
                  {expanded === step.name ? <ChevronUp size={14} color="var(--text-tertiary)" /> : <ChevronDown size={14} color="var(--text-tertiary)" />}
                </button>

                {expanded === step.name && (
                  <div style={{ marginTop: "4px", padding: "12px 16px", borderRadius: "10px", background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", fontFamily: "monospace", fontSize: "12px", color: "#aaa" }}>
                    {step.error
                      ? <span style={{ color: "#ff4d4d" }}>Error: {step.error}</span>
                      : <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{JSON.stringify(step.result, null, 2)}</pre>
                    }
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
