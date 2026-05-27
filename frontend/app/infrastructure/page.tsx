"use client";

import AppShell from "@/components/AppShell";
import Section from "@/components/Section";
import { useMetrics } from "@/hooks/useMetrics";
import { formatUptime } from "@/utils/formatters";

function GaugeBar({ value, label, color }: { value: number; label: string; color: string }) {
  const status = value > 90 ? "Critical" : value > 70 ? "Warning" : "Healthy";
  const statusColor = value > 90 ? "#ff4d4d" : value > 70 ? "#ffb347" : "#33ff88";
  return (
    <div className="hover-card" style={{
      background: "var(--card-bg)", border: `1px solid ${color}33`,
      borderRadius: "16px", padding: "20px", backdropFilter: "blur(12px)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "14px" }}>{label}</span>
        <span className="badge" style={{ background: `${statusColor}18`, color: statusColor, border: `1px solid ${statusColor}44`, fontSize: "11px" }}>{status}</span>
      </div>
      <div style={{ color, fontSize: "36px", fontWeight: 700, marginBottom: "10px" }}>{value}%</div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${value}%`, background: `linear-gradient(to right,${color},${statusColor})` }} />
      </div>
    </div>
  );
}

export default function InfrastructurePage() {
  const { metrics, error } = useMetrics();

  return (
    <AppShell>
      <div className="fade-up" style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>
          Infrastructure
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>
          Real-time system metrics · refreshes every 15s
          {metrics && <span> · Last updated {new Date(metrics.timestamp).toLocaleTimeString()}</span>}
        </p>
      </div>

      {error && <div style={{ color: "#ff4d4d", fontFamily: "monospace", marginBottom: "16px" }}>⚠ {error}</div>}

      {!metrics ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: "16px" }}>
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: "120px" }} />)}
        </div>
      ) : (
        <>
          <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: "16px", marginBottom: "24px" }}>
            <GaugeBar value={metrics.cpu_usage} label="CPU Usage" color="#00c3ff" />
            <GaugeBar value={metrics.memory_usage} label="Memory Usage" color="#ffb347" />
            <GaugeBar value={metrics.disk_usage} label="Disk Usage" color="#ff7a00" />
          </div>

          <Section title="Detailed Stats">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: "14px" }}>
              {[
                { label: "Memory Used", value: `${(metrics.memory_used_mb / 1024).toFixed(1)} GB`, color: "#ffb347" },
                { label: "Memory Total", value: `${(metrics.memory_total_mb / 1024).toFixed(1)} GB`, color: "#888" },
                { label: "System Uptime", value: formatUptime(metrics.uptime_seconds), color: "#33ff88" },
                { label: "CPU Cores", value: `${Math.round(metrics.cpu_usage / 10)} active`, color: "#00c3ff" },
              ].map(s => (
                <div key={s.label} style={{ background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "12px", padding: "16px" }}>
                  <div style={{ color: "var(--text-tertiary)", fontSize: "12px", marginBottom: "4px" }}>{s.label}</div>
                  <div style={{ color: s.color, fontSize: "22px", fontWeight: 700 }}>{s.value}</div>
                </div>
              ))}
            </div>
          </Section>
        </>
      )}
    </AppShell>
  );
}
