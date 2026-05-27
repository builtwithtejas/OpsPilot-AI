interface Props {
  title: string;
  children: React.ReactNode;
}

export default function Section({ title, children }: Props) {
  return (
    <div
      className="hover-card"
      style={{
        background: "rgba(10,10,10,0.7)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "24px",
        padding: "30px",
        marginBottom: "30px",
        backdropFilter: "blur(14px)",
      }}
    >
      <h2 style={{ fontSize: "26px", marginBottom: "24px", fontWeight: 700 }}>{title}</h2>
      {children}
    </div>
  );
}
