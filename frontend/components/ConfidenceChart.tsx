"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from "recharts";
import { useTheme } from "@/context/ThemeContext";
import type { Incident } from "@/types";

interface Props { incidents: Incident[]; }

export default function ConfidenceChart({ incidents }: Props) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const data = [...incidents]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .slice(-20)
    .map((inc, i) => ({
      index: i + 1,
      confidence: inc.confidence,
      severity: inc.severity,
      label: `#${inc.id}`,
      title: inc.title.slice(0, 30) + (inc.title.length > 30 ? "…" : ""),
    }));

  const avg = data.length ? Math.round(data.reduce((s, d) => s + d.confidence, 0) / data.length) : 0;

  const gridColor   = isDark ? "#1b1b1b" : "#e0e0e0";
  const axisColor   = isDark ? "#888"    : "#555";
  const tooltipBg   = isDark ? "#111"    : "#fff";
  const tooltipBorder = isDark ? "#222"  : "#ccc";

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    const color = payload.severity === "Critical" ? "#ff4d4d" : payload.severity === "High" ? "#ff7a00" : payload.severity === "Medium" ? "#ffb347" : "#33ff88";
    return <circle cx={cx} cy={cy} r={5} fill={color} stroke="transparent" />;
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div style={{ background: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: "10px", padding: "10px 14px", fontSize: "13px" }}>
        <div style={{ fontWeight: 700, marginBottom: "4px" }}>{d.title}</div>
        <div>Confidence: <strong style={{ color: "#33ff88" }}>{d.confidence}%</strong></div>
        <div style={{ color: axisColor }}>Severity: {d.severity}</div>
      </div>
    );
  };

  if (data.length === 0) {
    return <div style={{ height: "220px", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-tertiary)", fontSize: "14px" }}>No incidents yet — upload logs to see confidence trends</div>;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <span style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>Last {data.length} incidents · dots coloured by severity</span>
        <span style={{ fontSize: "13px", fontWeight: 600 }}>
          Avg: <span style={{ color: avg >= 80 ? "#33ff88" : avg >= 60 ? "#ffb347" : "#ff4d4d" }}>{avg}%</span>
        </span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid stroke={gridColor} />
          <XAxis dataKey="label" stroke={axisColor} tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} stroke={axisColor} tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={avg} stroke="#555" strokeDasharray="4 4" label={{ value: `avg ${avg}%`, fill: axisColor, fontSize: 11 }} />
          <Line type="monotone" dataKey="confidence" stroke="#00c3ff" strokeWidth={2} dot={<CustomDot />} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
