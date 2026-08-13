import React, { useRef, useState, useEffect } from "react";
import type { DraftImage } from "./useDraft";
import { canPreviewReceipt } from "./receiptFile";

interface ReceiptDraftProps {
  images: DraftImage[];
  errorMessage: string | null;
  onAddMore: (files: File[]) => void;
  onRemove: (id: string) => void;
  onReplace: (id: string, file: File) => void;
  onSubmit: () => void;
  onClearError: () => void;
}

export function ReceiptDraft({
  images,
  errorMessage,
  onAddMore,
  onRemove,
  onReplace,
  onSubmit,
  onClearError,
}: ReceiptDraftProps) {
  const addMoreRef = useRef<HTMLInputElement>(null);
  const replaceRefs = useRef<Record<string, HTMLInputElement | null>>({});

  function handleAddMore(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) onAddMore(files);
    e.target.value = "";
  }

  function handleReplace(id: string, e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onReplace(id, file);
    e.target.value = "";
  }

  const [selected, setSelected] = useState<string | null>(
    images[0]?.id ?? null,
  );

  const selectedImage = images.find((img) => img.id === selected) ?? images[0];

  useEffect(() => {
    if (!selected && images.length > 0) setSelected(images[0].id);
    if (images.length === 0) setSelected(null);
    if (selected && !images.find((i) => i.id === selected)) {
      setSelected(images[images.length - 1]?.id ?? null);
    }
  }, [images, selected]);

  return (
    <main className="receipt-draft" aria-label="Receipt draft">
      <h1 className="receipt-draft__title">Receipt draft</h1>

      <p className="receipt-draft__hint" id="draft-hint">
        For long receipts, add overlapping photos in order.
      </p>

      {errorMessage && (
        <div role="alert" className="alert alert--error">
          <span>{errorMessage}</span>
          <button
            type="button"
            className="alert__close"
            aria-label="Dismiss error"
            onClick={onClearError}
          >
            ✕
          </button>
        </div>
      )}

      {/* Thumbnail strip */}
      <div
        className="draft-thumbnails"
        role="list"
        aria-label="Receipt images"
        aria-describedby="draft-hint"
      >
        {images.map((img, i) => (
          <div
            key={img.id}
            className={`draft-thumbnail${img.id === selected ? " draft-thumbnail--selected" : ""}`}
            role="listitem"
          >
            <button
              type="button"
              className="draft-thumbnail__btn"
              aria-label={`Image ${i + 1}${img.id === selected ? ", selected" : ""}`}
              aria-pressed={img.id === selected}
              onClick={() => setSelected(img.id)}
            >
              {canPreviewReceipt(img.file) ? (
                <img
                  src={img.objectUrl}
                  alt={`Receipt image ${i + 1}`}
                  className="draft-thumbnail__img"
                />
              ) : (
                <span className="draft-thumbnail__fallback" aria-hidden="true">
                  HEIC
                </span>
              )}
              <span className="draft-thumbnail__num" aria-hidden="true">
                {i + 1}
              </span>
            </button>
          </div>
        ))}
      </div>

      {/* Full preview */}
      {selectedImage && (
        <div className="draft-preview">
          {canPreviewReceipt(selectedImage.file) ? (
            <img
              src={selectedImage.objectUrl}
              alt={`Preview of receipt image ${images.indexOf(selectedImage) + 1}`}
              className="draft-preview__img"
            />
          ) : (
            <div className="draft-preview__fallback" role="status">
              <strong>HEIC photo ready</strong>
              <span>This browser cannot preview HEIC, but the original photo can still upload.</span>
            </div>
          )}

          <div className="draft-preview__actions" role="group" aria-label="Image actions">
            <button
              type="button"
              className="btn btn--ghost btn--small"
              aria-label={`Replace image ${images.indexOf(selectedImage) + 1}`}
              onClick={() => replaceRefs.current[selectedImage.id]?.click()}
            >
              Retake / Replace
            </button>
            <input
              ref={(el) => {
                replaceRefs.current[selectedImage.id] = el;
              }}
              type="file"
              accept="image/*"
              className="sr-only"
              aria-hidden="true"
              tabIndex={-1}
              onChange={(e) => handleReplace(selectedImage.id, e)}
            />

            <button
              type="button"
              className="btn btn--ghost btn--small btn--danger"
              aria-label={`Remove image ${images.indexOf(selectedImage) + 1}`}
              onClick={() => onRemove(selectedImage.id)}
            >
              Remove
            </button>
          </div>
        </div>
      )}

      <div className="draft-footer">
        {images.length < 10 && (
          <>
            <button
              type="button"
              className="btn btn--ghost"
              aria-label="Add another photo"
              onClick={() => addMoreRef.current?.click()}
            >
              + Add another photo
            </button>
            <input
              ref={addMoreRef}
              type="file"
              accept="image/*"
              multiple
              className="sr-only"
              aria-hidden="true"
              tabIndex={-1}
              onChange={handleAddMore}
            />
          </>
        )}

        <button
          type="button"
          className="btn btn--primary"
          aria-label="Submit receipt for saving"
          disabled={images.length === 0}
          onClick={onSubmit}
        >
          Submit receipt
        </button>
      </div>
    </main>
  );
}
