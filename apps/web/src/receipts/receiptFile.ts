const MIME_BY_EXTENSION: Readonly<Record<string, string>> = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  heic: "image/heic",
  heif: "image/heif",
  webp: "image/webp",
};

const ALLOWED_MIME_TYPES = new Set(Object.values(MIME_BY_EXTENSION));

/**
 * Return the canonical receipt MIME type.
 *
 * Safari and Chromium can expose imported HEIC/HEIF files with an empty
 * `File.type`. Signed GCS uploads bind Content-Type, so extension fallback is
 * required to keep reservation and upload headers identical.
 */
export function receiptMimeType(file: File): string | null {
  const browserType = file.type.trim().toLowerCase();
  if (browserType === "image/jpg") return "image/jpeg";
  if (ALLOWED_MIME_TYPES.has(browserType)) return browserType;

  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return MIME_BY_EXTENSION[extension] ?? null;
}

export function canPreviewReceipt(file: File): boolean {
  const mimeType = receiptMimeType(file);
  return mimeType !== "image/heic" && mimeType !== "image/heif";
}
