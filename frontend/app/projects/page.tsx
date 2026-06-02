"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import Section from "@/components/Section";

const BASE    = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

interface Project {
  id: number;
  gitlab_project_id: string;
  name: string;
  description: string | null;
  active: boolean;
  created_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects]   = useState<Project[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState("");
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving]       = useState(false);
  const [form, setForm] = useState({
    gitlab_project_id: "",
    name: "",
    description: "",
  });

  async function load() {
    try {
      const res = await fetch(`${BASE}/projects/`, { headers: { "X-API-Key": API_KEY } });
      if (res.ok) setProjects(await res.json());
    } catch (e) {
      setError("Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function register() {
    if (!form.gitlab_project_id.trim() || !form.name.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${BASE}/projects/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Failed to register");
      }
      await load();
      setShowModal(false);
      setForm({ gitlab_project_id: "", name: "", description: "" });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to register project");
    } finally {
      setSaving(false);
    }
  }

  async function toggleProject(id: number) {
    await fetch(`${BASE}/projects/${id}/toggle`, {
      method: "PATCH",
      headers: { "X-API-Key": API_KEY },
    });
    await load();
  }

  async function removeProject(id: number) {
    if (!confirm("Remove this project from monitoring?")) return;
    await fetch(`${BASE}/projects/${id}`, {
      method: "DELETE",
      headers: { "X-API-Key": API_KEY },
    });
    await load();
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="fade-up" style={{ marginBottom: "28px", display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#fc6d26,#e24329)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>
            Monitored Projects
          </h1>
          <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>
            GitLab repositories monitored by OpsPilot AI · {projects.length} registered
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="glow-button"
          style={{ padding: "12px 20px", borderRadius: "12px", background: "linear-gradient(to right,#e24329,#fc6d26)", border: "none", color: "white", fontWeight: 700, fontSize: "14px", cursor: "pointer" }}
        >
          + Register Project
        </button>
      </div>

      {/* Stats */}
      <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "14px", marginBottom: "28px" }}>
        {[
          { label: "Total Projects",  value: projects.length,                              color: "#fc6d26" },
          { label: "Active",          value: projects.filter(p => p.active).length,        color: "#33ff88" },
          { label: "Paused",          value: projects.filter(p => !p.active).length,       color: "#ffb347" },
          { label: "Webhook Ready",   value: projects.length > 0 ? "✓" : "—",             color: "#00c3ff" },
        ].map(s => (
          <div key={s.label} className="hover-card" style={{ background: "var(--card-bg)", border: `1px solid ${s.color}33`, borderRadius: "16px", padding: "18px", backdropFilter: "blur(12px)" }}>
            <div style={{ color: "var(--text-tertiary)", fontSize: "13px", marginBottom: "6px" }}>{s.label}</div>
            <div style={{ color: s.color, fontSize: "30px", fontWeight: 700 }}>{s.value}</div>
          </div>
        ))}
      </div>

      {error && (
        <div style={{ color: "#ff4d4d", background: "rgba(255,77,77,0.08)", border: "1px solid rgba(255,77,77,0.2)", borderRadius: "12px", padding: "12px 16px", marginBottom: "16px", fontSize: "13px" }}>
          ⚠ {error}
        </div>
      )}

      {/* Project list */}
      <Section title="Registered Repositories">
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: "80px", borderRadius: "16px" }} />)}
          </div>
        ) : projects.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-tertiary)" }}>
            <div style={{ fontSize: "40px", marginBottom: "12px" }}>🦊</div>
            <div style={{ fontSize: "15px", marginBottom: "6px" }}>No projects registered yet</div>
            <div style={{ fontSize: "13px" }}>Register a GitLab project to start autonomous monitoring</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {projects.map(p => (
              <div key={p.id} className="hover-card" style={{
                background: "var(--card-bg)",
                border: `1px solid ${p.active ? "rgba(51,255,136,0.2)" : "var(--border)"}`,
                borderLeft: `3px solid ${p.active ? "#33ff88" : "#888"}`,
                borderRadius: "16px",
                padding: "18px 20px",
                backdropFilter: "blur(12px)",
                display: "flex",
                alignItems: "center",
                gap: "16px",
                flexWrap: "wrap",
              }}>
                {/* Icon */}
                <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "linear-gradient(135deg,#e24329,#fc6d26)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", flexShrink: 0 }}>
                  🦊
                </div>

                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px", flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 700, fontSize: "15px", color: "var(--text-primary)" }}>{p.name}</span>
                    <span style={{
                      fontSize: "11px", fontWeight: 600, padding: "2px 8px", borderRadius: "6px",
                      background: p.active ? "rgba(51,255,136,0.12)" : "rgba(136,136,136,0.12)",
                      color: p.active ? "#33ff88" : "#888",
                      border: `1px solid ${p.active ? "rgba(51,255,136,0.3)" : "rgba(136,136,136,0.3)"}`,
                    }}>
                      {p.active ? "● Active" : "○ Paused"}
                    </span>
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-tertiary)", display: "flex", gap: "12px", flexWrap: "wrap" }}>
                    <span>ID: {p.gitlab_project_id}</span>
                    {p.description && <span>{p.description}</span>}
                    <span>Added {new Date(p.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Webhook URL */}
                <div style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px 10px", fontSize: "11px", fontFamily: "monospace", color: "var(--text-tertiary)", maxWidth: "260px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  /webhooks/gitlab
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: "6px", flexShrink: 0 }}>
                  <button
                    onClick={() => toggleProject(p.id)}
                    aria-label={p.active ? "Pause monitoring" : "Resume monitoring"}
                    title={p.active ? "Pause" : "Resume"}
                    style={{ padding: "8px 14px", borderRadius: "8px", background: "var(--input-bg)", border: "1px solid var(--border)", color: p.active ? "#ffb347" : "#33ff88", cursor: "pointer", fontSize: "12px", fontWeight: 600 }}
                  >
                    {p.active ? "⏸ Pause" : "▶ Resume"}
                  </button>
                  <button
                    onClick={() => removeProject(p.id)}
                    aria-label="Remove project"
                    title="Remove"
                    style={{ padding: "8px 10px", borderRadius: "8px", background: "rgba(255,77,77,0.08)", border: "1px solid rgba(255,77,77,0.2)", color: "#ff4d4d", cursor: "pointer", fontSize: "13px" }}
                  >
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Webhook setup guide */}
      {projects.length > 0 && (
        <Section title="Webhook Configuration">
          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "16px", padding: "20px", backdropFilter: "blur(12px)" }}>
            <div style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: "12px" }}>
              Configure this webhook URL in each GitLab project to enable autonomous pipeline monitoring:
            </div>
            <div style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "10px", padding: "12px 16px", fontFamily: "monospace", fontSize: "13px", color: "#33ff88", marginBottom: "12px", wordBreak: "break-all" }}>
              {BASE}/webhooks/gitlab
            </div>
            <div style={{ fontSize: "13px", color: "var(--text-tertiary)", lineHeight: 1.8 }}>
              <div>1. Go to your GitLab project → <strong>Settings → Webhooks</strong></div>
              <div>2. Paste the URL above</div>
              <div>3. Enable <strong>Pipeline events</strong> trigger</div>
              <div>4. Add your <strong>GITLAB_WEBHOOK_SECRET</strong> as the secret token</div>
              <div>5. Click <strong>Add webhook</strong></div>
            </div>
          </div>
        </Section>
      )}

      {/* Register modal */}
      {showModal && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
          display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000, backdropFilter: "blur(8px)",
        }}>
          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "20px", padding: "28px", width: "min(480px,90vw)", backdropFilter: "blur(24px)" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "6px" }}>Register GitLab Project</h2>
            <p style={{ fontSize: "13px", color: "var(--text-tertiary)", marginBottom: "20px" }}>Add a GitLab project to monitor for pipeline failures</p>

            <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginBottom: "20px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "var(--text-tertiary)", display: "block", marginBottom: "6px" }}>
                  GitLab Project ID or namespace/project *
                </label>
                <input
                  value={form.gitlab_project_id}
                  onChange={e => setForm(f => ({ ...f, gitlab_project_id: e.target.value }))}
                  placeholder="e.g. 82734152 or mygroup/myproject"
                  style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "10px", padding: "10px 14px", color: "var(--text-primary)", fontSize: "13px", outline: "none", boxSizing: "border-box" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--text-tertiary)", display: "block", marginBottom: "6px" }}>
                  Project name *
                </label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. opspilot-demo"
                  style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "10px", padding: "10px 14px", color: "var(--text-primary)", fontSize: "13px", outline: "none", boxSizing: "border-box" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--text-tertiary)", display: "block", marginBottom: "6px" }}>
                  Description (optional)
                </label>
                <input
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="e.g. Main deployment pipeline"
                  style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "10px", padding: "10px 14px", color: "var(--text-primary)", fontSize: "13px", outline: "none", boxSizing: "border-box" }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                onClick={() => { setShowModal(false); setError(""); }}
                style={{ padding: "10px 18px", borderRadius: "10px", background: "var(--input-bg)", border: "1px solid var(--border)", color: "var(--text-secondary)", cursor: "pointer", fontSize: "13px" }}
              >
                Cancel
              </button>
              <button
                onClick={register}
                disabled={saving || !form.gitlab_project_id.trim() || !form.name.trim()}
                style={{ padding: "10px 20px", borderRadius: "10px", background: saving ? "rgba(252,109,38,0.3)" : "linear-gradient(to right,#e24329,#fc6d26)", border: "none", color: "white", fontWeight: 700, fontSize: "13px", cursor: saving ? "not-allowed" : "pointer" }}
              >
                {saving ? "Registering..." : "Register Project"}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}