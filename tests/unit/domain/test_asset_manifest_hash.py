"""Unit tests for the canonical asset manifest hash algorithm (A-03).

Tests that the algorithm is:
- Deterministic: same inputs → same output.
- Order-sensitive: ordinal determines sort; swapping A/B ≠ B/A.
- Content-sensitive: different sha256 → different hash.
- Cross-path consistent: calling from any context with same inputs gives same result.
"""

import pytest

from financial_os.domain.money import compute_asset_manifest_hash


@pytest.mark.unit
class TestAssetManifestHash:
    def _make_assets(self, n: int = 2) -> list[dict]:
        return [
            {
                "ordinal": i + 1,
                "object_key": f"originals/owner-1/receipt-1/asset-{i + 1}",
                "sha256": f"{'a' * (i + 1)}{'0' * (63 - i)}",
            }
            for i in range(n)
        ]

    def test_deterministic_same_input(self):
        assets = self._make_assets(3)
        h1 = compute_asset_manifest_hash(assets)
        h2 = compute_asset_manifest_hash(assets)
        assert h1 == h2

    def test_is_64_hex_characters(self):
        assets = self._make_assets(1)
        h = compute_asset_manifest_hash(assets)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_order_sensitive(self):
        """Swapping ordinal 1 and 2 must produce a different hash."""
        assets_ab = [
            {"ordinal": 1, "object_key": "key-a", "sha256": "a" * 64},
            {"ordinal": 2, "object_key": "key-b", "sha256": "b" * 64},
        ]
        assets_ba = [
            {"ordinal": 1, "object_key": "key-b", "sha256": "b" * 64},
            {"ordinal": 2, "object_key": "key-a", "sha256": "a" * 64},
        ]
        assert compute_asset_manifest_hash(assets_ab) != compute_asset_manifest_hash(assets_ba)

    def test_unsorted_input_sorted_by_ordinal(self):
        """Input provided in reverse ordinal order still produces the same hash."""
        forward = [
            {"ordinal": 1, "object_key": "k1", "sha256": "a" * 64},
            {"ordinal": 2, "object_key": "k2", "sha256": "b" * 64},
        ]
        reversed_input = list(reversed(forward))
        assert compute_asset_manifest_hash(forward) == compute_asset_manifest_hash(reversed_input)

    def test_content_sensitive(self):
        """Different sha256 for same ordinal/key must produce a different hash."""
        assets_v1 = [{"ordinal": 1, "object_key": "key", "sha256": "a" * 64}]
        assets_v2 = [{"ordinal": 1, "object_key": "key", "sha256": "b" * 64}]
        assert compute_asset_manifest_hash(assets_v1) != compute_asset_manifest_hash(assets_v2)

    def test_empty_list(self):
        """Empty asset list produces a stable hash (SHA-256 of empty JSON array)."""
        h = compute_asset_manifest_hash([])
        assert len(h) == 64

    def test_cross_path_consistent(self):
        """Calling from three different code paths produces the same hash (A-03)."""
        assets = [{"ordinal": 1, "object_key": "originals/o/r/a", "sha256": "c" * 64}]
        # Path 1: direct call
        h1 = compute_asset_manifest_hash(assets)
        # Path 2: copy of list
        h2 = compute_asset_manifest_hash(list(assets))
        # Path 3: dict copy
        h3 = compute_asset_manifest_hash([dict(a) for a in assets])
        assert h1 == h2 == h3

    def test_known_vector(self):
        """Regression test with a known input/output pair."""
        import hashlib
        import json

        assets = [
            {"ordinal": 1, "object_key": "originals/owner/receipt/asset", "sha256": "d" * 64},
        ]
        expected_input = json.dumps(
            [{"ordinal": 1, "object_key": "originals/owner/receipt/asset", "sha256": "d" * 64}],
            separators=(",", ":"),
            sort_keys=True,
        )
        expected = hashlib.sha256(expected_input.encode("utf-8")).hexdigest()
        assert compute_asset_manifest_hash(assets) == expected
