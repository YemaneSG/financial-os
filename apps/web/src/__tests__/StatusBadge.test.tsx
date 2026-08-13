import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProcessingStatusBadge, VerificationStatusBadge } from "@/components/StatusBadge";
import type { ProcessingStatus, VerificationStatus } from "@/api/types";

describe("ProcessingStatusBadge", () => {
  const statuses: ProcessingStatus[] = [
    "reserved", "uploading", "uploaded", "queued", "processing",
    "extracted", "retryable_failed", "failed", "abandoned",
  ];

  statuses.forEach((status) => {
    it(`renders "${status}" with aria-label`, () => {
      render(<ProcessingStatusBadge status={status} />);
      // The badge element carries an aria-label — verify it is present.
      const badge = document.querySelector(`[aria-label*="Processing:"]`);
      expect(badge).not.toBeNull();
    });
  });

  it("includes text label so status is not color-only (A11Y)", () => {
    render(<ProcessingStatusBadge status="failed" />);
    // Text content must include human-readable label — not just the icon.
    expect(screen.getByText(/Failed/i)).toBeInTheDocument();
  });

  it("includes text label for extracted status", () => {
    render(<ProcessingStatusBadge status="extracted" />);
    expect(screen.getByText(/Extracted/i)).toBeInTheDocument();
  });
});

describe("VerificationStatusBadge", () => {
  const statuses: VerificationStatus[] = [
    "unreviewed", "system_validated", "needs_review", "human_verified",
  ];

  statuses.forEach((status) => {
    it(`renders "${status}" with aria-label`, () => {
      render(<VerificationStatusBadge status={status} />);
      const badge = document.querySelector(`[aria-label*="Verification:"]`);
      expect(badge).not.toBeNull();
    });
  });

  it("shows human-readable text for needs_review", () => {
    render(<VerificationStatusBadge status="needs_review" />);
    expect(screen.getByText(/Needs review/i)).toBeInTheDocument();
  });
});
