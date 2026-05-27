"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchAnalytics, fetchWorkflows, fetchMetrics } from "@/lib/api";
import type { AnalyticsData, WorkflowRun, SystemMetrics } from "@/types";

interface State {
  analytics: AnalyticsData | null;
  workflows: WorkflowRun[];
  metrics: SystemMetrics | null;
  loading: boolean;
  error: string | null;
  latency: number | null;
}

export function useAnalytics(refreshInterval = 30_000) {
  const [state, setState] = useState<State>({
    analytics: null,
    workflows: [],
    metrics: null,
    loading: true,
    error: null,
    latency: null,
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    const start = performance.now();
    try {
      const [analytics, workflows, metrics] = await Promise.all([
        fetchAnalytics(),
        fetchWorkflows(),
        fetchMetrics().catch(() => null), // metrics failure shouldn't break the page
      ]);
      setState({
        analytics,
        workflows,
        metrics,
        loading: false,
        error: null,
        latency: Math.round(performance.now() - start),
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Unknown error",
        latency: null,
      }));
    }
  }, []);

  useEffect(() => {
    void load();

    const tick = () => {
      if (!document.hidden) void load();
    };

    intervalRef.current = setInterval(tick, refreshInterval);
    document.addEventListener("visibilitychange", tick);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [load, refreshInterval]);

  return { ...state, refresh: load };
}
