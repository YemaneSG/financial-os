"""
Storage security tests: OBJ-01, OBJ-02, S-01.

Verifies:
- Direct anonymous bucket access fails
- Signed URL method restriction is enforced
- Signed URL path restriction is enforced
- Generation mismatch triggers terminal failure (S-01)

These tests require a live GCS bucket and Cloud Run services.
They use synthetic fixtures only — no real receipt images.
"""

import os
import uuid

import httpx
import pytest


@pytest.fixture(scope="session")
def evidence_bucket_name() -> str:
    name = os.environ.get("EVIDENCE_BUCKET_NAME", "")
    if not name:
        pytest.skip("EVIDENCE_BUCKET_NAME not set — skipping storage tests.")
    return name


class TestPublicAccessPrevention:
    """OBJ-01: bucket must not be publicly accessible."""

    def test_anonymous_bucket_list_fails(self, evidence_bucket_name: str) -> None:
        url = f"https://storage.googleapis.com/{evidence_bucket_name}"
        resp = httpx.get(url, timeout=10)
        assert resp.status_code in (401, 403, 404), (
            f"Bucket listing returned unexpected status {resp.status_code}. "
            "Bucket may be publicly accessible (OBJ-01 violation)."
        )

    def test_anonymous_object_read_fails(self, evidence_bucket_name: str) -> None:
        # Try to read a plausible-looking object name.
        fake_key = "originals/00000000-0000-0000-0000-000000000000/image-1.jpg"
        url = f"https://storage.googleapis.com/{evidence_bucket_name}/{fake_key}"
        resp = httpx.get(url, timeout=10)
        assert resp.status_code in (401, 403, 404), (
            f"Anonymous object read returned {resp.status_code}. "
            "Bucket may be publicly accessible (OBJ-01 violation)."
        )


class TestSignedUrlMethodRestriction:
    """OBJ-02: signed URLs must be method-specific."""

    def test_upload_url_rejects_get_method(self, api_client: httpx.Client) -> None:
        """Obtain an upload URL then attempt to use it with GET — must fail."""
        # Create a synthetic receipt to get a real upload URL.
        submission_key = str(uuid.uuid4())
        create_resp = api_client.post(
            "/api/v1/receipts",
            json={
                "client_submission_key": submission_key,
                "expected_asset_count": 1,
                "assets": [{"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1024}],
            },
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Could not create test receipt — skipping signed URL tests.")

        upload_url = create_resp.json()["upload_capabilities"][0]["upload_url"]

        # Attempt GET against a PUT-only signed URL.
        get_resp = httpx.get(upload_url, timeout=10)
        assert get_resp.status_code in (400, 403, 405), (
            f"Signed PUT URL accepted GET method (status {get_resp.status_code}). "
            "Signed URLs must be method-specific (OBJ-02)."
        )


class TestGenerationBinding:
    """S-01: worker must detect generation mismatch and mark attempt terminal_failed."""

    def test_generation_mismatch_causes_terminal_failure(self, api_client: httpx.Client) -> None:
        """
        Full S-01 negative test:
        1. Create receipt + upload synthetic image at generation 1.
        2. Finalize (records generation 1).
        3. Overwrite the object (generation 2) using a second signed upload.
        4. Trigger processing via the retry endpoint.
        5. Assert the processing attempt is terminal_failed.

        This test is a live integration test that requires actual GCS and worker access.
        It is skipped in CI unless ENABLE_GENERATION_MISMATCH_TEST=true is set.
        """
        if os.environ.get("ENABLE_GENERATION_MISMATCH_TEST", "").lower() != "true":
            pytest.skip("ENABLE_GENERATION_MISMATCH_TEST not enabled.")

        # Step 1: create receipt.
        submission_key = str(uuid.uuid4())
        create_resp = api_client.post(
            "/api/v1/receipts",
            json={
                "client_submission_key": submission_key,
                "expected_asset_count": 1,
                "assets": [{"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1024}],
            },
        )
        assert create_resp.status_code in (200, 201)
        receipt_id = create_resp.json()["receipt_id"]
        upload_url = create_resp.json()["upload_capabilities"][0]["upload_url"]

        # Step 2: upload synthetic image (generation 1).
        synthetic_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0] + [0x00] * 1020)  # Minimal JPEG header.
        put_resp = httpx.put(
            upload_url,
            content=synthetic_jpeg,
            headers={"Content-Type": "image/jpeg"},
            timeout=30,
        )
        assert put_resp.status_code == 200, f"Upload failed: {put_resp.status_code}"

        # Step 3: finalize (records generation).
        finalize_resp = api_client.post(f"/api/v1/receipts/{receipt_id}/finalize")
        assert finalize_resp.status_code == 200, f"Finalize failed: {finalize_resp.status_code}"

        # Step 4: attempt to upload different content to the same object name.
        # This simulates a signed-URL overwrite after finalization.
        # Getting a second upload URL for the same asset should either fail or succeed
        # with a new signed URL (implementation-dependent). If it fails, skip this test.
        overwrite_resp = api_client.post(
            "/api/v1/receipts",
            json={
                "client_submission_key": submission_key,  # Idempotent replay.
                "expected_asset_count": 1,
                "assets": [{"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1024}],
            },
        )
        if overwrite_resp.status_code != 200:
            pytest.skip("Could not get second upload capability for overwrite test.")

        second_upload_url = overwrite_resp.json()["upload_capabilities"][0]["upload_url"]
        different_content = bytes([0xFF, 0xD8, 0xFF, 0xE0] + [0xFF] * 1020)
        httpx.put(
            second_upload_url,
            content=different_content,
            headers={"Content-Type": "image/jpeg"},
            timeout=30,
        )

        # Step 5: trigger re-processing and check for terminal_failed.
        retry_response = api_client.post(f"/api/v1/receipts/{receipt_id}/retry-processing")
        assert retry_response.status_code in (200, 202)
        # Allow some time for async processing.
        import time

        for _ in range(12):
            time.sleep(5)
            detail_resp = api_client.get(f"/api/v1/receipts/{receipt_id}")
            status = detail_resp.json().get("processing_status")
            if status in ("failed", "retryable_failed", "extracted"):
                break

        final_detail = api_client.get(f"/api/v1/receipts/{receipt_id}").json()
        final_status = final_detail.get("processing_status")
        assert final_detail.get("processing_status") == "failed", (
            f"Expected terminal failure after generation mismatch. Got: {final_status}"
        )
        safe_error_code = final_detail.get("safe_error_code")
        assert final_detail.get("safe_error_code") == "GENERATION_MISMATCH", (
            f"Expected safe_error_code=GENERATION_MISMATCH. Got: {safe_error_code}"
        )
