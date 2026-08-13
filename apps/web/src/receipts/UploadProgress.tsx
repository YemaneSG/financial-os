import type { UploadProgress as UploadProgressType } from "./useDraft";

interface UploadProgressProps {
  progressMap: Record<string, UploadProgressType>;
  totalImages: number;
  phase: "uploading" | "finalizing";
  errorMessage: string | null;
  onRetry: () => void;
  onRetryFinalize: () => void;
}

export function UploadProgressScreen({
  progressMap,
  totalImages,
  phase,
  errorMessage,
  onRetry,
  onRetryFinalize,
}: UploadProgressProps) {
  const items = Object.values(progressMap).sort((a, b) => a.ordinal - b.ordinal);
  const doneCount = items.filter((p) => p.done).length;
  const hasUploadError = items.some((p) => p.error);

  const statusLabel =
    phase === "finalizing"
      ? "Finishing save…"
      : errorMessage
        ? "Upload paused"
        : `Uploading ${doneCount} of ${totalImages}`;

  return (
    <main className="upload-progress" aria-label="Upload progress" aria-live="polite" aria-atomic="false">
      <h1 className="upload-progress__title">{statusLabel}</h1>

      <ul className="upload-progress__list" role="list">
        {items.map((item) => {
          const pct = item.total > 0 ? Math.round((item.loaded / item.total) * 100) : 0;
          return (
            <li key={item.assetId} className="upload-progress__item">
              <span className="upload-progress__label">
                Image {item.ordinal}
                {item.done && <span className="sr-only"> — uploaded</span>}
                {item.error && <span className="sr-only"> — failed</span>}
              </span>
              {item.error ? (
                <span
                  className="upload-progress__error"
                  role="img"
                  aria-label="Upload failed"
                >
                  ⚠ Failed
                </span>
              ) : item.done ? (
                <span
                  className="upload-progress__done"
                  role="img"
                  aria-label="Uploaded"
                >
                  ✓ Done
                </span>
              ) : (
                <progress
                  className="upload-progress__bar"
                  value={pct}
                  max={100}
                  aria-label={`Image ${item.ordinal}: ${pct}%`}
                />
              )}
            </li>
          );
        })}
      </ul>

      {phase === "finalizing" && !errorMessage && (
        <p className="upload-progress__hint" aria-live="polite">
          Verifying evidence and saving receipt…
        </p>
      )}

      {errorMessage && (
        <div role="alert" className="alert alert--error">
          <p>{errorMessage}</p>
          <div className="alert__actions">
            {hasUploadError && (
              <button type="button" className="btn btn--primary" onClick={onRetry}>
                Retry upload
              </button>
            )}
            {!hasUploadError && (
              <button type="button" className="btn btn--primary" onClick={onRetryFinalize}>
                Retry finish
              </button>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
