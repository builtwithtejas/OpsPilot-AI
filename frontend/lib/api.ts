// frontend/lib/api.ts

import type {
  AgentRun, AnalyzeResult, AnalyticsData, GitLabJob, GitLabPipeline,
  Incident, SystemMetrics, WorkflowRun,
} from "@/types";
import type { Project } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Token cache ──────────────────────────────────────────────────
let _cachedToken: string | null = null;
let _tokenExpiry: number = 0;

async function getToken(): Promise<string> {
  if (_cachedToken && Date.now() < _tokenExpiry - 30_000) {
    return _cachedToken;
  }
  const res = await fetch("/api/token", { method: "POST" });
  if (!res.ok) throw new Error("Failed to obtain access token");
  const data = await res.json() as { access_token: string; expires_in: number };
  _cachedToken = data.access_token;
  _tokenExpiry = Date.now() + data.expires_in * 1000;
  return _cachedToken;
}

// ── Core fetch wrapper ───────────────────────────────────────────
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail: string }).detail ?? "Request failed");
  }
  // FIX: 204 No Content (DELETE responses) has an empty body.
  // Calling res.json() on an empty body throws a SyntaxError.
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ── GitHub ──────────────────────────────────────────────────────
export const fetchWorkflows = () => request<WorkflowRun[]>("/github/workflows");
export const fetchAnalytics = () => request<AnalyticsData>("/github/analytics");
export const fetchMetrics   = () => request<SystemMetrics>("/metrics/");

// ── Incidents ────────────────────────────────────────────────────
export const fetchIncidents = (skip = 0, limit = 100) =>
  request<Incident[]>(`/incidents/?skip=${skip}&limit=${limit}`);

export const fetchIncidentById = (id: number | string) =>
  request<Incident>(`/incidents/${id}`);

export const fetchIncidentAudit = (id: number | string) =>
  request<AuditEntry[]>(`/incidents/${id}/audit`);

export const updateIncidentStatus = (id: number, status: string) =>
  request<Incident>(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });

// FIX: returns void — 204 is now handled in request() above, no JSON parse attempt.
export const deleteIncident = (id: number) =>
  request<void>(`/incidents/${id}`, { method: "DELETE" });

export const createIncident = (payload: Record<string, unknown>) =>
  request<Incident>("/incidents/", { method: "POST", body: JSON.stringify(payload) });

// ── Auto-fix ─────────────────────────────────────────────────────
export const triggerAutoFix = (incidentId: number) =>
  request<{ mr_url: string }>(`/incidents/${incidentId}/autofix`, { method: "POST" });

// ── Logs / AI ────────────────────────────────────────────────────
export const analyzeLogFile = async (file: File): Promise<AnalyzeResult> => {
  const token = await getToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/logs/analyze`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` },
    body: formData,
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

// ── Forecast ─────────────────────────────────────────────────────
export const fetchForecast = (refresh = false) =>
  request<{ forecasts: Forecast[]; cached: boolean; generated_at: number }>(
    `/forecast/?refresh=${refresh}`
  );

// ── Projects ─────────────────────────────────────────────────────
export const fetchProjects = () => request<Project[]>("/projects/");

export const registerProject = (payload: { gitlab_project_id: string; name: string; description: string }) =>
  request<Project>("/projects/", { method: "POST", body: JSON.stringify(payload) });

export const toggleProject = (id: number) =>
  request<{ id: number; active: boolean }>(`/projects/${id}/toggle`, { method: "PATCH" });

// FIX: returns void — 204 No Content handled in request().
export const removeProject = (id: number) =>
  request<void>(`/projects/${id}`, { method: "DELETE" });

// ── Chat streaming ────────────────────────────────────────────────
export const chatStream = async (
  incidentId: number,
  messages: { role: string; content: string }[]
): Promise<Response> => {
  const token = await getToken();
  return fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ incident_id: incidentId, messages }),
  });
};

// ── PDF export ───────────────────────────────────────────────────
export const downloadIncidentPdf = async (incidents: Incident[], analytics: AnalyticsData | null) => {
  const { default: jsPDF } = await import("jspdf");
  const doc = new jsPDF();
  doc.setFontSize(22); doc.text("OpsPilot AI — Incident Report", 20, 20);
  doc.setFontSize(11); doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 30);
  doc.setFontSize(10); doc.text("Powered by Google Gemini x GitLab MCP", 20, 38);
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

// ── Shared types used by callers ──────────────────────────────────
export interface AuditEntry {
  id: number;
  action: string;
  detail: string;
  actor: string;
  created_at: string;
}

export interface Forecast {
  project: string;
  risk_type: string;
  description: string;
  confidence: number;
  timeframe: string;
  recommended_action: string;
}