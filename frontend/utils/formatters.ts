// frontend/utils/formatters.ts
// FIX: severityColor and statusColor now return CSS variable references
// instead of hardcoded hex strings. This means changing the theme in
// globals.css automatically updates every badge, card, and label.

export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

// FIX: returns CSS variable references — no hardcoded hex
export function severityColor(severity: string): string {
  switch (severity) {
    case "Critical": return "var(--color-severity-critical)";
    case "High":     return "var(--color-severity-high)";
    case "Medium":   return "var(--color-severity-medium)";
    case "Low":      return "var(--color-severity-low)";
    default:         return "var(--color-muted)";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "Open":        return "var(--color-status-open)";
    case "In Progress": return "var(--color-status-in-progress)";
    case "Resolved":    return "var(--color-status-resolved)";
    case "Closed":      return "var(--color-status-closed)";
    default:            return "var(--color-muted)";
  }
}

export function conclusionColor(conclusion: string | null): string {
  if (conclusion === "success") return "var(--color-accent)";
  if (conclusion === "failure") return "var(--color-danger)";
  return "var(--color-warning)";
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

// H-3 FIX: All string fields are now properly CSV-escaped (quotes doubled, every field
// wrapped in quotes). CSV injection is prevented by prefixing cells that start with
// formula characters (=, +, -, @, \t, \r) with a single-quote — standard mitigation.
function csvCell(value: string | number): string {
  const str = String(value);
  // CSV injection protection: prefix formula starters with a literal apostrophe
  const safe = /^[=+\-@\t\r]/.test(str) ? "'" + str : str;
  // Escape double-quotes by doubling them, then wrap the field in double-quotes
  return `"${safe.replace(/"/g, '""')}"`; 
}

export function exportIncidentsCSV(incidents: import("@/types").Incident[]) {
  const header = ["ID","Title","Severity","Status","Confidence","Created"].map(csvCell).join(",") + "\n";
  const rows = incidents.map(i => [
    i.id,
    i.title,
    i.severity,
    i.status,
    `${i.confidence}%`,
    new Date(i.created_at).toLocaleString(),
  ].map(csvCell).join(",")).join("\n");
  const blob = new Blob([header + rows], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "opspilot-incidents.csv"; a.click();
  URL.revokeObjectURL(url);
}

