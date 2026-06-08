"use client";

// M FIX: visibilitychange previously triggered a fetch unconditionally on every tab focus.
// Now it only refetches if data is actually stale (older than the refresh interval).
// This avoids a burst of API calls every time the user alt-tabs back.

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

  const intervalRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastFetchRef = useRef<number>(0);

  const load = useCallback(async () => {
    const start = performance.now();
    lastFetchRef.current = Date.now();
    try {
      const [analytics, workflows, metrics] = await Promise.all([
        fetchAnalytics(),
        fetchWorkflows(),
        fetchMetrics().catch(() => null),
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

    // M FIX: Only refetch on tab focus if data is stale (past the refresh interval).
    // Without this check, every alt-tab triggers a full API round-trip unnecessarily.
    const onVisibilityChange = () => {
      if (!document.hidden) {
        const age = Date.now() - lastFetchRef.current;
        if (age >= refreshInterval) {
          void load();
        }
      }
    };

    intervalRef.current = setInterval(tick, refreshInterval);
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [load, refreshInterval]);

  return { ...state, refresh: load };
}
