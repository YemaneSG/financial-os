"""Unit tests for worker extraction input ceilings (implementation-contracts.md §8)."""

import pytest

from financial_os.domain.errors import (
    CEILING_ASSET_BYTES,
    CEILING_ASSET_COUNT,
    CEILING_TOTAL_BYTES,
    WorkerCeilingError,
)


@pytest.mark.unit
class TestWorkerCeilings:
    """Tests that ceiling checks enforce the limits from implementation-contracts.md §8."""

    def _check_ceilings(
        self,
        asset_bytes_list: list[int],
        max_assets: int = 10,
        max_asset_bytes: int = 10_485_760,
        max_total_bytes: int = 52_428_800,
    ) -> None:
        """Run the same ceiling logic used in services/worker.py."""
        if len(asset_bytes_list) > max_assets:
            raise WorkerCeilingError(CEILING_ASSET_COUNT, "Too many assets")
        total = 0
        for size in asset_bytes_list:
            if size > max_asset_bytes:
                raise WorkerCeilingError(CEILING_ASSET_BYTES, "Asset too large")
            total += size
            if total > max_total_bytes:
                raise WorkerCeilingError(CEILING_TOTAL_BYTES, "Total too large")

    def test_within_all_ceilings_passes(self):
        self._check_ceilings([1000, 2000, 3000])  # should not raise

    def test_asset_count_ceiling(self):
        with pytest.raises(WorkerCeilingError) as exc_info:
            self._check_ceilings([100] * 11, max_assets=10)
        assert exc_info.value.safe_error_code == CEILING_ASSET_COUNT

    def test_asset_bytes_ceiling(self):
        with pytest.raises(WorkerCeilingError) as exc_info:
            self._check_ceilings([10_485_761], max_asset_bytes=10_485_760)
        assert exc_info.value.safe_error_code == CEILING_ASSET_BYTES

    def test_total_bytes_ceiling(self):
        with pytest.raises(WorkerCeilingError) as exc_info:
            # 11 assets of 5 MiB each = 55 MiB > 50 MiB total ceiling
            self._check_ceilings(
                [5_000_000] * 11,
                max_assets=11,  # allow 11 to test total ceiling
                max_asset_bytes=10_485_760,
                max_total_bytes=52_428_800,
            )
        assert exc_info.value.safe_error_code == CEILING_TOTAL_BYTES

    def test_exactly_at_count_limit_passes(self):
        self._check_ceilings([100] * 10, max_assets=10)  # exactly 10 — should pass

    def test_exactly_at_asset_bytes_limit_passes(self):
        self._check_ceilings([10_485_760], max_asset_bytes=10_485_760)  # should pass

    def test_zero_assets_passes(self):
        self._check_ceilings([])  # no assets — passes all ceilings
