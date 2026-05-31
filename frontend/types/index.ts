export type Severity = "Low" | "Medium" | "High" | "Critical";
export type IncidentStatus = "Open" | "In Progress" | "Resolved" | "Closed";

export interface Incident {
  id:               number;
  title:            string;
  severity:         Severity;
  status:           IncidentStatus;
  description:      string;
  remediation:      string;
  confidence:       number;
  source:           string | null;
  pipeline_id:      string | null;
  gitlab_issue_url: string | null;
  created_at:       string;
  updated_at:       string;
}

export interface WorkflowRun {
  workflow:   string;
  status:     string;
  conclusion: string | null;
  branch:     string;
  commit:     string;
  actor:      string;
  run_number: number;
  url:        string;
  created_at: string;
}

export interface AnalyticsData {
  analysis:             string;
  incident_trends:      { day: string; incidents: number }[];
  deployment_activity:  { time: string; deployments: number }[];
  severity_distribution: { name: string; value: number }[];
  suggested_commands:   string[];
  stats: {
    success:      number;
    failed:       number;
    total:        number;
    success_rate: number;
  };
}

export interface AnalyzeResult {
  incident_id: number;
  summary:     string;
  severity:    Severity;
  root_cause:  string;
  remediation: string;
  confidence:  number;
  status:      string;
}

export interface SystemMetrics {
  cpu_usage:       number;
  memory_usage:    number;
  memory_used_mb:  number;
  memory_total_mb: number;
  disk_usage:      number;
  uptime_seconds:  number;
  timestamp:       string;
}

export interface Notification {
  id:        string;
  title:     string;
  message:   string;
  severity:  Severity;
  timestamp: string;
  read:      boolean;
}

// ── Agent types ─────────────────────────────────────────────────
export interface AgentStep {
  name:   string;
  status: "pending" | "running" | "done" | "failed";
  result: Record<string, unknown>;
  error:  string | null;
}

export interface AgentRun {
  run_id:          string;
  status:          "running" | "completed" | "failed" | "healthy";
  incident_id:     number | null;
  gitlab_issue_url: string | null;
  steps:           AgentStep[];
}

export interface GitLabPipeline {
  id:         number;
  status:     string;
  ref:        string;
  sha:        string;
  web_url:    string;
  created_at: string;
}

export interface GitLabJob {
  id:             number;
  name:           string;
  stage:          string;
  status:         string;
  failure_reason: string | null;
  web_url:        string;
}
