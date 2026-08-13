
export function LoadingSpinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="spinner-wrap" role="status" aria-label={label}>
      <span className="spinner" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
}
