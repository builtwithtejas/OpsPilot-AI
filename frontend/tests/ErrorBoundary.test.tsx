import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import ErrorBoundary from "@/components/ErrorBoundary";

function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error("Test explosion");
  return <div>All good</div>;
}

describe("ErrorBoundary", () => {
  // Suppress console.error output from React's error boundary mechanism
  beforeEach(() => { jest.spyOn(console, "error").mockImplementation(() => {}); });
  afterEach(() => { jest.restoreAllMocks(); });

  it("renders children normally when no error", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>
    );
    expect(screen.getByText("All good")).toBeInTheDocument();
  });

  it("shows error UI when child throws", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Test explosion")).toBeInTheDocument();
  });

  it("clears error when Try again is clicked", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    );
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    // After reset, ErrorBoundary re-renders children (will throw again in this test,
    // but the reset mechanism itself is what we're verifying)
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });
});
