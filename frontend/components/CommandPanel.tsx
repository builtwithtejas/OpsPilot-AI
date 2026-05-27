"use client";

import { useClipboard } from "@/hooks/useClipboard";

interface Props {
  commands: string[];
}

export default function CommandPanel({ commands }: Props) {
  const { copied, copy } = useClipboard();

  if (commands.length === 0) {
    return <div style={{ color: "#555", fontFamily: "monospace", fontSize: "14px" }}>No commands suggested — all pipelines healthy.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      {commands.map((cmd, index) => (
        <div
          key={index}
          className="hover-card"
          style={{
            background: "rgba(0,0,0,0.5)",
            padding: "16px 18px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.07)",
            fontFamily: "monospace",
            color: "#33ff88",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <span style={{ fontSize: "14px" }}>{cmd}</span>
          <button
            onClick={() => copy(cmd)}
            className="glow-button"
            style={{
              background: copied === cmd ? "#33ff88" : "transparent",
              color: copied === cmd ? "black" : "#33ff88",
              border: "1px solid #33ff88",
              borderRadius: "8px",
              padding: "6px 14px",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 600,
              flexShrink: 0,
              transition: "all 0.2s",
            }}
          >
            {copied === cmd ? "Copied!" : "Copy"}
          </button>
        </div>
      ))}
    </div>
  );
}
