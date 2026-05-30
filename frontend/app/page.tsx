"use client";

import AppShell from "@/components/AppShell";
import Charts from "@/components/Charts";
import ConfidenceChart from "@/components/ConfidenceChart";
import ActivityFeed from "@/components/ActivityFeed";
import CommandPanel from "@/components/CommandPanel";
import Section from "@/components/Section";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useIncidents } from "@/hooks/useIncidents";

export default function AnalyticsPage() {
  const { analytics, workflows, loading, error, latency } = useAnalytics(30_000);
  const { incidents } = useIncidents();

  return (
    <AppShell>
      <div className="fade-up" style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>
          Analytics
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>
          Real-time CI/CD pipeline intelligence{latency ? ` · ${latency}ms` : ""}
        </p>
      </div>

      {loading && !analytics ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {[120, 300, 260, 260].map((h, i) => <div key={i} className="skeleton" style={{ height: `${h}px`, borderRadius: "16px" }} />)}
        </div>
      ) : error ? (
        <div style={{ color: "#ff4d4d", fontFamily: "monospace", padding: "20px" }}>⚠ {error}</div>
      ) : analytics ? (
        <>
          <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "14px", marginBottom: "28px" }}>
            {[
              { label: "Total Runs",   value: analytics.stats.total,              color: "#00c3ff" },
              { label: "Successful",   value: analytics.stats.success,            color: "#33ff88" },
              { label: "Failed",       value: analytics.stats.failed,             color: "#ff4d4d" },
              { label: "Success Rate", value: `${analytics.stats.success_rate}%`, color: "#ffb347" },
            ].map(s => (
              <div key={s.label} className="hover-card" style={{ background: "var(--card-bg)", border: `1px solid ${s.color}33`, borderRadius: "16px", padding: "18px", backdropFilter: "blur(12px)" }}>
                <div style={{ color: "var(--text-tertiary)", fontSize: "13px", marginBottom: "6px" }}>{s.label}</div>
                <div style={{ color: s.color, fontSize: "30px", fontWeight: 700 }}>{s.value}</div>
              </div>
            ))}
          </div>

          <Section title="AI System Analysis">
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, fontSize: "15px", fontFamily: "monospace" }}>{analytics.analysis}</p>
          </Section>

          <Section title="AI Confidence Score History">
            <ConfidenceChart incidents={incidents} />
          </Section>

          <Section title="Pipeline Charts">
            <Charts analytics={analytics} />
          </Section>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
            <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "20px", padding: "24px", backdropFilter: "blur(12px)" }}>
              <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "20px" }}>Activity Feed</h2>
              <ActivityFeed incidents={incidents} workflows={workflows} />
            </div>
            <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "20px", padding: "24px", backdropFilter: "blur(12px)" }}>
              <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "20px" }}>AI Suggested Commands</h2>
              <CommandPanel commands={analytics.suggested_commands} />
            </div>
          </div>
        </>
      ) : null}
    </AppShell>
  );
}