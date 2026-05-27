"use client";

import { Component, type ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { error: Error | null; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            minHeight: "100vh",
            background: "#000",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "monospace",
            gap: "16px",
            padding: "40px",
          }}
        >
          <div style={{ fontSize: "48px" }}>⚠</div>
          <h2 style={{ color: "#ff4d4d", fontSize: "22px", margin: 0 }}>Something went wrong</h2>
          <p style={{ color: "#666", fontSize: "15px", margin: 0, textAlign: "center", maxWidth: "500px" }}>
            {this.state.error.message}
          </p>
          <button
            onClick={() => this.setState({ error: null })}
            style={{
              marginTop: "8px",
              padding: "12px 28px",
              background: "linear-gradient(to right, #33ff88, #00c3ff)",
              border: "none",
              borderRadius: "12px",
              color: "black",
              fontWeight: 700,
              fontSize: "15px",
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
