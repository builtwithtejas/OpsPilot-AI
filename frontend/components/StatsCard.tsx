"use client";

import CountUp from "react-countup";

interface Props {
  title: string;
  value: number;
  color: string;
  suffix?: string;
  decimals?: number;
}

export default function StatsCard({ title, value, color, suffix = "", decimals = 0 }: Props) {
  return (
    <div
      className="hover-card"
      style={{
        background: "rgba(10,10,10,0.7)",
        border: `1px solid ${color}`,
        borderRadius: "20px",
        padding: "22px",
        boxShadow: `0 0 20px ${color}18`,
      }}
    >
      <div style={{ color: "#777", marginBottom: "10px", fontSize: "14px" }}>{title}</div>
      <div style={{ color, fontSize: "40px", fontWeight: "bold" }}>
        <CountUp end={value} duration={2} decimals={decimals} suffix={suffix} />
      </div>
    </div>
  );
}
