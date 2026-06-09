"use client";

// FIX: useIncidents() was called unconditionally (React hooks cannot be called
// conditionally), which meant AppShell always ran its own polling loop even when
// the parent had already passed incidents as a prop — causing two independent
// fetch loops and double API traffic.
//
// Correct fix: split into two components.
// AppShellInner — used when incidents ARE provided by the parent (no hook).
// AppShellWithHook — used when incidents are NOT provided (runs useIncidents).
// AppShell picks the right one based on whether the prop is present.

import { useMemo, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import Toast from "@/components/Toast";
import CommandPalette from "@/components/CommandPalette";
import { useNotifications } from "@/hooks/useNotifications";
import { useSearch } from "@/hooks/useSearch";
import { useIncidents } from "@/hooks/useIncidents";
import { useToast } from "@/hooks/useToast";
import type { Incident } from "@/types";

interface Props {
  children: React.ReactNode;
  showParticles?: boolean;
  onRefresh?: () => void;
  incidents?: Incident[];
}

// Shared shell chrome — accepts incidents directly, runs no hooks that fetch data.
function AppShellInner({
  children,
  showParticles = true,
  onRefresh,
  incidents,
}: {
  children: React.ReactNode;
  showParticles?: boolean;
  onRefresh?: () => void;
  incidents: Incident[];
}) {
  const { notifications, unreadCount, open, setOpen, markAllRead } = useNotifications(incidents);
  const { query, setQuery } = useSearch(incidents);
  const { toasts, add: addToast, remove: removeToast } = useToast();
  const [paletteOpen, setPaletteOpen] = useState(false);

  const particles = useMemo(
    () => Array.from({ length: 40 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      duration: `${8 + Math.random() * 12}s`,
      delay: `${Math.random() * 6}s`,
    })), []
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen(p => !p);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)" }}>
      <Sidebar />

      <div style={{ flex: 1, padding: "32px", position: "relative", overflow: "hidden", minWidth: 0 }}>
        {showParticles && (
          <>
            <div className="scan-line" />
            <div className="orb" />
            <div className="particles">
              {particles.map(p => (
                <div key={p.id} className="particle"
                  style={{ left: p.left, animationDuration: p.duration, animationDelay: p.delay }} />
              ))}
            </div>
          </>
        )}

        <div style={{ position: "relative", zIndex: 1 }}>
          <Navbar
            searchQuery={query}
            onSearchChange={setQuery}
            notifications={notifications}
            unreadCount={unreadCount}
            notifOpen={open}
            setNotifOpen={setOpen}
            markAllRead={markAllRead}
            onOpenPalette={() => setPaletteOpen(true)}
          />
          {children}
        </div>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onRefresh={onRefresh} />
      <Toast toasts={toasts} remove={removeToast} />
    </div>
  );
}

// Variant that owns its own useIncidents() polling loop.
// Only used when the parent does NOT supply incidents.
function AppShellWithHook({
  children,
  showParticles,
  onRefresh,
}: Omit<Props, "incidents">) {
  const { incidents } = useIncidents();
  return (
    <AppShellInner incidents={incidents} showParticles={showParticles} onRefresh={onRefresh}>
      {children}
    </AppShellInner>
  );
}

// Public component — picks the right inner component to avoid the conditional-hook problem.
export default function AppShell({ children, showParticles = true, onRefresh, incidents }: Props) {
  if (incidents !== undefined) {
    // Parent has already fetched incidents — pass them straight through, no extra hook.
    return (
      <AppShellInner incidents={incidents} showParticles={showParticles} onRefresh={onRefresh}>
        {children}
      </AppShellInner>
    );
  }
  // No prop — run our own hook.
  return (
    <AppShellWithHook showParticles={showParticles} onRefresh={onRefresh}>
      {children}
    </AppShellWithHook>
  );
}