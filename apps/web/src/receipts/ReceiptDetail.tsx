import { useEffect, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { apiClient, ApiClientError } from "@/api/client";
import type { ReceiptDetail as ReceiptDetailType, AssetSummary } from "@/api/types";
import { ProcessingStatusBadge, VerificationStatusBadge } from "@/components/StatusBadge";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { formatMinorUnits } from "./formatters";
import { HumanReviewForm } from "./HumanReviewForm";

export function ReceiptDetailPage() {
  const { receiptId } = useParams<{ receiptId: string }>();
  const [receipt, setReceipt] = useState<ReceiptDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);
  const [assetUrls, setAssetUrls] = useState<Record<string, string>>({});
  const [showReviewForm, setShowReviewForm] = useState(false);

  const load = useCallback(async () => {
    if (!receiptId) return;
    try {
      const data = await apiClient.getReceipt(receiptId);
      setReceipt(data);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setError("Receipt not found.");
      } else if (err instanceof ApiClientError && err.status === 401) {
        setError("Your session has expired. Please sign in again.");
      } else {
        setError("Could not load receipt. Please try again.");
      }
    }
  }, [receiptId]);

  useEffect(() => {
    setLoading(true);
    load().finally(() => setLoading(false));
  }, [load]);

  const loadAsset = useCallback(
    async (asset: AssetSummary) => {
      if (!receiptId) return;
      if (assetUrls[asset.asset_id]) return;
      try {
        const res = await apiClient.getAssetDownloadCapability(receiptId, asset.asset_id);
        // URL is a bearer secret — stored only in local component state, never in
        // service-worker cache, localStorage, or analytics (APP-02, OBJ-02).
        setAssetUrls((prev) => ({ ...prev, [asset.asset_id]: res.download_url }));
      } catch {
        // Non-critical — image will show as unavailable.
      }
    },
    [receiptId, assetUrls],
  );

  const handleRetry = useCallback(async () => {
    if (!receiptId) return;
    setRetrying(true);
    setRetryError(null);
    try {
      await apiClient.retryProcessing(receiptId);
      await load();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setRetryError(err.body.message || "Retry failed.");
      } else {
        setRetryError("Retry failed. Please try again.");
      }
    } finally {
      setRetrying(false);
    }
  }, [receiptId, load]);

  const canRetry = receipt?.processing_status === "retryable_failed";

  if (loading) return <LoadingSpinner label="Loading receipt…" />;

  if (error) {
    return (
      <main className="receipt-detail" aria-label="Receipt detail">
        <Link to="/receipts" className="btn btn--ghost btn--small">
          ← Receipts
        </Link>
        <div role="alert" className="alert alert--error">
          {error}
        </div>
      </main>
    );
  }

  if (!receipt) return null;

  const rev = receipt.current_revision;

  const canCorrect =
    (receipt.verification_status === "needs_review" ||
      receipt.verification_status === "system_validated") &&
    receipt.current_revision != null;

  return (
    <main className="receipt-detail" aria-label="Receipt detail">
      {showReviewForm && receipt.current_revision?.revision_id ? (
        <HumanReviewForm
          receiptId={receipt.receipt_id}
          currentRevisionId={receipt.current_revision.revision_id}
          initialData={receipt}
          onSuccess={async () => {
            setShowReviewForm(false);
            await load();
          }}
          onCancel={() => setShowReviewForm(false)}
        />
      ) : (
        <>
          <header className="receipt-detail__header">
            <Link to="/receipts" className="btn btn--ghost btn--small" aria-label="Back to receipts">
              ← Receipts
            </Link>
            <h1 className="receipt-detail__title">
              {rev?.merchant_normalized ?? "Receipt"}
            </h1>
          </header>

          <section aria-label="Status">
            <ProcessingStatusBadge status={receipt.processing_status} />
            <VerificationStatusBadge status={receipt.verification_status} />

            {receipt.safe_error_code && (
              <p className="receipt-detail__error-code" role="status">
                Failure code: <code>{receipt.safe_error_code}</code>
              </p>
            )}

            {canCorrect && (
              <div className="receipt-detail__review-action">
                <button
                  type="button"
                  className="btn btn--primary"
                  onClick={() => setShowReviewForm(true)}
                  aria-label="Correct this receipt"
                >
                  Correct this receipt
                </button>
              </div>
            )}

            {canRetry && (
              <div className="receipt-detail__retry">
                {retryError && (
                  <div role="alert" className="alert alert--error">
                    {retryError}
                  </div>
                )}
                <button
                  type="button"
                  className="btn btn--primary btn--small"
                  onClick={handleRetry}
                  disabled={retrying}
                  aria-label="Retry processing this receipt"
                >
                  {retrying ? "Retrying…" : "Retry processing"}
                </button>
              </div>
            )}
          </section>

      {/* Images — loaded on demand via authenticated download capability */}
      {receipt.assets && receipt.assets.length > 0 && (
        <section aria-label="Receipt images" className="receipt-detail__assets">
          <h2 className="receipt-detail__section-title">Images</h2>
          <div className="asset-grid">
            {receipt.assets
              .slice()
              .sort((a, b) => a.ordinal - b.ordinal)
              .map((asset) => {
                const url = assetUrls[asset.asset_id];
                return (
                  <div
                    key={asset.asset_id}
                    className="asset-item"
                    aria-label={`Image ${asset.ordinal}`}
                  >
                    {url ? (
                      <img
                        src={url}
                        alt={`Receipt image ${asset.ordinal}`}
                        className="asset-item__img"
                      />
                    ) : (
                      <button
                        type="button"
                        className="asset-item__load-btn"
                        aria-label={`Load image ${asset.ordinal}`}
                        onClick={() => void loadAsset(asset)}
                      >
                        Load image {asset.ordinal}
                      </button>
                    )}
                  </div>
                );
              })}
          </div>
        </section>
      )}

      {/* Extracted data */}
      {rev && (
        <section aria-label="Extracted data" className="receipt-detail__revision">
          <h2 className="receipt-detail__section-title">Extracted data</h2>
          <dl className="receipt-detail__fields">
            {rev.merchant_normalized && (
              <>
                <dt>Merchant</dt>
                <dd>{rev.merchant_normalized}</dd>
              </>
            )}
            {rev.purchase_datetime && (
              <>
                <dt>Purchase date</dt>
                <dd>{new Date(rev.purchase_datetime).toLocaleString()}</dd>
              </>
            )}
            {rev.subtotal_minor != null && (
              <>
                <dt>Subtotal</dt>
                <dd>{formatMinorUnits(rev.subtotal_minor, rev.currency)}</dd>
              </>
            )}
            {rev.tax_minor != null && (
              <>
                <dt>Tax</dt>
                <dd>{formatMinorUnits(rev.tax_minor, rev.currency)}</dd>
              </>
            )}
            {rev.tip_minor != null && (
              <>
                <dt>Tip</dt>
                <dd>{formatMinorUnits(rev.tip_minor, rev.currency)}</dd>
              </>
            )}
            {rev.discount_minor != null && (
              <>
                <dt>Discount</dt>
                <dd>{formatMinorUnits(rev.discount_minor, rev.currency)}</dd>
              </>
            )}
            {rev.total_minor != null && (
              <>
                <dt>Total</dt>
                <dd>
                  <strong>{formatMinorUnits(rev.total_minor, rev.currency)}</strong>
                </dd>
              </>
            )}
            {rev.overall_confidence != null && (
              <>
                <dt>Confidence</dt>
                <dd>{Math.round(rev.overall_confidence * 100)}%</dd>
              </>
            )}
          </dl>
        </section>
      )}

      {/* Line items */}
      {receipt.line_items && receipt.line_items.length > 0 && (
        <section aria-label="Line items" className="receipt-detail__line-items">
          <h2 className="receipt-detail__section-title">Line items</h2>
          <ul role="list" className="line-items-list">
            {receipt.line_items
              .slice()
              .sort((a, b) => a.ordinal - b.ordinal)
              .map((item) => (
                <li key={item.ordinal} className="line-items-list__item">
                  <span className="line-item__desc">
                    {/* Raw text rendered as escaped plain text — APP-01 */}
                    {item.normalized_description ?? item.raw_description}
                  </span>
                  {item.quantity && (
                    <span className="line-item__qty">
                      × {item.quantity} {item.unit ?? ""}
                    </span>
                  )}
                  {item.line_total_minor != null && (
                    <span className="line-item__total">
                      {formatMinorUnits(item.line_total_minor, receipt.current_revision?.currency)}
                    </span>
                  )}
                </li>
              ))}
          </ul>
        </section>
      )}

      {/* Validation findings */}
      {receipt.validation_findings && receipt.validation_findings.length > 0 && (
        <section aria-label="Validation" className="receipt-detail__validation">
          <h2 className="receipt-detail__section-title">Validation</h2>
          <ul role="list" className="validation-list">
            {receipt.validation_findings.map((f) => (
              <li
                key={f.check_code}
                className={`validation-list__item validation-list__item--${f.outcome}`}
              >
                <code>{f.check_code}</code>: {f.outcome}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Provenance — safe summary only, no credentials or prompt text */}
      {receipt.provenance_summary && (
        <section aria-label="Extraction provenance" className="receipt-detail__provenance">
          <h2 className="receipt-detail__section-title">Provenance</h2>
          <dl className="receipt-detail__fields">
            <dt>Provider</dt>
            <dd>{receipt.provenance_summary.provider}</dd>
            <dt>Model</dt>
            <dd>{receipt.provenance_summary.model_id}</dd>
            <dt>Attempts</dt>
            <dd>{receipt.provenance_summary.attempt_count}</dd>
          </dl>
        </section>
      )}
        </>
      )}
    </main>
  );
}
