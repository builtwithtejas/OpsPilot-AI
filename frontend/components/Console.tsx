"use client";

import { useEffect, useRef } from "react";
import type { WorkflowRun } from "@/types";
import { conclusionColor } from "@/utils/formatters";

interface Props {
  workflows: WorkflowRun[];
}

function formatLog(run: WorkflowRun): string {
  const time = run.created_at ? run.created_at.slice(11, 19) : "??:??:??";
  const status = run.conclusion ?? run.status;
  return `[${time}] ${run.workflow} | branch: ${run.branch} | commit: ${run.commit} | ${status.toUpperCase()}`;
}

export default function Console({ workflows }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [workflows]);

  return (
    <div
      ref={ref}
      style={{
        background: "rgba(0,0,0,0.7)",
        borderRadius: "16px",
        padding: "20px",
        height: "280px",
        overflowY: "auto",
        border: "1px solid rgba(255,255,255,0.06)",
        backdropFilter: "blur(12px)",
        fontFamily: "monospace",
      }}
    >
      {workflows.length === 0 ? (
        <div style={{ color: "#555", fontSize: "14px" }}>Waiting for workflow data...</div>
      ) : (
        workflows.map((run, i) => (
          <div
            key={i}
            style={{
              color: conclusionColor(run.conclusion),
              marginBottom: "10px",
              fontSize: "13px",
              lineHeight: 1.5,
            }}
          >
            {formatLog(run)}
          </div>
        ))
      )}
    </div>
  );
}
