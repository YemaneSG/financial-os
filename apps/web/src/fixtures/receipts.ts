// Synthetic-only test fixtures. No real receipt images, real receipts, or owner data.
// These fixtures are used exclusively in unit and component tests.

import type {
  ReceiptListItem,
  ReceiptDetail,
  CreateReceiptResponse,
  FinalizeReceiptResponse,
  UploadCapability,
} from "@/api/types";

export const FIXTURE_RECEIPT_ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
export const FIXTURE_ASSET_ID_1 = "11111111-2222-4333-8444-555555555555";
export const FIXTURE_ASSET_ID_2 = "66666666-7777-4888-8999-aaaaaaaaaaaa";
export const FIXTURE_CLIENT_KEY = "cccccccc-dddd-4eee-8fff-000000000001";

export const FIXTURE_UPLOAD_CAPABILITIES: UploadCapability[] = [
  {
    asset_id: FIXTURE_ASSET_ID_1,
    ordinal: 1,
    upload_url: "https://storage.example.invalid/upload/1",
    method: "PUT",
    expires_at: "2099-01-01T00:00:00.000Z",
    allowed_mime_types: ["image/jpeg", "image/png", "image/heic"],
  },
];

export const FIXTURE_CREATE_RECEIPT_RESPONSE: CreateReceiptResponse = {
  receipt_id: FIXTURE_RECEIPT_ID,
  processing_status: "uploading",
  upload_capabilities: FIXTURE_UPLOAD_CAPABILITIES,
};

export const FIXTURE_FINALIZE_RESPONSE: FinalizeReceiptResponse = {
  receipt_id: FIXTURE_RECEIPT_ID,
  processing_status: "queued",
  acknowledged_at: "2026-08-12T14:30:00.000Z",
};

export const FIXTURE_RECEIPT_LIST_ITEM_PROCESSING: ReceiptListItem = {
  receipt_id: FIXTURE_RECEIPT_ID,
  processing_status: "processing",
  verification_status: "unreviewed",
  financial_context: "personal",
  expected_asset_count: 1,
  acknowledged_at: "2026-08-12T14:30:00.000Z",
  created_at: "2026-08-12T14:29:50.000Z",
  current_revision: null,
};

export const FIXTURE_RECEIPT_LIST_ITEM_EXTRACTED: ReceiptListItem = {
  receipt_id: FIXTURE_RECEIPT_ID,
  processing_status: "extracted",
  verification_status: "system_validated",
  financial_context: "personal",
  expected_asset_count: 1,
  acknowledged_at: "2026-08-12T14:30:00.000Z",
  created_at: "2026-08-12T14:29:50.000Z",
  current_revision: {
    revision_id: "r1111111-2222-4333-8444-555555555555",
    source_type: "extractor",
    merchant_normalized: "Acme Market",
    purchase_datetime: "2026-08-12T12:00:00.000Z",
    currency: "USD",
    subtotal_minor: 1050,
    tax_minor: 84,
    tip_minor: null,
    discount_minor: null,
    total_minor: 1134,
    overall_confidence: 0.97,
  },
};

export const FIXTURE_RECEIPT_LIST_ITEM_FAILED: ReceiptListItem = {
  receipt_id: FIXTURE_RECEIPT_ID,
  processing_status: "retryable_failed",
  verification_status: "unreviewed",
  financial_context: "personal",
  expected_asset_count: 1,
  acknowledged_at: "2026-08-12T14:30:00.000Z",
  created_at: "2026-08-12T14:29:50.000Z",
  current_revision: null,
};

export const FIXTURE_RECEIPT_DETAIL: ReceiptDetail = {
  ...FIXTURE_RECEIPT_LIST_ITEM_EXTRACTED,
  assets: [
    {
      asset_id: FIXTURE_ASSET_ID_1,
      ordinal: 1,
      upload_status: "verified",
      verified_mime_type: "image/jpeg",
      byte_size: 524288,
    },
  ],
  line_items: [
    {
      ordinal: 1,
      raw_description: "Organic Milk 1gal",
      normalized_description: "Organic Milk 1gal",
      quantity: "1",
      unit: "ea",
      unit_price_decimal: "5.99",
      line_total_minor: 599,
      discount_minor: null,
      category_suggestion: null,
    },
    {
      ordinal: 2,
      raw_description: "Sourdough Bread",
      normalized_description: "Sourdough Bread",
      quantity: "1",
      unit: "ea",
      unit_price_decimal: "4.51",
      line_total_minor: 451,
      discount_minor: null,
      category_suggestion: null,
    },
  ],
  validation_findings: [
    { check_code: "TOTALS_ARITHMETIC_V1", outcome: "pass" },
    { check_code: "CURRENCY_CONSISTENT_V1", outcome: "pass" },
  ],
  safe_error_code: null,
  provenance_summary: {
    provider: "vertex-ai",
    model_id: "gemini-2.0-flash-001",
    prompt_version: "v1",
    schema_version: "v1",
    attempt_count: 1,
  },
};
