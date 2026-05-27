export default function LoadingScreen() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#000",
        color: "white",
        padding: "40px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {[400, 300, 500, 200].map((w, i) => (
        <div
          key={i}
          style={{
            height: i === 0 ? "80px" : "30px",
            width: `${w}px`,
            background: "#111",
            borderRadius: "14px",
            animation: "pulse 1.5s infinite",
          }}
        />
      ))}
    </main>
  );
}
