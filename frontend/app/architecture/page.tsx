export default function ArchitecturePage() {
  return (
    <div style={{ minHeight: "100vh", background: "#000", color: "white", padding: "40px", fontFamily: "Arial" }}>
      <h1 style={{ fontSize: "32px", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "8px" }}>
        OpsPilot AI — Architecture
      </h1>
      <p style={{ color: "#666", marginBottom: "40px" }}>Google Cloud Rapid Agent Hackathon · GitLab Track</p>
      <div style={{ display: "grid", gap: "20px" }}>
        {[
          { step: "1 — Detect",  color: "#33ff88", desc: "Agent calls GitLab MCP → get_failed_pipelines() to find recent failures" },
          { step: "2 — Gather",  color: "#00c3ff", desc: "Agent calls GitLab MCP → get_pipeline_jobs() to collect failure details and logs" },
          { step: "3 — Analyse", color: "#ffb347", desc: "Google Gemini 1.5 Flash analyses logs → returns structured JSON: severity, root_cause, remediation, confidence" },
          { step: "4 — Record",  color: "#ff7a00", desc: "Incident persisted to database with full audit trail" },
          { step: "5 — Act",     color: "#ff4d4d", desc: "Agent calls GitLab MCP → creates issue with Gemini analysis + posts remediation comment on open MR" },
          { step: "6 — Notify",  color: "#a855f7", desc: "Slack webhook + SendGrid email fired for High/Critical incidents" },
        ].map(s => (
          <div key={s.step} style={{ padding: "20px", borderRadius: "14px", background: "#0a0a0a", border: `1px solid ${s.color}33`, display: "flex", gap: "16px", alignItems: "flex-start" }}>
            <div style={{ color: s.color, fontWeight: 800, fontSize: "15px", whiteSpace: "nowrap", fontFamily: "monospace" }}>{s.step}</div>
            <div style={{ color: "#aaa", fontSize: "14px", lineHeight: 1.6 }}>{s.desc}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: "40px", padding: "24px", borderRadius: "14px", background: "#050505", border: "1px solid #222", fontFamily: "monospace", fontSize: "13px", color: "#555", lineHeight: 1.8 }}>
        <div style={{ color: "#33ff88", marginBottom: "12px", fontWeight: 700 }}>Tech Stack</div>
        {[
          ["AI Model",       "Google Gemini 1.5 Flash"],
          ["MCP Integration","GitLab REST API"],
          ["Backend",        "FastAPI + Python 3.11 → Google Cloud Run"],
          ["Frontend",       "Next.js 14 → Vercel"],
          ["Database",       "SQLite / Postgres (SQLAlchemy)"],
          ["Notifications",  "Slack + SendGrid"],
          ["Auth",           "API Key middleware"],
          ["Rate limiting",  "slowapi 200 req/min"],
        ].map(([k, v]) => (
          <div key={k}><span style={{ color: "#444" }}>{k.padEnd(18)}</span><span style={{ color: "#888" }}>{v}</span></div>
        ))}
      </div>
    </div>
  );
}
