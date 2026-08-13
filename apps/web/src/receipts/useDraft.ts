import { useState, useCallback, useRef } from "react";

export interface DraftImage {
  id: string;
  file: File;
  objectUrl: string;
}

export interface UploadProgress {
  assetId: string;
  ordinal: number;
  loaded: number;
  total: number;
  done: boolean;
  error: string | null;
}

export interface DraftState {
  clientSubmissionKey: string;
  images: DraftImage[];
  uploadProgressMap: Record<string, UploadProgress>;
  phase: "idle" | "drafting" | "uploading" | "finalizing" | "saved";
  savedReceiptId: string | null;
  acknowledgedAt: string | null;
  errorMessage: string | null;
}

function makeDraftImage(file: File): DraftImage {
  return {
    id: crypto.randomUUID(),
    file,
    objectUrl: URL.createObjectURL(file),
  };
}

function newKey(): string {
  if (typeof crypto.randomUUID !== "function") {
    throw new Error(
      "crypto.randomUUID() is unavailable in this context. Use HTTPS.",
    );
  }
  return crypto.randomUUID();
}

export function useDraft() {
  const keyRef = useRef<string>(newKey());

  const [state, setState] = useState<DraftState>({
    clientSubmissionKey: keyRef.current,
    images: [],
    uploadProgressMap: {},
    phase: "idle",
    savedReceiptId: null,
    acknowledgedAt: null,
    errorMessage: null,
  });

  const revokeImage = useCallback((img: DraftImage) => {
    URL.revokeObjectURL(img.objectUrl);
  }, []);

  const addImages = useCallback(
    (files: File[]) => {
      const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/heic", "image/heif", "image/webp"];
      const MAX_BYTES = 10 * 1024 * 1024;
      const MAX_COUNT = 10;

      const errors: string[] = [];
      const valid: File[] = [];

      for (const file of files) {
        if (!ALLOWED_TYPES.includes(file.type) && !file.name.toLowerCase().match(/\.(heic|heif)$/)) {
          errors.push(`"${file.name}" is not a supported image format (JPEG, PNG, HEIC, WebP).`);
          continue;
        }
        if (file.size > MAX_BYTES) {
          errors.push(`"${file.name}" exceeds the 10 MB limit.`);
          continue;
        }
        valid.push(file);
      }

      setState((prev) => {
        const total = prev.images.length + valid.length;
        if (total > MAX_COUNT) {
          return {
            ...prev,
            errorMessage: `A receipt can have at most ${MAX_COUNT} images.`,
          };
        }
        const newImages = valid.map(makeDraftImage);
        return {
          ...prev,
          images: [...prev.images, ...newImages],
          phase: prev.images.length === 0 && newImages.length > 0 ? "drafting" : prev.phase,
          errorMessage: errors.length > 0 ? errors.join(" ") : null,
        };
      });
    },
    [],
  );

  const removeImage = useCallback(
    (id: string) => {
      setState((prev) => {
        const target = prev.images.find((i) => i.id === id);
        if (target) revokeImage(target);
        const images = prev.images.filter((i) => i.id !== id);
        return {
          ...prev,
          images,
          phase: images.length === 0 ? "idle" : prev.phase,
        };
      });
    },
    [revokeImage],
  );

  const replaceImage = useCallback(
    (id: string, file: File) => {
      setState((prev) => {
        const target = prev.images.find((i) => i.id === id);
        if (target) revokeImage(target);
        return {
          ...prev,
          images: prev.images.map((img) =>
            img.id === id ? makeDraftImage(file) : img,
          ),
        };
      });
    },
    [revokeImage],
  );

  const setPhase = useCallback((phase: DraftState["phase"]) => {
    setState((prev) => ({ ...prev, phase }));
  }, []);

  const setUploadProgress = useCallback((progress: UploadProgress) => {
    setState((prev) => ({
      ...prev,
      uploadProgressMap: {
        ...prev.uploadProgressMap,
        [progress.assetId]: progress,
      },
    }));
  }, []);

  const setSaved = useCallback((receiptId: string, acknowledgedAt: string) => {
    setState((prev) => ({
      ...prev,
      phase: "saved",
      savedReceiptId: receiptId,
      acknowledgedAt,
    }));
  }, []);

  // Sets an error message without changing the phase — the current screen handles
  // the error in context (upload screen shows retry, draft screen shows inline alert).
  const setError = useCallback((msg: string) => {
    setState((prev) => ({ ...prev, errorMessage: msg }));
  }, []);

  const reset = useCallback(() => {
    const freshKey = newKey();
    keyRef.current = freshKey;
    setState((prev) => {
      prev.images.forEach(revokeImage);
      return {
        clientSubmissionKey: freshKey,
        images: [],
        uploadProgressMap: {},
        phase: "idle",
        savedReceiptId: null,
        acknowledgedAt: null,
        errorMessage: null,
      };
    });
  }, [revokeImage]);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, errorMessage: null }));
  }, []);

  return {
    state,
    addImages,
    removeImage,
    replaceImage,
    setPhase,
    setUploadProgress,
    setSaved,
    setError,
    reset,
    clearError,
  };
}
