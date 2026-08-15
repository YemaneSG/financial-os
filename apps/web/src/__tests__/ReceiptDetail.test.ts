import { describe, expect, it } from "vitest";
import type { ReceiptDetail } from "@/api/types";
import { buildConfirmedAsShownRequest } from "@/receipts/confirmedAsShown";

function syntheticReceipt(): ReceiptDetail {
  return {
    receipt_id: "00000000-0000-4000-8000-000000000001",
    processing_status: "extracted",
    verification_status: "needs_review",
    financial_context: "personal",
    expected_asset_count: 1,
    created_at: "2026-08-14T12:00:00Z",
    current_revision: {
      revision_id: "00000000-0000-4000-8000-000000000002",
      source_type: "extractor",
      merchant_normalized: "SYNTHETIC STORE",
      purchase_datetime: "2026-08-14T12:00:00Z",
      purchase_timezone: "America/Chicago",
      currency: "USD",
      subtotal_minor: 1000,
      tax_minor: 80,
      discount_minor: 50,
      total_minor: 1030,
    },
    line_items: [
      {
        ordinal: 1,
        raw_description: "SYNTHETIC RAW ITEM",
        normalized_description: "Synthetic Item",
        quantity: "2.000000",
        unit: "ea",
        unit_price_decimal: "5.000000",
        line_total_minor: 1000,
        discount_minor: 50,
        category_suggestion: "synthetic-category",
      },
    ],
  };
}

describe("buildConfirmedAsShownRequest", () => {
  it("copies the complete parent snapshot without substituting normalized text", () => {
    const request = buildConfirmedAsShownRequest(syntheticReceipt());

    expect(request).toMatchObject({
      merchant_normalized: "SYNTHETIC STORE",
      purchase_datetime: "2026-08-14T12:00:00Z",
      purchase_timezone: "America/Chicago",
      currency: "USD",
      subtotal_minor: 1000,
      tax_minor: 80,
      discount_minor: 50,
      total_minor: 1030,
      review_disposition: "confirmed_as_shown",
    });
    expect(request?.line_items).toEqual([
      {
        description: "SYNTHETIC RAW ITEM",
        normalized_description: "Synthetic Item",
        quantity: "2.000000",
        unit: "ea",
        unit_price_decimal: "5.000000",
        line_total_minor: 1000,
        discount_minor: 50,
        category_suggestion: "synthetic-category",
      },
    ]);
  });

  it("does not fabricate a zero total when the parent total is absent", () => {
    const receipt = syntheticReceipt();
    if (!receipt.current_revision) throw new Error("Synthetic revision is required");
    receipt.current_revision.total_minor = null;
    expect(buildConfirmedAsShownRequest(receipt)).toBeNull();
  });
});
