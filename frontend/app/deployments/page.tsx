"use client";

import AppShell from "@/components/AppShell";
import DeploymentPipeline from "@/components/DeploymentPipeline";
import WorkflowList from "@/components/WorkflowList";
import Console from "@/components/Console";
import Section from "@/components/Section";
import { useAnalytics } from "@/hooks/useAnalytics";
import { conclusionColor } from "@/utils/formatters";

export default function DeploymentsPage() {
  const { workflows, analytics, loading } = useAnalytics(30_000);
  const latest = workflows[0] ?? null;

  return (
    <AppShell>
      <div className="fade-up" style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>
          Deployments
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>GitHub Actions workflow runs</p>
      </div>

      {/* Stats row */}
      {analytics && (
        <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: "14px", marginBottom: "24px" }}>
          {[
            { label: "Total", value: analytics.stats.total, color: "#00c3ff" },
            { label: "Success", value: analytics.stats.success, color: "#33ff88" },
            { label: "Failed", value: analytics.stats.failed, color: "#ff4d4d" },
            { label: "Success Rate", value: `${analytics.stats.success_rate}%`, color: "#ffb347" },
          ].map(s => (
            <div key={s.label} className="hover-card" style={{
              background: "var(--card-bg)", border: `1px solid ${s.color}33`,
              borderRadius: "16px", padding: "16px", backdropFilter: "blur(12px)",
            }}>
              <div style={{ color: "var(--text-tertiary)", fontSize: "12px", marginBottom: "4px" }}>{s.label}</div>
              <div style={{ color: s.color, fontSize: "28px", fontWeight: 700 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      <Section title="Current Pipeline">
        {loading ? <div className="skeleton" style={{ height: "80px" }} /> : <DeploymentPipeline latestRun={latest} />}
      </Section>

      <Section title="Live Console">
        <Console workflows={workflows} />
      </Section>

      <Section title="Recent Workflow Runs">
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: "64px" }} />)}
          </div>
        ) : <WorkflowList workflows={workflows} />}
      </Section>
    </AppShell>
  );
}
