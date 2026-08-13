import { describe, expect, it } from "vitest";
import { getCanonicalFirebaseUrl } from "@/auth/canonicalHost";

describe("getCanonicalFirebaseUrl", () => {
  it("canonicalizes the web.app alias to the same-site Firebase auth domain", () => {
    expect(
      getCanonicalFirebaseUrl(
        "https://example-project.web.app/receipts/abc?source=test#items",
      ),
    ).toBe(
      "https://example-project.firebaseapp.com/receipts/abc?source=test#items",
    );
  });

  it("does not redirect the canonical firebaseapp.com domain", () => {
    expect(
      getCanonicalFirebaseUrl("https://example-project.firebaseapp.com/"),
    ).toBeNull();
  });

  it("does not redirect localhost or unrelated hosts", () => {
    expect(getCanonicalFirebaseUrl("http://localhost:5173/")).toBeNull();
    expect(getCanonicalFirebaseUrl("https://example.com/")).toBeNull();
  });

  it("rejects nested web.app hostnames", () => {
    expect(
      getCanonicalFirebaseUrl("https://nested.example-project.web.app/"),
    ).toBeNull();
  });
});
