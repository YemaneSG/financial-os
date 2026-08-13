import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, ApiClientError, NetworkError, setTokenProvider } from "@/api/client";
import {
  FIXTURE_CREATE_RECEIPT_RESPONSE,
  FIXTURE_FINALIZE_RESPONSE,
  FIXTURE_RECEIPT_DETAIL,
  FIXTURE_RECEIPT_ID,
  FIXTURE_ASSET_ID_1,
  FIXTURE_CLIENT_KEY,
} from "@/fixtures/receipts";

function mockFetch(status: number, body: unknown): void {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function mockFetchNetworkError(): void {
  vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new TypeError("Failed to fetch"));
}

beforeEach(() => {
  setTokenProvider(async () => "test-firebase-token");
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("apiClient.createReceipt", () => {
  it("sends POST with correct body and returns response", async () => {
    mockFetch(201, FIXTURE_CREATE_RECEIPT_RESPONSE);
    const res = await apiClient.createReceipt({
      client_submission_key: FIXTURE_CLIENT_KEY,
      expected_asset_count: 1,
      assets: [{ ordinal: 1, declared_mime_type: "image/jpeg", byte_size: 1024 }],
    });
    expect(res.receipt_id).toBe(FIXTURE_RECEIPT_ID);
    expect(res.upload_capabilities).toHaveLength(1);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/receipts"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("returns 200 on idempotent replay", async () => {
    mockFetch(200, FIXTURE_CREATE_RECEIPT_RESPONSE);
    const res = await apiClient.createReceipt({
      client_submission_key: FIXTURE_CLIENT_KEY,
      expected_asset_count: 1,
      assets: [{ ordinal: 1, declared_mime_type: "image/jpeg", byte_size: 1024 }],
    });
    expect(res.receipt_id).toBe(FIXTURE_RECEIPT_ID);
  });

  it("throws ApiClientError on 401", async () => {
    mockFetch(401, { error_code: "UNAUTHORIZED", message: "Authentication required." });
    await expect(
      apiClient.createReceipt({
        client_submission_key: FIXTURE_CLIENT_KEY,
        expected_asset_count: 1,
        assets: [{ ordinal: 1, declared_mime_type: "image/jpeg", byte_size: 1024 }],
      }),
    ).rejects.toBeInstanceOf(ApiClientError);
  });

  it("throws NetworkError on fetch failure", async () => {
    mockFetchNetworkError();
    await expect(
      apiClient.createReceipt({
        client_submission_key: FIXTURE_CLIENT_KEY,
        expected_asset_count: 1,
        assets: [{ ordinal: 1, declared_mime_type: "image/jpeg", byte_size: 1024 }],
      }),
    ).rejects.toBeInstanceOf(NetworkError);
  });
});

describe("apiClient.finalizeReceipt", () => {
  it("sends POST to finalize endpoint", async () => {
    mockFetch(200, FIXTURE_FINALIZE_RESPONSE);
    const res = await apiClient.finalizeReceipt(FIXTURE_RECEIPT_ID);
    expect(res.acknowledged_at).toBeTruthy();
    expect(res.processing_status).toBe("queued");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/receipts/${FIXTURE_RECEIPT_ID}/finalize`),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws ApiClientError on 422 (evidence incomplete)", async () => {
    mockFetch(422, {
      error_code: "EVIDENCE_INCOMPLETE",
      message: "One or more expected images are missing.",
    });
    await expect(apiClient.finalizeReceipt(FIXTURE_RECEIPT_ID)).rejects.toBeInstanceOf(
      ApiClientError,
    );
  });
});

describe("apiClient.getReceipt", () => {
  it("fetches receipt detail", async () => {
    mockFetch(200, FIXTURE_RECEIPT_DETAIL);
    const res = await apiClient.getReceipt(FIXTURE_RECEIPT_ID);
    expect(res.receipt_id).toBe(FIXTURE_RECEIPT_ID);
    expect(res.current_revision?.total_minor).toBe(1134);
  });

  it("throws ApiClientError on 404", async () => {
    mockFetch(404, { error_code: "RECEIPT_NOT_FOUND", message: "Receipt not found." });
    const err = await apiClient.getReceipt("nonexistent-id").catch((e) => e);
    expect(err).toBeInstanceOf(ApiClientError);
    expect((err as ApiClientError).status).toBe(404);
  });
});

describe("apiClient.listReceipts", () => {
  it("constructs correct query params", async () => {
    mockFetch(200, { receipts: [], next_cursor: null });
    await apiClient.listReceipts("cursor-abc", 10);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("cursor=cursor-abc"),
      expect.anything(),
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=10"),
      expect.anything(),
    );
  });
});

describe("apiClient.retryProcessing", () => {
  it("sends POST to retry endpoint", async () => {
    mockFetch(200, { receipt_id: FIXTURE_RECEIPT_ID, processing_status: "queued" });
    const res = await apiClient.retryProcessing(FIXTURE_RECEIPT_ID);
    expect(res.processing_status).toBe("queued");
  });

  it("throws ApiClientError on 409 (not retryable)", async () => {
    mockFetch(409, {
      error_code: "RETRY_NOT_PERMITTED",
      message: "Receipt is not in a retryable state.",
    });
    const err = await apiClient.retryProcessing(FIXTURE_RECEIPT_ID).catch((e) => e);
    expect(err).toBeInstanceOf(ApiClientError);
    expect((err as ApiClientError).status).toBe(409);
  });
});

describe("apiClient.getAssetDownloadCapability", () => {
  it("sends POST and returns download URL", async () => {
    mockFetch(200, {
      download_url: "https://storage.example.invalid/download/asset1",
      method: "GET",
      expires_at: "2099-01-01T00:00:00.000Z",
    });
    const res = await apiClient.getAssetDownloadCapability(
      FIXTURE_RECEIPT_ID,
      FIXTURE_ASSET_ID_1,
    );
    expect(res.download_url).toContain("storage.example.invalid");
    expect(res.method).toBe("GET");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/assets/${FIXTURE_ASSET_ID_1}/download`),
      expect.objectContaining({ method: "POST" }),
    );
  });
});

describe("Authorization header", () => {
  it("attaches Bearer token to every request", async () => {
    setTokenProvider(async () => "my-firebase-jwt");
    mockFetch(200, { receipts: [], next_cursor: null });
    await apiClient.listReceipts();
    expect(fetch).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer my-firebase-jwt",
        }),
      }),
    );
  });

  it("omits Authorization header when no token", async () => {
    setTokenProvider(async () => null);
    mockFetch(401, { error_code: "UNAUTHORIZED", message: "Authentication required." });
    await apiClient.listReceipts().catch(() => null);
    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls.at(-1) as [
      string,
      RequestInit & { headers: Record<string, string> },
    ];
    expect(options.headers).not.toHaveProperty("Authorization");
  });
});
