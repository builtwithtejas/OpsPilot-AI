"use client";

import { useEffect } from "react";
import AppShell from "@/components/AppShell";
import HealthCard from "@/components/HealthCard";
import MetricsCard from "@/components/MetricsCard";
import StatsCard from "@/components/StatsCard";
import Section from "@/components/Section";
import UploadBox from "@/components/UploadBox";
import AnalysisPanel from "@/components/AnalysisPanel";
import DeploymentPipeline from "@/components/DeploymentPipeline";
import Console from "@/components/Console";
import WorkflowList from "@/components/WorkflowList";
import CommandPanel from "@/components/CommandPanel";
import Charts from "@/components/Charts";
import ActivityFeed from "@/components/ActivityFeed";
import LoadingScreen from "@/components/LoadingScreen";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useLogUpload } from "@/hooks/useLogUpload";
import { useIncidents } from "@/hooks/useIncidents";
import { formatUptime } from "@/utils/formatters";

export default function Home() {
  const { analytics, workflows, metrics, loading, error, latency, refresh } = useAnalytics(30_000);
  const { result: uploadResult, loading: uploading, error: uploadError, upload } = useLogUpload();
  const { incidents } = useIncidents();
  const latestWorkflow = workflows[0] ?? null;

  // R to refresh
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "r" && !["INPUT","SELECT","TEXTAREA"].includes((document.activeElement as HTMLElement)?.tagName ?? "")) {
        void refresh();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [refresh]);

  if (loading && !analytics) return <LoadingScreen />;

  const apiColor = error ? "#ff4d4d" : "#33ff88";

  return (
    <AppShell onRefresh={refresh}>
      {/* Header */}
      <div className="fade-up" style={{ marginBottom: "32px", display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "clamp(36px,5vw,68px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>OpsPilot AI</h1>
          <p style={{ color: "var(--text-tertiary)", fontSize: "16px" }}>AI-Powered CI/CD Incident Intelligence</p>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <span className="kbd">R</span><span style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>refresh</span>
          <span className="kbd">⌘K</span><span style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>palette</span>
          <button onClick={() => void refresh()} className="glow-button" style={{ padding: "10px 18px", borderRadius: "12px", background: "rgba(0,195,255,0.1)", border: "1px solid #00c3ff55", color: "#00c3ff", fontWeight: 600, cursor: "pointer", fontSize: "13px" }}>↻ Refresh</button>
        </div>
      </div>

      {/* Health */}
      <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: "16px", marginBottom: "20px" }}>
        <HealthCard title="API Status"      value={`● ${error ? "Offline" : "Operational"}`}       color={apiColor} />
        <HealthCard title="Backend Latency" value={latency ? `${latency} ms` : "—"}                  color="#00c3ff" />
        <HealthCard title="Total Runs"      value={analytics ? String(analytics.stats.total) : "—"} color="#ffb347" />
        <HealthCard title="AI Engine"       value="GROQ ACTIVE"                                      color="#ff7a00" />
      </div>

      {/* System metrics */}
      {metrics && (
        <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: "16px", marginBottom: "20px" }}>
          <MetricsCard title="CPU"         value={`${metrics.cpu_usage}%`}                              color="#00c3ff" />
          <MetricsCard title="Memory"      value={`${metrics.memory_usage}%`}                           color="#ffb347" />
          <MetricsCard title="Memory Used" value={`${(metrics.memory_used_mb/1024).toFixed(1)} GB`}     color="#33ff88" />
          <MetricsCard title="Disk"        value={`${metrics.disk_usage}%`}                             color="#ff7a00" />
          <MetricsCard title="Uptime"      value={formatUptime(metrics.uptime_seconds)}                 color="#ff4d4d" />
          <MetricsCard title="Updated"     value={new Date(metrics.timestamp).toLocaleTimeString()}     color="#888" />
        </div>
      )}

      {/* Latest workflow */}
      {latestWorkflow && (
        <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: "16px", marginBottom: "20px" }}>
          <MetricsCard title="Workflow" value={latestWorkflow.workflow} color="#00c3ff" />
          <MetricsCard title="Branch"   value={latestWorkflow.branch}   color="#ffb347" />
          <MetricsCard title="Commit"   value={latestWorkflow.commit}   color="#33ff88" />
          <MetricsCard title="Actor"    value={latestWorkflow.actor}    color="#ff7a00" />
          <MetricsCard title="Run #"    value={latestWorkflow.run_number ? `#${latestWorkflow.run_number}` : "—"} color="#ff4d4d" />
          <MetricsCard title="Status"   value={latestWorkflow.conclusion ?? latestWorkflow.status}
            color={latestWorkflow.conclusion === "success" ? "#33ff88" : latestWorkflow.conclusion === "failure" ? "#ff4d4d" : "#ffb347"} />
        </div>
      )}

      {/* Stats */}
      {analytics && (
        <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: "16px", marginBottom: "28px" }}>
          <StatsCard title="Successful Runs" value={analytics.stats.success}           color="#33ff88" />
          <StatsCard title="Failed Runs"     value={analytics.stats.failed}            color="#ff4d4d" />
          <StatsCard title="Total Runs"      value={analytics.stats.total}             color="#00c3ff" />
          <StatsCard title="Success Rate"    value={analytics.stats.success_rate ?? 0} color="#ffb347" suffix="%" decimals={1} />
        </div>
      )}

      {/* Activity feed on dashboard too */}
      {(incidents.length > 0 || workflows.length > 0) && (
        <Section title="Recent Activity">
          <ActivityFeed incidents={incidents} workflows={workflows} />
        </Section>
      )}

      <Section title="Upload & Analyze Logs">
        <UploadBox onFile={upload} loading={uploading} />
      </Section>

      <Section title="AI Incident Analysis">
        <AnalysisPanel result={uploadResult} analytics={analytics} loading={uploading} error={uploadError} />
      </Section>

      <Section title="Deployment Pipeline">
        <DeploymentPipeline latestRun={latestWorkflow} />
      </Section>

      <Section title="Live DevOps Console">
        <Console workflows={workflows} />
      </Section>

      <Section title="Recent GitHub Workflows">
        <WorkflowList workflows={workflows} />
      </Section>

      {analytics && (
        <Section title="AI Suggested Commands">
          <CommandPanel commands={analytics.suggested_commands} />
        </Section>
      )}

      {analytics && (
        <Section title="Analytics">
          <Charts analytics={analytics} />
        </Section>
      )}
    </AppShell>
  );
}
