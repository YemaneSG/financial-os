import type {
  LineItemSummary,
  ReviewCandidate,
  ReviewGuidance,
  RevisionSummary,
} from "@/api/types";
import { formatMinorUnits } from "./formatters";

interface ValidationGuidanceProps {
  guidance: ReviewGuidance;
  currency: string;
  revision?: RevisionSummary | null;
  lineItems?: LineItemSummary[] | null;
  onApplyCandidate: (candidate: ReviewCandidate) => void;
  onConfirmAsShown: () => void;
  onEditManually: () => void;
}

function friendlyFieldName(field: string | null | undefined): string {
  if (!field) return "receipt";
  const map: Record<string, string> = {
    discount_minor: "Discount",
    subtotal_minor: "Subtotal",
    line_total_minor: "Line total",
    tax_minor: "Tax",
  };
  return map[field] ?? field;
}

function kindLabel(kind: string): string {
  const map: Record<string, string> = {
    confirm_discount_included_in_subtotal: "Confirm discount is included in subtotal",
    clear_receipt_discount: "Clear duplicate discount",
    use_gross_line_sum_as_subtotal: "Set subtotal from line items",
    use_net_line_sum_as_subtotal: "Set subtotal from net line items",
    clear_line_discount: "Clear duplicate line discount",
    replace_line_total_with_qty_price: "Correct line total from quantity × price",
    remove_line_item: "Remove duplicate line item",
  };
  return map[kind] ?? kind;
}

function describeCandidate(
  c: ReviewCandidate,
  currency: string,
  lineItems: LineItemSummary[] | null | undefined,
): string {
  const lineItem =
    c.target_item_ordinal == null
      ? null
      : lineItems?.find((item) => item.ordinal === c.target_item_ordinal);
  const description = lineItem?.normalized_description ?? lineItem?.raw_description;
  const clippedDescription =
    description && description.length > 80 ? `${description.slice(0, 77)}…` : description;
  const target =
    c.target_item_ordinal != null
      ? `line item ${c.target_item_ordinal}${clippedDescription ? `, “${clippedDescription}”` : ""}`
      : friendlyFieldName(c.target_field);
  const amountStr =
    c.amount_minor != null ? ` (${formatMinorUnits(c.amount_minor, currency)})` : "";
  if (c.kind === "clear_receipt_discount") {
    return `${kindLabel(c.kind)}${amountStr}`;
  }
  if (c.kind === "confirm_discount_included_in_subtotal") {
    return `${kindLabel(c.kind)}${amountStr}`;
  }
  if (
    c.kind === "use_gross_line_sum_as_subtotal" ||
    c.kind === "use_net_line_sum_as_subtotal"
  ) {
    return `${kindLabel(c.kind)}${amountStr}`;
  }
  return `${kindLabel(c.kind)} on ${target}${amountStr}`;
}

function formattedComponentEquation(
  revision: RevisionSummary | null | undefined,
  guidance: ReviewGuidance,
  currency: string,
): string {
  if (!revision) return guidance.component_equation;
  const components: string[] = [];
  if (revision.subtotal_minor != null) {
    components.push(`Subtotal ${formatMinorUnits(revision.subtotal_minor, currency)}`);
  }
  if (revision.tax_minor != null) {
    components.push(`Tax ${formatMinorUnits(revision.tax_minor, currency)}`);
  }
  if (revision.tip_minor != null) {
    components.push(`Tip ${formatMinorUnits(revision.tip_minor, currency)}`);
  }
  let equation = components.join(" + ");
  if (revision.discount_minor != null) {
    equation += ` − Discount ${formatMinorUnits(revision.discount_minor, currency)}`;
  }
  if (!equation) return guidance.component_equation;
  return `${equation} = ${formatMinorUnits(guidance.computed_total_minor, currency)}`;
}

function candidateReason(c: ReviewCandidate): string {
  const reasons: Record<string, string> = {
    subtotal_already_includes_receipt_discount:
      "Subtotal already includes this discount; keep both evidenced values and apply the discount only once",
    receipt_discount_matches_delta: "Receipt discount equals the arithmetic difference",
    gross_line_sum_restores_total: "Sum of line totals restores the receipt total",
    net_line_sum_restores_total: "Net line sum (after discounts) restores the receipt total",
    line_discount_matches_delta: "Line discount equals the arithmetic difference",
    qty_price_product_matches_delta: "Quantity × price matches the arithmetic difference",
    line_total_matches_delta_and_restores_equations:
      "Line total matches the difference and its removal restores a failed equation",
  };
  return c.reason_codes.map((code) => reasons[code] ?? code).join("; ");
}

function evidenceBandLabel(band: "strong" | "possible" | "ambiguous"): string {
  if (band === "strong") return "Strong evidence";
  if (band === "possible") return "Possible match";
  return "Ambiguous — multiple equal explanations";
}

export function ValidationGuidance({
  guidance,
  currency,
  revision,
  lineItems,
  onApplyCandidate,
  onConfirmAsShown,
  onEditManually,
}: ValidationGuidanceProps) {
  const {
    signed_delta_minor,
    receipt_total_minor,
    computed_total_minor,
    review_candidates,
  } = guidance;

  const absStr = formatMinorUnits(Math.abs(signed_delta_minor), currency);
  const signedDeltaStr =
    signed_delta_minor > 0 ? `+${absStr}` : signed_delta_minor < 0 ? `-${absStr}` : absStr;

  const topCandidate = review_candidates.length > 0 ? review_candidates[0] : null;
  const secondaryCandidates = review_candidates.slice(1);
  const isAmbiguous = topCandidate?.evidence_band === "ambiguous";

  return (
    <section aria-label="Validation guidance" className="validation-guidance">
      <div className="validation-guidance__delta">
        Difference: <strong>{signedDeltaStr}</strong>
      </div>
      <div className="validation-guidance__equation">
        Receipt total: {formatMinorUnits(receipt_total_minor, currency)} ·{" "}
        Calculated: {formatMinorUnits(computed_total_minor, currency)} ·{" "}
        {formattedComponentEquation(revision, guidance, currency)}
      </div>

      {topCandidate && (
        <div className="validation-guidance__proposal">
          {isAmbiguous && (
            <p className="validation-guidance__ambiguity-note">
              Multiple equal explanations found — review each and choose, or edit manually
            </p>
          )}
          <span className={`guidance-band guidance-band--${topCandidate.evidence_band}`}>
            {evidenceBandLabel(topCandidate.evidence_band)}
          </span>
          <p className="validation-guidance__candidate-desc">
            {describeCandidate(topCandidate, currency, lineItems)}
          </p>
          <p className="validation-guidance__candidate-reason">{candidateReason(topCandidate)}</p>
          <div className="validation-guidance__actions">
            <button
              type="button"
              onClick={() => onApplyCandidate(topCandidate)}
              className="btn btn--primary"
              aria-label="Apply and preview this proposal"
            >
              Apply and preview
            </button>
            <button
              type="button"
              onClick={onConfirmAsShown}
              className="btn btn--ghost"
              aria-label="Confirm receipt as shown with exception"
            >
              Confirm as shown
            </button>
            <button
              type="button"
              onClick={onEditManually}
              className="btn btn--ghost btn--small"
              aria-label="Edit receipt manually"
            >
              Edit manually
            </button>
          </div>
        </div>
      )}

      {secondaryCandidates.length > 0 && (
        <ul className="validation-guidance__secondary-candidates">
          {secondaryCandidates.map((candidate, idx) => (
            <li key={idx} className="validation-guidance__secondary-candidate">
              <span className={`guidance-band guidance-band--${candidate.evidence_band}`}>
                {evidenceBandLabel(candidate.evidence_band)}
              </span>
              <span className="validation-guidance__candidate-desc">
                {describeCandidate(candidate, currency, lineItems)}
              </span>
              <span className="validation-guidance__candidate-reason">{candidateReason(candidate)}</span>
              <button
                type="button"
                onClick={() => onApplyCandidate(candidate)}
                className="btn btn--ghost btn--small"
                aria-label={`Apply and preview: ${describeCandidate(candidate, currency, lineItems)}`}
              >
                Apply
              </button>
            </li>
          ))}
        </ul>
      )}

      {review_candidates.length === 0 && (
        <div className="validation-guidance__no-proposal">
          No specific proposal found. Use "Confirm as shown" to retain the exception, or "Edit
          manually" to correct.
          <div className="validation-guidance__actions">
            <button
              type="button"
              onClick={onConfirmAsShown}
              className="btn btn--ghost"
              aria-label="Confirm receipt as shown with exception"
            >
              Confirm as shown
            </button>
            <button
              type="button"
              onClick={onEditManually}
              className="btn btn--ghost btn--small"
              aria-label="Edit receipt manually"
            >
              Edit manually
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
