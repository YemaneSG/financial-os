import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReceiptDraft } from "@/receipts/ReceiptDraft";
import type { DraftImage } from "@/receipts/useDraft";

function makeImage(id: string, name = "photo.jpg", type = "image/jpeg"): DraftImage {
  return {
    id,
    file: new File(["content"], name, { type }),
    objectUrl: `blob:test/${id}`,
  };
}

function renderDraft(
  images: DraftImage[],
  opts: {
    errorMessage?: string | null;
    onAddMore?: ReturnType<typeof vi.fn>;
    onRemove?: ReturnType<typeof vi.fn>;
    onReplace?: ReturnType<typeof vi.fn>;
    onSubmit?: ReturnType<typeof vi.fn>;
    onClearError?: ReturnType<typeof vi.fn>;
  } = {},
) {
  return render(
    <ReceiptDraft
      images={images}
      errorMessage={opts.errorMessage ?? null}
      onAddMore={opts.onAddMore ?? vi.fn()}
      onRemove={opts.onRemove ?? vi.fn()}
      onReplace={opts.onReplace ?? vi.fn()}
      onSubmit={opts.onSubmit ?? vi.fn()}
      onClearError={opts.onClearError ?? vi.fn()}
    />,
  );
}

describe("ReceiptDraft", () => {
  it("renders heading", () => {
    renderDraft([makeImage("1")]);
    expect(screen.getByRole("heading", { name: /receipt draft/i })).toBeInTheDocument();
  });

  it("renders thumbnail list with ordinal labels", () => {
    renderDraft([makeImage("img1"), makeImage("img2")]);
    expect(screen.getByRole("list", { name: /receipt images/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Image 1, selected" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Image 2" })).toBeInTheDocument();
  });

  it("shows an intentional fallback instead of a broken HEIC preview", () => {
    renderDraft([makeImage("heic-1", "IMG_0001.HEIC", "")]);
    expect(screen.getByRole("status")).toHaveTextContent("HEIC photo ready");
    expect(screen.getByRole("status")).toHaveTextContent("original photo can still upload");
    expect(screen.queryByAltText(/preview of receipt image/i)).not.toBeInTheDocument();
  });

  it("submit button is disabled when no images", () => {
    renderDraft([]);
    const btn = screen.getByRole("button", { name: /submit receipt/i });
    expect(btn).toBeDisabled();
  });

  it("submit button is enabled with images", () => {
    renderDraft([makeImage("img1")]);
    const btn = screen.getByRole("button", { name: /submit receipt/i });
    expect(btn).not.toBeDisabled();
  });

  it("calls onSubmit when submit button clicked", () => {
    const onSubmit = vi.fn();
    renderDraft([makeImage("img1")], { onSubmit });
    fireEvent.click(screen.getByRole("button", { name: /submit receipt/i }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("shows error message with dismiss", () => {
    const onClearError = vi.fn();
    renderDraft([makeImage("img1")], {
      errorMessage: "Something went wrong",
      onClearError,
    });
    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
    fireEvent.click(screen.getByRole("button", { name: /dismiss error/i }));
    expect(onClearError).toHaveBeenCalledOnce();
  });

  it("shows 'Add another photo' when fewer than 10 images", () => {
    renderDraft([makeImage("img1")]);
    expect(screen.getByRole("button", { name: /add another photo/i })).toBeInTheDocument();
  });

  it("hides 'Add another photo' when 10 images present", () => {
    const images = Array.from({ length: 10 }, (_, i) => makeImage(`img${i}`));
    renderDraft(images);
    expect(screen.queryByRole("button", { name: /add another photo/i })).not.toBeInTheDocument();
  });

  it("renders remove and retake buttons for selected image", () => {
    renderDraft([makeImage("img1")]);
    expect(screen.getByRole("button", { name: /remove image 1/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /replace image 1/i })).toBeInTheDocument();
  });

  it("calls onRemove with image id", () => {
    const onRemove = vi.fn();
    const images = [makeImage("test-id-1")];
    renderDraft(images, { onRemove });
    fireEvent.click(screen.getByRole("button", { name: /remove image 1/i }));
    expect(onRemove).toHaveBeenCalledWith("test-id-1");
  });
});
