"use client";

import AppShell from "@/components/AppShell";
import AgentPanel from "@/components/AgentPanel";
import Section from "@/components/Section";

export default function AgentPage() {
  return (
    <AppShell>
      <div className="fade-up" style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>
          AI Agent
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>
          Autonomous 6-step CI/CD incident response — Gemini × GitLab MCP
        </p>
      </div>

      {/* How it works */}
      <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "12px", marginBottom: "28px" }}>
        {[
          { step: "1", label: "Detect",   desc: "Finds failed pipelines in GitLab",        color: "#33ff88" },
          { step: "2", label: "Gather",   desc: "Retrieves job logs and failure details",   color: "#00c3ff" },
          { step: "3", label: "Analyse",  desc: "Gemini diagnoses root cause & severity",   color: "#ffb347" },
          { step: "4", label: "Record",   desc: "Persists incident to database",            color: "#ff7a00" },
          { step: "5", label: "Act",      desc: "Creates GitLab issue + MR comment",        color: "#ff4d4d" },
          { step: "6", label: "Notify",   desc: "Sends Slack + email alerts",               color: "#a855f7" },
        ].map(s => (
          <div key={s.step} className="hover-card" style={{ background: "var(--card-bg)", border: `1px solid ${s.color}33`, borderRadius: "14px", padding: "14px", backdropFilter: "blur(12px)" }}>
            <div style={{ width: "28px", height: "28px", borderRadius: "8px", background: `${s.color}18`, border: `1px solid ${s.color}44`, display: "flex", alignItems: "center", justifyContent: "center", color: s.color, fontWeight: 800, fontSize: "13px", marginBottom: "8px" }}>
              {s.step}
            </div>
            <div style={{ fontWeight: 700, fontSize: "13px", color: s.color, marginBottom: "4px" }}>{s.label}</div>
            <div style={{ fontSize: "12px", color: "var(--text-tertiary)", lineHeight: 1.4 }}>{s.desc}</div>
          </div>
        ))}
      </div>

      <Section title="Run the Agent">
        <AgentPanel />
      </Section>
    </AppShell>
  );
}
