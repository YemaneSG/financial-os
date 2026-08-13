import { Link } from "react-router-dom";

interface SavedAcknowledgementProps {
  receiptId: string;
  acknowledgedAt: string;
  onCaptureAnother: () => void;
}

export function SavedAcknowledgement({
  receiptId,
  acknowledgedAt,
  onCaptureAnother,
}: SavedAcknowledgementProps) {
  const shortId = receiptId.slice(0, 8);
  const formattedTime = new Date(acknowledgedAt).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <main className="saved-ack" aria-label="Receipt saved" aria-live="polite">
      <div className="saved-ack__icon" aria-hidden="true">✓</div>
      <h1 className="saved-ack__title">Receipt saved</h1>
      <p className="saved-ack__ref">
        Reference:{" "}
        <span className="saved-ack__id" aria-label={`Receipt ID starting ${shortId}`}>
          {shortId}…
        </span>
        <span className="saved-ack__time"> at {formattedTime}</span>
      </p>
      <p className="saved-ack__async">Processing in the background</p>

      <div className="saved-ack__actions">
        <button
          type="button"
          className="btn btn--primary"
          onClick={onCaptureAnother}
          aria-label="Capture another receipt"
        >
          Capture another
        </button>
        <Link
          to={`/receipts/${receiptId}`}
          className="btn btn--ghost"
          aria-label="View this receipt's processing status"
        >
          View receipt
        </Link>
      </div>
    </main>
  );
}
