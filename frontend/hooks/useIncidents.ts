"use client";
import { useState, useCallback, useEffect } from "react";
import { fetchIncidents, updateIncidentStatus, deleteIncident } from "@/lib/api";
import type { Incident, IncidentStatus } from "@/types";

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchIncidents();
      setIncidents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load incidents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const updateStatus = useCallback(async (id: number, status: IncidentStatus) => {
    try {
      const updated = await updateIncidentStatus(id, status);
      setIncidents(prev => prev.map(i => i.id === id ? updated : i));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update");
    }
  }, []);

  const remove = useCallback(async (id: number) => {
    try {
      await deleteIncident(id);
      setIncidents(prev => prev.filter(i => i.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }, []);

  return { incidents, loading, error, refresh: load, updateStatus, remove };
}
