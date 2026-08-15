"""Unit tests for the deterministic receipt reconciliation engine (Sprint 2B).

All fixtures are entirely synthetic — no real receipt content, merchant names,
or financial data. Amounts and ordinals only.
"""

from __future__ import annotations

import pytest

from financial_os.services.reconciliation import compute_review_guidance
from tests.fixtures.factories import make_synthetic_extraction_result


def _make_findings(raw: dict) -> list:
    """Run validation and return duck-typed finding objects for reconciliation."""
    from financial_os.services.validation import run_deterministic_checks

    findings = run_deterministic_checks(raw)
    # Return duck-typed wrappers matching what get_receipt provides
    return [type("FD", (), {"check_code": f.check_code, "outcome": f.outcome})() for f in findings]


@pytest.mark.unit
class TestReconciliationEngine:
    def test_no_guidance_when_no_material_fail(self):
        """A correct receipt with passing arithmetic returns None."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        # line_total_minor == subtotal_minor by default → LINE_ITEMS_TO_SUBTOTAL passes
        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)
        assert result is None

    def test_clear_receipt_discount_strong(self):
        """Receipt discount exactly equals the arithmetic delta → strong candidate."""
        # subtotal=1000, tax=80, discount=50, total=1030
        # computed = 1000+80-50 = 1030 but we want delta of 50 by setting discount wrong
        # Scenario: subtotal=1000, tax=80, discount=50 (but already deducted from total)
        # total=1030, computed=1000+80-50=1030 → that passes. Instead:
        # total=1080, computed=1000+80-50=1030 → delta=50 == discount(50) → clear discount
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50  # duplicated — already reflected in total
        raw["line_items"][0]["line_total_minor"] = 1000

        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)

        assert result is not None
        assert result.signed_delta_minor == 50  # total(1080) - computed(1000+80-50=1030) = 50
        # There should be a clear_receipt_discount candidate
        kinds = [c.kind for c in result.review_candidates]
        assert "clear_receipt_discount" in kinds
        # The clear_discount candidate should be strong (sole restoring candidate)
        clear_cand = next(c for c in result.review_candidates if c.kind == "clear_receipt_discount")
        assert clear_cand.evidence_band == "strong"

    def test_gross_line_sum_as_subtotal(self):
        """Wrong subtotal corrected by gross line sum → candidate generated."""
        # Lines sum to 1050, subtotal recorded as 1000, total = 1050+80 = 1130
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1130)
        raw["line_items"][0]["line_total_minor"] = 1050

        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)

        assert result is not None
        kinds = [c.kind for c in result.review_candidates]
        assert "use_gross_line_sum_as_subtotal" in kinds

    def test_discount_inclusive_subtotal_is_system_valid_without_correction(self):
        """New validation preserves both evidenced values and recognizes their semantics."""
        raw = make_synthetic_extraction_result(
            subtotal_minor=21702,
            tax_minor=198,
            total_minor=21900,
        )
        raw["discount_minor"] = 600
        raw["line_items"][0]["line_total_minor"] = 22302

        assert compute_review_guidance(raw, _make_findings(raw)) is None

    def test_historical_failure_offers_strong_discount_interpretation(self):
        """A stored V1 failure gets a no-value-change V2 interpretation proposal."""
        from financial_os.domain.states import ValidationOutcome

        raw = make_synthetic_extraction_result(
            subtotal_minor=21702,
            tax_minor=198,
            total_minor=21900,
        )
        raw["discount_minor"] = 600
        raw["line_items"][0]["line_total_minor"] = 22302
        historical_findings = [
            type(
                "FD",
                (),
                {
                    "check_code": "TOTALS_ARITHMETIC_V1",
                    "outcome": ValidationOutcome.FAIL,
                },
            )()
        ]

        result = compute_review_guidance(raw, historical_findings)

        assert result is not None
        assert result.signed_delta_minor == 600
        assert result.review_candidates[0].kind == "confirm_discount_included_in_subtotal"
        assert result.review_candidates[0].evidence_band == "strong"
        assert "subtotal_already_includes_receipt_discount" in (
            result.review_candidates[0].reason_codes
        )
        assert result.review_candidates[0].draft_patch == []

    def test_discount_not_included_in_subtotal_requires_no_guidance(self):
        """A gross subtotal with a separately applied discount is already consistent."""
        raw = make_synthetic_extraction_result(
            subtotal_minor=22302,
            tax_minor=198,
            total_minor=21900,
        )
        raw["discount_minor"] = 600
        raw["line_items"][0]["line_total_minor"] = 22302

        assert compute_review_guidance(raw, _make_findings(raw)) is None

    def test_incomplete_line_coverage_cannot_make_discount_candidate_strong(self):
        """An exact amount match alone is possible evidence, not a strong recommendation."""
        raw = make_synthetic_extraction_result(
            subtotal_minor=1000,
            tax_minor=80,
            total_minor=1080,
        )
        raw["discount_minor"] = 50
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM WITH TOTAL",
                "line_total_minor": 500,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM WITHOUT TOTAL",
                "line_total_minor": None,
            },
        ]

        result = compute_review_guidance(raw, _make_findings(raw))

        assert result is not None
        clear_candidate = next(
            candidate
            for candidate in result.review_candidates
            if candidate.kind == "clear_receipt_discount"
        )
        assert clear_candidate.evidence_band == "possible"

    def test_clear_receipt_discount_is_strong_when_only_restoring_candidate(self):
        """When clear_receipt_discount is the unique fully-restoring candidate, it is 'strong'.

        The line discount in this scenario has equations_restored=0 (it doesn't fix TOTALS)
        so it does not tie with clear_receipt_discount.  clear_receipt_discount alone
        produces remaining_fails=0 and is correctly rated 'strong'.
        """
        # subtotal=1000, tax=80, discount=50, total=1080
        # computed = 1000+80-50=1030; delta=50
        # clear_receipt_discount: restores TOTALS → equations_restored=1, remaining_fails=0 → strong
        # clear_line_discount(50): TOTALS still fails → equations_restored=0 → possible
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        raw["discount_minor"] = 50
        raw["line_items"][0]["line_total_minor"] = 1000
        raw["line_items"][0]["discount_minor"] = 50  # matches delta but doesn't fix TOTALS

        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)

        assert result is not None
        strong_candidates = [c for c in result.review_candidates if c.evidence_band == "strong"]
        assert len(strong_candidates) == 1, (
            "clear_receipt_discount uniquely restores all equations → must be strong"
        )
        assert strong_candidates[0].kind == "clear_receipt_discount"

    def test_no_coincidental_delete(self):
        """Line item whose amount matches delta but whose removal doesn't restore equations
        is NOT returned as a remove_line_item candidate."""
        # Set up: single line with total=50. Delta = 50 (total wrong).
        # But removing the only line makes LINE_ITEMS_TO_SUBTOTAL not_applicable, not passing.
        # Also TOTALS_ARITHMETIC_V1 still fails after removal (subtotal stays wrong).
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1130)
        # total=1130, computed=1000+80=1080, delta=50
        # Only one line with total=50 — removing it doesn't restore TOTALS_ARITHMETIC
        raw["line_items"][0]["line_total_minor"] = 50

        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)

        assert result is not None
        kinds = [c.kind for c in result.review_candidates]
        # remove_line_item should not appear because it doesn't restore any equation
        assert "remove_line_item" not in kinds

    def test_at_most_three_candidates(self):
        """Even when many rules fire, no more than 3 candidates are returned."""
        # Craft a receipt where multiple rules match
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1130)
        raw["discount_minor"] = 50
        # Multiple lines whose individual totals might match deltas
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM 1",
                "quantity": "1",
                "unit_price_decimal": "10.00",
                "line_total_minor": 1050,
                "discount_minor": None,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM 2",
                "quantity": "1",
                "unit_price_decimal": "5.00",
                "line_total_minor": 500,
                "discount_minor": 50,
            },
        ]

        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)

        assert result is not None
        assert len(result.review_candidates) <= 3

    def test_signed_delta_correct(self):
        """signed_delta_minor == total - computed (can be negative)."""
        # total=1000, subtotal=900, tax=150, computed=1050, delta=-50
        raw = make_synthetic_extraction_result(subtotal_minor=900, tax_minor=150, total_minor=1000)
        raw["line_items"][0]["line_total_minor"] = 900

        findings = _make_findings(raw)
        result = compute_review_guidance(raw, findings)

        assert result is not None
        # computed = 900 + 150 = 1050; signed_delta = 1000 - 1050 = -50
        assert result.signed_delta_minor == -50
        assert result.receipt_total_minor == 1000
        assert result.computed_total_minor == 1050

    def test_partial_line_coverage_does_not_drive_sum_guidance(self):
        """A partial item sum is omitted instead of becoming a false proposal."""
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1100)
        raw["line_items"] = [
            {
                "ordinal": 1,
                "raw_description": "SYNTHETIC ITEM WITH TOTAL",
                "line_total_minor": 500,
            },
            {
                "ordinal": 2,
                "raw_description": "SYNTHETIC ITEM WITHOUT TOTAL",
                "line_total_minor": None,
            },
        ]

        result = compute_review_guidance(raw, _make_findings(raw))

        assert result is not None
        assert result.gross_line_sum_minor is None
        assert result.net_line_sum_minor is None
        assert all(
            candidate.kind not in {"use_gross_line_sum_as_subtotal", "use_net_line_sum_as_subtotal"}
            for candidate in result.review_candidates
        )
