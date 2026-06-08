interface Props {
  title: string;
  value: string;
  color: string;  // still accepts a dynamic accent color (severity color etc.)
}

export default function MetricsCard({ title, value, color }: Props) {
  return (
    <div
      className="hover-card op-card"
      style={{ border: `1px solid ${color}`, boxShadow: `0 0 20px ${color}18` }}
    >
      <div className="op-card-label">{title}</div>
      <div className="op-card-value" style={{ color }}>{value}</div>
    </div>
  );
}
