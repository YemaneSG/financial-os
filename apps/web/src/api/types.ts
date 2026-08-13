// Types derived from contracts/openapi.yaml — do not add fields not in the contract.

export type UUID = string;
export type Timestamp = string;
export type Currency = string;
export type MinorUnits = number | null;

export type ProcessingStatus =
  | "reserved"
  | "uploading"
  | "uploaded"
  | "queued"
  | "processing"
  | "extracted"
  | "retryable_failed"
  | "failed"
  | "abandoned";

export type VerificationStatus =
  | "unreviewed"
  | "system_validated"
  | "needs_review"
  | "human_verified";

export type FinancialContext = "personal" | "rental_property";

export type UploadStatus = "reserved" | "uploaded" | "verified" | "rejected";

export interface AssetInput {
  ordinal: number;
  declared_mime_type: string;
  byte_size: number;
}

export interface UploadCapability {
  asset_id: UUID;
  ordinal: number;
  upload_url: string;
  method: "PUT";
  expires_at: Timestamp;
  allowed_mime_types: string[];
}

export interface AssetSummary {
  asset_id: UUID;
  ordinal: number;
  upload_status: UploadStatus;
  verified_mime_type?: string | null;
  byte_size?: number | null;
}

export interface LineItemSummary {
  ordinal: number;
  raw_description: string;
  normalized_description?: string | null;
  quantity?: string | null;
  unit?: string | null;
  unit_price_decimal?: string | null;
  line_total_minor?: MinorUnits;
  discount_minor?: MinorUnits;
  category_suggestion?: string | null;
}

export interface ValidationFindingSummary {
  check_code: string;
  outcome: "pass" | "warn" | "fail" | "not_applicable";
  rule_version?: string;
}

export interface RevisionSummary {
  revision_id?: UUID;
  source_type?: "extractor" | "human" | "import";
  merchant_normalized?: string | null;
  purchase_datetime?: string | null;
  currency?: Currency;
  subtotal_minor?: MinorUnits;
  tax_minor?: MinorUnits;
  tip_minor?: MinorUnits;
  discount_minor?: MinorUnits;
  total_minor?: MinorUnits;
  overall_confidence?: number | null;
}

export interface ReceiptListItem {
  receipt_id: UUID;
  processing_status: ProcessingStatus;
  verification_status: VerificationStatus;
  financial_context: FinancialContext;
  expected_asset_count: number;
  acknowledged_at?: string | null;
  created_at: Timestamp;
  current_revision?: RevisionSummary | null;
}

export interface ReceiptDetail extends ReceiptListItem {
  assets?: AssetSummary[];
  line_items?: LineItemSummary[] | null;
  validation_findings?: ValidationFindingSummary[] | null;
  safe_error_code?: string | null;
  provenance_summary?: {
    provider: string;
    model_id: string;
    prompt_version: string;
    schema_version: string;
    attempt_count: number;
  } | null;
}

export interface CreateReceiptRequest {
  client_submission_key: UUID;
  expected_asset_count: number;
  financial_context?: FinancialContext;
  captured_at?: string | null;
  assets: AssetInput[];
}

export interface CreateReceiptResponse {
  receipt_id: UUID;
  processing_status: ProcessingStatus;
  upload_capabilities: UploadCapability[];
}

export interface FinalizeReceiptResponse {
  receipt_id: UUID;
  processing_status: ProcessingStatus;
  acknowledged_at: Timestamp;
}

export interface ListReceiptsResponse {
  receipts: ReceiptListItem[];
  next_cursor?: string | null;
}

export interface RetryProcessingResponse {
  receipt_id: UUID;
  processing_status: ProcessingStatus;
}

export interface DownloadCapabilityResponse {
  download_url: string;
  method: "GET";
  expires_at: Timestamp;
}

export interface ApiError {
  error_code: string;
  message: string;
  request_id?: string | null;
}
