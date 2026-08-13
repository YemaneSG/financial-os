import { describe, expect, it } from "vitest";
import { canPreviewReceipt, receiptMimeType } from "@/receipts/receiptFile";

describe("receiptMimeType", () => {
  it("infers HEIC when the browser leaves File.type empty", () => {
    const file = new File(["synthetic"], "IMG_0001.HEIC", { type: "" });
    expect(receiptMimeType(file)).toBe("image/heic");
  });

  it("normalizes image/jpg", () => {
    const file = new File(["synthetic"], "receipt.jpg", { type: "image/jpg" });
    expect(receiptMimeType(file)).toBe("image/jpeg");
  });

  it("rejects an unsupported extension with no browser MIME", () => {
    const file = new File(["synthetic"], "receipt.pdf", { type: "" });
    expect(receiptMimeType(file)).toBeNull();
  });
});

describe("canPreviewReceipt", () => {
  it("uses a fallback for HEIC rather than rendering a broken image", () => {
    const file = new File(["synthetic"], "IMG_0001.HEIC", { type: "" });
    expect(canPreviewReceipt(file)).toBe(false);
  });
});
