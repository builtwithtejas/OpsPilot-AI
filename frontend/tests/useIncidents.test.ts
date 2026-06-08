import { renderHook, act, waitFor } from "@testing-library/react";
import { useIncidents } from "@/hooks/useIncidents";
import * as api from "@/lib/api";

// Mock the entire api module
jest.mock("@/lib/api");
const mockApi = api as jest.Mocked<typeof api>;

const MOCK_INCIDENTS = [
  {
    id: 1,
    title: "Test incident one",
    severity: "High" as const,
    status: "Open" as const,
    description: "Something broke in the pipeline.",
    remediation: "Fix the thing.",
    confidence: 85,
    source: "agent",
    pipeline_id: "123",
    gitlab_issue_url: null,
    autofix_mr_url: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    title: "Test incident two",
    severity: "Low" as const,
    status: "Resolved" as const,
    description: "Minor issue in staging.",
    remediation: "Restart.",
    confidence: 60,
    source: "upload",
    pipeline_id: null,
    gitlab_issue_url: null,
    autofix_mr_url: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];


describe("useIncidents", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads incidents on mount", async () => {
    mockApi.fetchIncidents.mockResolvedValue(MOCK_INCIDENTS);

    const { result } = renderHook(() => useIncidents());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.incidents).toHaveLength(2);
    expect(result.current.incidents[0].title).toBe("Test incident one");
    expect(result.current.error).toBeNull();
  });

  it("sets error state when fetch fails", async () => {
    mockApi.fetchIncidents.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useIncidents());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.incidents).toHaveLength(0);
  });

  it("optimistically updates status before server responds", async () => {
    mockApi.fetchIncidents.mockResolvedValue(MOCK_INCIDENTS);
    const updated = { ...MOCK_INCIDENTS[0], status: "Resolved" as const };
    mockApi.updateIncidentStatus.mockResolvedValue(updated);

    const { result } = renderHook(() => useIncidents());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      void result.current.updateStatus(1, "Resolved");
    });

    // Optimistic — applied immediately before the server responds
    expect(result.current.incidents[0].status).toBe("Resolved");
  });

  it("reverts status on server error", async () => {
    mockApi.fetchIncidents.mockResolvedValue(MOCK_INCIDENTS);
    mockApi.updateIncidentStatus.mockRejectedValue(new Error("Server error"));

    const { result } = renderHook(() => useIncidents());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.updateStatus(1, "Resolved");
    });

    // Should have reverted back to "Open"
    expect(result.current.incidents[0].status).toBe("Open");
    expect(result.current.error).toBe("Failed to update status");
  });

  it("removes incident from list on delete", async () => {
    mockApi.fetchIncidents.mockResolvedValue(MOCK_INCIDENTS);
    mockApi.deleteIncident.mockResolvedValue(undefined);

    const { result } = renderHook(() => useIncidents());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.remove(1);
    });

    expect(result.current.incidents).toHaveLength(1);
    expect(result.current.incidents[0].id).toBe(2);
  });

  it("sets error when delete fails", async () => {
    mockApi.fetchIncidents.mockResolvedValue(MOCK_INCIDENTS);
    mockApi.deleteIncident.mockRejectedValue(new Error("Delete failed"));

    const { result } = renderHook(() => useIncidents());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.remove(1);
    });

    // Incidents unchanged, error set
    expect(result.current.incidents).toHaveLength(2);
    expect(result.current.error).toBe("Failed to delete");
  });

  it("refresh reloads incidents from server", async () => {
    mockApi.fetchIncidents.mockResolvedValue(MOCK_INCIDENTS);

    const { result } = renderHook(() => useIncidents());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const newIncident = { ...MOCK_INCIDENTS[0], id: 99, title: "Brand new incident" };
    mockApi.fetchIncidents.mockResolvedValue([...MOCK_INCIDENTS, newIncident]);

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.incidents).toHaveLength(3);
    expect(result.current.incidents[2].title).toBe("Brand new incident");
  });
});
