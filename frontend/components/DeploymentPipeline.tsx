"use client";

import type { WorkflowRun } from "@/types";

const STATIC_STEPS = ["Build", "Test", "Security", "Docker", "Deploy", "Monitor"];

interface Props {
  latestRun: WorkflowRun | null;
}

function getStepStatus(stepIndex: number, conclusion: string | null): "success" | "active" | "pending" {
  if (conclusion === "success") return "success";
  if (conclusion === "failure") {
    // failed partway through — show progress up to step 2
    if (stepIndex < 2) return "success";
    if (stepIndex === 2) return "active";
    return "pending";
  }
  // in_progress: show first step done, next active
  if (stepIndex === 0) return "success";
  if (stepIndex === 1) return "active";
  return "pending";
}

export default function DeploymentPipeline({ latestRun }: Props) {
  const conclusion = latestRun?.conclusion ?? null;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
      {STATIC_STEPS.map((step, index) => {
        const status = getStepStatus(index, conclusion);
        const color =
          status === "success" ? "#33ff88" : status === "active" ? "#00c3ff" : "#333";
        const bg =
          status === "success"
            ? "rgba(0,255,170,0.1)"
            : status === "active"
            ? "rgba(0,195,255,0.1)"
            : "rgba(255,255,255,0.03)";

        return (
          <div key={index} style={{ display: "flex", alignItems: "center", flex: 1, minWidth: "100px" }}>
            <div
              style={{
                width: "64px",
                height: "64px",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: "13px",
                color: "white",
                border: `2px solid ${color}`,
                background: bg,
                animation: status === "active" ? "pulse 1.8s infinite" : "none",
                flexShrink: 0,
              }}
            >
              {step}
            </div>

            {index < STATIC_STEPS.length - 1 && (
              <div
                style={{
                  flex: 1,
                  height: "4px",
                  marginInline: "6px",
                  borderRadius: "999px",
                  background: status === "success" ? "linear-gradient(to right,#33ff88,#00c3ff)" : "#222",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                {status === "active" && (
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      background: "linear-gradient(to right,transparent,#00c3ff,transparent)",
                      animation: "moveLine 1.5s linear infinite",
                    }}
                  />
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
