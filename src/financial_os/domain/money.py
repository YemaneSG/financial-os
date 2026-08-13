"""Money primitives and the canonical asset manifest hash algorithm.

Currency totals are always integer minor units (e.g. cents for USD).
Quantities and unit prices use Python Decimal for exact decimal arithmetic.
Never use float for any financial calculation.

Manifest hash algorithm is specified exactly in implementation-contracts.md §4.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any


def compute_asset_manifest_hash(verified_assets: list[dict[str, Any]]) -> str:
    """Compute a deterministic, order-sensitive hash over the verified asset set.

    Args:
        verified_assets: list of dicts with keys:
            - ordinal (int): 1-based position
            - object_key (str): opaque private object name
            - sha256 (str): hex-encoded SHA-256 of the asset content

    Returns:
        Hex-encoded SHA-256 of the canonical JSON serialisation.
    """
    entries = sorted(verified_assets, key=lambda a: a["ordinal"])
    manifest_input = json.dumps(
        [
            {
                "ordinal": int(entry["ordinal"]),
                "object_key": str(entry["object_key"]),
                "sha256": str(entry["sha256"]),
            }
            for entry in entries
        ],
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(manifest_input.encode("utf-8")).hexdigest()


def validate_minor_units(value: object, field_name: str = "amount") -> int | None:
    """Validate that a value is a non-negative integer minor-unit amount or None.

    Raises:
        ValueError: if value is non-None and not a valid non-negative integer.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer, not bool")
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer minor-unit amount, got {type(value)}")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative, got {value}")
    return value


def parse_decimal_string(value: str | None, field_name: str = "decimal") -> Decimal | None:
    """Parse a decimal string safely, returning None for None input.

    Raises:
        ValueError: if the string cannot be parsed as a valid decimal.
    """
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is not a valid decimal string: {value!r}") from exc


def check_totals_arithmetic(
    subtotal_minor: int | None,
    tax_minor: int | None,
    tip_minor: int | None,
    discount_minor: int | None,
    total_minor: int | None,
    tolerance_minor: int = 1,
) -> tuple[bool, int | None, int | None]:
    """Check whether subtotal + tax + tip - discount ≈ total.

    Returns:
        (passes, computed_total, delta)
        passes is True when the check is not applicable or the difference is within tolerance.
        computed_total is the computed value when all inputs are available.
        delta is total_minor - computed_total when both are available.
    """
    components = [subtotal_minor, tax_minor, tip_minor, discount_minor, total_minor]
    evidenced = [v for v in components if v is not None]

    if len(evidenced) < 2 or total_minor is None:
        return True, None, None

    computed = (subtotal_minor or 0) + (tax_minor or 0) + (tip_minor or 0) - (discount_minor or 0)
    delta = total_minor - computed
    passes = abs(delta) <= tolerance_minor
    return passes, computed, delta
