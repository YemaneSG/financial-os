import { useCallback, useRef } from "react";
import { apiClient, uploadAsset, ApiClientError, NetworkError } from "@/api/client";
import type { DraftImage, UploadProgress } from "./useDraft";
import { receiptMimeType } from "./receiptFile";

interface SubmitCallbacks {
  onUploadProgress: (progress: UploadProgress) => void;
  onSaved: (receiptId: string, acknowledgedAt: string) => void;
  onError: (message: string) => void;
  onPhase: (phase: "uploading" | "finalizing") => void;
}

// Tracks which ordinals already uploaded successfully so retries skip them.
type UploadState = "pending" | "done" | "failed";

interface PendingSubmission {
  receiptId: string;
  clientSubmissionKey: string;
  assetStates: Map<number, UploadState>; // keyed by ordinal
}

export function useSubmitReceipt() {
  const pendingRef = useRef<PendingSubmission | null>(null);

  const submit = useCallback(
    async (
      clientSubmissionKey: string,
      images: DraftImage[],
      callbacks: SubmitCallbacks,
    ) => {
      const { onUploadProgress, onSaved, onError, onPhase } = callbacks;
      onPhase("uploading");

      const mimeTypes = images.map((image) => receiptMimeType(image.file));
      if (mimeTypes.some((mimeType) => mimeType === null)) {
        onError("One or more images have an unsupported file type.");
        return;
      }

      // Always POST createReceipt — idempotent by client_submission_key.
      // Server returns same receipt with FRESH upload capabilities on replay.
      let receiptId: string;
      let capabilities;
      try {
        const res = await apiClient.createReceipt({
          client_submission_key: clientSubmissionKey,
          expected_asset_count: images.length,
          assets: images.map((img, i) => ({
            ordinal: i + 1,
            declared_mime_type: mimeTypes[i] as string,
            byte_size: img.file.size,
          })),
        });
        receiptId = res.receipt_id;
        capabilities = res.upload_capabilities;
      } catch (err) {
        onError(friendlyError(err, "Could not create receipt. Check your connection."));
        return;
      }

      // Initialize or reuse asset state to skip already-uploaded ordinals.
      if (
        !pendingRef.current ||
        pendingRef.current.clientSubmissionKey !== clientSubmissionKey
      ) {
        pendingRef.current = {
          receiptId,
          clientSubmissionKey,
          assetStates: new Map(images.map((_, i) => [i + 1, "pending"])),
        };
      } else {
        // Retain successes from prior attempt; reset failures to pending.
        for (const [ordinal, state] of pendingRef.current.assetStates) {
          if (state !== "done") pendingRef.current.assetStates.set(ordinal, "pending");
        }
      }

      const assetStates = pendingRef.current.assetStates;
      const capByOrdinal = new Map(capabilities.map((c) => [c.ordinal, c]));

      // Upload only pending assets (not already done).
      const uploadResults = await Promise.all(
        images.map(async (img, i) => {
          const ordinal = i + 1;
          if (assetStates.get(ordinal) === "done") return true;

          const cap = capByOrdinal.get(ordinal);
          if (!cap) {
            assetStates.set(ordinal, "failed");
            return false;
          }

          const progressBase = { assetId: cap.asset_id, ordinal, total: img.file.size };
          onUploadProgress({ ...progressBase, loaded: 0, done: false, error: null });

          try {
            const signedContentType = cap.allowed_mime_types[0] ?? mimeTypes[i];
            if (!signedContentType) throw new NetworkError("Upload type is unavailable");
            await uploadAsset(cap.upload_url, img.file, signedContentType, (loaded, total) => {
              onUploadProgress({ ...progressBase, loaded, total, done: false, error: null });
            });
            onUploadProgress({ ...progressBase, loaded: img.file.size, done: true, error: null });
            assetStates.set(ordinal, "done");
            return true;
          } catch (err) {
            const msg = err instanceof NetworkError ? err.message : "Upload failed";
            onUploadProgress({ ...progressBase, loaded: 0, done: false, error: msg });
            assetStates.set(ordinal, "failed");
            return false;
          }
        }),
      );

      const failCount = uploadResults.filter((ok) => !ok).length;
      if (failCount > 0) {
        onError(
          `${failCount} image${failCount > 1 ? "s" : ""} could not be uploaded. Tap Retry to try again.`,
        );
        return;
      }

      // All assets uploaded — finalize for durable acknowledgement.
      onPhase("finalizing");
      try {
        const finalizeRes = await apiClient.finalizeReceipt(receiptId);
        pendingRef.current = null;
        onSaved(finalizeRes.receipt_id, finalizeRes.acknowledged_at);
      } catch (err) {
        onError(friendlyError(err, "Finishing save failed. Tap 'Retry finish' to try again."));
      }
    },
    [],
  );

  const retryFinalize = useCallback(
    async (callbacks: SubmitCallbacks) => {
      const pending = pendingRef.current;
      if (!pending) {
        callbacks.onError("Nothing to retry.");
        return;
      }
      callbacks.onPhase("finalizing");
      try {
        const res = await apiClient.finalizeReceipt(pending.receiptId);
        pendingRef.current = null;
        callbacks.onSaved(res.receipt_id, res.acknowledged_at);
      } catch (err) {
        callbacks.onError(friendlyError(err, "Finishing save failed. Please try again."));
      }
    },
    [],
  );

  return { submit, retryFinalize };
}

function friendlyError(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 401 || err.status === 403) {
      return "Your session has expired. Please sign in again.";
    }
    if (err.status === 422) {
      return `Validation error: ${err.body.message}`;
    }
    return err.body.message || fallback;
  }
  if (err instanceof NetworkError) return err.message;
  return fallback;
}
