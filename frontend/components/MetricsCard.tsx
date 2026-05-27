interface Props {
  title: string;
  value: string;
  color: string;
}

export default function MetricsCard({ title, value, color }: Props) {
  return (
    <div
      className="hover-card"
      style={{
        background: "rgba(10,10,10,0.7)",
        border: `1px solid ${color}`,
        borderRadius: "20px",
        padding: "22px",
        backdropFilter: "blur(12px)",
        boxShadow: `0 0 20px ${color}18`,
      }}
    >
      <div style={{ color: "#777", marginBottom: "10px", fontSize: "14px" }}>{title}</div>
      <div style={{ color, fontSize: "26px", fontWeight: "bold" }}>{value}</div>
    </div>
  );
}
