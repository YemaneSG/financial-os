import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ValidationGuidance } from "@/receipts/ValidationGuidance";
import type { ReviewGuidance, ReviewCandidate } from "@/api/types";

// Synthetic fixture — no real receipt content (APP-01, OBJ-02)
const syntheticCandidate: ReviewCandidate = {
  kind: "clear_receipt_discount",
  evidence_band: "strong",
  target_field: "discount_minor",
  target_item_ordinal: null,
  amount_minor: 200,
  reason_codes: ["receipt_discount_matches_delta"],
  equations_before: ["total(1080) - computed(1280) = delta(-200)"],
  equations_after: ["total(1080) - computed(1080) = delta(0)"],
  draft_patch: [{ op: "clear_receipt_discount" }],
};

const syntheticGuidance: ReviewGuidance = {
  signed_delta_minor: -200, // receipt total 200 cents below computed
  receipt_total_minor: 1080,
  computed_total_minor: 1280,
  component_equation: "subtotal(1200) + tax(80) = 1280",
  gross_line_sum_minor: 1200,
  net_line_sum_minor: 1200,
  review_candidates: [syntheticCandidate],
};

function renderGuidance(
  guidanceOverrides: Partial<ReviewGuidance> = {},
  callbacks: {
    onApplyCandidate?: (c: ReviewCandidate) => void;
    onConfirmAsShown?: () => void;
    onEditManually?: () => void;
  } = {},
) {
  const guidance: ReviewGuidance = { ...syntheticGuidance, ...guidanceOverrides };
  return render(
    <ValidationGuidance
      guidance={guidance}
      currency="USD"
      revision={{
        currency: "USD",
        subtotal_minor: 1200,
        tax_minor: 80,
        total_minor: 1080,
      }}
      lineItems={[
        {
          ordinal: 7,
          raw_description: "SYNTHETIC ITEM",
          normalized_description: "Synthetic item",
          line_total_minor: 200,
        },
      ]}
      onApplyCandidate={callbacks.onApplyCandidate ?? vi.fn()}
      onConfirmAsShown={callbacks.onConfirmAsShown ?? vi.fn()}
      onEditManually={callbacks.onEditManually ?? vi.fn()}
    />,
  );
}

describe("ValidationGuidance", () => {
  it("renders_signed_delta", () => {
    renderGuidance();
    expect(screen.getByText(/Difference:/i)).toBeInTheDocument();
    // The delta is -200 minor units; absolute value $2.00 with "-" prefix
    const deltaEl = screen.getByText(/Difference:/i).closest("div");
    expect(deltaEl).toBeInTheDocument();
    if (!deltaEl) throw new Error("Difference container was not rendered");
    expect(deltaEl.textContent).toContain("Difference:");
    // Verify the strong element contains a formatted amount with leading "-"
    const strong = deltaEl.querySelector("strong");
    expect(strong).not.toBeNull();
    if (!strong) throw new Error("Signed difference was not rendered");
    expect(strong.textContent).toMatch(/^-/);
  });

  it("renders_top_candidate_with_strong_band", () => {
    renderGuidance();
    expect(screen.getByText("Strong evidence")).toBeInTheDocument();
  });

  it("renders_the_component_equation_in_currency", () => {
    renderGuidance();
    expect(
      screen.getByText(/Subtotal \$12\.00 \+ Tax \$0\.80 = \$12\.80/),
    ).toBeInTheDocument();
  });

  it("renders_confirm_as_shown_button", () => {
    renderGuidance();
    expect(
      screen.getByRole("button", { name: /confirm receipt as shown with exception/i }),
    ).toBeInTheDocument();
  });

  it("calls_onApplyCandidate_when_apply_clicked", () => {
    const onApplyCandidate = vi.fn();
    renderGuidance({}, { onApplyCandidate });
    fireEvent.click(screen.getByRole("button", { name: /apply and preview this proposal/i }));
    expect(onApplyCandidate).toHaveBeenCalledOnce();
    expect(onApplyCandidate).toHaveBeenCalledWith(syntheticCandidate);
  });

  it("calls_onConfirmAsShown_when_confirm_clicked", () => {
    const onConfirmAsShown = vi.fn();
    renderGuidance({}, { onConfirmAsShown });
    fireEvent.click(
      screen.getByRole("button", { name: /confirm receipt as shown with exception/i }),
    );
    expect(onConfirmAsShown).toHaveBeenCalledOnce();
  });

  it("renders_no_proposal_message_when_empty_candidates", () => {
    renderGuidance({ review_candidates: [] });
    expect(screen.getByText(/no specific proposal found/i)).toBeInTheDocument();
    // Confirm as shown and Edit manually buttons still present in the fallback
    expect(
      screen.getByRole("button", { name: /confirm receipt as shown with exception/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /edit receipt manually/i })).toBeInTheDocument();
  });

  it("shows_possible_match_band_label", () => {
    const possibleCandidate: ReviewCandidate = {
      ...syntheticCandidate,
      evidence_band: "possible",
    };
    renderGuidance({ review_candidates: [possibleCandidate] });
    expect(screen.getByText("Possible match")).toBeInTheDocument();
  });

  it("shows_ambiguous_band_label_with_explanation", () => {
    const ambiguousCandidate: ReviewCandidate = {
      ...syntheticCandidate,
      evidence_band: "ambiguous",
    };
    renderGuidance({ review_candidates: [ambiguousCandidate] });
    expect(screen.getByText(/ambiguous — multiple equal explanations/i)).toBeInTheDocument();
  });

  it("shows_ambiguity_note_when_top_candidate_is_ambiguous", () => {
    const ambiguousCandidate: ReviewCandidate = {
      ...syntheticCandidate,
      evidence_band: "ambiguous",
    };
    renderGuidance({ review_candidates: [ambiguousCandidate] });
    expect(screen.getByText(/multiple equal explanations found/i)).toBeInTheDocument();
  });

  it("shows_candidate_formatted_amount_in_description", () => {
    renderGuidance();
    // The candidate description should include the formatted amount (200 cents = $2.00)
    const candidateDesc = screen.getByText(/clear duplicate discount/i);
    expect(candidateDesc).toBeInTheDocument();
    expect(candidateDesc.textContent).toMatch(/\$2\.00|\$2,00|2\.00/);
  });

  it("shows_candidate_reason_text", () => {
    renderGuidance();
    // The reason for receipt_discount_matches_delta should be human-readable
    expect(
      screen.getByText(/receipt discount equals the arithmetic difference/i),
    ).toBeInTheDocument();
  });

  it("identifies_the_target_item_by_ordinal_description_and_amount", () => {
    const lineCandidate: ReviewCandidate = {
      ...syntheticCandidate,
      kind: "remove_line_item",
      target_field: null,
      target_item_ordinal: 7,
      amount_minor: 200,
      reason_codes: ["line_total_matches_delta_and_restores_equations"],
      draft_patch: [{ op: "remove_line_item", ordinal: 7 }],
    };
    renderGuidance({ review_candidates: [lineCandidate] });
    expect(
      screen.getByText(/line item 7, “Synthetic item” \(\$2\.00\)/i),
    ).toBeInTheDocument();
  });

  it("does_not_show_probability_percentage", () => {
    renderGuidance();
    // No "%" characters anywhere in the rendered output
    const container = document.querySelector("section.validation-guidance");
    expect(container).not.toBeNull();
    if (!container) throw new Error("Guidance container was not rendered");
    expect(container.textContent).not.toContain("%");
  });
});
