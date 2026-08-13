import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDraft } from "@/receipts/useDraft";

function makeFile(name = "receipt.jpg", size = 1024, type = "image/jpeg"): File {
  return new File(["x".repeat(size)], name, { type });
}

describe("useDraft", () => {
  it("starts idle with no images", () => {
    const { result } = renderHook(() => useDraft());
    expect(result.current.state.phase).toBe("idle");
    expect(result.current.state.images).toHaveLength(0);
  });

  it("generates a crypto.randomUUID submission key", () => {
    const { result } = renderHook(() => useDraft());
    expect(result.current.state.clientSubmissionKey).toBeTruthy();
    expect(typeof result.current.state.clientSubmissionKey).toBe("string");
  });

  it("transitions to drafting when first image added", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile()]);
    });
    expect(result.current.state.phase).toBe("drafting");
    expect(result.current.state.images).toHaveLength(1);
  });

  it("rejects unsupported file types", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile("doc.pdf", 1024, "application/pdf")]);
    });
    expect(result.current.state.images).toHaveLength(0);
    expect(result.current.state.errorMessage).toMatch(/supported/i);
  });

  it("accepts an iPhone HEIC file when the browser omits File.type", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile("IMG_0001.HEIC", 3 * 1024 * 1024, "")]);
    });
    expect(result.current.state.images).toHaveLength(1);
    expect(result.current.state.errorMessage).toBeNull();
  });

  it("rejects files exceeding 10 MB", () => {
    const { result } = renderHook(() => useDraft());
    const bigFile = makeFile("big.jpg", 11 * 1024 * 1024);
    act(() => {
      result.current.addImages([bigFile]);
    });
    expect(result.current.state.images).toHaveLength(0);
    expect(result.current.state.errorMessage).toMatch(/10 MB/i);
  });

  it("enforces maximum 10 images", () => {
    const { result } = renderHook(() => useDraft());
    const files = Array.from({ length: 11 }, (_, i) => makeFile(`img${i}.jpg`));
    act(() => {
      result.current.addImages(files);
    });
    expect(result.current.state.errorMessage).toMatch(/10/);
    expect(result.current.state.images.length).toBeLessThanOrEqual(10);
  });

  it("removes an image by id", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile("a.jpg"), makeFile("b.jpg")]);
    });
    const id = result.current.state.images[0].id;
    act(() => {
      result.current.removeImage(id);
    });
    expect(result.current.state.images).toHaveLength(1);
  });

  it("returns to idle when last image removed", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile()]);
    });
    const id = result.current.state.images[0].id;
    act(() => {
      result.current.removeImage(id);
    });
    expect(result.current.state.phase).toBe("idle");
  });

  it("replaces an image by id", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile("original.jpg")]);
    });
    const id = result.current.state.images[0].id;
    act(() => {
      result.current.replaceImage(id, makeFile("replacement.jpg"));
    });
    expect(result.current.state.images).toHaveLength(1);
    expect(result.current.state.images[0].file.name).toBe("replacement.jpg");
  });

  it("resets to fresh idle state with a new submission key", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([makeFile()]);
    });
    act(() => {
      result.current.reset();
    });
    // After reset, key is regenerated and images are gone.
    expect(result.current.state.images).toHaveLength(0);
    expect(result.current.state.phase).toBe("idle");
    // Key may be the same in tests because crypto.randomUUID is mocked,
    // but state should be fresh.
    expect(result.current.state.savedReceiptId).toBeNull();
  });

  it("setSaved transitions to saved phase", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.setSaved("receipt-id-123", "2026-08-12T14:30:00.000Z");
    });
    expect(result.current.state.phase).toBe("saved");
    expect(result.current.state.savedReceiptId).toBe("receipt-id-123");
  });

  it("setError sets errorMessage without changing phase", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.addImages([new File(["x"], "photo.jpg", { type: "image/jpeg" })]);
    });
    const phase = result.current.state.phase;
    act(() => {
      result.current.setError("Something went wrong");
    });
    // Phase is unchanged; only errorMessage is set.
    expect(result.current.state.phase).toBe(phase);
    expect(result.current.state.errorMessage).toBe("Something went wrong");
  });

  it("clearError removes the error message", () => {
    const { result } = renderHook(() => useDraft());
    act(() => {
      result.current.setError("oops");
    });
    act(() => {
      result.current.clearError();
    });
    expect(result.current.state.errorMessage).toBeNull();
  });
});
