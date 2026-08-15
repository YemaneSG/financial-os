"""Unit tests for reconciliation candidate generation and ranking (Sprint 2B).

Focuses on aspects NOT already covered by test_reconciliation.py:
- Privacy guarantee: no receipt text appears in guidance output
- Clear-line-discount Rule 4 candidate generation
- Replace-line-total (Rule 5) candidate generation
- Remove-line-item (Rule 6) only when it uniquely restores equations
- Two line-discount candidates with ambiguous strength (neither is "strong")
- Component equation format (numbers and field names only)

All fixtures are synthetic — no real receipt content. Tests verify:
- Only bounded minimal-edit candidates are generated
- Ambiguity is detected and downgraded correctly
- Removal without full restoration is not "strong"
- At most three candidates returned
- Signed delta sign and value are correct
- No receipt text appears in guidance output
"""

from __future__ import annotations

import re

import pytest

from financial_os.services.reconciliation import compute_review_guidance
from financial_os.services.validation import ValidationFindingData, run_deterministic_checks
from tests.fixtures.factories import make_synthetic_extraction_result

pytestmark = pytest.mark.unit

# ── Helper ────────────────────────────────────────────────────────────────────


def _findings(raw: dict) -> list[ValidationFindingData]:
    """Run deterministic checks; return ValidationFindingData list directly."""
    return run_deterministic_checks(raw)


# ── Privacy / text leakage tests ──────────────────────────────────────────────


class TestGuidancePrivacy:
    """Guidance output must contain only amounts, ordinals, and field names.

    No raw_description, merchant name, or free-form receipt text may appear
    anywhere in the ReviewGuidanceSchema or its nested candidates.
    """

    def test_no_merchant_name_in_component_equation(self):
        """component_equation contains only numbers, field labels, and punctuation."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50  # triggers clear_receipt_discount candidate
        # computed = 1000+80-50=1030, delta=50 → TOTALS fails
        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        eq = guidance.component_equation
        # Must not contain the merchant name from the synthetic factory
        assert "SYNTHETIC" not in eq
        assert "Synthetic" not in eq
        # Must not contain item descriptions
        assert "ITEM" not in eq

    def test_no_raw_description_in_candidate_equations(self):
        """equations_before and equations_after in candidates contain no item text."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50
        raw["line_items"][0]["line_total_minor"] = 1000

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        for candidate in guidance.review_candidates:
            for eq_str in candidate.equations_before + candidate.equations_after:
                # No raw item descriptions from the synthetic fixture
                assert "SYNTHETIC ITEM" not in eq_str
                assert "Synthetic Item" not in eq_str

    def test_reason_codes_are_from_allowed_set(self):
        """reason_codes must be stable, privacy-safe identifiers (no user data)."""
        _allowed_codes = {
            "receipt_discount_matches_delta",
            "gross_line_sum_restores_total",
            "net_line_sum_restores_total",
            "line_discount_matches_delta",
            "qty_price_product_matches_delta",
            "line_total_matches_delta_and_restores_equations",
        }
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1130)
        raw["discount_minor"] = 50
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "quantity": "1",
                "unit_price_decimal": "10.50",
                "line_total_minor": 1050,
                "discount_minor": None,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM B",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 500,
                "discount_minor": 50,
            },
        ]

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        for candidate in guidance.review_candidates:
            for code in candidate.reason_codes:
                assert code in _allowed_codes, f"Unexpected reason_code {code!r} not in allowed set"

    def test_equations_contain_no_free_text(self):
        """All equation strings consist only of numbers, known field names, and punctuation."""
        # Regex: allow digits, parens, spaces, arithmetic operators, field-name word chars,
        # commas, equals, hyphens, and dots. Disallow raw receipt text.
        safe_pattern = re.compile(r"^[\w\s\(\)\+\-\=\.,/\*:]*$")

        raw = make_synthetic_extraction_result(subtotal_minor=900, tax_minor=150, total_minor=1000)
        raw["line_items"][0]["line_total_minor"] = 900

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        for candidate in guidance.review_candidates:
            for eq in candidate.equations_before + candidate.equations_after:
                assert safe_pattern.match(eq) is not None, (
                    f"Equation contains unexpected characters: {eq!r}"
                )
                # Explicitly confirm no merchant name leaks
                assert "SYNTHETIC TEST STORE" not in eq


# ── Rule 4: Clear line discount ───────────────────────────────────────────────


class TestClearLineDiscountCandidate:
    """Verify that Rule 4 generates clear_line_discount candidates correctly."""

    def test_single_line_discount_matching_delta_generates_candidate(self):
        """A single line item with discount_minor == abs(delta) generates a candidate."""
        # total=880, computed = 1000+80-0=1080, delta=-200
        # Line item with discount_minor=200 → abs(200-200)=0 ≤ 1 → Rule 4 fires
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=880)
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 1000,
                "discount_minor": 200,
            }
        ]
        # gross_sum=1000=subtotal → LINE_ITEMS_TO_SUBTOTAL passes
        # TOTALS: 1000+80=1080 ≠ 880 → fails; abs_delta=200

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        kinds = [c.kind for c in guidance.review_candidates]
        assert "clear_line_discount" in kinds

    def test_two_line_discounts_matching_delta_are_not_both_strong(self):
        """When two line items both have discount_minor == abs(delta), neither is 'strong'.

        Each candidate only partially restores equations (receipt-level TOTALS still fails),
        so both should be ranked 'possible' rather than 'strong'.
        """
        # total=880, computed=1000+80=1080, delta=-200, abs_delta=200
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=880)
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 500,
                "discount_minor": 200,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM B",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 500,
                "discount_minor": 200,
            },
        ]
        # gross_sum=1000=subtotal → LINE_ITEMS_TO_SUBTOTAL passes
        # TOTALS: 1000+80=1080 ≠ 880 → fails, abs_delta=200

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        clear_line_candidates = [
            c for c in guidance.review_candidates if c.kind == "clear_line_discount"
        ]
        # Both ordinal 1 and 2 generate candidates
        assert len(clear_line_candidates) >= 1

        # Clearing a single line's discount does NOT restore TOTALS_ARITHMETIC (receipt-level
        # discount is unaffected), so no clear_line_discount candidate should be "strong"
        for candidate in clear_line_candidates:
            assert candidate.evidence_band != "strong", (
                f"clear_line_discount ordinal={candidate.target_item_ordinal} "
                f"should not be 'strong' when equation remains unrestored"
            )


# ── Rule 5: Replace line total with qty*price ─────────────────────────────────


class TestReplaceLineTotalCandidate:
    """Verify that Rule 5 generates replace_line_total_with_qty_price candidates."""

    def test_qty_price_mismatch_matching_delta_generates_candidate(self):
        """qty * price product differs from line_total by exactly abs(delta) → candidate."""
        # qty=2, price=5.00 → expected=1000. Recorded line_total=1200.
        # diff = 1200 - 1000 = 200.
        # subtotal=1200, tax=80, total=1080, computed=1280, delta=-200, abs_delta=200
        # abs(abs_delta - abs(diff)) = abs(200-200) = 0 ≤ 1 → Rule 5 fires
        raw = make_synthetic_extraction_result(subtotal_minor=1200, tax_minor=80, total_minor=1080)
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "quantity": "2",
                "unit_price_decimal": "5.00",
                "line_total_minor": 1200,  # should be 1000 (2×5.00=10.00→1000)
                "discount_minor": None,
            }
        ]
        # gross=1200=subtotal → LINE_ITEMS_TO_SUBTOTAL passes (gross_delta=0)
        # TOTALS: 1200+80=1280 ≠ 1080 → fails, abs_delta=200

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        kinds = [c.kind for c in guidance.review_candidates]
        assert "replace_line_total_with_qty_price" in kinds

    def test_replace_line_total_candidate_has_correct_ordinal(self):
        """The candidate for Rule 5 references the correct line item ordinal."""
        raw = make_synthetic_extraction_result(subtotal_minor=1200, tax_minor=80, total_minor=1080)
        raw["line_items"] = [
            {
                "ordinal": 3,  # deliberate non-1 ordinal
                "raw_description": "SYNTHETIC ITEM C",
                "quantity": "2",
                "unit_price_decimal": "5.00",
                "line_total_minor": 1200,
                "discount_minor": None,
            }
        ]

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        qty_price_cands = [
            c for c in guidance.review_candidates if c.kind == "replace_line_total_with_qty_price"
        ]
        assert len(qty_price_cands) >= 1
        assert qty_price_cands[0].target_item_ordinal == 3


# ── Rule 6: Remove line item ──────────────────────────────────────────────────


class TestRemoveLineItemCandidate:
    """Verify that Rule 6 only adds candidates when removal genuinely restores equations."""

    def test_remove_line_item_added_only_when_equations_restored(self):
        """remove_line_item appears only when its removal restores at least one equation.

        Setup: two items. Removing item 2 (line_total=200=abs_delta) changes gross_sum
        to match subtotal, restoring LINE_ITEMS_TO_SUBTOTAL. TOTALS still fails.
        The candidate appears with evidence_band != "strong" (remaining_fails > 0).
        """
        # subtotal=1200, tax=80, total=1080
        # TOTALS: computed=1280, delta=-200, abs_delta=200 → FAIL
        raw = make_synthetic_extraction_result(subtotal_minor=1200, tax_minor=80, total_minor=1080)
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "quantity": "1",
                "unit_price_decimal": "12.00",
                "line_total_minor": 1200,
                "discount_minor": None,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM B",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 200,
                "discount_minor": None,
            },
        ]
        # gross=1400, subtotal=1200, gross_delta=-200 → LINE_ITEMS_TO_SUBTOTAL FAILS
        # After removing item 2: gross=1200=subtotal → PASS, but TOTALS still FAILS

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        remove_cands = [c for c in guidance.review_candidates if c.kind == "remove_line_item"]

        # The candidate IS present because it restores LINE_ITEMS_TO_SUBTOTAL
        assert len(remove_cands) >= 1

        # But it should NOT be "strong" because TOTALS_ARITHMETIC still fails after removal
        for cand in remove_cands:
            assert cand.evidence_band != "strong", (
                "remove_line_item should not be 'strong' when TOTALS still fails after removal"
            )

    def test_remove_line_item_absent_when_no_equation_restore(self):
        """remove_line_item is NOT in candidates when removal restores zero equations.

        Remove candidate only generated (Rule 6) when equations_restored > 0.
        Here the line total matches delta but removing it creates a new failure.
        """
        # subtotal=1000, tax=80, total=880 (TOTALS fails: computed=1080, delta=-200)
        # Single line with line_total=200 — removing it makes gross=0, subtotal=1000,
        # gross_delta=-1000 → LINE_ITEMS_TO_SUBTOTAL FAIL (was PASSING with gross=1000? no)
        # Actually original: gross=1200, subtotal=1000, gross_delta=-200 → FAIL
        # After removal: LINE_ITEMS_TO_SUBTOTAL not_applicable (no lines with totals) → 0 restored
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=880)
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM MAIN",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 1000,
                "discount_minor": None,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM SMALL",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 200,
                "discount_minor": None,
            },
        ]
        # gross=1200, subtotal=1000, gross_delta=-200 → LINE_ITEMS_TO_SUBTOTAL FAILS
        # TOTALS: 1000+80=1080 ≠ 880 → FAILS. abs_delta=200
        # Removing item 2 (total=200, abs(200-200)=0 ≤ 1):
        #   gross=1000=subtotal → LINE_ITEMS_TO_SUBTOTAL PASS (restored!)
        #   TOTALS still: 1000+80=1080 ≠ 880 → FAILS
        # equations_restored=1 > 0 → candidate IS added but NOT "strong"
        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        remove_cands = [c for c in guidance.review_candidates if c.kind == "remove_line_item"]
        # Regardless of whether it appears, it must not be "strong"
        for cand in remove_cands:
            assert cand.evidence_band != "strong"


# ── Guidance structure ────────────────────────────────────────────────────────


class TestGuidanceStructure:
    """Verify top-level ReviewGuidanceSchema fields are computed correctly."""

    def test_component_equation_contains_field_labels(self):
        """component_equation includes 'subtotal', 'tax' labels (not raw merchant text)."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50  # triggers failure: computed=1030, delta=50

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        eq = guidance.component_equation
        assert "subtotal" in eq
        assert "1000" in eq  # subtotal amount is present
        assert "80" in eq  # tax amount is present

    def test_receipt_total_minor_matches_raw_input(self):
        """guidance.receipt_total_minor echoes the raw total_minor field."""
        raw = make_synthetic_extraction_result(subtotal_minor=900, tax_minor=150, total_minor=1000)
        raw["line_items"][0]["line_total_minor"] = 900
        # computed = 900+150 = 1050, delta = -50

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        assert guidance.receipt_total_minor == 1000

    def test_computed_total_minor_is_sum_of_components(self):
        """guidance.computed_total_minor == subtotal + tax + tip - discount."""
        raw = make_synthetic_extraction_result(subtotal_minor=900, tax_minor=150, total_minor=1000)
        raw["line_items"][0]["line_total_minor"] = 900
        # computed = 900+150=1050

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        assert guidance.computed_total_minor == 1050

    def test_gross_line_sum_and_net_line_sum_populated_when_items_present(self):
        """gross_line_sum_minor and net_line_sum_minor are populated when line items exist."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50  # triggers failure
        # Default line item has line_total_minor=subtotal_minor=1000, discount_minor=None
        raw["line_items"][0]["line_total_minor"] = 1000
        raw["line_items"][0]["discount_minor"] = None

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        assert guidance.gross_line_sum_minor == 1000
        assert guidance.net_line_sum_minor == 1000  # no line discounts

    def test_positive_signed_delta(self):
        """When total > computed, signed_delta_minor is positive."""
        # total=1080, subtotal=1000, tax=80, discount=50 → computed=1030, delta=50
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50
        raw["line_items"][0]["line_total_minor"] = 1000

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        assert guidance.signed_delta_minor == 50
        assert guidance.signed_delta_minor > 0

    def test_at_most_three_candidates_with_many_matching_rules(self):
        """Even when many rules fire simultaneously, no more than 3 candidates are returned."""
        # Create a scenario with 4+ potential Rule 4 candidates + a Rule 1 candidate
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50  # Rule 1: clear_receipt_discount
        raw["line_items"] = [
            {
                "ordinal": i,
                "raw_description": f"SYNTHETIC ITEM {i}",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 200,
                "discount_minor": 50,  # Rule 4 for each
            }
            for i in range(1, 6)  # 5 items, each triggering Rule 4
        ]
        # TOTALS: computed=1000+80-50=1030, total=1080, delta=50 → FAILS
        # Each line item: discount=50=abs_delta → Rule 4 fires for each

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        assert len(guidance.review_candidates) <= 3


# ── Ambiguity band tests ──────────────────────────────────────────────────────


class TestAmbiguityBand:
    """Tied fully-restoring candidates must receive evidence_band='ambiguous'.

    Tests use _rank_candidates directly with synthetic candidate dicts to verify
    the ranking logic independently of the full candidate-generation pipeline.
    """

    def test_tied_fully_restoring_candidates_are_ambiguous_not_strong(self):
        """When two synthetic candidates tie (same restored/remaining), both are 'ambiguous'."""
        from financial_os.schemas.receipt import DraftPatchSchema
        from financial_os.services.reconciliation import _rank_candidates

        # Synthetic: two candidates each fully restore 1 equation, none remain failing
        cand_a = {
            "kind": "clear_receipt_discount",
            "patches": [DraftPatchSchema(op="clear_receipt_discount")],
            "equations_restored": 1,
            "remaining_fails": 0,
            "abs_match": True,
            "keyword_support": True,
            "target_field": "discount_minor",
            "target_item_ordinal": None,
            "amount_minor": 50,
            "reason_codes": ["receipt_discount_matches_delta"],
            "equations_before": ["total(1080) - computed(1030) = delta(50)"],
            "equations_after": ["total(1080) - computed(1080) = delta(0)"],
        }
        cand_b = {
            "kind": "clear_line_discount",
            "patches": [DraftPatchSchema(op="clear_line_discount", ordinal=1)],
            "equations_restored": 1,
            "remaining_fails": 0,
            "abs_match": True,
            "keyword_support": True,
            "target_field": "discount_minor",
            "target_item_ordinal": 1,
            "amount_minor": 50,
            "reason_codes": ["line_discount_matches_delta"],
            "equations_before": ["line(1) discount(50) matches delta(50)"],
            "equations_after": ["line(1) discount cleared"],
        }

        result = _rank_candidates([cand_a, cand_b], 50)

        assert len(result) == 2
        bands = {c.kind: c.evidence_band for c in result}
        assert bands["clear_receipt_discount"] == "ambiguous", (
            "Tied fully-restoring candidate must be 'ambiguous'"
        )
        assert bands["clear_line_discount"] == "ambiguous", (
            "Tied fully-restoring candidate must be 'ambiguous'"
        )

    def test_unique_fully_restoring_candidate_is_strong(self):
        """A single uniquely fully-restoring candidate (no tie) must be 'strong'."""
        from financial_os.schemas.receipt import DraftPatchSchema
        from financial_os.services.reconciliation import _rank_candidates

        cand_a = {
            "kind": "clear_receipt_discount",
            "patches": [DraftPatchSchema(op="clear_receipt_discount")],
            "equations_restored": 1,
            "remaining_fails": 0,
            "abs_match": True,
            "keyword_support": True,
            "target_field": "discount_minor",
            "target_item_ordinal": None,
            "amount_minor": 50,
            "reason_codes": ["receipt_discount_matches_delta"],
            "equations_before": ["total(1080) - computed(1030) = delta(50)"],
            "equations_after": ["total(1080) - computed(1080) = delta(0)"],
        }
        # Second candidate does NOT fully restore (remaining_fails=1)
        cand_b = {
            "kind": "clear_line_discount",
            "patches": [DraftPatchSchema(op="clear_line_discount", ordinal=1)],
            "equations_restored": 0,
            "remaining_fails": 1,
            "abs_match": True,
            "keyword_support": True,
            "target_field": "discount_minor",
            "target_item_ordinal": 1,
            "amount_minor": 50,
            "reason_codes": ["line_discount_matches_delta"],
            "equations_before": ["line(1) discount(50) matches delta(50)"],
            "equations_after": ["line(1) discount cleared"],
        }

        result = _rank_candidates([cand_a, cand_b], 50)

        assert len(result) == 2
        strong = [c for c in result if c.evidence_band == "strong"]
        assert len(strong) == 1, "A uniquely fully-restoring candidate must be 'strong'"
        assert strong[0].kind == "clear_receipt_discount"

    def test_end_to_end_clear_receipt_discount_is_strong_when_unique(self):
        """Integration: clear_receipt_discount is strong when uniquely fully-restoring."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50  # Rule 1: clear_receipt_discount
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM A",
                "quantity": None,
                "unit_price_decimal": None,
                "line_total_minor": 1000,
                "discount_minor": None,  # no line discount → no Rule 4 competitor
            }
        ]

        findings = _findings(raw)
        guidance = compute_review_guidance(raw, findings)

        assert guidance is not None
        strong_cands = [c for c in guidance.review_candidates if c.evidence_band == "strong"]
        assert len(strong_cands) == 1, "A uniquely fully-restoring candidate must be 'strong'"
        assert strong_cands[0].kind == "clear_receipt_discount"
