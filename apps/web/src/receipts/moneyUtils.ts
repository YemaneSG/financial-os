/**
 * Client-side money utilities for the human review form.
 *
 * All conversion uses integer string arithmetic — never binary floating-point.
 * These functions are exported for focused unit tests.
 */

/** Return the number of minor-unit decimal places for a given ISO 4217 currency code. */
export function decimalPlacesForCurrency(currency: string): number {
  const upper = currency.toUpperCase();
  const zeroDecimal = new Set([
    "BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW", "MGA", "PYG",
    "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
  ]);
  if (zeroDecimal.has(upper)) return 0;
  const threeDecimal = new Set(["BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"]);
  if (threeDecimal.has(upper)) return 3;
  return 2;
}

/**
 * Convert an exact decimal dollar string to integer minor units.
 *
 * Uses only integer string arithmetic — never binary floating-point.
 * Rejects: blank, negative, non-numeric characters, and more fractional
 * digits than the currency allows.
 */
export function parseDollarsToMinor(dollars: string, maxFractionalDigits: number): number {
  const trimmed = dollars.trim();
  if (trimmed === "") throw new Error("Amount is required");
  if (maxFractionalDigits === 0) {
    if (!/^\d+$/.test(trimmed)) throw new Error("Amount must be a non-negative integer");
    const minor = BigInt(trimmed);
    if (minor > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Amount is too large");
    return Number(minor);
  }
  const pattern = new RegExp(`^\\d+(\\.\\d{1,${maxFractionalDigits}})?$`);
  if (!pattern.test(trimmed)) {
    throw new Error(
      `Amount must be a non-negative decimal with at most ${maxFractionalDigits} ` +
        `decimal place${maxFractionalDigits !== 1 ? "s" : ""}`,
    );
  }
  const [intStr, fracStr = ""] = trimmed.split(".");
  const frac = fracStr.padEnd(maxFractionalDigits, "0");
  const scale = 10n ** BigInt(maxFractionalDigits);
  const minor = BigInt(intStr) * scale + BigInt(frac);
  if (minor > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Amount is too large");
  return Number(minor);
}

/** Optional money parse: returns null for blank, throws for malformed values. */
export function parseDollarsToMinorOptional(dollars: string, dp: number): number | null {
  if (dollars.trim() === "") return null;
  return parseDollarsToMinor(dollars, dp);
}

/** Display: integer minor units → decimal string (for pre-populating form inputs). */
export function minorToDollars(minor: number | null | undefined, dp: number = 2): string {
  if (minor == null) return "";
  if (!Number.isSafeInteger(minor) || minor < 0) {
    throw new Error("Minor-unit amount must be a non-negative safe integer");
  }
  if (dp === 0) return String(minor);
  const digits = String(minor).padStart(dp + 1, "0");
  return `${digits.slice(0, -dp)}.${digits.slice(-dp)}`;
}

/** Convert a UTC ISO string to a datetime-local value in the device's local time. */
export function toLocalDatetimeString(isoString: string): string {
  const d = new Date(isoString);
  if (Number.isNaN(d.getTime())) throw new Error("Invalid date/time");
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}
