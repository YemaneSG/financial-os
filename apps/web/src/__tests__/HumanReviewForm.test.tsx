import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { HumanReviewForm } from "@/receipts/HumanReviewForm";
import { parseDollarsToMinor } from "@/receipts/moneyUtils";
import type { ReceiptDetail } from "@/api/types";

// Mock the API client. vi.mock is hoisted so this runs before any imports.
vi.mock("@/api/client", () => {
  class MockApiClientError extends Error {
    status: number;
    body: { error_code: string; message: string; request_id?: string | null };
    constructor(
      status: number,
      body: { error_code: string; message: string; request_id?: string | null },
    ) {
      super(body.message);
      this.name = "ApiClientError";
      this.status = status;
      this.body = body;
    }
  }
  return {
    apiClient: {
      createHumanRevision: vi.fn(),
    },
    ApiClientError: MockApiClientError,
    NetworkError: class NetworkError extends Error {
      constructor(msg: string) {
        super(msg);
        this.name = "NetworkError";
      }
    },
  };
});

import { apiClient, ApiClientError } from "@/api/client";

const mockCreateHumanRevision = vi.mocked(apiClient.createHumanRevision);

const RECEIPT_ID = "receipt-uuid-001";
const REVISION_ID = "revision-uuid-001";

function makeInitialData(overrides: Partial<ReceiptDetail> = {}): ReceiptDetail {
  return {
    receipt_id: RECEIPT_ID,
    processing_status: "extracted",
    verification_status: "needs_review",
    financial_context: "personal",
    expected_asset_count: 1,
    created_at: "2024-01-15T10:00:00Z",
    current_revision: {
      revision_id: REVISION_ID,
      source_type: "extractor",
      merchant_normalized: "Test Grocery Store",
      purchase_datetime: "2024-01-15T10:00:00Z",
      currency: "USD",
      subtotal_minor: 1000,
      tax_minor: 80,
      total_minor: 1080,
    },
    line_items: [
      {
        ordinal: 1,
        raw_description: "Apple",
        normalized_description: "Apple",
        quantity: "2",
        unit: "ea",
        unit_price_decimal: "0.50",
        line_total_minor: 100,
      },
    ],
    ...overrides,
  };
}

function renderForm(
  initialDataOverrides: Partial<ReceiptDetail> = {},
  onSuccess = vi.fn((): Promise<void> => Promise.resolve()),
  onCancel = vi.fn(),
) {
  const initialData = makeInitialData(initialDataOverrides);
  return render(
    <HumanReviewForm
      receiptId={RECEIPT_ID}
      currentRevisionId={REVISION_ID}
      initialData={initialData}
      onSuccess={onSuccess}
      onCancel={onCancel}
    />,
  );
}

// ── parseDollarsToMinor unit tests ────────────────────────────────────────────

describe("parseDollarsToMinor", () => {
  it("converts 12.99 to 1299 exactly (no floating-point error)", () => {
    expect(parseDollarsToMinor("12.99", 2)).toBe(1299);
  });

  it("rejects 1.005 for a 2-decimal-place currency (excessive fractional digits)", () => {
    expect(() => parseDollarsToMinor("1.005", 2)).toThrow();
  });

  it("rejects blank string as required total", () => {
    expect(() => parseDollarsToMinor("", 2)).toThrow(/required/i);
  });

  it("rejects whitespace-only string", () => {
    expect(() => parseDollarsToMinor("   ", 2)).toThrow(/required/i);
  });

  it("rejects negative values", () => {
    expect(() => parseDollarsToMinor("-1.00", 2)).toThrow();
  });

  it("rejects non-numeric string", () => {
    expect(() => parseDollarsToMinor("abc", 2)).toThrow();
  });

  it("converts 0.01 to 1 (one cent)", () => {
    expect(parseDollarsToMinor("0.01", 2)).toBe(1);
  });

  it("converts integer 5 to 500 for 2-decimal currency", () => {
    expect(parseDollarsToMinor("5", 2)).toBe(500);
  });

  it("converts 10.50 to 1050 exactly", () => {
    expect(parseDollarsToMinor("10.50", 2)).toBe(1050);
  });

  it("converts 0 to 0 for 2-decimal currency", () => {
    expect(parseDollarsToMinor("0", 2)).toBe(0);
  });

  it("rejects NaN-like strings", () => {
    expect(() => parseDollarsToMinor("NaN", 2)).toThrow();
  });

  it("handles zero-decimal currency (JPY): rejects decimal string", () => {
    expect(() => parseDollarsToMinor("1.5", 0)).toThrow();
  });

  it("handles zero-decimal currency (JPY): accepts integer string", () => {
    expect(parseDollarsToMinor("1500", 0)).toBe(1500);
  });

  it("rejects amounts above JavaScript safe-integer range", () => {
    expect(() => parseDollarsToMinor("90071992547409.92", 2)).toThrow(/too large/i);
  });
});

// ── Form render and interaction tests ────────────────────────────────────────

describe("HumanReviewForm", () => {
  beforeEach(() => {
    mockCreateHumanRevision.mockReset();
  });

  it("renders with pre-populated merchant from initial data", () => {
    renderForm();
    const merchantInput = screen.getByLabelText(/^merchant$/i) as HTMLInputElement;
    expect(merchantInput.value).toBe("Test Grocery Store");
  });

  it("calls onCancel when Cancel is clicked", () => {
    const onCancel = vi.fn();
    renderForm({}, vi.fn((): Promise<void> => Promise.resolve()), onCancel);
    fireEvent.click(screen.getByRole("button", { name: /^cancel$/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("shows submitting state while API call is in progress", async () => {
    let resolveApi: (value: ReceiptDetail) => void = () => {};
    mockCreateHumanRevision.mockReturnValue(
      new Promise<ReceiptDetail>((res) => {
        resolveApi = res;
      }),
    );

    const onSuccess = vi.fn((): Promise<void> => Promise.resolve());
    renderForm({}, onSuccess);

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /saving/i })).toBeInTheDocument();
    });

    // Resolve to allow cleanup
    resolveApi(makeInitialData({ verification_status: "human_verified" }));
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it("calls onSuccess after successful submission", async () => {
    const onSuccess = vi.fn((): Promise<void> => Promise.resolve());
    mockCreateHumanRevision.mockResolvedValue(
      makeInitialData({ verification_status: "human_verified" }),
    );

    renderForm({}, onSuccess);
    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledOnce();
    });
  });

  it("shows conflict error on 409", async () => {
    mockCreateHumanRevision.mockRejectedValue(
      new ApiClientError(409, {
        error_code: "STALE_PARENT_REVISION",
        message: "Stale parent revision",
      }),
    );

    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/another change was made to this receipt/i),
      ).toBeInTheDocument();
    });
  });

  it("shows validation error on 422", async () => {
    mockCreateHumanRevision.mockRejectedValue(
      new ApiClientError(422, {
        error_code: "VALIDATION_ERROR",
        message: "Total does not match sum of line items",
      }),
    );

    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/total does not match sum of line items/i),
      ).toBeInTheDocument();
    });
  });

  it("rejects an empty line-item description without calling the API", async () => {
    renderForm({
      line_items: [{ ordinal: 1, raw_description: "", line_total_minor: 100 }],
    });

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(screen.getByText(/each line item needs a description/i)).toBeInTheDocument();
    });
    expect(mockCreateHumanRevision).not.toHaveBeenCalled();
  });

  it("converts 12.99 in total field to 1299 minor units", async () => {
    mockCreateHumanRevision.mockResolvedValue(
      makeInitialData({ verification_status: "human_verified" }),
    );

    renderForm();

    // Label is now "Total (USD) *" — match with partial regex
    const totalInput = screen.getByLabelText(/^total \(/i) as HTMLInputElement;
    fireEvent.change(totalInput, { target: { value: "12.99" } });

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(mockCreateHumanRevision).toHaveBeenCalledWith(
        RECEIPT_ID,
        expect.objectContaining({ total_minor: 1299 }),
      );
    });
  });

  it("rejects 1.005 as total and shows error without calling API", async () => {
    renderForm();

    const totalInput = screen.getByLabelText(/^total \(/i) as HTMLInputElement;
    fireEvent.change(totalInput, { target: { value: "1.005" } });

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(mockCreateHumanRevision).not.toHaveBeenCalled();
  });

  it("rejects blank total and shows error without calling API", async () => {
    renderForm();

    const totalInput = screen.getByLabelText(/^total \(/i) as HTMLInputElement;
    fireEvent.change(totalInput, { target: { value: "" } });

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(mockCreateHumanRevision).not.toHaveBeenCalled();
  });

  it("shows the parent revision currency as read-only (not an editable field)", () => {
    renderForm();
    // Currency input is replaced by a read-only display; no editable currency input
    const currencyInputs = screen
      .queryAllByRole("textbox")
      .filter((el) => el.id === "hrf-currency");
    expect(currencyInputs).toHaveLength(0);
    // The read-only display is present
    expect(screen.getByLabelText(/^currency: USD$/i)).toBeInTheDocument();
  });

  // ── Line-item discount editing ─────────────────────────────────────────────

  it("includes line-item discount in submission", async () => {
    mockCreateHumanRevision.mockResolvedValue(
      makeInitialData({ verification_status: "human_verified" }),
    );
    renderForm();

    const discountInputs = screen.getAllByLabelText(/^item discount \(/i);
    expect(discountInputs.length).toBeGreaterThan(0);
    fireEvent.change(discountInputs[0], { target: { value: "0.50" } });

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(mockCreateHumanRevision).toHaveBeenCalledWith(
        RECEIPT_ID,
        expect.objectContaining({
          line_items: expect.arrayContaining([
            expect.objectContaining({ discount_minor: 50 }),
          ]),
        }),
      );
    });
  });

  it("omits line-item discount when the field is blank", async () => {
    mockCreateHumanRevision.mockResolvedValue(
      makeInitialData({ verification_status: "human_verified" }),
    );
    renderForm();

    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      const call = mockCreateHumanRevision.mock.calls[0][1];
      const items: LineItemInput[] = (call as { line_items: LineItemInput[] }).line_items;
      expect(items[0]).not.toHaveProperty("discount_minor");
    });
  });

  // ── Move up / Move down reorder ───────────────────────────────────────────

  it("moves a line item up when the ↑ button is clicked", () => {
    renderForm({
      line_items: [
        { ordinal: 1, raw_description: "Alpha", line_total_minor: 100 },
        { ordinal: 2, raw_description: "Beta", line_total_minor: 200 },
      ],
    });

    // "Move item 2 up" button
    const moveUpBtn = screen.getByRole("button", { name: /move item 2 up/i });
    fireEvent.click(moveUpBtn);

    // After moving up, the first description input should be "Beta"
    const descInputs = screen.getAllByLabelText(/^description$/i) as HTMLInputElement[];
    expect(descInputs[0].value).toBe("Beta");
    expect(descInputs[1].value).toBe("Alpha");
  });

  it("moves a line item down when the ↓ button is clicked", () => {
    renderForm({
      line_items: [
        { ordinal: 1, raw_description: "Alpha", line_total_minor: 100 },
        { ordinal: 2, raw_description: "Beta", line_total_minor: 200 },
      ],
    });

    // "Move item 1 down" button
    const moveDownBtn = screen.getByRole("button", { name: /move item 1 down/i });
    fireEvent.click(moveDownBtn);

    const descInputs = screen.getAllByLabelText(/^description$/i) as HTMLInputElement[];
    expect(descInputs[0].value).toBe("Beta");
    expect(descInputs[1].value).toBe("Alpha");
  });

  it("disables the ↑ button on the first item and ↓ button on the last", () => {
    renderForm({
      line_items: [
        { ordinal: 1, raw_description: "Alpha", line_total_minor: 100 },
        { ordinal: 2, raw_description: "Beta", line_total_minor: 200 },
      ],
    });

    const moveUpBtns = screen.getAllByRole("button", { name: /move item \d+ up/i });
    const moveDownBtns = screen.getAllByRole("button", { name: /move item \d+ down/i });

    expect(moveUpBtns[0]).toBeDisabled(); // first item cannot move up
    expect(moveDownBtns[moveDownBtns.length - 1]).toBeDisabled(); // last cannot move down
  });

  it("submits line items in the reordered sequence after a move", async () => {
    mockCreateHumanRevision.mockResolvedValue(
      makeInitialData({ verification_status: "human_verified" }),
    );

    renderForm({
      line_items: [
        { ordinal: 1, raw_description: "Alpha", line_total_minor: 100 },
        { ordinal: 2, raw_description: "Beta", line_total_minor: 200 },
      ],
    });

    fireEvent.click(screen.getByRole("button", { name: /move item 2 up/i }));
    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      const call = mockCreateHumanRevision.mock.calls[0][1];
      const items = (call as { line_items: Array<{ description: string }> }).line_items;
      expect(items[0].description).toBe("Beta");
      expect(items[1].description).toBe("Alpha");
    });
  });
});

// Type alias needed for the line-item discount test assertion
type LineItemInput = {
  description: string;
  discount_minor?: number;
  line_total_minor?: number;
};
