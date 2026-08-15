/**
 * ReceiptsDiscovery — Mobile-first receipt search and discovery view.
 *
 * Features:
 *  - Pinned "Search merchant or item" field (query in POST body, never URL)
 *  - Quick filter chips: needs-review, duplicates, verified
 *  - Filter sheet: date range, amount range, processing/verification/dedup status, sort
 *  - Removable active-filter chips + clear-all
 *  - Total result count with live announcement
 *  - Purchase-month grouping by effective date
 *  - Matched-line-item explanation when a line item caused the match
 *  - Load more (keyset cursor — no infinite scroll)
 *  - Restoration of search, filters, loaded pages, and scroll position on back-navigation
 *  - Accessibility: labeled inputs, keyboard operation, 44 px touch targets, focus ring, live region
 */

import {
  type RefObject,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import { apiClient, ApiClientError } from "@/api/client";
import type {
  DeduplicationStatus,
  ProcessingStatus,
  SearchReceiptItem,
  SearchReceiptsRequest,
  SearchSortOrder,
  VerificationStatus,
} from "@/api/types";
import { ProcessingStatusBadge, VerificationStatusBadge } from "@/components/StatusBadge";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { formatMinorUnits } from "@/receipts/formatters";

// ── Effective-date helper ──────────────────────────────────────────────────────

function effectiveDate(r: SearchReceiptItem): Date {
  const raw =
    r.current_revision?.purchase_datetime ??
    r.captured_at ??
    r.acknowledged_at ??
    r.created_at;
  return new Date(raw);
}

function monthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(key: string): string {
  const [year, month] = key.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleString("default", {
    month: "long",
    year: "numeric",
  });
}

function localDayBoundaryIso(value: string, endOfDay: boolean): string {
  const suffix = endOfDay ? "T23:59:59.999" : "T00:00:00.000";
  return new Date(`${value}${suffix}`).toISOString();
}

function amountToMinorUnits(value: string): number | undefined {
  if (!value) return undefined;
  const amount = Number(value);
  return Number.isFinite(amount) && amount >= 0 ? Math.round(amount * 100) : undefined;
}

// ── State persistence (module-level, survives React unmount) ───────────────────

interface DiscoveryState {
  query: string;
  quickFilter: QuickFilter | null;
  filters: ActiveFilters;
  receipts: SearchReceiptItem[];
  totalCount: number;
  cursors: (string | null)[];
  scrollY: number;
  hasRestored: boolean;
}

type QuickFilter = "needs_review" | "duplicates" | "verified";

interface ActiveFilters {
  sort: SearchSortOrder;
  processingStatus: ProcessingStatus[];
  verificationStatus: VerificationStatus[];
  deduplicationStatus: DeduplicationStatus[];
  dateFrom: string;
  dateTo: string;
  amountMin: string;
  amountMax: string;
}

const DEFAULT_FILTERS: ActiveFilters = {
  sort: "effective_date_desc",
  processingStatus: [],
  verificationStatus: [],
  deduplicationStatus: [],
  dateFrom: "",
  dateTo: "",
  amountMin: "",
  amountMax: "",
};

const _store: DiscoveryState = {
  query: "",
  quickFilter: null,
  filters: { ...DEFAULT_FILTERS },
  receipts: [],
  totalCount: 0,
  cursors: [null],
  scrollY: 0,
  hasRestored: false,
};

/** Reset module-level state — used only by test suites. */
// eslint-disable-next-line react-refresh/only-export-components
export function resetDiscoveryStore(): void {
  _store.query = "";
  _store.quickFilter = null;
  _store.filters = { ...DEFAULT_FILTERS };
  _store.receipts = [];
  _store.totalCount = 0;
  _store.cursors = [null];
  _store.scrollY = 0;
  _store.hasRestored = false;
}

// ── Filter-to-API mapping ──────────────────────────────────────────────────────

function buildRequest(
  query: string,
  quickFilter: QuickFilter | null,
  filters: ActiveFilters,
  cursor: string | null,
  limit: number,
): SearchReceiptsRequest {
  const req: SearchReceiptsRequest = {
    sort: filters.sort,
    limit,
    cursor: cursor ?? undefined,
  };

  if (query.trim()) req.query = query.trim();

  if (filters.processingStatus.length) req.processing_status = filters.processingStatus;

  // A quick filter overrides only its own status axis. All other advanced
  // filters remain composed with it.
  if (quickFilter === "needs_review") {
    req.verification_status = ["needs_review"];
  } else if (quickFilter === "verified") {
    req.verification_status = ["human_verified"];
  } else if (quickFilter === "duplicates") {
    req.deduplication_status = ["suspected_duplicate", "confirmed_duplicate"];
  } else {
    if (filters.verificationStatus.length) req.verification_status = filters.verificationStatus;
    if (filters.deduplicationStatus.length) req.deduplication_status = filters.deduplicationStatus;
  }

  if (filters.dateFrom) req.date_from = localDayBoundaryIso(filters.dateFrom, false);
  if (filters.dateTo) req.date_to = localDayBoundaryIso(filters.dateTo, true);
  const amountMin = amountToMinorUnits(filters.amountMin);
  const amountMax = amountToMinorUnits(filters.amountMax);
  if (amountMin !== undefined) req.amount_min_minor = amountMin;
  if (amountMax !== undefined) req.amount_max_minor = amountMax;

  return req;
}

function activeFilterCount(quickFilter: QuickFilter | null, filters: ActiveFilters): number {
  return (
    (quickFilter ? 1 : 0) +
    filters.processingStatus.length +
    filters.verificationStatus.length +
    filters.deduplicationStatus.length +
    (filters.dateFrom || filters.dateTo ? 1 : 0) +
    (filters.amountMin || filters.amountMax ? 1 : 0) +
    (filters.sort !== "effective_date_desc" ? 1 : 0)
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20;

export function ReceiptsDiscovery() {
  const [query, setQuery] = useState(() => _store.query);
  const [quickFilter, setQuickFilter] = useState<QuickFilter | null>(() => _store.quickFilter);
  const [filters, setFilters] = useState<ActiveFilters>(() => ({ ..._store.filters }));
  const [showFilterSheet, setShowFilterSheet] = useState(false);
  const [draftFilters, setDraftFilters] = useState<ActiveFilters>({ ...DEFAULT_FILTERS });

  const [receipts, setReceipts] = useState<SearchReceiptItem[]>(() => _store.receipts);
  const [totalCount, setTotalCount] = useState(() => _store.totalCount);
  const [cursors, setCursors] = useState<(string | null)[]>(() => [..._store.cursors]);

  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const liveRegionRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestSequenceRef = useRef(0);

  // ── Scroll restoration ────────────────────────────────────────────────────

  useLayoutEffect(() => {
    if (_store.hasRestored && _store.receipts.length > 0) {
      window.scrollTo(0, _store.scrollY);
    }
  }, []);

  useEffect(() => {
    const onScroll = () => {
      _store.scrollY = window.scrollY;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // ── Keep restoration state current; mark restorable on unmount ───────────

  useEffect(() => {
    _store.query = query;
    _store.quickFilter = quickFilter;
    _store.filters = { ...filters };
    _store.receipts = receipts;
    _store.totalCount = totalCount;
    _store.cursors = cursors;
  }, [query, quickFilter, filters, receipts, totalCount, cursors]);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      _store.hasRestored = true;
    };
  }, []);

  // ── Search ────────────────────────────────────────────────────────────────

  const doSearch = useCallback(
    async (
      q: string,
      qf: QuickFilter | null,
      f: ActiveFilters,
      cursor: string | null,
      append: boolean,
    ) => {
      const requestSequence = ++requestSequenceRef.current;
      const req = buildRequest(q, qf, f, cursor, PAGE_SIZE);
      append ? setLoadingMore(true) : setLoading(true);
      try {
        const res = await apiClient.searchReceipts(req);
        if (requestSequence !== requestSequenceRef.current) return;
        setReceipts((prev) => (append ? [...prev, ...res.receipts] : res.receipts));
        setTotalCount(res.total_count);
        setCursors((prev) => {
          const next = append ? [...prev, res.next_cursor ?? null] : [null, res.next_cursor ?? null];
          return next;
        });
        if (liveRegionRef.current) {
          liveRegionRef.current.textContent =
            res.total_count === 1 ? "1 receipt found" : `${res.total_count} receipts found`;
        }
        setError(null);
      } catch (err) {
        if (requestSequence !== requestSequenceRef.current) return;
        if (err instanceof ApiClientError && err.status === 401) {
          setError("Your session has expired. Please sign in again.");
        } else {
          setError("Could not load receipts. Please try again.");
        }
      } finally {
        if (requestSequence === requestSequenceRef.current) {
          append ? setLoadingMore(false) : setLoading(false);
        }
      }
    },
    [],
  );

  // Initial load or restoration
  useEffect(() => {
    if (_store.hasRestored && _store.receipts.length > 0) {
      // State already restored from store; replay remaining pages if any
      return;
    }
    void doSearch(query, quickFilter, filters, null, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-search when query/filters change (debounced for text input)
  const triggerSearch = useCallback(
    (q: string, qf: QuickFilter | null, f: ActiveFilters) => {
      setCursors([null]);
      void doSearch(q, qf, f, null, false);
    },
    [doSearch],
  );

  const handleQueryChange = (val: string) => {
    setQuery(val);
    _store.hasRestored = false;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      triggerSearch(val, quickFilter, filters);
    }, 350);
  };

  const handleQuickFilter = (qf: QuickFilter | null) => {
    const next = quickFilter === qf ? null : qf;
    const nextFilters = { ...filters };
    if (next === "needs_review" || next === "verified") {
      nextFilters.verificationStatus = [];
    } else if (next === "duplicates") {
      nextFilters.deduplicationStatus = [];
    }
    setFilters(nextFilters);
    setQuickFilter(next);
    _store.hasRestored = false;
    triggerSearch(query, next, nextFilters);
  };

  const handleApplyFilters = (f: ActiveFilters) => {
    setFilters(f);
    setShowFilterSheet(false);
    _store.hasRestored = false;
    triggerSearch(query, quickFilter, f);
  };

  const handleClearAll = () => {
    setQuery("");
    setQuickFilter(null);
    setFilters({ ...DEFAULT_FILTERS });
    _store.hasRestored = false;
    triggerSearch("", null, { ...DEFAULT_FILTERS });
  };

  const handleLoadMore = useCallback(async () => {
    const nextCursor = cursors[cursors.length - 1];
    if (!nextCursor) return;
    await doSearch(query, quickFilter, filters, nextCursor, true);
  }, [cursors, doSearch, filters, query, quickFilter]);

  // ── Group by effective purchase month ─────────────────────────────────────

  const grouped: { key: string; label: string; items: SearchReceiptItem[] }[] = [];
  for (const r of receipts) {
    const key = monthKey(effectiveDate(r));
    const last = grouped[grouped.length - 1];
    if (!last || last.key !== key) {
      grouped.push({ key, label: monthLabel(key), items: [r] });
    } else {
      last.items.push(r);
    }
  }

  const filterCount = activeFilterCount(quickFilter, filters);
  const nextCursor = cursors[cursors.length - 1];

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <main className="discovery" aria-label="Receipt discovery">
      {/* ── Live region for screen readers ── */}
      <div
        ref={liveRegionRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />

      {/* ── Header ── */}
      <header className="discovery__header">
        <Link to="/" className="btn btn--ghost btn--small" aria-label="Back to capture">
          ← Back
        </Link>
        <h1 className="discovery__title">Receipts</h1>
        <button
          ref={filterButtonRef}
          type="button"
          className="btn btn--ghost btn--small discovery__filter-btn"
          aria-label={`Filters${filterCount > 0 ? ` (${filterCount} active)` : ""}`}
          aria-expanded={showFilterSheet}
          onClick={() => {
            setDraftFilters({ ...filters });
            setShowFilterSheet(true);
          }}
        >
          Filters{filterCount > 0 ? ` (${filterCount})` : ""}
        </button>
      </header>

      {/* ── Search bar ── */}
      <div className="discovery__search-row">
        <label htmlFor="discovery-search" className="sr-only">
          Search merchant or item
        </label>
        <input
          ref={searchInputRef}
          id="discovery-search"
          type="search"
          className="discovery__search-input"
          placeholder="Search merchant or item"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          autoComplete="off"
          spellCheck={false}
          aria-label="Search merchant or item"
        />
        {query && (
          <button
            type="button"
            className="discovery__search-clear"
            aria-label="Clear search"
            onClick={() => handleQueryChange("")}
          >
            ×
          </button>
        )}
      </div>

      {/* ── Quick filter chips ── */}
      <div className="discovery__chips" role="group" aria-label="Quick filters">
        {(
          [
            { id: "needs_review" as const, label: "Needs review" },
            { id: "duplicates" as const, label: "Duplicates" },
            { id: "verified" as const, label: "Verified" },
          ] as const
        ).map(({ id, label }) => (
          <button
            key={id}
            type="button"
            className={`chip${quickFilter === id ? " chip--active" : ""}`}
            aria-pressed={quickFilter === id}
            onClick={() => handleQuickFilter(id)}
          >
            {label}
          </button>
        ))}
        {filterCount > 0 && (
          <button
            type="button"
            className="chip chip--clear"
            onClick={handleClearAll}
            aria-label="Clear all filters and search"
          >
            Clear all
          </button>
        )}
      </div>

      {/* ── Active filter chips ── */}
      {(filters.processingStatus.length > 0 ||
        filters.verificationStatus.length > 0 ||
        filters.deduplicationStatus.length > 0 ||
        filters.dateFrom ||
        filters.dateTo ||
        filters.amountMin ||
        filters.amountMax) && (
          <div className="discovery__active-filters" aria-label="Active filters">
            {filters.processingStatus.map((s) => (
              <span key={s} className="chip chip--filter">
                {s}
                <button
                  type="button"
                  aria-label={`Remove processing status filter: ${s}`}
                  className="chip__remove"
                  onClick={() =>
                    handleApplyFilters({
                      ...filters,
                      processingStatus: filters.processingStatus.filter((x) => x !== s),
                    })
                  }
                >
                  ×
                </button>
              </span>
            ))}
            {filters.verificationStatus.map((s) => (
              <span key={s} className="chip chip--filter">
                {s}
                <button
                  type="button"
                  aria-label={`Remove verification status filter: ${s}`}
                  className="chip__remove"
                  onClick={() =>
                    handleApplyFilters({
                      ...filters,
                      verificationStatus: filters.verificationStatus.filter((x) => x !== s),
                    })
                  }
                >
                  ×
                </button>
              </span>
            ))}
            {filters.deduplicationStatus.map((s) => (
              <span key={s} className="chip chip--filter">
                {s}
                <button
                  type="button"
                  aria-label={`Remove deduplication filter: ${s}`}
                  className="chip__remove"
                  onClick={() =>
                    handleApplyFilters({
                      ...filters,
                      deduplicationStatus: filters.deduplicationStatus.filter((x) => x !== s),
                    })
                  }
                >
                  ×
                </button>
              </span>
            ))}
            {(filters.dateFrom || filters.dateTo) && (
              <span className="chip chip--filter">
                {filters.dateFrom || "…"} – {filters.dateTo || "…"}
                <button
                  type="button"
                  aria-label="Remove date range filter"
                  className="chip__remove"
                  onClick={() =>
                    handleApplyFilters({ ...filters, dateFrom: "", dateTo: "" })
                  }
                >
                  ×
                </button>
              </span>
            )}
            {(filters.amountMin || filters.amountMax) && (
              <span className="chip chip--filter">
                ${filters.amountMin || "0"} – ${filters.amountMax || "∞"}
                <button
                  type="button"
                  aria-label="Remove amount range filter"
                  className="chip__remove"
                  onClick={() =>
                    handleApplyFilters({ ...filters, amountMin: "", amountMax: "" })
                  }
                >
                  ×
                </button>
              </span>
            )}
          </div>
        )}

      {/* ── Result count ── */}
      {!loading && !error && (
        <p className="discovery__count" aria-live="off">
          {totalCount === 0
            ? "No receipts"
            : totalCount === 1
              ? "1 receipt"
              : `${totalCount} receipts`}
        </p>
      )}

      {/* ── States ── */}
      {loading && <LoadingSpinner label="Searching receipts…" />}
      {error && (
        <div role="alert" className="alert alert--error">
          {error}
        </div>
      )}

      {!loading && !error && receipts.length === 0 && (
        <div className="discovery__empty">
          <p>
            {query || filterCount > 0
              ? "No receipts match this search and filter combination."
              : "No receipts have been captured yet."}
          </p>
          {(query || filterCount > 0) && (
            <button type="button" className="btn btn--ghost" onClick={handleClearAll}>
              Clear search and filters
            </button>
          )}
        </div>
      )}

      {/* ── Results grouped by month ── */}
      {grouped.map(({ key, label, items }) => (
        <section key={key} aria-label={label}>
          <h2 className="discovery__month-heading">{label}</h2>
          <ul className="receipts-list" role="list">
            {items.map((r) => (
              <ReceiptCard key={r.receipt_id} receipt={r} />
            ))}
          </ul>
        </section>
      ))}

      {/* ── Load more ── */}
      {nextCursor && (
        <button
          type="button"
          className="btn btn--ghost discovery__load-more"
          onClick={handleLoadMore}
          disabled={loadingMore}
          aria-label="Load more receipts"
        >
          {loadingMore ? "Loading…" : "Load more"}
        </button>
      )}

      {/* ── Filter sheet ── */}
      {showFilterSheet && (
        <FilterSheet
          draft={draftFilters}
          onChange={setDraftFilters}
          onApply={handleApplyFilters}
          onCancel={() => setShowFilterSheet(false)}
          returnFocusRef={filterButtonRef}
        />
      )}
    </main>
  );
}

// ── Receipt card ───────────────────────────────────────────────────────────────

function ReceiptCard({ receipt: r }: { receipt: SearchReceiptItem }) {
  const eff = effectiveDate(r);
  const merchant = r.current_revision?.merchant_normalized ?? "Processing receipt";
  const dateStr = eff.toLocaleDateString();
  const matchCtx = r.match_context;

  return (
    <li className="receipts-list__item" role="listitem">
      <Link
        to={`/receipts/${r.receipt_id}`}
        className="receipts-list__link"
        aria-label={`${merchant}, ${dateStr}, ${r.processing_status}`}
      >
        <div className="receipts-list__meta">
          <span className="receipts-list__merchant">{merchant}</span>
          <span className="receipts-list__amount">
            {r.current_revision?.total_minor != null
              ? formatMinorUnits(r.current_revision.total_minor, r.current_revision.currency)
              : ""}
          </span>
        </div>

        {matchCtx?.source === "line_item" && matchCtx.matched_description && (
          <p className="discovery__match-hint" aria-label="Matched item">
            Matched: {matchCtx.matched_description}
          </p>
        )}

        <div className="receipts-list__status">
          <ProcessingStatusBadge status={r.processing_status} />
          <VerificationStatusBadge status={r.verification_status} />
          {r.deduplication_status === "suspected_duplicate" && (
            <span className="status-badge status-badge--warning">Possible duplicate</span>
          )}
          {r.deduplication_status === "confirmed_duplicate" && (
            <span className="status-badge status-badge--muted">Duplicate</span>
          )}
        </div>
        <div className="receipts-list__detail">
          <span className="receipts-list__time">{dateStr}</span>
          <span className="receipts-list__count">
            {r.expected_asset_count} image{r.expected_asset_count !== 1 ? "s" : ""}
          </span>
        </div>
      </Link>
    </li>
  );
}

// ── Filter sheet ───────────────────────────────────────────────────────────────

interface FilterSheetProps {
  draft: ActiveFilters;
  onChange: (f: ActiveFilters) => void;
  onApply: (f: ActiveFilters) => void;
  onCancel: () => void;
  returnFocusRef: RefObject<HTMLButtonElement | null>;
}

function FilterSheet({
  draft,
  onChange,
  onApply,
  onCancel,
  returnFocusRef,
}: FilterSheetProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const returnFocusElement = returnFocusRef.current;
    closeRef.current?.focus();
    return () => returnFocusElement?.focus();
  }, [returnFocusRef]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
        return;
      }
      if (e.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onCancel]);

  const handleReset = () => onChange({ ...DEFAULT_FILTERS });

  return (
    <div
      className="filter-sheet-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Filter receipts"
    >
      <div ref={dialogRef} className="filter-sheet">
        <header className="filter-sheet__header">
          <h2 className="filter-sheet__title">Filters</h2>
          <button
            ref={closeRef}
            type="button"
            className="btn btn--ghost btn--small"
            aria-label="Close filters"
            onClick={onCancel}
          >
            ×
          </button>
        </header>

        <div className="filter-sheet__body">
          {/* Sort */}
          <fieldset className="filter-sheet__group">
            <legend className="filter-sheet__legend">Sort</legend>
            <label className="filter-sheet__label" htmlFor="fs-sort">
              Order
            </label>
            <select
              id="fs-sort"
              className="filter-sheet__select"
              value={draft.sort}
              onChange={(e) => onChange({ ...draft, sort: e.target.value as SearchSortOrder })}
            >
              <option value="effective_date_desc">Date (newest first)</option>
              <option value="effective_date_asc">Date (oldest first)</option>
              <option value="amount_desc">Amount (highest first)</option>
              <option value="amount_asc">Amount (lowest first)</option>
            </select>
          </fieldset>

          {/* Date range */}
          <fieldset className="filter-sheet__group">
            <legend className="filter-sheet__legend">Purchase date</legend>
            <label className="filter-sheet__label" htmlFor="fs-date-from">
              From
            </label>
            <input
              id="fs-date-from"
              type="date"
              className="filter-sheet__input"
              value={draft.dateFrom}
              onChange={(e) => onChange({ ...draft, dateFrom: e.target.value })}
            />
            <label className="filter-sheet__label" htmlFor="fs-date-to">
              To
            </label>
            <input
              id="fs-date-to"
              type="date"
              className="filter-sheet__input"
              value={draft.dateTo}
              onChange={(e) => onChange({ ...draft, dateTo: e.target.value })}
            />
          </fieldset>

          {/* Amount range */}
          <fieldset className="filter-sheet__group">
            <legend className="filter-sheet__legend">Amount ($)</legend>
            <label className="filter-sheet__label" htmlFor="fs-amount-min">
              Min
            </label>
            <input
              id="fs-amount-min"
              type="number"
              min="0"
              step="0.01"
              className="filter-sheet__input"
              placeholder="0.00"
              value={draft.amountMin}
              onChange={(e) => onChange({ ...draft, amountMin: e.target.value })}
            />
            <label className="filter-sheet__label" htmlFor="fs-amount-max">
              Max
            </label>
            <input
              id="fs-amount-max"
              type="number"
              min="0"
              step="0.01"
              className="filter-sheet__input"
              placeholder="No limit"
              value={draft.amountMax}
              onChange={(e) => onChange({ ...draft, amountMax: e.target.value })}
            />
          </fieldset>

          {/* Processing status */}
          <FilterCheckGroup
            legend="Processing status"
            options={[
              { value: "extracted", label: "Extracted" },
              { value: "queued", label: "Queued" },
              { value: "processing", label: "Processing" },
              { value: "retryable_failed", label: "Retryable failed" },
              { value: "failed", label: "Failed" },
            ]}
            selected={draft.processingStatus}
            onChange={(vals) => onChange({ ...draft, processingStatus: vals as ProcessingStatus[] })}
          />

          {/* Verification status */}
          <FilterCheckGroup
            legend="Verification status"
            options={[
              { value: "unreviewed", label: "Unreviewed" },
              { value: "system_validated", label: "System validated" },
              { value: "needs_review", label: "Needs review" },
              { value: "human_verified", label: "Human verified" },
            ]}
            selected={draft.verificationStatus}
            onChange={(vals) => onChange({ ...draft, verificationStatus: vals as VerificationStatus[] })}
          />

          {/* Duplicate status */}
          <FilterCheckGroup
            legend="Duplicate status"
            options={[
              { value: "unchecked", label: "Unchecked" },
              { value: "unique", label: "Unique" },
              { value: "suspected_duplicate", label: "Suspected duplicate" },
              { value: "confirmed_duplicate", label: "Confirmed duplicate" },
            ]}
            selected={draft.deduplicationStatus}
            onChange={(vals) =>
              onChange({ ...draft, deduplicationStatus: vals as DeduplicationStatus[] })
            }
          />
        </div>

        <footer className="filter-sheet__footer">
          <button type="button" className="btn btn--ghost" onClick={handleReset}>
            Reset
          </button>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => onApply(draft)}
          >
            Apply
          </button>
        </footer>
      </div>
    </div>
  );
}

interface FilterCheckGroupProps {
  legend: string;
  options: { value: string; label: string }[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

function FilterCheckGroup({ legend, options, selected, onChange }: FilterCheckGroupProps) {
  const toggle = (val: string) => {
    onChange(
      selected.includes(val) ? selected.filter((x) => x !== val) : [...selected, val],
    );
  };

  return (
    <fieldset className="filter-sheet__group">
      <legend className="filter-sheet__legend">{legend}</legend>
      {options.map(({ value, label }) => (
        <label key={value} className="filter-sheet__check-label">
          <input
            type="checkbox"
            className="filter-sheet__check"
            checked={selected.includes(value)}
            onChange={() => toggle(value)}
          />
          {label}
        </label>
      ))}
    </fieldset>
  );
}
