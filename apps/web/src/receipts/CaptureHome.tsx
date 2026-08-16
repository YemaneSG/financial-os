import React, { useRef } from "react";
import { Link } from "react-router-dom";
import { ReceiptDashboard } from "./ReceiptDashboard";

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

  const today = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());

  return (
    <main className="capture-home" aria-label="Capture receipt">
      <header className="premium-appbar">
        <div>
          <p>Financial OS</p>
          <span>{today}</span>
        </div>
        <Link to="/receipts" className="premium-profile" aria-label="Open receipt history">
          YO
        </Link>
      </header>

      <div className="capture-home__content">
        <section className="capture-home__intro" aria-labelledby="capture-home-heading">
          <p className="premium-kicker">Your financial memory</p>
          <h1 id="capture-home-heading">Capture it. Trust that it’s there.</h1>
          <p>Photograph the receipt now. Review and enrich it when you have time.</p>
        </section>

        <section className="premium-capture-card" aria-label="New receipt">
          <div className="premium-capture-card__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false">
              <path d="M4 8.5h3l1.4-2h7.2l1.4 2h3v10H4v-10Zm8 7a3.25 3.25 0 1 0 0-6.5 3.25 3.25 0 0 0 0 6.5Z" />
            </svg>
          </div>
          <div className="premium-capture-card__copy">
            <p className="premium-kicker">Private and durable</p>
            <h2>Save a receipt</h2>
            <p>One clear photo is fastest. Long receipts can use up to ten ordered photos.</p>
          </div>

          <button
            type="button"
            className="btn btn--primary btn--large premium-capture-primary"
            aria-label="Photograph a receipt"
            onClick={() => cameraInputRef.current?.click()}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 8.5h3l1.4-2h7.2l1.4 2h3v10H4v-10Zm8 7a3.25 3.25 0 1 0 0-6.5 3.25 3.25 0 0 0 0 6.5Z" />
            </svg>
            Photograph receipt
          </button>

          <button
            type="button"
            className="premium-library-action"
            aria-label="Choose existing photo from library"
            onClick={() => libraryInputRef.current?.click()}
          >
            Choose from photos
          </button>

          <p className="premium-durability-note">
            <span aria-hidden="true">✓</span>
            “Saved” appears only after every photo is durably verified.
          </p>
        </section>

        <ReceiptDashboard />
      </div>

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

      <nav className="premium-bottom-nav" aria-label="Primary navigation">
        <span className="premium-bottom-nav__active" aria-current="page">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8.5h3l1.4-2h7.2l1.4 2h3v10H4v-10Zm8 7a3.25 3.25 0 1 0 0-6.5 3.25 3.25 0 0 0 0 6.5Z" /></svg>
          Capture
        </span>
        <Link to="/receipts">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Zm3 5h6M9 12h6" /></svg>
          Receipts
        </Link>
      </nav>
    </main>
  );
}
