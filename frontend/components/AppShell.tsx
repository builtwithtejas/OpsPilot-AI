"use client";

// H-2 FIX: AppShell previously called useIncidents() unconditionally, creating a
// second independent polling loop when page.tsx (which wraps AppShell) also calls
// useIncidents(). This caused double API calls on every poll interval.
//
// Fix: Accept optional `incidents` prop. If the parent already has them (page.tsx),
// pass them in and AppShell skips its own useIncidents() call.
// If not provided (other pages that don't use incidents), the internal hook runs as before.

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
  /** H-2 FIX: Pass incidents from the parent to avoid a second polling loop. */
  incidents?: Incident[];
}

export default function AppShell({ children, showParticles = true, onRefresh, incidents: incidentsProp }: Props) {
  // H-2 FIX: Only run useIncidents() if the parent didn't supply incidents already.
  // This prevents two simultaneous polling loops when the parent also calls useIncidents().
  const ownHook = useIncidents();
  const incidents = incidentsProp ?? ownHook.incidents;

  const { notifications, unreadCount, open, setOpen, markAllRead } = useNotifications(incidents);
  const { query, setQuery } = useSearch(incidents);
  const { toasts, add: addToast, remove: removeToast } = useToast();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const router = useRouter();

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
