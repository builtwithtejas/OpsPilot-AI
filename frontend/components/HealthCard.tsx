interface Props {
  title: string;
  value: string;
  color: string;
}

export default function HealthCard({ title, value, color }: Props) {
  return (
    <div
      className="hover-card op-card"
      style={{ border: `1px solid ${color}55` }}
    >
      <div className="op-card-label">{title}</div>
      <div className="op-card-value" style={{ color }}>{value}</div>
    </div>
  );
}