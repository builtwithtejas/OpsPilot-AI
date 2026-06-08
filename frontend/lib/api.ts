// frontend/lib/api.ts
// C-5 FIX: The master API_KEY is no longer NEXT_PUBLIC_API_KEY (which bakes it into
// the JS bundle). The browser now calls /api/token (a Next.js Route Handler that keeps
// the key server-side) to obtain a short-lived JWT. All subsequent API calls use that JWT.

import type {
  AgentRun, AnalyzeResult, AnalyticsData, GitLabJob, GitLabPipeline,
  Incident, SystemMetrics, WorkflowRun,
} from "@/types";
import type { Project } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Token cache ──────────────────────────────────────────────────
// Fetches a short-lived JWT via our own /api/token Route Handler (server-side proxy).
// The master API key never leaves the server. Cached in memory, refreshed 30s before expiry.
let _cachedToken: string | null = null;
let _tokenExpiry: number = 0;

async function getToken(): Promise<string> {
  if (_cachedToken && Date.now() < _tokenExpiry - 30_000) {
    return _cachedToken;
  }
  // C-5 FIX: Call our own Route Handler (/api/token) instead of the backend directly.
  // The Route Handler holds the master API_KEY server-side and exchanges it for a JWT.
  const res = await fetch("/api/token", { method: "POST" });
  if (!res.ok) {
    throw new Error("Failed to obtain access token");
  }
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

// ── Projects ─────────────────────────────────────────────────────
export const fetchProjects = () => request<Project[]>("/projects/");
