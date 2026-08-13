"""Deterministic validation checks for extraction output.

These checks run AFTER JSON Schema validation. They produce ValidationFinding
records stored with the revision. They never modify the evidence or invent values.

Check codes are versioned identifiers for reproducibility (VAL-001, AI-03).
No receipt content appears in observed/expected fields — only numeric values.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import jsonschema

from financial_os.domain.states import ValidationOutcome

logger = logging.getLogger(__name__)

_SCHEMA_FILENAME = "extraction-result.schema.json"
_schema_cache: dict[str, Any] | None = None


def _schema_path() -> Path:
    """Resolve the frozen extraction contract in source and runtime layouts."""
    configured_dir = os.environ.get("FINANCIAL_OS_CONTRACTS_DIR")
    candidates = [
        Path(configured_dir) / _SCHEMA_FILENAME if configured_dir else None,
        Path.cwd() / "contracts" / _SCHEMA_FILENAME,
        Path(__file__).resolve().parents[3] / "contracts" / _SCHEMA_FILENAME,
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    raise FileNotFoundError("Extraction schema is not available in the runtime image")


def load_extraction_schema() -> dict[str, Any]:
    """Load the canonical extraction contract shared by generation and validation."""
    global _schema_cache
    if _schema_cache is None:
        with _schema_path().open() as f:
            _schema_cache = json.load(f)
    return _schema_cache


@dataclass
class ValidationFindingData:
    """Data for inserting one ValidationFinding row."""

    check_code: str
    outcome: str
    observed: dict[str, Any]
    expected: dict[str, Any] | None
    rule_version: str


def validate_extraction_schema(raw: dict[str, Any]) -> None:
    """Validate raw extraction output against the versioned JSON Schema.

    Raises jsonschema.ValidationError on any violation (VAL-001, AI-03).
    """
    schema = load_extraction_schema()
    jsonschema.validate(instance=raw, schema=schema)


def run_deterministic_checks(
    raw: dict[str, Any],
    tolerance_minor: int = 1,
) -> list[ValidationFindingData]:
    """Run all deterministic arithmetic checks against extraction output.

    Returns one ValidationFindingData per check; checks that are not applicable
    (e.g. missing inputs) return outcome=not_applicable.

    No receipt content (text, merchant name, etc.) appears in observed or expected.
    """
    findings: list[ValidationFindingData] = []
    findings.append(_check_totals_arithmetic(raw, tolerance_minor))
    findings.extend(_check_line_item_arithmetic(raw))
    findings.append(_check_schema_version(raw))
    return findings


def _check_totals_arithmetic(
    raw: dict[str, Any],
    tolerance_minor: int,
) -> ValidationFindingData:
    """TOTALS_ARITHMETIC_V1: subtotal + tax + tip - discount ≈ total."""
    sub = raw.get("subtotal_minor")
    tax = raw.get("tax_minor")
    tip = raw.get("tip_minor")
    dis = raw.get("discount_minor")
    tot = raw.get("total_minor")

    evidenced = [v for v in [sub, tax, tip, dis, tot] if v is not None]
    if len(evidenced) < 2 or tot is None:
        return ValidationFindingData(
            check_code="TOTALS_ARITHMETIC_V1",
            outcome=ValidationOutcome.NOT_APPLICABLE,
            observed={"available_fields": len(evidenced)},
            expected=None,
            rule_version="1",
        )

    computed = (sub or 0) + (tax or 0) + (tip or 0) - (dis or 0)
    delta = tot - computed
    passes = abs(delta) <= tolerance_minor

    return ValidationFindingData(
        check_code="TOTALS_ARITHMETIC_V1",
        outcome=ValidationOutcome.PASS if passes else ValidationOutcome.FAIL,
        observed={"total_minor": tot, "computed_minor": computed, "delta_minor": delta},
        expected={"tolerance_minor": tolerance_minor},
        rule_version="1",
    )


def _check_line_item_arithmetic(
    raw: dict[str, Any],
) -> list[ValidationFindingData]:
    """LINE_ITEM_ARITHMETIC_V1: quantity * unit_price_decimal ≈ line_total_minor."""
    findings = []
    line_items = raw.get("line_items") or []

    for item in line_items:
        ordinal = item.get("ordinal", 0)
        qty_str = item.get("quantity")
        price_str = item.get("unit_price_decimal")
        line_total = item.get("line_total_minor")

        if qty_str is None or price_str is None or line_total is None:
            findings.append(
                ValidationFindingData(
                    check_code="LINE_ITEM_ARITHMETIC_V1",
                    outcome=ValidationOutcome.NOT_APPLICABLE,
                    observed={"ordinal": ordinal},
                    expected=None,
                    rule_version="1",
                )
            )
            continue

        try:
            qty = Decimal(qty_str)
            price = Decimal(price_str)
        except Exception:
            findings.append(
                ValidationFindingData(
                    check_code="LINE_ITEM_ARITHMETIC_V1",
                    outcome=ValidationOutcome.WARN,
                    observed={"ordinal": ordinal},
                    expected=None,
                    rule_version="1",
                )
            )
            continue

        # Compute line total in minor units from decimal price.
        # Example: qty=2, price=3.99 USD → computed=798 cents.
        computed_minor = int((qty * price * 100).to_integral_value())
        delta = line_total - computed_minor
        passes = abs(delta) <= 2  # allow 2-cent rounding tolerance per line item

        findings.append(
            ValidationFindingData(
                check_code="LINE_ITEM_ARITHMETIC_V1",
                outcome=ValidationOutcome.PASS if passes else ValidationOutcome.FAIL,
                observed={
                    "ordinal": ordinal,
                    "line_total_minor": line_total,
                    "computed_minor": computed_minor,
                    "delta_minor": delta,
                },
                expected={"tolerance_minor": 2},
                rule_version="1",
            )
        )

    return findings


def _check_schema_version(raw: dict[str, Any]) -> ValidationFindingData:
    """SCHEMA_VERSION_V1: schema_version field must be 'v1'."""
    version = raw.get("schema_version")
    passes = version == "v1"
    return ValidationFindingData(
        check_code="SCHEMA_VERSION_V1",
        outcome=ValidationOutcome.PASS if passes else ValidationOutcome.FAIL,
        observed={"schema_version_present": version is not None},
        expected={"required_value": "v1"},
        rule_version="1",
    )


def determine_verification_status(findings: list[ValidationFindingData]) -> str:
    """Determine verification status from validation findings.

    - Any FAIL → needs_review
    - All PASS or NOT_APPLICABLE → system_validated
    """
    from financial_os.domain.states import VerificationStatus

    for f in findings:
        if f.outcome == ValidationOutcome.FAIL:
            return VerificationStatus.NEEDS_REVIEW
    return VerificationStatus.SYSTEM_VALIDATED
