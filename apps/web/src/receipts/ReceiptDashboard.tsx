import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiClient, ApiClientError } from "@/api/client";
import type { ReceiptListItem } from "@/api/types";
import { formatMinorUnits } from "@/receipts/formatters";

interface DashboardSnapshot {
  total: number;
  processing: number;
  needsReview: number;
  failed: number;
  recent: ReceiptListItem[];
}

type DashboardState =
  | { status: "loading" }
  | { status: "ready"; snapshot: DashboardSnapshot }
  | { status: "error"; message: string };

export function ReceiptDashboard() {
  const [state, setState] = useState<DashboardState>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const [recent, all, processing, needsReview, failed] = await Promise.all([
        apiClient.listReceipts(undefined, 5),
        apiClient.searchReceipts({ limit: 1 }),
        apiClient.searchReceipts({
          processing_status: ["queued", "processing"],
          limit: 1,
        }),
        apiClient.searchReceipts({ verification_status: ["needs_review"], limit: 1 }),
        apiClient.searchReceipts({
          processing_status: ["retryable_failed", "failed", "abandoned"],
          limit: 1,
        }),
      ]);

      setState({
        status: "ready",
        snapshot: {
          total: all.total_count,
          processing: processing.total_count,
          needsReview: needsReview.total_count,
          failed: failed.total_count,
          recent: recent.receipts,
        },
      });
    } catch (error) {
      const message =
        error instanceof ApiClientError && (error.status === 401 || error.status === 403)
          ? "Your receipt session needs to be refreshed."
          : "Receipt activity could not be refreshed. Capture still works.";
      setState({ status: "error", message });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="receipt-dashboard" aria-labelledby="dashboard-heading">
      <div className="premium-section-heading">
        <div>
          <p className="premium-kicker">Your data</p>
          <h2 id="dashboard-heading">Receipt dashboard</h2>
        </div>
        <button
          type="button"
          className="dashboard-refresh"
          onClick={() => void load()}
          aria-label="Refresh receipt dashboard"
          disabled={state.status === "loading"}
        >
          <span aria-hidden="true">↻</span>
          Refresh
        </button>
      </div>

      {state.status === "loading" && (
        <div className="dashboard-loading" role="status">
          <span className="dashboard-loading__pulse" aria-hidden="true" />
          Checking your receipt data…
        </div>
      )}

      {state.status === "error" && (
        <div className="dashboard-error" role="alert">
          <strong>Dashboard unavailable</strong>
          <span>{state.message}</span>
          <button type="button" onClick={() => void load()}>Try again</button>
        </div>
      )}

      {state.status === "ready" && (
        <>
          <div className="dashboard-metrics" aria-label="Receipt ingestion summary">
            <Metric value={state.snapshot.total} label="Captured" tone="calm" />
            <Metric value={state.snapshot.processing} label="Processing" tone="active" />
            <Metric value={state.snapshot.needsReview} label="Needs review" tone="attention" />
            <Metric value={state.snapshot.failed} label="Failed" tone="danger" />
          </div>

          <div className="dashboard-recent-heading">
            <h3>Recent receipts</h3>
            <Link to="/receipts">View all</Link>
          </div>

          {state.snapshot.recent.length === 0 ? (
            <div className="dashboard-empty">
              <span aria-hidden="true">⌁</span>
              <strong>Your history starts here</strong>
              <p>Your first durably saved receipt will appear in this dashboard.</p>
            </div>
          ) : (
            <ul className="dashboard-receipts" aria-label="Recent receipt activity">
              {state.snapshot.recent.map((receipt) => (
                <li key={receipt.receipt_id}>
                  <Link to={`/receipts/${receipt.receipt_id}`} aria-label={receiptLabel(receipt)}>
                    <span className="dashboard-merchant-mark" aria-hidden="true">
                      {merchantName(receipt).slice(0, 1).toUpperCase()}
                    </span>
                    <span className="dashboard-receipt-copy">
                      <strong>{merchantName(receipt)}</strong>
                      <span>{formatReceiptDate(receipt)}</span>
                    </span>
                    <span className="dashboard-receipt-value">
                      <strong>{receiptAmount(receipt)}</strong>
                      <span data-tone={receiptTone(receipt)}>{receiptStatus(receipt)}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}

function Metric({ value, label, tone }: { value: number; label: string; tone: string }) {
  return (
    <article className="dashboard-metric" data-tone={tone}>
      <strong>{value.toLocaleString()}</strong>
      <span>{label}</span>
    </article>
  );
}

function merchantName(receipt: ReceiptListItem): string {
  return receipt.current_revision?.merchant_normalized ?? "Processing receipt";
}

function receiptAmount(receipt: ReceiptListItem): string {
  const total = receipt.current_revision?.total_minor;
  if (total == null) return "—";
  return formatMinorUnits(total, receipt.current_revision?.currency);
}

function formatReceiptDate(receipt: ReceiptListItem): string {
  const value = receipt.current_revision?.purchase_datetime ?? receipt.acknowledged_at ?? receipt.created_at;
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));
}

function receiptStatus(receipt: ReceiptListItem): string {
  if (receipt.processing_status === "failed" || receipt.processing_status === "retryable_failed") {
    return "Needs attention";
  }
  if (receipt.verification_status === "needs_review") return "Needs review";
  if (receipt.processing_status === "extracted") return "Ready";
  if (receipt.processing_status === "processing") return "Processing";
  return "Saved";
}

function receiptTone(receipt: ReceiptListItem): string {
  if (receipt.processing_status === "failed" || receipt.processing_status === "retryable_failed") {
    return "danger";
  }
  if (receipt.verification_status === "needs_review") return "attention";
  if (receipt.processing_status === "extracted") return "ready";
  return "active";
}

function receiptLabel(receipt: ReceiptListItem): string {
  return `${merchantName(receipt)}, ${receiptAmount(receipt)}, ${receiptStatus(receipt)}`;
}
