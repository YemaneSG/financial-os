import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SavedAcknowledgement } from "@/receipts/SavedAcknowledgement";
import { FIXTURE_RECEIPT_ID } from "@/fixtures/receipts";

function renderSaved(onCaptureAnother = vi.fn()) {
  return render(
    <MemoryRouter>
      <SavedAcknowledgement
        receiptId={FIXTURE_RECEIPT_ID}
        acknowledgedAt="2026-08-12T14:30:00.000Z"
        onCaptureAnother={onCaptureAnother}
      />
    </MemoryRouter>,
  );
}

describe("SavedAcknowledgement", () => {
  it("shows Receipt saved heading", () => {
    renderSaved();
    expect(screen.getByRole("heading", { name: /receipt saved/i })).toBeInTheDocument();
  });

  it("shows short reference ID", () => {
    renderSaved();
    // First 8 chars of FIXTURE_RECEIPT_ID
    expect(screen.getByText(/aaaaaaaa/i)).toBeInTheDocument();
  });

  it("shows async processing note", () => {
    renderSaved();
    expect(screen.getByText(/processing in the background/i)).toBeInTheDocument();
  });

  it("calls onCaptureAnother when button clicked", () => {
    const onCaptureAnother = vi.fn();
    renderSaved(onCaptureAnother);
    fireEvent.click(screen.getByRole("button", { name: /capture another/i }));
    expect(onCaptureAnother).toHaveBeenCalledOnce();
  });

  it("renders 'View receipt' link pointing to detail", () => {
    renderSaved();
    const link = screen.getByRole("link", { name: /view this receipt/i });
    expect(link).toHaveAttribute("href", `/receipts/${FIXTURE_RECEIPT_ID}`);
  });

  it("live region announces saved state", () => {
    renderSaved();
    const main = screen.getByRole("main", { name: /receipt saved/i });
    expect(main).toHaveAttribute("aria-live", "polite");
  });
});
