"use client";
import { useState } from "react";

const BASE    = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

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
      const res = await fetch(`${BASE}/incidents/${incidentId}/autofix`, {
        method: "POST",
        headers: { "X-API-Key": API_KEY },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Fix failed");
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
        onClick={handleFix}
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