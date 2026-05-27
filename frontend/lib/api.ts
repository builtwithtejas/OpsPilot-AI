import type {
  AgentRun, AnalyzeResult, AnalyticsData, GitLabJob, GitLabPipeline,
  Incident, SystemMetrics, WorkflowRun,
} from "@/types";

const BASE    = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", "X-API-Key": API_KEY, ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail: string }).detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── GitHub ──────────────────────────────────────────────────────
export const fetchWorkflows = () => request<WorkflowRun[]>("/github/workflows");
export const fetchAnalytics = () => request<AnalyticsData>("/github/analytics");
export const fetchMetrics   = () => request<SystemMetrics>("/metrics/");

// ── Incidents ────────────────────────────────────────────────────
export const fetchIncidents = (skip = 0, limit = 100) =>
  request<Incident[]>(`/incidents/?skip=${skip}&limit=${limit}`);

export const updateIncidentStatus = (id: number, status: string) =>
  request<Incident>(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });

export const deleteIncident = (id: number) =>
  request<void>(`/incidents/${id}`, { method: "DELETE" });

// ── Logs / AI ────────────────────────────────────────────────────
export const analyzeLogFile = async (file: File): Promise<AnalyzeResult> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/logs/analyze`, {
    method: "POST", headers: { "X-API-Key": API_KEY }, body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail: string }).detail ?? "Upload failed");
  }
  return res.json() as Promise<AnalyzeResult>;
};

// ── Agent ────────────────────────────────────────────────────────
export const triggerAgent = (projectId: string, pipelineId?: number) =>
  request<AgentRun>("/agent/run", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, pipeline_id: pipelineId ?? null }),
  });

export const fetchFailedPipelines = (projectId: string) =>
  request<{ project_id: string; failed_pipelines: GitLabPipeline[] }>(`/agent/pipelines/${projectId}`);

export const fetchPipelineJobs = (projectId: string, pipelineId: number) =>
  request<{ pipeline_id: number; jobs: GitLabJob[] }>(`/agent/pipelines/${projectId}/${pipelineId}/jobs`);

// ── GitLab ───────────────────────────────────────────────────────
export const triggerWorkflowRerun = (workflowUrl: string) =>
  request<{ message: string }>("/github/rerun", {
    method: "POST", body: JSON.stringify({ workflow_url: workflowUrl }),
  });

// ── PDF export ───────────────────────────────────────────────────
export const downloadIncidentPdf = async (incidents: Incident[], analytics: AnalyticsData | null) => {
  const { default: jsPDF } = await import("jspdf");
  const doc = new jsPDF();
  doc.setFontSize(22); doc.text("OpsPilot AI — Incident Report", 20, 20);
  doc.setFontSize(11); doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 30);
  doc.setFontSize(10); doc.text("Powered by Google Gemini × GitLab MCP", 20, 38);
  if (analytics) {
    doc.setFontSize(15); doc.text("System Overview", 20, 52);
    doc.setFontSize(11);
    doc.text(`Total: ${analytics.stats.total}  Success: ${analytics.stats.success}  Failed: ${analytics.stats.failed}  Rate: ${analytics.stats.success_rate}%`, 20, 62);
  }
  doc.setFontSize(15); doc.text("Incidents", 20, 76);
  let y = 86;
  incidents.forEach((inc, i) => {
    if (y > 260) { doc.addPage(); y = 20; }
    doc.setFontSize(12); doc.text(`${i + 1}. [${inc.severity}] ${inc.title}`, 20, y); y += 7;
    doc.setFontSize(10);
    const desc = doc.splitTextToSize(`   ${inc.description}`, 170);
    doc.text(desc, 20, y); y += desc.length * 6 + 4;
  });
  doc.save("OpsPilot-Report.pdf");
};
