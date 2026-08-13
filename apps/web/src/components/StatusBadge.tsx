import type { ProcessingStatus, VerificationStatus } from "@/api/types";

const PROCESSING_LABELS: Record<ProcessingStatus, string> = {
  reserved: "Preparing",
  uploading: "Uploading",
  uploaded: "Uploaded",
  queued: "Queued",
  processing: "Processing",
  extracted: "Extracted",
  retryable_failed: "Processing failed — retry available",
  failed: "Processing failed",
  abandoned: "Abandoned",
};

const PROCESSING_ICONS: Record<ProcessingStatus, string> = {
  reserved: "⏳",
  uploading: "⬆",
  uploaded: "✓",
  queued: "⏳",
  processing: "⚙",
  extracted: "✓",
  retryable_failed: "⚠",
  failed: "✗",
  abandoned: "✗",
};

const VERIFICATION_LABELS: Record<VerificationStatus, string> = {
  unreviewed: "Unreviewed",
  system_validated: "System validated",
  needs_review: "Needs review",
  human_verified: "Verified",
};

export function ProcessingStatusBadge({
  status,
}: {
  status: ProcessingStatus;
}) {
  return (
    <span
      className={`status-badge status-badge--processing status-badge--${status}`}
      aria-label={`Processing: ${PROCESSING_LABELS[status]}`}
    >
      <span aria-hidden="true">{PROCESSING_ICONS[status]}</span>{" "}
      {PROCESSING_LABELS[status]}
    </span>
  );
}

export function VerificationStatusBadge({
  status,
}: {
  status: VerificationStatus;
}) {
  return (
    <span
      className={`status-badge status-badge--verification status-badge--${status}`}
      aria-label={`Verification: ${VERIFICATION_LABELS[status]}`}
    >
      {VERIFICATION_LABELS[status]}
    </span>
  );
}
