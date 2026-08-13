import type {
  CreateReceiptRequest,
  CreateReceiptResponse,
  FinalizeReceiptResponse,
  ListReceiptsResponse,
  ReceiptDetail,
  RetryProcessingResponse,
  DownloadCapabilityResponse,
  ApiError,
  UUID,
} from "./types";

export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiError,
  ) {
    super(body.message);
    this.name = "ApiClientError";
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

type TokenProvider = () => Promise<string | null>;

let tokenProvider: TokenProvider = async () => null;

export function setTokenProvider(provider: TokenProvider): void {
  tokenProvider = provider;
}

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await tokenProvider();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new NetworkError("Network request failed. Check your connection.");
  }

  if (!response.ok) {
    let body: ApiError;
    try {
      body = (await response.json()) as ApiError;
    } catch {
      body = { error_code: "UNKNOWN", message: response.statusText };
    }
    throw new ApiClientError(response.status, body);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  createReceipt(req: CreateReceiptRequest): Promise<CreateReceiptResponse> {
    return request<CreateReceiptResponse>("/api/v1/receipts", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  finalizeReceipt(receiptId: UUID): Promise<FinalizeReceiptResponse> {
    return request<FinalizeReceiptResponse>(
      `/api/v1/receipts/${receiptId}/finalize`,
      { method: "POST", body: JSON.stringify({}) },
    );
  },

  listReceipts(cursor?: string, limit = 20): Promise<ListReceiptsResponse> {
    const params = new URLSearchParams();
    if (cursor) params.set("cursor", cursor);
    params.set("limit", String(limit));
    return request<ListReceiptsResponse>(`/api/v1/receipts?${params}`);
  },

  getReceipt(receiptId: UUID): Promise<ReceiptDetail> {
    return request<ReceiptDetail>(`/api/v1/receipts/${receiptId}`);
  },

  retryProcessing(receiptId: UUID): Promise<RetryProcessingResponse> {
    return request<RetryProcessingResponse>(
      `/api/v1/receipts/${receiptId}/retry-processing`,
      { method: "POST", body: JSON.stringify({}) },
    );
  },

  getAssetDownloadCapability(
    receiptId: UUID,
    assetId: UUID,
  ): Promise<DownloadCapabilityResponse> {
    return request<DownloadCapabilityResponse>(
      `/api/v1/receipts/${receiptId}/assets/${assetId}/download`,
      { method: "POST", body: JSON.stringify({}) },
    );
  },
};

/**
 * Upload a single asset directly to GCS using the signed PUT URL.
 * Never logs or persists the URL — treat it as a bearer secret.
 */
export async function uploadAsset(
  uploadUrl: string,
  file: File,
  onProgress?: (loaded: number, total: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", uploadUrl);
    xhr.setRequestHeader("Content-Type", file.type);
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) onProgress(e.loaded, e.total);
      });
    }
    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new NetworkError(`Upload failed: HTTP ${xhr.status}`));
      }
    });
    xhr.addEventListener("error", () =>
      reject(new NetworkError("Upload network error")),
    );
    xhr.addEventListener("abort", () =>
      reject(new NetworkError("Upload aborted")),
    );
    xhr.send(file);
  });
}
