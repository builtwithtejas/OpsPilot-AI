"use client";

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

interface Props {
  children: React.ReactNode;
  showParticles?: boolean;
  onRefresh?: () => void;
}

export default function AppShell({ children, showParticles = true, onRefresh }: Props) {
  const { incidents } = useIncidents();
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

  // Keyboard shortcuts: Cmd+K → palette, R → refresh, Esc → clear search
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
