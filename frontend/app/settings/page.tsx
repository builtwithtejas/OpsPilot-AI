"use client";

import { useState } from "react";
import AppShell from "@/components/AppShell";
import Section from "@/components/Section";
import { useTheme } from "@/context/ThemeContext";
import { Moon, Sun, Bell, Shield, RefreshCw, Keyboard } from "lucide-react";

export default function SettingsPage() {
  const { theme, toggle } = useTheme();
  const [refreshInterval, setRefreshInterval] = useState("30");
  const [notifications, setNotifications] = useState(true);

  const row = (label: string, description: string, control: React.ReactNode) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "18px 0", borderBottom: "1px solid var(--border)" }}>
      <div>
        <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-primary)", marginBottom: "2px" }}>{label}</div>
        <div style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>{description}</div>
      </div>
      {control}
    </div>
  );

  const toggle_btn = (on: boolean, onClick: () => void) => (
    <button onClick={onClick} style={{
      width: "48px", height: "26px", borderRadius: "999px", border: "none",
      background: on ? "#33ff88" : "var(--border)", cursor: "pointer",
      position: "relative", transition: "background 0.2s",
    }}>
      <div style={{
        position: "absolute", top: "3px",
        left: on ? "25px" : "3px",
        width: "20px", height: "20px", borderRadius: "50%",
        background: "white", transition: "left 0.2s",
      }} />
    </button>
  );

  return (
    <AppShell>
      <div className="fade-up" style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "clamp(28px,4vw,48px)", fontWeight: 800, background: "linear-gradient(to right,#33ff88,#00c3ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: "6px" }}>
          Settings
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "15px" }}>Configure your OpsPilot dashboard</p>
      </div>

      <Section title="Appearance">
        {row(
          "Theme",
          `Currently using ${theme} mode`,
          <button onClick={toggle} className="glow-button" style={{
            display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px",
            borderRadius: "10px", background: "var(--input-bg)", border: "1px solid var(--border)",
            color: "var(--text-primary)", cursor: "pointer", fontWeight: 600, fontSize: "13px",
          }}>
            {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
            {theme === "dark" ? "Switch to Light" : "Switch to Dark"}
          </button>
        )}
      </Section>

      <Section title="Data & Refresh">
        {row(
          "Refresh Interval",
          "How often the dashboard polls the backend",
          <select value={refreshInterval} onChange={e => setRefreshInterval(e.target.value)} style={{
            background: "var(--input-bg)", border: "1px solid var(--border)",
            color: "var(--text-primary)", borderRadius: "8px", padding: "8px 12px",
            fontSize: "13px", cursor: "pointer", outline: "none",
          }}>
            <option value="15">Every 15s</option>
            <option value="30">Every 30s</option>
            <option value="60">Every 60s</option>
            <option value="300">Every 5m</option>
          </select>
        )}
      </Section>

      <Section title="Notifications">
        {row("Incident Alerts", "Show notifications for new incidents in the bell menu", toggle_btn(notifications, () => setNotifications(n => !n)))}
      </Section>

      <Section title="Keyboard Shortcuts">
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {[
            ["Cmd + K", "Focus search bar"],
            ["Esc", "Clear search"],
            ["R", "Refresh data (when not in input)"],
          ].map(([key, desc]) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ fontSize: "14px", color: "var(--text-secondary)" }}>{desc}</span>
              <kbd className="kbd">{key}</kbd>
            </div>
          ))}
        </div>
      </Section>

      <Section title="API">
        {row("Backend URL", process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000", <span style={{ fontSize: "12px", color: "#33ff88" }}>● Connected</span>)}
      </Section>
    </AppShell>
  );
}
