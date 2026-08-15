"""Unit tests for CreateHumanRevisionRequest and LineItemInputSchema Pydantic validation.

These are pure schema validation tests — no database, no service layer, no fixtures.
All data is synthetic.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from financial_os.schemas.receipt import CreateHumanRevisionRequest, LineItemInputSchema


@pytest.mark.unit
class TestLineItemInputSchemaValidation:
    """LineItemInputSchema field-level validation."""

    def test_valid_decimal_strings_pass(self):
        item = LineItemInputSchema(
            description="Widget",
            quantity="2",
            unit_price_decimal="9.99",
            line_total_minor=1998,
        )
        assert item.quantity == "2"
        assert item.unit_price_decimal == "9.99"

    def test_non_numeric_quantity_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            LineItemInputSchema(description="Widget", quantity="not-a-number")
        errors = exc_info.value.errors()
        assert any("quantity" in (e.get("loc", ("",))[0] if e.get("loc") else "") for e in errors)

    def test_non_numeric_unit_price_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            LineItemInputSchema(description="Widget", unit_price_decimal="cheap")
        errors = exc_info.value.errors()
        assert any(
            "unit_price_decimal" in (e.get("loc", ("",))[0] if e.get("loc") else "") for e in errors
        )

    def test_null_quantity_is_allowed(self):
        item = LineItemInputSchema(description="Widget", quantity=None)
        assert item.quantity is None

    def test_null_unit_price_is_allowed(self):
        item = LineItemInputSchema(description="Widget", unit_price_decimal=None)
        assert item.unit_price_decimal is None

    def test_empty_description_raises(self):
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="")

    def test_whitespace_only_description_raises(self):
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="   ")

    def test_description_max_length_enforced(self):
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="x" * 501)

    def test_description_at_max_length_passes(self):
        item = LineItemInputSchema(description="x" * 500)
        assert len(item.description) == 500

    def test_negative_line_total_minor_raises(self):
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", line_total_minor=-1)

    def test_zero_line_total_minor_is_allowed(self):
        item = LineItemInputSchema(description="Widget", line_total_minor=0)
        assert item.line_total_minor == 0

    def test_negative_discount_minor_raises(self):
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", discount_minor=-5)

    def test_zero_discount_minor_is_allowed(self):
        item = LineItemInputSchema(description="Widget", discount_minor=0)
        assert item.discount_minor == 0

    def test_integer_decimal_string_passes(self):
        item = LineItemInputSchema(description="Widget", quantity="1")
        assert item.quantity == "1"

    def test_negative_quantity_raises(self):
        """Negative quantities are rejected at the schema layer (Sprint 2A fix)."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", quantity="-1")

    def test_negative_unit_price_raises(self):
        """Negative unit prices are rejected at the schema layer."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", unit_price_decimal="-0.50")

    def test_nan_quantity_raises(self):
        """NaN is not a valid decimal value."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", quantity="nan")

    def test_infinity_quantity_raises(self):
        """Infinity is not a valid decimal value."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", quantity="Infinity")

    def test_negative_infinity_quantity_raises(self):
        """-Infinity is not a valid decimal value."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", quantity="-Infinity")

    def test_nan_unit_price_raises(self):
        """NaN is not a valid unit price."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", unit_price_decimal="NaN")

    def test_quantity_excessive_scale_raises(self):
        """More than 6 decimal places exceeds NUMERIC(18,6) scale."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", quantity="1.1234567")  # 7 dp

    def test_quantity_at_max_scale_passes(self):
        """Exactly 6 decimal places is within NUMERIC(18,6) bounds."""
        item = LineItemInputSchema(description="Widget", quantity="1.123456")
        assert item.quantity == "1.123456"

    def test_unit_price_excessive_scale_raises(self):
        """More than 6 decimal places exceeds NUMERIC(18,6) scale for unit_price_decimal."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(description="Widget", unit_price_decimal="0.1234567")  # 7 dp

    def test_line_total_exceeds_bigint_raises(self):
        """line_total_minor values outside signed BIGINT must be rejected."""
        with pytest.raises(ValidationError):
            LineItemInputSchema(
                description="Widget",
                line_total_minor=9_223_372_036_854_775_808,  # BIGINT_MAX + 1
            )

    def test_line_total_at_bigint_max_passes(self):
        """BIGINT_MAX is the largest valid line_total_minor."""
        item = LineItemInputSchema(
            description="Widget",
            line_total_minor=9_223_372_036_854_775_807,
        )
        assert item.line_total_minor == 9_223_372_036_854_775_807


@pytest.mark.unit
class TestCreateHumanRevisionRequestValidation:
    """CreateHumanRevisionRequest field-level Pydantic validation."""

    def _valid_base(self, **overrides) -> dict:
        base: dict = {
            "expected_parent_revision_id": "00000000-0000-0000-0000-000000000001",
            "currency": "USD",
            "total_minor": 500,
        }
        base.update(overrides)
        return base

    def test_valid_minimal_request_passes(self):
        req = CreateHumanRevisionRequest(**self._valid_base())
        assert req.currency == "USD"
        assert req.total_minor == 500
        assert req.line_items == []

    def test_lowercase_currency_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CreateHumanRevisionRequest(**self._valid_base(currency="usd"))
        errors = exc_info.value.errors()
        assert any("currency" in str(e) for e in errors)

    def test_mixed_case_currency_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CreateHumanRevisionRequest(**self._valid_base(currency="Usd"))
        errors = exc_info.value.errors()
        assert any("currency" in str(e) for e in errors)

    def test_two_letter_currency_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(currency="US"))

    def test_four_letter_currency_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(currency="USDD"))

    def test_valid_three_letter_uppercase_currency_passes(self):
        req = CreateHumanRevisionRequest(**self._valid_base(currency="GBP"))
        assert req.currency == "GBP"

    def test_negative_total_minor_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(total_minor=-1))

    def test_zero_total_minor_is_allowed(self):
        req = CreateHumanRevisionRequest(**self._valid_base(total_minor=0))
        assert req.total_minor == 0

    def test_negative_subtotal_minor_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(subtotal_minor=-1))

    def test_negative_tax_minor_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(tax_minor=-1))

    def test_negative_tip_minor_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(tip_minor=-1))

    def test_negative_discount_minor_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(discount_minor=-1))

    def test_too_many_line_items_raises(self):
        items = [{"description": f"Item {i}"} for i in range(201)]
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(line_items=items))

    def test_exactly_200_line_items_passes(self):
        items = [{"description": f"Item {i}"} for i in range(200)]
        req = CreateHumanRevisionRequest(**self._valid_base(line_items=items))
        assert len(req.line_items) == 200

    def test_line_item_with_invalid_decimal_quantity_raises(self):
        items = [{"description": "Widget", "quantity": "not-a-decimal"}]
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(line_items=items))

    def test_line_item_with_empty_description_raises(self):
        items = [{"description": ""}]
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(line_items=items))

    def test_merchant_normalized_max_length_enforced(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(merchant_normalized="x" * 501))

    def test_merchant_normalized_at_max_length_passes(self):
        req = CreateHumanRevisionRequest(**self._valid_base(merchant_normalized="x" * 500))
        assert len(req.merchant_normalized) == 500

    def test_missing_currency_raises(self):
        payload = {
            "expected_parent_revision_id": "00000000-0000-0000-0000-000000000001",
            "total_minor": 500,
        }
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**payload)

    def test_missing_total_minor_raises(self):
        payload = {
            "expected_parent_revision_id": "00000000-0000-0000-0000-000000000001",
            "currency": "USD",
        }
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**payload)

    def test_missing_expected_parent_revision_id_raises(self):
        payload = {
            "currency": "USD",
            "total_minor": 500,
        }
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**payload)

    def test_invalid_uuid_for_parent_revision_id_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(expected_parent_revision_id="not-a-uuid"))

    def test_valid_line_items_list_is_accepted(self):
        items = [
            {
                "description": "Coffee",
                "quantity": "2",
                "unit_price_decimal": "3.50",
                "line_total_minor": 700,
            }
        ]
        req = CreateHumanRevisionRequest(**self._valid_base(line_items=items))
        assert len(req.line_items) == 1
        assert req.line_items[0].description == "Coffee"

    def test_total_minor_exceeds_bigint_raises(self):
        """Integer amounts outside signed BIGINT must be rejected before DB work."""
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(total_minor=9_223_372_036_854_775_808))

    def test_total_minor_at_bigint_max_passes(self):
        """BIGINT_MAX (2^63 - 1) is the largest valid total_minor."""
        req = CreateHumanRevisionRequest(**self._valid_base(total_minor=9_223_372_036_854_775_807))
        assert req.total_minor == 9_223_372_036_854_775_807

    def test_subtotal_minor_exceeds_bigint_raises(self):
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(subtotal_minor=9_223_372_036_854_775_808))

    def test_line_item_negative_quantity_in_request_raises(self):
        """Negative quantity inside a CreateHumanRevisionRequest must be rejected."""
        items = [{"description": "Widget", "quantity": "-2"}]
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(line_items=items))

    def test_line_item_nan_quantity_in_request_raises(self):
        """NaN quantity inside a CreateHumanRevisionRequest must be rejected."""
        items = [{"description": "Widget", "quantity": "nan"}]
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(line_items=items))

    def test_numeric_integer_digits_exceed_column_range_raises(self):
        items = [{"description": "Widget", "quantity": "1000000000000"}]
        with pytest.raises(ValidationError):
            CreateHumanRevisionRequest(**self._valid_base(line_items=items))

    def test_numeric_max_value_passes(self):
        items = [
            {
                "description": "Widget",
                "quantity": "999999999999.999999",
            }
        ]
        req = CreateHumanRevisionRequest(**self._valid_base(line_items=items))
        assert req.line_items[0].quantity == "999999999999.999999"
