import React, { useRef } from "react";
import { Link } from "react-router-dom";

interface CaptureHomeProps {
  onImages: (files: File[]) => void;
}

export function CaptureHome({ onImages }: CaptureHomeProps) {
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const libraryInputRef = useRef<HTMLInputElement>(null);

  function handleFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) onImages(files);
    // Reset so the same file can be re-selected after a replace.
    e.target.value = "";
  }

  return (
    <main className="capture-home" aria-label="Capture receipt">
      <div className="capture-home__hero" aria-hidden="true">
        <svg
          className="receipt-icon"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
          focusable="false"
        >
          <rect x="8" y="4" width="32" height="40" rx="3" fill="currentColor" opacity="0.15" />
          <rect x="12" y="10" width="16" height="2" rx="1" fill="currentColor" />
          <rect x="12" y="15" width="24" height="2" rx="1" fill="currentColor" />
          <rect x="12" y="20" width="20" height="2" rx="1" fill="currentColor" />
          <rect x="12" y="25" width="24" height="2" rx="1" fill="currentColor" />
          <circle cx="34" cy="34" r="10" fill="var(--color-accent)" />
          <path d="M34 30v4m0 4h.01" stroke="white" strokeWidth="2" strokeLinecap="round" />
          <path d="M30 34a4 4 0 1 0 8 0 4 4 0 0 0-8 0z" stroke="white" strokeWidth="1.5" />
        </svg>
      </div>

      <h1 className="capture-home__title">Financial OS</h1>
      <p className="capture-home__tagline">Private receipt capture</p>

      {/* Primary: camera capture via HTML Media Capture */}
      <button
        type="button"
        className="btn btn--primary btn--large"
        aria-label="Photograph a receipt"
        onClick={() => cameraInputRef.current?.click()}
      >
        Photograph receipt
      </button>

      {/* Hidden camera input — HTML Media Capture for reliable iPhone camera access */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
        onChange={handleFiles}
      />

      {/* Fallback: photo library */}
      <button
        type="button"
        className="btn btn--ghost btn--small"
        aria-label="Choose existing photo from library"
        onClick={() => libraryInputRef.current?.click()}
      >
        Choose existing photo
      </button>

      <input
        ref={libraryInputRef}
        type="file"
        accept="image/*"
        multiple
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
        onChange={handleFiles}
      />

      <nav className="capture-home__nav" aria-label="Secondary navigation">
        <Link to="/receipts" className="link">
          Recent receipts
        </Link>
      </nav>
    </main>
  );
}
