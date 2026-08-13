import { useCallback } from "react";
import { useDraft } from "./useDraft";
import { useSubmitReceipt } from "./useSubmitReceipt";
import { CaptureHome } from "./CaptureHome";
import { ReceiptDraft } from "./ReceiptDraft";
import { UploadProgressScreen } from "./UploadProgress";
import { SavedAcknowledgement } from "./SavedAcknowledgement";

export function CapturePage() {
  const draft = useDraft();
  const { submit, retryFinalize } = useSubmitReceipt();

  const handleSubmit = useCallback(async () => {
    draft.setPhase("uploading");
    await submit(draft.state.clientSubmissionKey, draft.state.images, {
      onUploadProgress: draft.setUploadProgress,
      onSaved: draft.setSaved,
      onError: draft.setError,
      onPhase: draft.setPhase,
    });
  }, [draft, submit]);

  const handleRetry = useCallback(async () => {
    draft.setPhase("uploading");
    await submit(draft.state.clientSubmissionKey, draft.state.images, {
      onUploadProgress: draft.setUploadProgress,
      onSaved: draft.setSaved,
      onError: draft.setError,
      onPhase: draft.setPhase,
    });
  }, [draft, submit]);

  const handleRetryFinalize = useCallback(async () => {
    await retryFinalize({
      onUploadProgress: draft.setUploadProgress,
      onSaved: draft.setSaved,
      onError: draft.setError,
      onPhase: draft.setPhase,
    });
  }, [draft, retryFinalize]);

  const { phase, images, uploadProgressMap, savedReceiptId, acknowledgedAt, errorMessage } =
    draft.state;

  if (phase === "saved" && savedReceiptId && acknowledgedAt) {
    return (
      <SavedAcknowledgement
        receiptId={savedReceiptId}
        acknowledgedAt={acknowledgedAt}
        onCaptureAnother={draft.reset}
      />
    );
  }

  if (phase === "uploading" || phase === "finalizing") {
    const uploadPhase = phase === "finalizing" ? "finalizing" : "uploading";
    return (
      <UploadProgressScreen
        progressMap={uploadProgressMap}
        totalImages={images.length}
        phase={uploadPhase}
        errorMessage={errorMessage}
        onRetry={handleRetry}
        onRetryFinalize={handleRetryFinalize}
      />
    );
  }

  if (phase === "idle") {
    return <CaptureHome onImages={draft.addImages} />;
  }

  // "drafting" phase (and any unhandled transition) shows the draft screen.
  return (
    <ReceiptDraft
      images={images}
      errorMessage={errorMessage}
      onAddMore={draft.addImages}
      onRemove={draft.removeImage}
      onReplace={draft.replaceImage}
      onSubmit={handleSubmit}
      onClearError={draft.clearError}
    />
  );
}
