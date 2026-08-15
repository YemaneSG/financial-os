import type { CreateHumanRevisionRequest, ReceiptDetail } from "@/api/types";

export function buildConfirmedAsShownRequest(
  receipt: ReceiptDetail,
): CreateHumanRevisionRequest | null {
  const revision = receipt.current_revision;
  if (!revision?.revision_id || !revision.currency || revision.total_minor == null) return null;

  const request: CreateHumanRevisionRequest = {
    expected_parent_revision_id: revision.revision_id,
    currency: revision.currency,
    total_minor: revision.total_minor,
    review_disposition: "confirmed_as_shown",
    line_items: (receipt.line_items ?? [])
      .slice()
      .sort((a, b) => a.ordinal - b.ordinal)
      .map((item) => ({
        description: item.raw_description,
        ...(item.normalized_description != null
          ? { normalized_description: item.normalized_description }
          : {}),
        ...(item.quantity != null ? { quantity: item.quantity } : {}),
        ...(item.unit != null ? { unit: item.unit } : {}),
        ...(item.unit_price_decimal != null
          ? { unit_price_decimal: item.unit_price_decimal }
          : {}),
        ...(item.line_total_minor != null ? { line_total_minor: item.line_total_minor } : {}),
        ...(item.discount_minor != null ? { discount_minor: item.discount_minor } : {}),
        ...(item.category_suggestion != null
          ? { category_suggestion: item.category_suggestion }
          : {}),
      })),
  };

  if (revision.subtotal_minor != null) request.subtotal_minor = revision.subtotal_minor;
  if (revision.tax_minor != null) request.tax_minor = revision.tax_minor;
  if (revision.tip_minor != null) request.tip_minor = revision.tip_minor;
  if (revision.discount_minor != null) request.discount_minor = revision.discount_minor;
  if (revision.merchant_normalized != null) {
    request.merchant_normalized = revision.merchant_normalized;
  }
  if (revision.purchase_datetime != null) {
    request.purchase_datetime = revision.purchase_datetime;
  }
  if (revision.purchase_timezone != null) {
    request.purchase_timezone = revision.purchase_timezone;
  }
  return request;
}
