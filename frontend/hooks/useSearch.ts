"use client";

import { useState, useMemo } from "react";
import type { Incident } from "@/types";

export function useSearch(incidents: Incident[]) {
  const [query, setQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("All");
  const [statusFilter, setStatusFilter] = useState<string>("All");

  // Client-side filter (instant, works on already-loaded incidents)
  const filtered = useMemo(() => {
    return incidents.filter(i => {
      const q = query.toLowerCase();
      const matchQ = !query ||
        i.title.toLowerCase().includes(q) ||
        i.description.toLowerCase().includes(q) ||
        i.remediation.toLowerCase().includes(q) ||
        String(i.id) === query;
      const matchS  = severityFilter === "All" || i.severity === severityFilter;
      const matchSt = statusFilter   === "All" || i.status   === statusFilter;
      return matchQ && matchS && matchSt;
    });
  }, [incidents, query, severityFilter, statusFilter]);

  return { query, setQuery, severityFilter, setSeverityFilter, statusFilter, setStatusFilter, filtered };
}
