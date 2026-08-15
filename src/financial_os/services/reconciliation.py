"""Deterministic receipt reconciliation engine for Sprint 2B.

Produces structured guidance for receipts with arithmetic exceptions.
All arithmetic uses exact integers (minor units). No LLM, no probability,
no open-ended subset-sum. At most three ranked candidates.
No receipt text appears in the output — amounts and ordinals only.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Literal, NotRequired, TypedDict, cast

from financial_os.domain.money import minor_unit_exponent
from financial_os.domain.states import ValidationOutcome
from financial_os.schemas.receipt import (
    DraftPatchSchema,
    ReviewCandidateSchema,
    ReviewGuidanceSchema,
)

_MATERIAL_CHECKS = {
    "TOTALS_ARITHMETIC_V1",
    "TOTALS_ARITHMETIC_V2",
    "LINE_ITEMS_TO_SUBTOTAL_V1",  # Stored historical findings.
    "LINE_ITEMS_TO_SUBTOTAL_V2",
}
_TOLERANCE = 1


class _CandidateData(TypedDict):
    kind: str
    patches: list[DraftPatchSchema]
    equations_restored: int
    remaining_fails: int
    abs_match: bool
    keyword_support: bool
    target_field: str | None
    target_item_ordinal: int | None
    amount_minor: int
    reason_codes: list[str]
    equations_before: list[str]
    equations_after: list[str]
    strong_eligible: NotRequired[bool]


def compute_review_guidance(
    raw: dict[str, Any],
    findings: list[Any],  # list of ValidationFindingData or duck-typed objects
) -> ReviewGuidanceSchema | None:
    """Compute review guidance if a material arithmetic failure exists.

    Returns None if no material failure or inputs are insufficient for guidance.
    raw: the extraction/correction dict with currency, subtotal_minor, tax_minor, etc.
    findings: ValidationFindingData list from run_deterministic_checks.
    """
    # Only produce guidance when a material check failed
    has_material_fail = any(
        f.check_code in _MATERIAL_CHECKS and f.outcome == ValidationOutcome.FAIL for f in findings
    )
    if not has_material_fail:
        return None

    total = raw.get("total_minor")
    if total is None:
        return None

    sub = raw.get("subtotal_minor")
    tax = raw.get("tax_minor")
    tip = raw.get("tip_minor")
    dis = raw.get("discount_minor")
    currency = str(raw.get("currency") or "USD")
    line_items = raw.get("line_items") or []

    computed = (sub or 0) + (tax or 0) + (tip or 0) - (dis or 0)
    signed_delta = total - computed

    # Build component equation string
    parts = []
    if sub is not None:
        parts.append(f"subtotal({sub})")
    if tax is not None:
        parts.append(f"tax({tax})")
    if tip is not None:
        parts.append(f"tip({tip})")
    if dis is not None:
        parts.append(f"- discount({dis})")
    eq = " + ".join(p for p in parts if not p.startswith("-"))
    neg = " ".join(p for p in parts if p.startswith("-"))
    component_equation = f"{eq} {neg} = {computed}" if neg else f"{eq} = {computed}"

    # Compute line sums
    lines_with_total = [li for li in line_items if li.get("line_total_minor") is not None]
    gross_line_sum = None
    net_line_sum = None
    subtotal_vs_gross = None
    subtotal_vs_net = None

    if line_items and len(lines_with_total) == len(line_items):
        gross_line_sum = sum(li["line_total_minor"] for li in lines_with_total)
        line_discount_sum = sum(li.get("discount_minor") or 0 for li in line_items)
        net_line_sum = gross_line_sum - line_discount_sum
        if sub is not None:
            subtotal_vs_gross = sub - gross_line_sum
            subtotal_vs_net = sub - net_line_sum

    # Generate candidates
    candidates = _generate_candidates(raw, signed_delta, gross_line_sum, net_line_sum, currency)
    # Rank and limit to 3
    ranked = _rank_candidates(candidates, signed_delta)[:3]

    return ReviewGuidanceSchema(
        signed_delta_minor=signed_delta,
        receipt_total_minor=total,
        computed_total_minor=computed,
        component_equation=component_equation,
        gross_line_sum_minor=gross_line_sum,
        net_line_sum_minor=net_line_sum,
        subtotal_vs_gross_delta_minor=subtotal_vs_gross,
        subtotal_vs_net_delta_minor=subtotal_vs_net,
        review_candidates=ranked,
    )


def _simulate_and_score(
    raw: dict[str, Any],
    patches: list[DraftPatchSchema],
) -> tuple[int, int]:
    """Apply patches to a copy of raw, run checks, return (equations_restored, remaining_fails).

    Returns (equations_restored_count, remaining_material_fails).
    """
    import copy

    from financial_os.services.validation import run_deterministic_checks

    sim = copy.deepcopy(raw)
    for patch in patches:
        op = patch.op
        if op == "clear_receipt_discount":
            sim["discount_minor"] = None
        elif op == "set_receipt_subtotal" and patch.value is not None:
            sim["subtotal_minor"] = patch.value
        elif op == "set_receipt_discount" and patch.value is not None:
            sim["discount_minor"] = patch.value
        elif op == "clear_receipt_subtotal":
            sim["subtotal_minor"] = None
        elif op == "clear_line_discount" and patch.ordinal is not None:
            for li in sim.get("line_items") or []:
                if li.get("ordinal") == patch.ordinal:
                    li["discount_minor"] = None
        elif op == "set_line_total" and patch.ordinal is not None and patch.value is not None:
            for li in sim.get("line_items") or []:
                if li.get("ordinal") == patch.ordinal:
                    li["line_total_minor"] = patch.value
        elif op == "remove_line_item" and patch.ordinal is not None:
            sim["line_items"] = [
                li for li in (sim.get("line_items") or []) if li.get("ordinal") != patch.ordinal
            ]

    sim_findings = run_deterministic_checks(sim)
    material_fails_after = sum(
        1
        for f in sim_findings
        if f.check_code in _MATERIAL_CHECKS and f.outcome == ValidationOutcome.FAIL
    )
    material_passes_after = sum(
        1
        for f in sim_findings
        if f.check_code in _MATERIAL_CHECKS and f.outcome == ValidationOutcome.PASS
    )
    # Count how many material checks pass vs. before — only FAIL→PASS transitions
    original_findings = run_deterministic_checks(raw)
    original_passes = sum(
        1
        for f in original_findings
        if f.check_code in _MATERIAL_CHECKS and f.outcome == ValidationOutcome.PASS
    )
    equations_restored = material_passes_after - original_passes
    return equations_restored, material_fails_after


def _generate_candidates(
    raw: dict[str, Any],
    signed_delta: int,
    gross_line_sum: int | None,
    net_line_sum: int | None,
    currency: str,
) -> list[_CandidateData]:
    """Generate bounded candidate patches. Returns list of candidate dicts."""
    candidates: list[_CandidateData] = []
    abs_delta = abs(signed_delta)

    sub = raw.get("subtotal_minor")
    tax = raw.get("tax_minor")
    tip = raw.get("tip_minor")
    dis = raw.get("discount_minor")
    total = raw.get("total_minor", 0)
    line_items = raw.get("line_items") or []
    multiplier = Decimal(10) ** minor_unit_exponent(currency)

    # --- Rule 0: Preserve values and confirm an evidenced discount convention ---
    subtotal_includes_receipt_discount = (
        dis is not None
        and dis > 0
        and sub is not None
        and net_line_sum is not None
        and abs(sub - (net_line_sum - dis)) <= _TOLERANCE
        and abs(total - ((sub or 0) + (tax or 0) + (tip or 0))) <= _TOLERANCE
    )
    if subtotal_includes_receipt_discount:
        candidates.append(
            {
                "kind": "confirm_discount_included_in_subtotal",
                "patches": [],
                # Existing receipts can carry a stored V1 failure. V2 proves the
                # same immutable values are internally consistent.
                "equations_restored": 1,
                "remaining_fails": 0,
                "abs_match": True,
                "keyword_support": True,
                "target_field": "discount_minor",
                "target_item_ordinal": None,
                "amount_minor": cast(int, dis),
                "reason_codes": ["subtotal_already_includes_receipt_discount"],
                "equations_before": [
                    f"subtotal({sub}) + tax({tax or 0}) + tip({tip or 0}) "
                    f"- discount({dis}) = {total - signed_delta}"
                ],
                "equations_after": [
                    f"subtotal({sub}) = net_line_sum({net_line_sum}) - receipt_discount({dis})",
                    f"subtotal({sub}) + tax({tax or 0}) + tip({tip or 0}) = total({total})",
                ],
                "strong_eligible": True,
            }
        )

    # --- Rule 1: Clear duplicated receipt discount ---
    if dis is not None and dis > 0 and abs(abs_delta - dis) <= _TOLERANCE:
        supported_line_sums = (
            [gross_line_sum, net_line_sum, net_line_sum - dis]
            if gross_line_sum is not None and net_line_sum is not None
            else []
        )
        has_complete_line_support = sub is not None and any(
            abs(sub - supported_sum) <= _TOLERANCE for supported_sum in supported_line_sums
        )
        subtotal_includes_receipt_discount = (
            sub is not None
            and net_line_sum is not None
            and abs(sub - (net_line_sum - dis)) <= _TOLERANCE
        )
        patches = [DraftPatchSchema(op="clear_receipt_discount")]
        eq_before = [f"total({total}) - computed({total - signed_delta}) = delta({signed_delta})"]
        new_computed = (sub or 0) + (tax or 0) + (tip or 0)
        eq_after = [f"total({total}) - computed({new_computed}) = delta({total - new_computed})"]
        reason_codes = ["receipt_discount_matches_delta"]
        if subtotal_includes_receipt_discount:
            reason_codes.insert(0, "subtotal_already_includes_receipt_discount")
            eq_after.append(
                f"subtotal({sub}) = net_line_sum({net_line_sum}) - receipt_discount({dis})"
            )
        scores, remaining = _simulate_and_score(raw, patches)
        candidates.append(
            {
                "kind": "clear_receipt_discount",
                "patches": patches,
                "equations_restored": scores,
                "remaining_fails": remaining,
                "abs_match": abs(abs_delta - dis) <= _TOLERANCE,
                "keyword_support": True,
                "target_field": "discount_minor",
                "target_item_ordinal": None,
                "amount_minor": dis,
                "reason_codes": reason_codes,
                "equations_before": eq_before,
                "equations_after": eq_after,
                # An amount match without complete line coverage remains a possible
                # explanation, not a strong recommendation.
                "strong_eligible": has_complete_line_support,
            }
        )

    # --- Rule 2: Use gross line sum as subtotal ---
    if gross_line_sum is not None and sub is not None:
        new_computed = gross_line_sum + (tax or 0) + (tip or 0) - (dis or 0)
        if abs(total - new_computed) <= _TOLERANCE:
            patches = [DraftPatchSchema(op="set_receipt_subtotal", value=gross_line_sum)]
            eq_before = [f"subtotal({sub}) vs gross_line_sum({gross_line_sum})"]
            eq_after = [
                f"subtotal({gross_line_sum}) + tax({tax or 0}) + tip({tip or 0}) "
                f"- discount({dis or 0}) = {new_computed}"
            ]
            scores, remaining = _simulate_and_score(raw, patches)
            candidates.append(
                {
                    "kind": "use_gross_line_sum_as_subtotal",
                    "patches": patches,
                    "equations_restored": scores,
                    "remaining_fails": remaining,
                    "abs_match": abs(total - new_computed) <= _TOLERANCE,
                    "keyword_support": False,
                    "target_field": "subtotal_minor",
                    "target_item_ordinal": None,
                    "amount_minor": gross_line_sum,
                    "reason_codes": ["gross_line_sum_restores_total"],
                    "equations_before": eq_before,
                    "equations_after": eq_after,
                }
            )

    # --- Rule 3: Use net line sum as subtotal ---
    if (
        net_line_sum is not None
        and sub is not None
        and net_line_sum != (gross_line_sum or net_line_sum)
    ):
        new_computed = net_line_sum + (tax or 0) + (tip or 0) - (dis or 0)
        if abs(total - new_computed) <= _TOLERANCE:
            patches = [DraftPatchSchema(op="set_receipt_subtotal", value=net_line_sum)]
            eq_before = [f"subtotal({sub}) vs net_line_sum({net_line_sum})"]
            eq_after = [
                f"subtotal({net_line_sum}) + tax({tax or 0}) + tip({tip or 0}) "
                f"- discount({dis or 0}) = {new_computed}"
            ]
            scores, remaining = _simulate_and_score(raw, patches)
            candidates.append(
                {
                    "kind": "use_net_line_sum_as_subtotal",
                    "patches": patches,
                    "equations_restored": scores,
                    "remaining_fails": remaining,
                    "abs_match": abs(total - new_computed) <= _TOLERANCE,
                    "keyword_support": False,
                    "target_field": "subtotal_minor",
                    "target_item_ordinal": None,
                    "amount_minor": net_line_sum,
                    "reason_codes": ["net_line_sum_restores_total"],
                    "equations_before": eq_before,
                    "equations_after": eq_after,
                }
            )

    # --- Rule 4: Clear duplicated line discount ---
    for li in line_items:
        li_dis = li.get("discount_minor")
        ordinal = li.get("ordinal", 0)
        if li_dis is not None and li_dis > 0 and abs(abs_delta - li_dis) <= _TOLERANCE:
            patches = [DraftPatchSchema(op="clear_line_discount", ordinal=ordinal)]
            eq_before = [f"line({ordinal}) discount({li_dis}) matches delta({signed_delta})"]
            eq_after = [f"line({ordinal}) discount cleared"]
            scores, remaining = _simulate_and_score(raw, patches)
            candidates.append(
                {
                    "kind": "clear_line_discount",
                    "patches": patches,
                    "equations_restored": scores,
                    "remaining_fails": remaining,
                    "abs_match": True,
                    "keyword_support": True,
                    "target_field": "discount_minor",
                    "target_item_ordinal": ordinal,
                    "amount_minor": li_dis,
                    "reason_codes": ["line_discount_matches_delta"],
                    "equations_before": eq_before,
                    "equations_after": eq_after,
                }
            )

    # --- Rule 5: Replace line total with qty*price ---
    for li in line_items:
        qty_str = li.get("quantity")
        price_str = li.get("unit_price_decimal")
        line_total = li.get("line_total_minor")
        ordinal = li.get("ordinal", 0)
        if qty_str is None or price_str is None or line_total is None:
            continue
        try:
            qty = Decimal(qty_str)
            price = Decimal(price_str)
        except (InvalidOperation, TypeError, ValueError):
            continue
        expected_total = int((qty * price * multiplier).to_integral_value())
        diff = line_total - expected_total
        if abs(abs_delta - abs(diff)) <= _TOLERANCE and diff != 0:
            patches = [DraftPatchSchema(op="set_line_total", ordinal=ordinal, value=expected_total)]
            eq_before = [f"line({ordinal}) total({line_total}) vs qty*price({expected_total})"]
            eq_after = [
                f"line({ordinal}) total({expected_total}) = qty({qty_str}) * price({price_str})"
            ]
            scores, remaining = _simulate_and_score(raw, patches)
            candidates.append(
                {
                    "kind": "replace_line_total_with_qty_price",
                    "patches": patches,
                    "equations_restored": scores,
                    "remaining_fails": remaining,
                    "abs_match": True,
                    "keyword_support": False,
                    "target_field": "line_total_minor",
                    "target_item_ordinal": ordinal,
                    "amount_minor": line_total,
                    "reason_codes": ["qty_price_product_matches_delta"],
                    "equations_before": eq_before,
                    "equations_after": eq_after,
                }
            )

    # --- Rule 6: Remove one line item (only when it restores equations) ---
    for li in line_items:
        li_total = li.get("line_total_minor")
        ordinal = li.get("ordinal", 0)
        if li_total is None:
            continue
        if abs(abs_delta - li_total) <= _TOLERANCE:
            patches = [DraftPatchSchema(op="remove_line_item", ordinal=ordinal)]
            eq_before = [f"line({ordinal}) total({li_total}) matches delta({signed_delta})"]
            eq_after = [f"line({ordinal}) removed"]
            scores, remaining = _simulate_and_score(raw, patches)
            # Only add if it actually restores equations — not just an amount match
            if scores > 0:
                candidates.append(
                    {
                        "kind": "remove_line_item",
                        "patches": patches,
                        "equations_restored": scores,
                        "remaining_fails": remaining,
                        "abs_match": True,
                        "keyword_support": False,
                        "target_field": None,
                        "target_item_ordinal": ordinal,
                        "amount_minor": li_total,
                        "reason_codes": ["line_total_matches_delta_and_restores_equations"],
                        "equations_before": eq_before,
                        "equations_after": eq_after,
                    }
                )

    return candidates


def _rank_candidates(
    candidates: list[_CandidateData], _signed_delta: int
) -> list[ReviewCandidateSchema]:
    """Rank candidates and assign evidence bands. Return ReviewCandidateSchema list."""
    if not candidates:
        return []

    def semantic_support(c: _CandidateData) -> int:
        return int("subtotal_already_includes_receipt_discount" in c["reason_codes"])

    def evidence_mutation_cost(c: _CandidateData) -> int:
        """Prefer preserving observed summary fields when equations are equivalent."""
        return {
            "confirm_discount_included_in_subtotal": 0,
            "clear_receipt_discount": 1,
            "clear_line_discount": 1,
            "replace_line_total_with_qty_price": 2,
            "use_gross_line_sum_as_subtotal": 2,
            "use_net_line_sum_as_subtotal": 2,
            "remove_line_item": 3,
        }.get(c["kind"], len(c["patches"]))

    def evidence_tier(c: _CandidateData) -> tuple[int, int, int, int, int, int]:
        """Evidence score excluding stable presentation tie-breakers."""
        return (
            c["equations_restored"],
            -c["remaining_fails"],
            semantic_support(c),
            -evidence_mutation_cost(c),
            int(c["keyword_support"]),
            -len(c["patches"]),
        )

    # Sort by restoration, semantic support, evidence mutation cost, then stable
    # deterministic presentation fields.
    def sort_key(
        c: _CandidateData,
    ) -> tuple[int, int, int, int, int, int, str, int, tuple[tuple[str, int, int], ...]]:
        tier = evidence_tier(c)
        return (
            -tier[0],
            -tier[1],
            -tier[2],
            -tier[3],
            -tier[4],
            -tier[5],
            c["kind"],  # stable alphabetic tie-break
            c.get("target_item_ordinal") or 0,
            tuple((patch.op, patch.ordinal or 0, patch.value or 0) for patch in c["patches"]),
        )

    sorted_cands = sorted(candidates, key=sort_key)

    # Only evidence-supported, fully-restoring candidates may be strong. If more
    # than one candidate has the same complete evidence tier, all top candidates
    # are ambiguous. A lower-evidence arithmetic solution remains possible.
    fully_restoring = [
        c
        for c in sorted_cands
        if c["equations_restored"] > 0
        and c["remaining_fails"] == 0
        and c.get("strong_eligible", True)
    ]
    top_tier = evidence_tier(fully_restoring[0]) if fully_restoring else None
    top_tier_tied = [c for c in fully_restoring if evidence_tier(c) == top_tier]

    result: list[ReviewCandidateSchema] = []
    for c in sorted_cands[:3]:
        is_fully_restoring = c["equations_restored"] > 0 and c["remaining_fails"] == 0
        is_top_tier = top_tier is not None and evidence_tier(c) == top_tier
        if is_fully_restoring and c.get("strong_eligible", True):
            if is_top_tier and len(top_tier_tied) > 1:
                band: Literal["strong", "possible", "ambiguous"] = "ambiguous"
            elif is_top_tier:
                band = "strong"
            else:
                band = "possible"
        elif c["abs_match"]:
            band = "possible"
        else:
            band = "ambiguous"

        result.append(
            ReviewCandidateSchema(
                kind=c["kind"],
                evidence_band=band,
                target_field=c.get("target_field"),
                target_item_ordinal=c.get("target_item_ordinal"),
                amount_minor=c.get("amount_minor"),
                reason_codes=c["reason_codes"],
                equations_before=c["equations_before"],
                equations_after=c["equations_after"],
                draft_patch=c["patches"],
            )
        )

    return result
