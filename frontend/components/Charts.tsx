"use client";

import {
  LineChart, Line, PieChart, Pie, AreaChart, Area,
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import { useTheme } from "@/context/ThemeContext";
import type { AnalyticsData } from "@/types";

const PIE_COLORS = ["#33ff88", "#ffb347", "#ff4d4d"];

interface Props { analytics: AnalyticsData; }

export default function Charts({ analytics }: Props) {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const gridColor   = isDark ? "#1b1b1b" : "#e0e0e0";
  const axisColor   = isDark ? "#888"    : "#555";
  const tooltipBg   = isDark ? "#111"    : "#fff";
  const tooltipBorder = isDark ? "#222"  : "#ccc";
  const tooltipText = isDark ? "#fff"    : "#111";

  const tooltipStyle = { contentStyle: { background: tooltipBg, border: `1px solid ${tooltipBorder}`, color: tooltipText, borderRadius: "10px" } };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: "24px" }}>
      <ChartCard title="Weekly Incident Trends">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={analytics.incident_trends}>
            <CartesianGrid stroke={gridColor} />
            <XAxis dataKey="day" stroke={axisColor} tick={{ fontSize: 11 }} />
            <YAxis stroke={axisColor} tick={{ fontSize: 11 }} />
            <Tooltip {...tooltipStyle} />
            <Line type="monotone" dataKey="incidents" stroke="#33ff88" strokeWidth={2} dot={{ fill: "#33ff88", r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Deployment Activity">
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={analytics.deployment_activity}>
            <CartesianGrid stroke={gridColor} />
            <XAxis dataKey="time" stroke={axisColor} tick={{ fontSize: 11 }} />
            <YAxis stroke={axisColor} tick={{ fontSize: 11 }} />
            <Tooltip {...tooltipStyle} />
            <Area type="monotone" dataKey="deployments" stroke="#00c3ff" fill={isDark ? "#00c3ff22" : "#00c3ff18"} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Severity Distribution">
        {analytics.severity_distribution.every(d => d.value === 0) ? (
          <div style={{ height: 240, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-tertiary)" }}>No data yet</div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={analytics.severity_distribution} dataKey="value" outerRadius={85} label={({ name, value }) => `${name}: ${value}`}>
                {analytics.severity_distribution.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip {...tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="hover-card" style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "20px", padding: "20px", backdropFilter: "blur(12px)" }}>
      <h3 style={{ marginBottom: "16px", fontSize: "16px", fontWeight: 600, color: "var(--text-secondary)" }}>{title}</h3>
      {children}
    </div>
  );
}
