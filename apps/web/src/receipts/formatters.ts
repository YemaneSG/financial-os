export function formatMinorUnits(
  minor: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (minor == null) return "";
  const code = currency ?? "USD";
  const major = minor / 100;
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: code,
    }).format(major);
  } catch {
    return `${code} ${(major).toFixed(2)}`;
  }
}

export function formatProcessingStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
