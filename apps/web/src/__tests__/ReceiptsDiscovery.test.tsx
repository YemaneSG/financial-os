/**
 * Tests for ReceiptsDiscovery component.
 *
 * Covers: initial render, search input, quick filters, filter sheet,
 * result grouping, load more, empty state, error state, match context,
 * accessibility attributes, and state restoration.
 *
 * All data is synthetic. api/client is mocked.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ReceiptsDiscovery } from "@/receipts/ReceiptsDiscovery";

// ── Synthetic fixtures ─────────────────────────────────────────────────────────

function makeReceipt(overrides: Partial<{
  receipt_id: string;
  merchant_normalized: string;
  total_minor: number;
  processing_status: string;
  verification_status: string;
  purchase_datetime: string;
  match_source: "merchant" | "line_item";
  matched_description: string;
}> = {}) {
  return {
    receipt_id: overrides.receipt_id ?? "aaaaaaaa-0000-0000-0000-000000000001",
    processing_status: overrides.processing_status ?? "extracted",
    verification_status: overrides.verification_status ?? "system_validated",
    financial_context: "personal",
    expected_asset_count: 1,
    acknowledged_at: "2026-08-01T12:00:00Z",
    created_at: "2026-08-01T12:00:00Z",
    current_revision: {
      merchant_normalized: overrides.merchant_normalized ?? "Synthetic Merchant",
      purchase_datetime: overrides.purchase_datetime ?? "2026-08-01T12:00:00Z",
      currency: "USD",
      total_minor: overrides.total_minor ?? 1000,
    },
    match_context: overrides.match_source
      ? {
          source: overrides.match_source,
          matched_description:
            overrides.match_source === "line_item"
              ? (overrides.matched_description ?? "Synthetic Item")
              : null,
        }
      : null,
  };
}

function makeSearchResponse(receipts = [makeReceipt()], totalCount = receipts.length) {
  return {
    receipts,
    total_count: totalCount,
    next_cursor: null,
  };
}

// ── Mock api/client ────────────────────────────────────────────────────────────

vi.mock("@/api/client", () => ({
  ApiClientError: class ApiClientError extends Error {
    constructor(public status: number, public body: { error_code: string; message: string }) {
      super(body.message);
    }
  },
  apiClient: {
    searchReceipts: vi.fn(),
  },
}));

import { apiClient } from "@/api/client";
import { resetDiscoveryStore } from "@/receipts/ReceiptsDiscovery";
const mockSearch = apiClient.searchReceipts as ReturnType<typeof vi.fn>;

// ── Helpers ────────────────────────────────────────────────────────────────────

function renderDiscovery() {
  return render(
    <MemoryRouter>
      <ReceiptsDiscovery />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  // Reset module-level store so each test gets a fresh component state.
  resetDiscoveryStore();
  mockSearch.mockResolvedValue(makeSearchResponse());
});

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("ReceiptsDiscovery — initial render", () => {
  it("renders the heading and search input", async () => {
    renderDiscovery();
    expect(screen.getByRole("heading", { name: /receipts/i })).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: /search merchant or item/i })).toBeInTheDocument();
    await waitFor(() => expect(mockSearch).toHaveBeenCalledTimes(1));
  });

  it("calls searchReceipts on mount with no filters", async () => {
    renderDiscovery();
    await waitFor(() => expect(mockSearch).toHaveBeenCalledTimes(1));
    const req = mockSearch.mock.calls[0][0];
    expect(req.query).toBeUndefined();
    expect(req.cursor).toBeUndefined();
  });

  it("shows result count after loading", async () => {
    mockSearch.mockResolvedValue(makeSearchResponse([makeReceipt()], 1));
    renderDiscovery();
    await waitFor(() => expect(screen.getByText("1 receipt")).toBeInTheDocument());
  });

  it("shows plural count", async () => {
    mockSearch.mockResolvedValue(makeSearchResponse([makeReceipt(), makeReceipt({ receipt_id: "bbb" })], 2));
    renderDiscovery();
    await waitFor(() => expect(screen.getByText("2 receipts")).toBeInTheDocument());
  });

  it("shows empty state when no results", async () => {
    mockSearch.mockResolvedValue(makeSearchResponse([], 0));
    renderDiscovery();
    await waitFor(() =>
      expect(screen.getByText(/no receipts have been captured/i)).toBeInTheDocument(),
    );
  });

  it("shows merchant name in card", async () => {
    mockSearch.mockResolvedValue(
      makeSearchResponse([makeReceipt({ merchant_normalized: "Coffee House" })]),
    );
    renderDiscovery();
    await waitFor(() => expect(screen.getByText("Coffee House")).toBeInTheDocument());
  });
});

describe("ReceiptsDiscovery — search input", () => {
  it("calls searchReceipts with query after debounce", async () => {
    renderDiscovery();
    await waitFor(() => expect(mockSearch).toHaveBeenCalledTimes(1));
    mockSearch.mockClear();

    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "coffee" } });

    await waitFor(() => expect(mockSearch).toHaveBeenCalledOnce());
    expect(mockSearch.mock.calls[0][0].query).toBe("coffee");
  });

  it("clear button resets query", async () => {
    renderDiscovery();
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "test" } });
    const clearBtn = screen.getByRole("button", { name: /clear search/i });
    expect(clearBtn).toBeInTheDocument();
    fireEvent.click(clearBtn);
    expect(input).toHaveValue("");
  });
});

describe("ReceiptsDiscovery — quick filters", () => {
  it("renders quick filter buttons", async () => {
    renderDiscovery();
    expect(screen.getByRole("button", { name: /needs review/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /duplicates/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /verified/i })).toBeInTheDocument();
  });

  it("quick filter sets aria-pressed and sends correct verification_status", async () => {
    renderDiscovery();
    await waitFor(() => expect(mockSearch).toHaveBeenCalledTimes(1));
    mockSearch.mockClear();

    const btn = screen.getByRole("button", { name: /needs review/i });
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "true");

    await waitFor(() => expect(mockSearch).toHaveBeenCalledOnce());
    expect(mockSearch.mock.calls[0][0].verification_status).toEqual(["needs_review"]);
  });

  it("clicking active quick filter deactivates it", async () => {
    renderDiscovery();
    const btn = screen.getByRole("button", { name: /verified/i });
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });
});

describe("ReceiptsDiscovery — match context", () => {
  it("shows match hint for line_item match", async () => {
    mockSearch.mockResolvedValue(
      makeSearchResponse([
        makeReceipt({
          match_source: "line_item",
          matched_description: "organic apples",
        }),
      ]),
    );
    renderDiscovery();
    await waitFor(() =>
      expect(screen.getByText(/matched: organic apples/i)).toBeInTheDocument(),
    );
  });

  it("does not show match hint for merchant match", async () => {
    mockSearch.mockResolvedValue(
      makeSearchResponse([makeReceipt({ match_source: "merchant" })]),
    );
    renderDiscovery();
    await waitFor(() => expect(screen.queryByText(/matched:/i)).not.toBeInTheDocument());
  });
});

describe("ReceiptsDiscovery — load more", () => {
  it("shows Load more button when next_cursor is set", async () => {
    mockSearch.mockResolvedValue({
      receipts: [makeReceipt()],
      total_count: 5,
      next_cursor: "abc123",
    });
    renderDiscovery();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /load more receipts/i })).toBeInTheDocument(),
    );
  });

  it("hides Load more when next_cursor is null", async () => {
    renderDiscovery();
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: /load more receipts/i })).not.toBeInTheDocument(),
    );
  });

  it("calls searchReceipts with cursor on Load more click", async () => {
    mockSearch.mockResolvedValueOnce({
      receipts: [makeReceipt()],
      total_count: 2,
      next_cursor: "cursor-page2",
    });
    mockSearch.mockResolvedValueOnce(makeSearchResponse([makeReceipt({ receipt_id: "bbb" })]));

    renderDiscovery();
    const loadMore = await screen.findByRole("button", { name: /load more receipts/i });
    fireEvent.click(loadMore);

    await waitFor(() => expect(mockSearch).toHaveBeenCalledTimes(2));
    expect(mockSearch.mock.calls[1][0].cursor).toBe("cursor-page2");
  });
});

describe("ReceiptsDiscovery — filter sheet", () => {
  it("opens filter sheet on Filters button click", async () => {
    renderDiscovery();
    const btn = screen.getByRole("button", { name: /filters/i });
    fireEvent.click(btn);
    await waitFor(() =>
      expect(screen.getByRole("dialog", { name: /filter receipts/i })).toBeInTheDocument(),
    );
  });

  it("closes filter sheet on Cancel (×)", async () => {
    renderDiscovery();
    fireEvent.click(screen.getByRole("button", { name: /filters/i }));
    const dialog = await screen.findByRole("dialog");
    const closeBtn = within(dialog).getByRole("button", { name: /close filters/i });
    fireEvent.click(closeBtn);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });
});

describe("ReceiptsDiscovery — error state", () => {
  it("shows error message on API failure", async () => {
    mockSearch.mockRejectedValue(new Error("Network failure"));
    renderDiscovery();
    await waitFor(() =>
      expect(screen.getByRole("alert")).toBeInTheDocument(),
    );
  });
});

describe("ReceiptsDiscovery — accessibility", () => {
  it("search input has accessible label", async () => {
    renderDiscovery();
    const input = screen.getByRole("searchbox", { name: /search merchant or item/i });
    expect(input).toBeInTheDocument();
  });

  it("quick filters have aria-pressed attribute", async () => {
    renderDiscovery();
    const btns = screen.getAllByRole("button", { name: /needs review|duplicates|verified/i });
    for (const btn of btns) {
      expect(btn).toHaveAttribute("aria-pressed");
    }
  });

  it("filters button has aria-expanded attribute", async () => {
    renderDiscovery();
    const btn = screen.getByRole("button", { name: /filters/i });
    expect(btn).toHaveAttribute("aria-expanded");
  });

  it("live region present for screen reader announcements", async () => {
    renderDiscovery();
    const live = document.querySelector("[role='status'][aria-live='polite']");
    expect(live).toBeInTheDocument();
  });
});

describe("ReceiptsDiscovery — month grouping", () => {
  it("groups receipts under month heading", async () => {
    mockSearch.mockResolvedValue(
      makeSearchResponse([
        makeReceipt({ purchase_datetime: "2026-06-15T10:00:00Z", merchant_normalized: "Store A" }),
        makeReceipt({ receipt_id: "bbb", purchase_datetime: "2026-07-05T10:00:00Z", merchant_normalized: "Store B" }),
      ], 2),
    );
    renderDiscovery();
    await waitFor(() => {
      expect(screen.getByText("Store A")).toBeInTheDocument();
      expect(screen.getByText("Store B")).toBeInTheDocument();
    });
    // Both months should appear as section headings
    expect(screen.getByRole("region", { name: /june 2026/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /july 2026/i })).toBeInTheDocument();
  });
});
