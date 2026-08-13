import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CaptureHome } from "@/receipts/CaptureHome";

function makeFile(name = "receipt.jpg", type = "image/jpeg"): File {
  return new File(["content"], name, { type });
}

function renderCapture(onImages = vi.fn()) {
  return render(
    <MemoryRouter>
      <CaptureHome onImages={onImages} />
    </MemoryRouter>,
  );
}

function requireFileInput(selector: string): HTMLInputElement {
  const input = document.querySelector<HTMLInputElement>(selector);
  if (!input) throw new Error(`Expected file input matching ${selector}`);
  return input;
}

describe("CaptureHome", () => {
  it("renders primary photograph button", () => {
    renderCapture();
    expect(screen.getByRole("button", { name: /photograph a receipt/i })).toBeInTheDocument();
  });

  it("renders photo library fallback button", () => {
    renderCapture();
    expect(screen.getByRole("button", { name: /choose existing photo/i })).toBeInTheDocument();
  });

  it("renders recent receipts link", () => {
    renderCapture();
    expect(screen.getByRole("link", { name: /recent receipts/i })).toBeInTheDocument();
  });

  it("has accessible landmark for main", () => {
    renderCapture();
    expect(screen.getByRole("main", { name: /capture receipt/i })).toBeInTheDocument();
  });

  it("calls onImages when files selected via library input", () => {
    const onImages = vi.fn();
    renderCapture(onImages);
    const input = requireFileInput('input[type="file"]:not([capture])');
    const file = makeFile();
    fireEvent.change(input, { target: { files: [file] } });
    expect(onImages).toHaveBeenCalledWith([file]);
  });

  it("does not call onImages when no files selected", () => {
    const onImages = vi.fn();
    renderCapture(onImages);
    const input = requireFileInput('input[type="file"]:not([capture])');
    fireEvent.change(input, { target: { files: [] } });
    expect(onImages).not.toHaveBeenCalled();
  });

  it("camera input has capture=environment attribute for iPhone camera", () => {
    renderCapture();
    const cameraInput = requireFileInput('input[type="file"][capture]');
    expect(cameraInput).toHaveAttribute("capture", "environment");
    expect(cameraInput).toHaveAttribute("accept", "image/*");
  });
});
