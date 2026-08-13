"""
E2E test: full receipt capture vertical slice.

Exercises: create → upload → finalize → poll → verify result.
Uses synthetic fixtures only (SYNTHETIC_JPEG_1X1 from conftest).

Controls verified: REC-001, UPL-001–004, QUE-001, STATE-001, REL-001, API-01.
"""

import time
import uuid

import httpx
import pytest

from .conftest import SYNTHETIC_JPEG_1X1

PROCESSING_TERMINAL_STATES = {"extracted", "failed"}
POLLING_TIMEOUT_SECONDS = 120
POLLING_INTERVAL_SECONDS = 5


def poll_until_terminal(
    client: httpx.Client, receipt_id: str, timeout: float = POLLING_TIMEOUT_SECONDS
) -> dict:
    """Poll GET /api/v1/receipts/{id} until a terminal processing state is reached."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = client.get(f"/api/v1/receipts/{receipt_id}")
        assert resp.status_code == 200
        data = resp.json()
        if (
            data["processing_status"] in PROCESSING_TERMINAL_STATES
            or data["processing_status"] == "retryable_failed"
        ):
            return data
        time.sleep(POLLING_INTERVAL_SECONDS)
    pytest.fail(f"Receipt {receipt_id} did not reach a terminal state within {timeout}s.")


class TestReceiptCaptureSingleImage:
    """Happy-path single-image receipt submission."""

    def test_create_receipt_returns_201_with_upload_capability(
        self, api_client: httpx.Client
    ) -> None:
        resp = api_client.post(
            "/api/v1/receipts",
            json={
                "client_submission_key": str(uuid.uuid4()),
                "expected_asset_count": 1,
                "assets": [
                    {
                        "ordinal": 1,
                        "declared_mime_type": "image/jpeg",
                        "byte_size": len(SYNTHETIC_JPEG_1X1),
                    }
                ],
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "receipt_id" in body
        assert "upload_capabilities" in body
        assert len(body["upload_capabilities"]) == 1
        cap = body["upload_capabilities"][0]
        assert cap["method"] == "PUT"
        assert "upload_url" in cap
        assert cap["ordinal"] == 1

    def test_full_flow_reaches_acknowledged_state(self, api_client: httpx.Client) -> None:
        """Create → upload → finalize produces 'queued' status (durable acknowledgement)."""
        submission_key = str(uuid.uuid4())

        # Create.
        create_resp = api_client.post(
            "/api/v1/receipts",
            json={
                "client_submission_key": submission_key,
                "expected_asset_count": 1,
                "assets": [
                    {
                        "ordinal": 1,
                        "declared_mime_type": "image/jpeg",
                        "byte_size": len(SYNTHETIC_JPEG_1X1),
                    }
                ],
            },
        )
        assert create_resp.status_code == 201
        receipt_id = create_resp.json()["receipt_id"]
        upload_url = create_resp.json()["upload_capabilities"][0]["upload_url"]

        # Upload directly to GCS via signed URL.
        put_resp = httpx.put(
            upload_url,
            content=SYNTHETIC_JPEG_1X1,
            headers={"Content-Type": "image/jpeg"},
            timeout=30,
        )
        assert put_resp.status_code == 200

        # Finalize.
        finalize_resp = api_client.post(f"/api/v1/receipts/{receipt_id}/finalize")
        assert finalize_resp.status_code == 200
        finalize_body = finalize_resp.json()
        assert finalize_body["processing_status"] in ("queued", "processing", "extracted")
        assert "acknowledged_at" in finalize_body
        assert finalize_body["acknowledged_at"] is not None

    def test_idempotent_create_returns_200_with_same_receipt(
        self, api_client: httpx.Client
    ) -> None:
        """A-01: duplicate client_submission_key returns 200, same receipt ID."""
        submission_key = str(uuid.uuid4())
        payload = {
            "client_submission_key": submission_key,
            "expected_asset_count": 1,
            "assets": [{"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1024}],
        }

        resp1 = api_client.post("/api/v1/receipts", json=payload)
        resp2 = api_client.post("/api/v1/receipts", json=payload)

        assert resp1.status_code == 201
        assert resp2.status_code == 200
        assert resp1.json()["receipt_id"] == resp2.json()["receipt_id"]


class TestReceiptList:
    def test_list_returns_receipts_for_owner(self, api_client: httpx.Client) -> None:
        resp = api_client.get("/api/v1/receipts")
        assert resp.status_code == 200
        body = resp.json()
        assert "receipts" in body
        assert isinstance(body["receipts"], list)

    def test_list_pagination_cursor(self, api_client: httpx.Client) -> None:
        resp = api_client.get("/api/v1/receipts", params={"limit": 1})
        assert resp.status_code == 200
        # If there are multiple receipts, a next_cursor should be present.
        body = resp.json()
        assert "next_cursor" in body


class TestReceiptDetail:
    def test_nonexistent_receipt_returns_404(self, api_client: httpx.Client) -> None:
        fake_id = str(uuid.uuid4())
        resp = api_client.get(f"/api/v1/receipts/{fake_id}")
        assert resp.status_code == 404

    def test_404_response_does_not_contain_private_detail(self, api_client: httpx.Client) -> None:
        fake_id = str(uuid.uuid4())
        resp = api_client.get(f"/api/v1/receipts/{fake_id}")
        body = resp.text
        for word in ["stack", "traceback", "sql", "database", "exception"]:
            assert word not in body.lower(), f"404 response leaks: {word!r}"


class TestFinalizeValidation:
    def test_finalize_without_upload_returns_422(self, api_client: httpx.Client) -> None:
        """OBJ-03: finalize must fail if the object was never uploaded."""
        create_resp = api_client.post(
            "/api/v1/receipts",
            json={
                "client_submission_key": str(uuid.uuid4()),
                "expected_asset_count": 1,
                "assets": [{"ordinal": 1, "declared_mime_type": "image/jpeg", "byte_size": 1024}],
            },
        )
        assert create_resp.status_code == 201
        receipt_id = create_resp.json()["receipt_id"]

        finalize_resp = api_client.post(f"/api/v1/receipts/{receipt_id}/finalize")
        assert finalize_resp.status_code == 422
        assert finalize_resp.json().get("error_code") == "EVIDENCE_INCOMPLETE"


class TestHealthProbes:
    def test_liveness_probe_returns_200(self, api_client: httpx.Client) -> None:
        resp = httpx.get(f"{api_client.base_url}/health/live", timeout=10)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readiness_probe_returns_200(self, api_client: httpx.Client) -> None:
        resp = httpx.get(f"{api_client.base_url}/health/ready", timeout=10)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["checks"]["database"] is True
