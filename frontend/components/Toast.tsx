"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, AlertCircle, X } from "lucide-react";

export type ToastType = "success" | "error" | "info";

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface Props {
  toasts: ToastItem[];
  remove: (id: string) => void;
}

const ICONS = { success: CheckCircle, error: XCircle, info: AlertCircle };
const COLORS = { success: "#33ff88", error: "#ff4d4d", info: "#00c3ff" };

export default function Toast({ toasts, remove }: Props) {
  return (
    <div style={{ position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)", zIndex: 9999, display: "flex", flexDirection: "column", gap: "10px", minWidth: "320px", maxWidth: "480px" }}>
      {toasts.map(t => {
        const Icon = ICONS[t.type];
        const color = COLORS[t.type];
        return (
          <div key={t.id} className="fade-up" style={{
            background: "var(--card-bg)", border: `1px solid ${color}44`,
            borderRadius: "14px", padding: "14px 18px",
            backdropFilter: "blur(20px)", boxShadow: `0 4px 30px rgba(0,0,0,0.4)`,
            display: "flex", alignItems: "center", gap: "12px",
          }}>
            <Icon size={18} color={color} style={{ flexShrink: 0 }} />
            <span style={{ flex: 1, fontSize: "14px", color: "var(--text-primary)" }}>{t.message}</span>
            <button onClick={() => remove(t.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-tertiary)", padding: 0, display: "flex" }}>
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
