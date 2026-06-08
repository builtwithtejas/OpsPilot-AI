
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
      className="hover-card op-card"
      style={{ border: `1px solid ${color}`, boxShadow: `0 0 20px ${color}18` }}
    >
      <div className="op-card-label">{title}</div>
      <div style={{ color, fontSize: "40px", fontWeight: "bold" }}>
        <CountUp end={value} duration={2} decimals={decimals} suffix={suffix} />
      </div>
    </div>
  );
}