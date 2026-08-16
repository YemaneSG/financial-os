import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { ReceiptDashboard } from "@/receipts/ReceiptDashboard";

vi.mock("@/api/client", () => ({
  ApiClientError: class ApiClientError extends Error {
    constructor(public status: number) { super("Synthetic API error"); }
  },
  apiClient: {
    listReceipts: vi.fn(),
    searchReceipts: vi.fn(),
  },
}));

import { apiClient } from "@/api/client";

const mockList = apiClient.listReceipts as ReturnType<typeof vi.fn>;
const mockSearch = apiClient.searchReceipts as ReturnType<typeof vi.fn>;

const syntheticReceipt = {
  receipt_id: "aaaaaaaa-0000-0000-0000-000000000001",
  processing_status: "extracted",
  verification_status: "system_validated",
  financial_context: "personal",
  expected_asset_count: 1,
  acknowledged_at: "2026-08-16T12:00:00Z",
  created_at: "2026-08-16T12:00:00Z",
  current_revision: {
    merchant_normalized: "Synthetic Market",
    purchase_datetime: "2026-08-16T12:00:00Z",
    currency: "USD",
    total_minor: 4242,
  },
};

function renderDashboard() {
  return render(
    <MemoryRouter>
      <ReceiptDashboard />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockList.mockResolvedValue({ receipts: [syntheticReceipt], next_cursor: null });
  mockSearch
    .mockResolvedValueOnce({ receipts: [], total_count: 18, next_cursor: null })
    .mockResolvedValueOnce({ receipts: [], total_count: 2, next_cursor: null })
    .mockResolvedValueOnce({ receipts: [], total_count: 1, next_cursor: null })
    .mockResolvedValueOnce({ receipts: [], total_count: 0, next_cursor: null });
});

describe("ReceiptDashboard", () => {
  it("shows owner-scoped ingestion totals and recent receipts", async () => {
    renderDashboard();

    expect(screen.getByRole("status")).toHaveTextContent("Checking your receipt data");
    await waitFor(() => expect(screen.getByText("18")).toBeInTheDocument());

    expect(screen.getByText("Captured")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
    expect(screen.getByText("Needs review")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("Synthetic Market")).toBeInTheDocument();
    expect(screen.getByText("$42.42")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it("requests bounded total, processing, review, and failure counts", async () => {
    renderDashboard();
    await waitFor(() => expect(mockSearch).toHaveBeenCalledTimes(4));

    expect(mockList).toHaveBeenCalledWith(undefined, 5);
    expect(mockSearch).toHaveBeenNthCalledWith(1, { limit: 1 });
    expect(mockSearch).toHaveBeenNthCalledWith(2, {
      processing_status: ["queued", "processing"],
      limit: 1,
    });
    expect(mockSearch).toHaveBeenNthCalledWith(3, {
      verification_status: ["needs_review"],
      limit: 1,
    });
    expect(mockSearch).toHaveBeenNthCalledWith(4, {
      processing_status: ["retryable_failed", "failed", "abandoned"],
      limit: 1,
    });
  });

  it("shows an empty state without inventing receipt data", async () => {
    mockList.mockResolvedValue({ receipts: [], next_cursor: null });
    renderDashboard();

    await waitFor(() => expect(screen.getByText("Your history starts here")).toBeInTheDocument());
    expect(screen.queryByText("Synthetic Market")).not.toBeInTheDocument();
  });

  it("keeps a retryable dashboard error separate from capture", async () => {
    mockList.mockRejectedValue(new Error("Synthetic network failure"));
    renderDashboard();

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Dashboard unavailable"));
    expect(screen.getByRole("alert")).toHaveTextContent("Capture still works");
  });

  it("refreshes all dashboard data on request", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("18")).toBeInTheDocument());

    mockSearch
      .mockResolvedValueOnce({ receipts: [], total_count: 19, next_cursor: null })
      .mockResolvedValueOnce({ receipts: [], total_count: 0, next_cursor: null })
      .mockResolvedValueOnce({ receipts: [], total_count: 0, next_cursor: null })
      .mockResolvedValueOnce({ receipts: [], total_count: 0, next_cursor: null });
    fireEvent.click(screen.getByRole("button", { name: "Refresh receipt dashboard" }));

    await waitFor(() => expect(screen.getByText("19")).toBeInTheDocument());
    expect(mockList).toHaveBeenCalledTimes(2);
  });
});
