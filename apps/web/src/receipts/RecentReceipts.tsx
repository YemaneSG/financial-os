import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { apiClient, ApiClientError } from "@/api/client";
import type { ReceiptListItem } from "@/api/types";
import { ProcessingStatusBadge, VerificationStatusBadge } from "@/components/StatusBadge";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { formatMinorUnits } from "@/receipts/formatters";

export function RecentReceipts() {
  const [receipts, setReceipts] = useState<ReceiptListItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (cursor?: string) => {
    try {
      const res = await apiClient.listReceipts(cursor);
      setReceipts((prev) => (cursor ? [...prev, ...res.receipts] : res.receipts));
      setNextCursor(res.next_cursor ?? null);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 401) {
        setError("Your session has expired. Please sign in again.");
      } else {
        setError("Could not load receipts. Please try again.");
      }
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    load().finally(() => setLoading(false));
  }, [load]);

  const handleLoadMore = useCallback(async () => {
    if (!nextCursor) return;
    setLoadingMore(true);
    await load(nextCursor);
    setLoadingMore(false);
  }, [load, nextCursor]);

  return (
    <main className="recent-receipts" aria-label="Recent receipts">
      <header className="recent-receipts__header">
        <Link to="/" className="btn btn--ghost btn--small" aria-label="Back to capture">
          ← Back
        </Link>
        <h1 className="recent-receipts__title">Recent receipts</h1>
      </header>

      {loading && <LoadingSpinner label="Loading receipts…" />}

      {error && (
        <div role="alert" className="alert alert--error">
          {error}
        </div>
      )}

      {!loading && !error && receipts.length === 0 && (
        <p className="recent-receipts__empty">No receipts yet. Photograph your first one.</p>
      )}

      <ul className="receipts-list" role="list">
        {receipts.map((r) => (
          <li key={r.receipt_id} className="receipts-list__item" role="listitem">
            <Link
              to={`/receipts/${r.receipt_id}`}
              className="receipts-list__link"
              aria-label={receiptLabel(r)}
            >
              <div className="receipts-list__meta">
                <span className="receipts-list__merchant">
                  {r.current_revision?.merchant_normalized ?? "Processing receipt"}
                </span>
                <span className="receipts-list__amount">
                  {r.current_revision?.total_minor != null
                    ? formatMinorUnits(
                        r.current_revision.total_minor,
                        r.current_revision.currency,
                      )
                    : ""}
                </span>
              </div>
              <div className="receipts-list__status">
                <ProcessingStatusBadge status={r.processing_status} />
                <VerificationStatusBadge status={r.verification_status} />
              </div>
              <div className="receipts-list__detail">
                <span className="receipts-list__time">
                  {new Date(r.created_at).toLocaleString()}
                </span>
                <span className="receipts-list__count">
                  {r.expected_asset_count} image{r.expected_asset_count !== 1 ? "s" : ""}
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>

      {nextCursor && (
        <button
          type="button"
          className="btn btn--ghost"
          onClick={handleLoadMore}
          aria-label="Load more receipts"
          disabled={loadingMore}
        >
          {loadingMore ? "Loading…" : "Load more"}
        </button>
      )}
    </main>
  );
}

function receiptLabel(r: ReceiptListItem): string {
  const merchant = r.current_revision?.merchant_normalized ?? "Processing receipt";
  const date = new Date(r.created_at).toLocaleDateString();
  return `${merchant}, ${date}, ${r.processing_status}`;
}
