"use client";
// FIX C-5: Removed NEXT_PUBLIC_API_KEY and direct fetch().
// Now uses triggerAutoFix() from lib/api.ts which goes through the JWT token proxy.
// FIX: The /incidents/{id}/autofix endpoint must exist on the backend (incidents.py).

import { useState } from "react";
import { triggerAutoFix } from "@/lib/api";

export default function AutoFixButton({
  incidentId,
  onFixed,
}: {
  incidentId: number;
  onFixed: (url: string) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function handleFix() {
    setLoading(true);
    setError("");
    try {
      const data = await triggerAutoFix(incidentId);
      onFixed(data.mr_url);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to generate fix");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        onClick={() => void handleFix()}
        disabled={loading}
        style={{
          display: "inline-flex", alignItems: "center", gap: "8px",
          padding: "12px 20px", borderRadius: "12px",
          background: loading
            ? "rgba(30,142,62,0.3)"
            : "linear-gradient(to right,#1E8E3E,#34A853)",
          color: "white", fontWeight: 700, fontSize: "14px",
          border: "none", cursor: loading ? "not-allowed" : "pointer",
          boxShadow: loading ? "none" : "0 0 20px #1E8E3E33",
        }}
      >
        {loading ? "⚙️ Generating fix..." : "🤖 Auto-Fix with AI"}
      </button>
      {error && (
        <div style={{ fontSize: "12px", color: "#ff4d4d", marginTop: "6px" }}>
          {error}
        </div>
      )}
    </div>
  );
}