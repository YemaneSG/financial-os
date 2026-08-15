import { useState, useCallback, useEffect } from "react";
import { apiClient, ApiClientError } from "@/api/client";
import type {
  ReceiptDetail,
  CreateHumanRevisionRequest,
  LineItemInput,
  ReviewCandidate,
  DraftPatch,
} from "@/api/types";
import {
  decimalPlacesForCurrency,
  parseDollarsToMinor,
  parseDollarsToMinorOptional,
  minorToDollars,
  toLocalDatetimeString,
} from "./moneyUtils";
import { formatMinorUnits } from "./formatters";

function applyPatchToFormState(
  patch: DraftPatch[],
  formState: { subtotal: string; discount: string; lineItems: FormLineItem[] },
  dp: number,
): typeof formState {
  let { subtotal, discount, lineItems } = { ...formState, lineItems: [...formState.lineItems] };
  for (const p of patch) {
    if (p.op === "clear_receipt_discount") {
      discount = "";
    } else if (p.op === "set_receipt_subtotal" && p.value != null) {
      subtotal = minorToDollars(p.value, dp);
    } else if (p.op === "set_receipt_discount" && p.value != null) {
      discount = minorToDollars(p.value, dp);
    } else if (p.op === "clear_receipt_subtotal") {
      subtotal = "";
    } else if (p.op === "clear_line_discount" && p.ordinal != null) {
      lineItems = lineItems.map((li, idx) =>
        idx + 1 === p.ordinal ? { ...li, discount: "" } : li,
      );
    } else if (p.op === "set_line_total" && p.ordinal != null && p.value != null) {
      const value = p.value;
      lineItems = lineItems.map((li, idx) =>
        idx + 1 === p.ordinal ? { ...li, line_total: minorToDollars(value, dp) } : li,
      );
    } else if (p.op === "remove_line_item" && p.ordinal != null) {
      lineItems = lineItems.filter((_, idx) => idx + 1 !== p.ordinal);
    }
  }
  return { subtotal, discount, lineItems };
}

interface HumanReviewFormProps {
  receiptId: string;
  currentRevisionId: string;
  initialData: ReceiptDetail;
  initialCandidatePatch?: ReviewCandidate | null;
  onSuccess: () => Promise<void>;
  onCancel: () => void;
}

interface FormLineItem {
  description: string;
  normalized_description: string;
  quantity: string;
  unit: string;
  unit_price_decimal: string;
  line_total: string;
  discount: string;
  category_suggestion: string;
}

export function HumanReviewForm({
  receiptId,
  currentRevisionId,
  initialData,
  initialCandidatePatch,
  onSuccess,
  onCancel,
}: HumanReviewFormProps) {
  const rev = initialData.current_revision;

  // Currency is read-only from the parent revision — never editable by the user.
  const currency = rev?.currency ?? "USD";
  const dp = decimalPlacesForCurrency(currency);

  const [merchant, setMerchant] = useState(rev?.merchant_normalized ?? "");

  // datetime-local must reflect device local time, not UTC.
  const [purchaseDatetime, setPurchaseDatetime] = useState(() => {
    if (!rev?.purchase_datetime) return "";
    try {
      return toLocalDatetimeString(rev.purchase_datetime);
    } catch {
      return "";
    }
  });

  const [subtotal, setSubtotal] = useState(() => {
    const base = minorToDollars(rev?.subtotal_minor, dp);
    if (!initialCandidatePatch) return base;
    return applyPatchToFormState(
      initialCandidatePatch.draft_patch,
      { subtotal: base, discount: "", lineItems: [] },
      dp,
    ).subtotal;
  });
  const [tax, setTax] = useState(() => minorToDollars(rev?.tax_minor, dp));
  const [tip, setTip] = useState(() => minorToDollars(rev?.tip_minor, dp));
  const [discount, setDiscount] = useState(() => {
    const base = minorToDollars(rev?.discount_minor, dp);
    if (!initialCandidatePatch) return base;
    return applyPatchToFormState(
      initialCandidatePatch.draft_patch,
      { subtotal: "", discount: base, lineItems: [] },
      dp,
    ).discount;
  });
  const [total, setTotal] = useState(() => minorToDollars(rev?.total_minor, dp));
  const discountIsIncludedInSubtotal =
    initialCandidatePatch?.kind === "confirm_discount_included_in_subtotal";

  const [lineItems, setLineItems] = useState<FormLineItem[]>(() => {
    const items = initialData.line_items;
    const baseItems: FormLineItem[] =
      !items || items.length === 0
        ? []
        : items
            .slice()
            .sort((a, b) => a.ordinal - b.ordinal)
            .map((item) => ({
              description: item.normalized_description ?? item.raw_description,
              normalized_description: item.normalized_description ?? "",
              quantity: item.quantity ?? "",
              unit: item.unit ?? "",
              unit_price_decimal: item.unit_price_decimal ?? "",
              line_total: minorToDollars(item.line_total_minor, dp),
              discount: minorToDollars(item.discount_minor, dp),
              category_suggestion: item.category_suggestion ?? "",
            }));
    if (!initialCandidatePatch) return baseItems;
    return applyPatchToFormState(
      initialCandidatePatch.draft_patch,
      { subtotal: "", discount: "", lineItems: baseItems },
      dp,
    ).lineItems;
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflictError, setConflictError] = useState(false);

  useEffect(() => {
    if (!initialCandidatePatch) return;
    const patch = initialCandidatePatch.draft_patch[0];
    if (!patch) return;

    let targetId = "hrf-subtotal";
    if (patch.op === "clear_receipt_discount" || patch.op === "set_receipt_discount") {
      targetId = "hrf-discount";
    } else if (patch.op === "clear_line_discount" && patch.ordinal != null) {
      targetId = `hrf-li-discount-${patch.ordinal - 1}`;
    } else if (patch.op === "set_line_total" && patch.ordinal != null) {
      targetId = `hrf-li-total-${patch.ordinal - 1}`;
    }

    const frame = window.requestAnimationFrame(() => {
      const target = document.getElementById(targetId);
      target?.focus();
      target?.scrollIntoView?.({ behavior: "smooth", block: "center" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [initialCandidatePatch]);

  const addLineItem = useCallback(() => {
    setLineItems((prev) => [
      ...prev,
      {
        description: "",
        normalized_description: "",
        quantity: "",
        unit: "",
        unit_price_decimal: "",
        line_total: "",
        discount: "",
        category_suggestion: "",
      },
    ]);
  }, []);

  const removeLineItem = useCallback((index: number) => {
    setLineItems((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const updateLineItem = useCallback(
    (index: number, field: keyof FormLineItem, value: string) => {
      setLineItems((prev) =>
        prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)),
      );
    },
    [],
  );

  const moveLineItemUp = useCallback((index: number) => {
    if (index === 0) return;
    setLineItems((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next;
    });
  }, []);

  const moveLineItemDown = useCallback((index: number) => {
    setLineItems((prev) => {
      if (index >= prev.length - 1) return prev;
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next;
    });
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);
      setError(null);
      setConflictError(false);

      // Client-side exact money validation — no parseFloat, no floating-point.
      let totalMinor: number;
      try {
        totalMinor = parseDollarsToMinor(total, dp);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Invalid total amount.");
        setSubmitting(false);
        return;
      }

      let subtotalMinor: number | null = null;
      let taxMinor: number | null = null;
      let tipMinor: number | null = null;
      let discountMinor: number | null = null;
      try {
        subtotalMinor = parseDollarsToMinorOptional(subtotal, dp);
        taxMinor = parseDollarsToMinorOptional(tax, dp);
        tipMinor = parseDollarsToMinorOptional(tip, dp);
        discountMinor = parseDollarsToMinorOptional(discount, dp);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Invalid amount.");
        setSubmitting(false);
        return;
      }

      const lineItemInputs: LineItemInput[] = [];
      for (const item of lineItems) {
        if (!item.description.trim()) {
          setError("Each line item needs a description. Remove empty items before saving.");
          setSubmitting(false);
          return;
        }
        let lineTotalMinor: number | null = null;
        let lineDiscountMinor: number | null = null;
        try {
          lineTotalMinor = parseDollarsToMinorOptional(item.line_total, dp);
          lineDiscountMinor = parseDollarsToMinorOptional(item.discount, dp);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Invalid line item amount.");
          setSubmitting(false);
          return;
        }
        const li: LineItemInput = { description: item.description.trim() };
        if (item.normalized_description.trim())
          li.normalized_description = item.normalized_description;
        if (item.quantity.trim()) li.quantity = item.quantity;
        if (item.unit.trim()) li.unit = item.unit;
        if (item.unit_price_decimal.trim()) li.unit_price_decimal = item.unit_price_decimal;
        if (lineTotalMinor !== null) li.line_total_minor = lineTotalMinor;
        if (lineDiscountMinor !== null) li.discount_minor = lineDiscountMinor;
        if (item.category_suggestion.trim()) li.category_suggestion = item.category_suggestion;
        lineItemInputs.push(li);
      }

      const req: CreateHumanRevisionRequest = {
        expected_parent_revision_id: currentRevisionId,
        currency,
        total_minor: totalMinor,
        line_items: lineItemInputs,
      };

      if (merchant.trim()) req.merchant_normalized = merchant.trim();
      if (purchaseDatetime.trim()) {
        const purchaseDate = new Date(purchaseDatetime);
        if (Number.isNaN(purchaseDate.getTime())) {
          setError("Purchase date/time is invalid.");
          setSubmitting(false);
          return;
        }
        // datetime-local is in device local time; toISOString() converts to UTC.
        req.purchase_datetime = purchaseDate.toISOString();
        // Submit the IANA device timezone so the server can recover local time.
        req.purchase_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      }
      if (subtotalMinor !== null) req.subtotal_minor = subtotalMinor;
      if (taxMinor !== null) req.tax_minor = taxMinor;
      if (tipMinor !== null) req.tip_minor = tipMinor;
      if (discountMinor !== null) req.discount_minor = discountMinor;

      try {
        await apiClient.createHumanRevision(receiptId, req);
        await onSuccess();
      } catch (err) {
        if (err instanceof ApiClientError) {
          if (err.status === 409) {
            setConflictError(true);
          } else {
            setError(err.body.message || "Submission failed. Please try again.");
          }
        } else {
          setError("Network error. Please check your connection and try again.");
        }
      } finally {
        setSubmitting(false);
      }
    },
    [
      receiptId,
      currentRevisionId,
      merchant,
      purchaseDatetime,
      currency,
      dp,
      subtotal,
      tax,
      tip,
      discount,
      total,
      lineItems,
      onSuccess,
    ],
  );

  return (
    <form
      className="human-review-form"
      onSubmit={(e) => void handleSubmit(e)}
      aria-label="Correct this receipt"
      noValidate
    >
      <h2 className="human-review-form__title">Correct this receipt</h2>

      {conflictError && (
        <div role="alert" className="alert alert--error">
          Another change was made to this receipt. Please refresh and try again.
        </div>
      )}
      {error && (
        <div role="alert" className="alert alert--error">
          {error}
        </div>
      )}

      {/* Live arithmetic preview */}
      {(() => {
        let sub: number | null = null;
        let t: number | null = null;
        let ti: number | null = null;
        let di: number | null = null;
        try {
          sub = parseDollarsToMinorOptional(subtotal, dp);
        } catch {
          /* ignore parse errors in preview */
        }
        try {
          t = parseDollarsToMinorOptional(tax, dp);
        } catch {
          /* ignore */
        }
        try {
          ti = parseDollarsToMinorOptional(tip, dp);
        } catch {
          /* ignore */
        }
        try {
          di = parseDollarsToMinorOptional(discount, dp);
        } catch {
          /* ignore */
        }
        if (sub != null || t != null) {
          const appliedDiscount = discountIsIncludedInSubtotal ? 0 : (di ?? 0);
          const computed = (sub ?? 0) + (t ?? 0) + (ti ?? 0) - appliedDiscount;
          const totalMinor = (() => {
            try {
              return parseDollarsToMinor(total, dp);
            } catch {
              return null;
            }
          })();
          const matches = totalMinor != null && computed === totalMinor;
          return (
            <div
              className={`form-preview ${matches ? "form-preview--ok" : "form-preview--warn"}`}
              aria-live="polite"
            >
              Calculated: {formatMinorUnits(computed, currency)}
              {discountIsIncludedInSubtotal && (
                <span> · Discount retained as already included in subtotal</span>
              )}
              {totalMinor != null && !matches && (
                <span className="form-preview__delta">
                  {" "}
                  (Difference: {formatMinorUnits(totalMinor - computed, currency)})
                </span>
              )}
            </div>
          );
        }
        return null;
      })()}

      <div className="form-field">
        <label htmlFor="hrf-merchant">Merchant</label>
        <input
          id="hrf-merchant"
          type="text"
          value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
          maxLength={500}
          autoComplete="off"
        />
      </div>

      <div className="form-field">
        <label htmlFor="hrf-purchase-datetime">Purchase date/time</label>
        <input
          id="hrf-purchase-datetime"
          type="datetime-local"
          value={purchaseDatetime}
          onChange={(e) => setPurchaseDatetime(e.target.value)}
        />
      </div>

      {/* Currency is read-only from the parent revision */}
      <div className="form-field form-field--readonly">
        <span className="form-field__label">Currency</span>
        <span
          className="human-review-form__currency-display"
          aria-label={`Currency: ${currency}`}
        >
          {currency}
        </span>
      </div>

      <div className="form-field">
        <label htmlFor="hrf-subtotal">Subtotal ({currency})</label>
        <input
          id="hrf-subtotal"
          type="text"
          inputMode="decimal"
          value={subtotal}
          onChange={(e) => setSubtotal(e.target.value)}
        />
      </div>

      <div className="form-field">
        <label htmlFor="hrf-tax">Tax ({currency})</label>
        <input
          id="hrf-tax"
          type="text"
          inputMode="decimal"
          value={tax}
          onChange={(e) => setTax(e.target.value)}
        />
      </div>

      <div className="form-field">
        <label htmlFor="hrf-tip">Tip ({currency}) (optional)</label>
        <input
          id="hrf-tip"
          type="text"
          inputMode="decimal"
          value={tip}
          onChange={(e) => setTip(e.target.value)}
        />
      </div>

      <div className="form-field">
        <label htmlFor="hrf-discount">Discount ({currency}) (optional)</label>
        <input
          id="hrf-discount"
          type="text"
          inputMode="decimal"
          value={discount}
          onChange={(e) => setDiscount(e.target.value)}
        />
      </div>

      <div className="form-field">
        <label htmlFor="hrf-total">
          Total ({currency})<span aria-hidden="true"> *</span>
        </label>
        <input
          id="hrf-total"
          type="text"
          inputMode="decimal"
          required
          value={total}
          onChange={(e) => setTotal(e.target.value)}
        />
      </div>

      <section aria-label="Line items" className="human-review-form__line-items">
        <h3 className="human-review-form__section-title">Line items</h3>

        {lineItems.map((item, index) => (
          <div
            key={index}
            className="line-item-editor"
            aria-label={`Line item ${index + 1}`}
          >
            <div className="line-item-editor__header">
              <span className="line-item-editor__index">Item {index + 1}</span>
              <div className="line-item-editor__order-btns">
                <button
                  type="button"
                  className="btn btn--ghost btn--small"
                  onClick={() => moveLineItemUp(index)}
                  disabled={index === 0}
                  aria-label={`Move item ${index + 1} up`}
                >
                  ↑
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--small"
                  onClick={() => moveLineItemDown(index)}
                  disabled={index === lineItems.length - 1}
                  aria-label={`Move item ${index + 1} down`}
                >
                  ↓
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--small btn--danger"
                  onClick={() => removeLineItem(index)}
                  aria-label={`Remove line item ${index + 1}`}
                >
                  Remove
                </button>
              </div>
            </div>

            <div className="form-field">
              <label htmlFor={`hrf-li-desc-${index}`}>Description</label>
              <input
                id={`hrf-li-desc-${index}`}
                type="text"
                value={item.description}
                onChange={(e) => updateLineItem(index, "description", e.target.value)}
                maxLength={500}
              />
            </div>

            <div className="line-item-editor__row">
              <div className="form-field">
                <label htmlFor={`hrf-li-qty-${index}`}>Quantity</label>
                <input
                  id={`hrf-li-qty-${index}`}
                  type="text"
                  inputMode="decimal"
                  value={item.quantity}
                  maxLength={20}
                  onChange={(e) => updateLineItem(index, "quantity", e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor={`hrf-li-unit-${index}`}>Unit</label>
                <input
                  id={`hrf-li-unit-${index}`}
                  type="text"
                  value={item.unit}
                  onChange={(e) => updateLineItem(index, "unit", e.target.value)}
                />
              </div>
            </div>

            <div className="line-item-editor__row">
              <div className="form-field">
                <label htmlFor={`hrf-li-price-${index}`}>Unit price ({currency})</label>
                <input
                  id={`hrf-li-price-${index}`}
                  type="text"
                  inputMode="decimal"
                  value={item.unit_price_decimal}
                  maxLength={30}
                  onChange={(e) => updateLineItem(index, "unit_price_decimal", e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor={`hrf-li-total-${index}`}>Line total ({currency})</label>
                <input
                  id={`hrf-li-total-${index}`}
                  type="text"
                  inputMode="decimal"
                  value={item.line_total}
                  onChange={(e) => updateLineItem(index, "line_total", e.target.value)}
                />
              </div>
            </div>

            <div className="form-field">
              <label htmlFor={`hrf-li-discount-${index}`}>
                Item discount ({currency})
              </label>
              <input
                id={`hrf-li-discount-${index}`}
                type="text"
                inputMode="decimal"
                value={item.discount}
                onChange={(e) => updateLineItem(index, "discount", e.target.value)}
              />
            </div>
          </div>
        ))}

        <button type="button" className="btn btn--ghost btn--small" onClick={addLineItem}>
          Add line item
        </button>
      </section>

      <div className="human-review-form__actions">
        <button
          type="button"
          className="btn btn--ghost"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </button>
        <button type="submit" className="btn btn--primary" disabled={submitting}>
          {submitting ? "Saving…" : "Save"}
        </button>
      </div>
    </form>
  );
}
