"""Unit tests for the privacy-safe deduplication backfill CLI."""

from __future__ import annotations

import sys

import pytest

from financial_os.operations.backfill_dedup import _build_parser, main


def test_require_zero_is_an_explicit_dry_run_gate() -> None:
    args = _build_parser().parse_args(["--require-zero"])

    assert args.require_zero is True
    assert args.apply is False


@pytest.mark.asyncio
async def test_require_zero_rejects_apply_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["backfill_dedup", "--apply", "--require-zero"])

    assert await main() == 2
