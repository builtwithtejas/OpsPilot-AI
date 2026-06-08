// frontend/hooks/useIncidents.ts
// FIX: Optimistic UI on updateStatus — shows new status immediately,
//      reverts to old value if the server call fails.

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

  // FIX: Optimistic update — set new status immediately, revert on error
  const updateStatus = useCallback(async (id: number, status: IncidentStatus) => {
    const previous = incidents.find(i => i.id === id);

    // Optimistically apply the new status right away
    setIncidents(prev => prev.map(i => i.id === id ? { ...i, status } : i));

    try {
      const updated = await updateIncidentStatus(id, status);
      // Sync with server response (may have updated_at etc.)
      setIncidents(prev => prev.map(i => i.id === id ? updated : i));
    } catch (err) {
      // Revert to the previous value on failure
      if (previous) {
        setIncidents(prev => prev.map(i => i.id === id ? previous : i));
      }
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  }, [incidents]);

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
