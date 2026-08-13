import { describe, it, expect } from "vitest";
import { formatMinorUnits } from "@/receipts/formatters";

describe("formatMinorUnits", () => {
  it("formats USD cents", () => {
    const result = formatMinorUnits(1099, "USD");
    expect(result).toMatch(/10\.99/);
  });

  it("returns empty string for null", () => {
    expect(formatMinorUnits(null, "USD")).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(formatMinorUnits(undefined, "USD")).toBe("");
  });

  it("handles zero", () => {
    const result = formatMinorUnits(0, "USD");
    expect(result).toMatch(/0\.00/);
  });

  it("falls back gracefully for unknown currency code", () => {
    // Should not throw; falls back to code + formatted amount.
    expect(() => formatMinorUnits(1000, "ZZZ")).not.toThrow();
  });

  it("handles null currency", () => {
    const result = formatMinorUnits(500, null);
    expect(result).toMatch(/5\.00/);
  });
});
