"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Search, LayoutDashboard, AlertTriangle, BarChart3, Rocket, Server, Settings, RefreshCw, Download } from "lucide-react";

interface Action {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  action: () => void;
  keywords: string[];
}

interface Props {
  open: boolean;
  onClose: () => void;
  onRefresh?: () => void;
}

export default function CommandPalette({ open, onClose, onRefresh }: Props) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const actions: Action[] = useMemo(() => [
    { id: "dashboard",      label: "Go to Dashboard",      icon: <LayoutDashboard size={16} />, action: () => router.push("/"),               keywords: ["home", "dashboard", "main"] },
    { id: "incidents",      label: "Go to Incidents",       icon: <AlertTriangle size={16} />,   action: () => router.push("/incidents"),        keywords: ["incidents", "alerts", "issues"] },
    { id: "analytics",      label: "Go to Analytics",       icon: <BarChart3 size={16} />,        action: () => router.push("/analytics"),        keywords: ["charts", "analytics", "graphs"] },
    { id: "deployments",    label: "Go to Deployments",     icon: <Rocket size={16} />,           action: () => router.push("/deployments"),      keywords: ["deploy", "pipeline", "ci", "cd"] },
    { id: "infrastructure", label: "Go to Infrastructure",  icon: <Server size={16} />,           action: () => router.push("/infrastructure"),   keywords: ["infra", "metrics", "cpu", "memory"] },
    { id: "settings",       label: "Go to Settings",        icon: <Settings size={16} />,         action: () => router.push("/settings"),         keywords: ["settings", "config", "theme"] },
    { id: "refresh",        label: "Refresh Data",          icon: <RefreshCw size={16} />,        action: () => { onRefresh?.(); onClose(); },    keywords: ["refresh", "reload", "update"] },
    { id: "export",         label: "Export Incidents CSV",  icon: <Download size={16} />,         action: () => router.push("/incidents"),        keywords: ["export", "csv", "download"] },
  ], [router, onRefresh, onClose]);

  const filtered = useMemo(() => {
    if (!query) return actions;
    const q = query.toLowerCase();
    return actions.filter(a =>
      a.label.toLowerCase().includes(q) ||
      a.keywords.some(k => k.includes(q))
    );
  }, [actions, query]);

  useEffect(() => {
    if (open) { setQuery(""); setSelected(0); setTimeout(() => inputRef.current?.focus(), 50); }
  }, [open]);

  useEffect(() => { setSelected(0); }, [query]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowDown") { e.preventDefault(); setSelected(s => Math.min(s + 1, filtered.length - 1)); }
      if (e.key === "ArrowUp")   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
      if (e.key === "Enter" && filtered[selected]) { filtered[selected].action(); onClose(); }
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, filtered, selected, onClose]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        width: "min(560px, 95vw)", background: "var(--card-bg)",
        border: "1px solid var(--border)", borderRadius: "20px",
        backdropFilter: "blur(24px)", overflow: "hidden",
        boxShadow: "0 25px 60px rgba(0,0,0,0.6)",
      }}>
        {/* Search input */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
          <Search size={18} color="var(--text-tertiary)" />
          <input ref={inputRef} value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search actions..."
            style={{ flex: 1, background: "transparent", border: "none", outline: "none", fontSize: "16px", color: "var(--text-primary)" }} />
          <kbd className="kbd">Esc</kbd>
        </div>

        {/* Results */}
        <div style={{ maxHeight: "360px", overflowY: "auto", padding: "8px" }}>
          {filtered.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-tertiary)", fontSize: "14px" }}>No actions found</div>
          ) : filtered.map((action, i) => (
            <button key={action.id} onClick={() => { action.action(); onClose(); }}
              style={{
                width: "100%", display: "flex", alignItems: "center", gap: "14px",
                padding: "12px 14px", borderRadius: "12px", border: "none",
                background: i === selected ? "rgba(57,255,136,0.08)" : "transparent",
                color: i === selected ? "var(--accent)" : "var(--text-primary)",
                cursor: "pointer", textAlign: "left", transition: "all 0.1s",
              }}
              onMouseEnter={() => setSelected(i)}
            >
              <span style={{ color: i === selected ? "var(--accent)" : "var(--text-tertiary)", flexShrink: 0 }}>{action.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "14px", fontWeight: 600 }}>{action.label}</div>
                {action.description && <div style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>{action.description}</div>}
              </div>
              {i === selected && <kbd className="kbd">↵</kbd>}
            </button>
          ))}
        </div>

        <div style={{ padding: "10px 20px", borderTop: "1px solid var(--border)", display: "flex", gap: "16px", color: "var(--text-tertiary)", fontSize: "12px" }}>
          <span><kbd className="kbd">↑↓</kbd> navigate</span>
          <span><kbd className="kbd">↵</kbd> select</span>
          <span><kbd className="kbd">Esc</kbd> close</span>
        </div>
      </div>
    </div>
  );
}
