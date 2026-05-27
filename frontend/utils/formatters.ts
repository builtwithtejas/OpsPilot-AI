export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "Critical": return "#ff4d4d";
    case "High":     return "#ff7a00";
    case "Medium":   return "#ffb347";
    case "Low":      return "#33ff88";
    default:         return "#888";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "Open":        return "#ff4d4d";
    case "In Progress": return "#ffb347";
    case "Resolved":    return "#33ff88";
    case "Closed":      return "#555";
    default:            return "#888";
  }
}

export function conclusionColor(conclusion: string | null): string {
  if (conclusion === "success") return "#33ff88";
  if (conclusion === "failure") return "#ff4d4d";
  return "#ffb347";
}

export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  const hrs  = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (days > 0)  return `${days}d ago`;
  if (hrs > 0)   return `${hrs}h ago`;
  if (mins > 0)  return `${mins}m ago`;
  return "just now";
}

export function exportIncidentsCSV(incidents: import("@/types").Incident[]) {
  const header = "ID,Title,Severity,Status,Confidence,Created\n";
  const rows = incidents.map(i =>
    `${i.id},"${i.title}",${i.severity},${i.status},${i.confidence}%,${new Date(i.created_at).toLocaleString()}`
  ).join("\n");
  const blob = new Blob([header + rows], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "opspilot-incidents.csv"; a.click();
  URL.revokeObjectURL(url);
}
