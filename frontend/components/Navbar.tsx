"use client";

import { Bell, Search, X, CheckCheck, Command } from "lucide-react";
import { useRef, useEffect, type KeyboardEvent } from "react";
import type { Notification } from "@/types";
import { severityColor, timeAgo } from "@/utils/formatters";

interface Props {
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
  notifications?: Notification[];
  unreadCount?: number;
  notifOpen?: boolean;
  setNotifOpen?: (open: boolean) => void;
  markAllRead?: () => void;
  onOpenPalette?: () => void;
}

export default function Navbar({ searchQuery = "", onSearchChange, notifications = [], unreadCount = 0, notifOpen = false, setNotifOpen, markAllRead, onOpenPalette }: Props) {
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setNotifOpen?.(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [setNotifOpen]);

  function handleKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") onSearchChange?.("");
  }

  return (
    <div style={{ width: "100%", padding: "16px 24px", borderRadius: "20px", background: "var(--card-bg)", border: "1px solid var(--border)", backdropFilter: "blur(20px)", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px" }}>

      {/* Search bar — clicking it opens command palette */}
      <div onClick={onOpenPalette} style={{ display: "flex", alignItems: "center", gap: "10px", background: "var(--input-bg)", border: "1px solid var(--border)", borderRadius: "12px", padding: "10px 14px", width: "320px", cursor: "pointer" }}>
        <Search size={16} color="var(--text-tertiary)" />
        <input value={searchQuery} onChange={e => onSearchChange?.(e.target.value)} onKeyDown={handleKey}
          placeholder="Search or ⌘K for commands..."
          onClick={e => e.stopPropagation()}
          style={{ background: "transparent", border: "none", outline: "none", color: "var(--text-primary)", width: "100%", fontSize: "14px", cursor: "text" }} />
        {searchQuery
          ? <button onClick={e => { e.stopPropagation(); onSearchChange?.(""); }} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-tertiary)", padding: 0, display: "flex" }}><X size={14} /></button>
          : <div style={{ display: "flex", alignItems: "center", gap: "2px", flexShrink: 0 }}><kbd className="kbd">⌘K</kbd></div>
        }
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div className="live-pulse" style={{ padding: "8px 14px", borderRadius: "10px", background: "rgba(0,255,170,0.08)", border: "1px solid rgba(0,255,170,0.2)", color: "#33ff88", fontWeight: 700, fontSize: "13px" }}>● LIVE</div>

        {/* Notifications */}
        <div ref={dropRef} style={{ position: "relative" }}>
          <button onClick={() => setNotifOpen?.(!notifOpen)} style={{ width: "42px", height: "42px", borderRadius: "12px", background: "var(--input-bg)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", position: "relative" }}>
            <Bell size={18} color="var(--text-primary)" />
            {unreadCount > 0 && (
              <div style={{ position: "absolute", top: "7px", right: "7px", width: "16px", height: "16px", borderRadius: "50%", background: "#ff4d4d", fontSize: "10px", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", color: "white" }}>
                {unreadCount > 9 ? "9+" : unreadCount}
              </div>
            )}
          </button>

          {notifOpen && (
            <div style={{ position: "absolute", top: "52px", right: 0, width: "360px", background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "16px", backdropFilter: "blur(20px)", boxShadow: "0 20px 60px rgba(0,0,0,0.5)", zIndex: 1000, overflow: "hidden" }}>
              <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 700, fontSize: "15px" }}>Notifications</span>
                {unreadCount > 0 && <button onClick={markAllRead} style={{ background: "none", border: "none", color: "#33ff88", cursor: "pointer", fontSize: "13px", display: "flex", alignItems: "center", gap: "4px" }}><CheckCheck size={14} /> Mark all read</button>}
              </div>
              <div style={{ maxHeight: "380px", overflowY: "auto" }}>
                {notifications.length === 0
                  ? <div style={{ padding: "24px", textAlign: "center", color: "var(--text-tertiary)", fontSize: "14px" }}>No notifications</div>
                  : notifications.map(n => (
                    <div key={n.id} style={{ padding: "14px 18px", borderBottom: "1px solid var(--border)", background: n.read ? "transparent" : "rgba(57,255,136,0.03)", display: "flex", gap: "12px", alignItems: "flex-start" }}>
                      <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: severityColor(n.severity), marginTop: "5px", flexShrink: 0 }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "2px" }}>{n.title}</div>
                        <div style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>{n.message}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-tertiary)", marginTop: "4px" }}>{timeAgo(n.timestamp)}</div>
                      </div>
                      {!n.read && <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#33ff88", marginTop: "5px", flexShrink: 0 }} />}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>

        {/* User */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", background: "var(--input-bg)", border: "1px solid var(--border)", padding: "6px 12px", borderRadius: "14px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "linear-gradient(135deg,#33ff88,#00c3ff)", display: "flex", alignItems: "center", justifyContent: "center", color: "black", fontWeight: 800, fontSize: "14px" }}>T</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "13px", color: "var(--text-primary)" }}>Tejas</div>
            <div style={{ color: "var(--text-tertiary)", fontSize: "11px" }}>DevOps Admin</div>
          </div>
        </div>
      </div>
    </div>
  );
}
