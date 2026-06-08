"use client";
// FIX C-5: Removed NEXT_PUBLIC_API_KEY and direct fetch().
// Now uses fetchForecast() from lib/api.ts (JWT token proxy, key stays server-side).

import { useEffect, useState } from "react";
import { fetchForecast, type Forecast } from "@/lib/api";

export default function ForecastCard() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [loading, setLoading]     = useState(true);
  const [cached, setCached]       = useState(false);
  const [error, setError]         = useState("");

  async function load(refresh = false) {
    setLoading(true);
    setError("");
    try {
      const data = await fetchForecast(refresh);
      setForecasts(data.forecasts ?? []);
      setCached(data.cached ?? false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load forecast");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  const confColor = (c: number) =>
    c >= 75 ? "#ff4d4d" : c >= 50 ? "#ffb347" : "#33ff88";

  return (
    <div style={{
      background: "var(--card-bg)",
      border: "1px solid var(--border)",
      borderRadius: "16px",
      padding: "20px",
      marginBottom: "20px",
      backdropFilter: "blur(12px)",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>
            🔮 Predictive Risk Forecast
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-tertiary)", marginTop: "2px" }}>
            AI-powered failure prediction · {cached ? "Cached" : "Live"}
          </div>
        </div>
        <button
          onClick={() => void load(true)}
          style={{
            padding: "6px 12px", borderRadius: "8px", fontSize: "12px",
            background: "rgba(0,195,255,0.1)", border: "1px solid #00c3ff55",
            color: "#00c3ff", cursor: "pointer", fontWeight: 600,
          }}
        >
          ↻ Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>
          Analysing incident patterns...
        </div>
      ) : error ? (
        <div style={{ color: "#ff4d4d", fontSize: "13px" }}>⚠ {error}</div>
      ) : forecasts.length === 0 ? (
        <div style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>
          Not enough incident history yet. Run the agent a few times to generate forecasts.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {forecasts.map((f, i) => (
            <div key={i} style={{
              background: "var(--input-bg)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              padding: "14px",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                <div>
                  <span style={{ fontSize: "13px", fontWeight: 700, color: confColor(f.confidence) }}>
                    {f.risk_type}
                  </span>
                  <span style={{ fontSize: "11px", color: "var(--text-tertiary)", marginLeft: "8px" }}>
                    {f.timeframe}
                  </span>
                </div>
                <span style={{
                  fontSize: "11px", fontWeight: 700,
                  color: confColor(f.confidence),
                  background: `${confColor(f.confidence)}18`,
                  padding: "2px 8px", borderRadius: "6px",
                }}>
                  {f.confidence}%
                </span>
              </div>

              {/* Confidence bar */}
              <div style={{ height: "4px", background: "var(--border)", borderRadius: "2px", marginBottom: "8px" }}>
                <div style={{
                  height: "100%", borderRadius: "2px",
                  width: `${f.confidence}%`,
                  background: confColor(f.confidence),
                  transition: "width .6s",
                }} />
              </div>

              <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "6px" }}>
                {f.description}
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-tertiary)" }}>
                💡 {f.recommended_action}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}