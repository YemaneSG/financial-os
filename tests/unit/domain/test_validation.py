"""Unit tests for deterministic validation checks (VAL-001, AI-03)."""

import pytest

from financial_os.domain.states import ValidationOutcome
from financial_os.services.validation import (
    ValidationFindingData,
    determine_verification_status,
    run_deterministic_checks,
    validate_extraction_schema,
)
from tests.fixtures.factories import make_synthetic_extraction_result


@pytest.mark.unit
class TestSchemaValidation:
    def test_valid_result_passes(self):
        raw = make_synthetic_extraction_result()
        validate_extraction_schema(raw)  # should not raise

    def test_missing_required_currency_fails(self):
        import jsonschema

        raw = make_synthetic_extraction_result()
        del raw["currency"]
        with pytest.raises(jsonschema.ValidationError):
            validate_extraction_schema(raw)

    def test_wrong_schema_version_fails(self):
        import jsonschema

        raw = make_synthetic_extraction_result(schema_version="v2")
        with pytest.raises(jsonschema.ValidationError):
            validate_extraction_schema(raw)

    def test_float_total_fails(self):
        import jsonschema

        raw = make_synthetic_extraction_result()
        raw["total_minor"] = 10.99  # float not allowed — must be integer
        with pytest.raises(jsonschema.ValidationError):
            validate_extraction_schema(raw)

    def test_negative_total_fails(self):
        import jsonschema

        raw = make_synthetic_extraction_result()
        raw["total_minor"] = -1
        with pytest.raises(jsonschema.ValidationError):
            validate_extraction_schema(raw)


@pytest.mark.unit
class TestDeterministicArithmetic:
    def test_correct_totals_pass(self):
        raw = make_synthetic_extraction_result(subtotal_minor=1000, tax_minor=80, total_minor=1080)
        findings = run_deterministic_checks(raw)
        totals_check = next(f for f in findings if f.check_code == "TOTALS_ARITHMETIC_V1")
        assert totals_check.outcome == ValidationOutcome.PASS

    def test_incorrect_totals_fail(self):
        raw = make_synthetic_extraction_result(
            subtotal_minor=1000,
            tax_minor=80,
            total_minor=999,  # wrong
        )
        findings = run_deterministic_checks(raw)
        totals_check = next(f for f in findings if f.check_code == "TOTALS_ARITHMETIC_V1")
        assert totals_check.outcome == ValidationOutcome.FAIL

    def test_one_cent_tolerance_passes(self):
        raw = make_synthetic_extraction_result(
            subtotal_minor=1000,
            tax_minor=80,
            total_minor=1081,  # 1 cent rounding
        )
        findings = run_deterministic_checks(raw)
        totals_check = next(f for f in findings if f.check_code == "TOTALS_ARITHMETIC_V1")
        assert totals_check.outcome == ValidationOutcome.PASS

    def test_totals_not_applicable_when_insufficient_evidence(self):
        raw = make_synthetic_extraction_result()
        raw["total_minor"] = None  # no total evidenced
        findings = run_deterministic_checks(raw)
        totals_check = next(f for f in findings if f.check_code == "TOTALS_ARITHMETIC_V1")
        assert totals_check.outcome == ValidationOutcome.NOT_APPLICABLE

    def test_line_item_arithmetic_pass(self):
        raw = make_synthetic_extraction_result(subtotal_minor=1000)
        # Default factory: qty=1, price=10.00, total=1000 → 1*10.00*100 = 1000 ✓
        findings = run_deterministic_checks(raw)
        li_checks = [f for f in findings if f.check_code == "LINE_ITEM_ARITHMETIC_V1"]
        assert all(f.outcome == ValidationOutcome.PASS for f in li_checks)

    def test_line_item_arithmetic_fail(self):
        raw = make_synthetic_extraction_result(subtotal_minor=1000)
        # A two-cent per-line rounding tolerance is intentional. Use a clearly
        # inconsistent total so this test exercises the failure path.
        raw["line_items"][0]["line_total_minor"] = 900
        raw["line_items"][0]["quantity"] = "1"
        raw["line_items"][0]["unit_price_decimal"] = "10.00"
        findings = run_deterministic_checks(raw)
        li_checks = [f for f in findings if f.check_code == "LINE_ITEM_ARITHMETIC_V1"]
        assert any(f.outcome == ValidationOutcome.FAIL for f in li_checks)

    def test_schema_version_check_pass(self):
        raw = make_synthetic_extraction_result()
        findings = run_deterministic_checks(raw)
        version_check = next(f for f in findings if f.check_code == "SCHEMA_VERSION_V1")
        assert version_check.outcome == ValidationOutcome.PASS

    def test_no_receipt_content_in_observed(self):
        """Observed fields must contain only numeric values — never receipt text (LOG-01)."""
        raw = make_synthetic_extraction_result()
        findings = run_deterministic_checks(raw)
        for finding in findings:
            for value in finding.observed.values():
                assert not isinstance(value, str) or value.isdigit() or value in ("v1",)


@pytest.mark.unit
class TestVerificationStatusDetermination:
    def test_all_pass_gives_system_validated(self):
        findings = [
            ValidationFindingData(
                check_code="X",
                outcome=ValidationOutcome.PASS,
                observed={},
                expected=None,
                rule_version="1",
            ),
        ]
        assert determine_verification_status(findings) == "system_validated"

    def test_any_fail_gives_needs_review(self):
        findings = [
            ValidationFindingData(
                check_code="X",
                outcome=ValidationOutcome.PASS,
                observed={},
                expected=None,
                rule_version="1",
            ),
            ValidationFindingData(
                check_code="Y",
                outcome=ValidationOutcome.FAIL,
                observed={},
                expected=None,
                rule_version="1",
            ),
        ]
        assert determine_verification_status(findings) == "needs_review"

    def test_not_applicable_gives_system_validated(self):
        findings = [
            ValidationFindingData(
                check_code="X",
                outcome=ValidationOutcome.NOT_APPLICABLE,
                observed={},
                expected=None,
                rule_version="1",
            ),
        ]
        assert determine_verification_status(findings) == "system_validated"
