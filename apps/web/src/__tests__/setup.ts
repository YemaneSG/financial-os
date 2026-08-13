import "@testing-library/jest-dom";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

// Provide crypto.randomUUID in test environment.
if (typeof crypto === "undefined" || typeof crypto.randomUUID === "undefined") {
  Object.defineProperty(globalThis, "crypto", {
    value: {
      randomUUID: () => "test-uuid-1234-5678-abcd-ef0123456789",
      getRandomValues: (arr: Uint8Array) => {
        for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
        return arr;
      },
    },
    writable: true,
  });
}

// Provide URL.createObjectURL / revokeObjectURL stubs.
if (typeof URL.createObjectURL === "undefined") {
  URL.createObjectURL = vi.fn(() => "blob:test-url");
  URL.revokeObjectURL = vi.fn();
}

// Suppress firebase initialization errors in unit tests.
vi.mock("firebase/app", () => ({
  initializeApp: vi.fn(),
  getApps: vi.fn(() => []),
}));

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(() => ({})),
  GoogleAuthProvider: vi.fn(() => ({})),
  signInWithPopup: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChanged: vi.fn((_, cb) => {
    cb(null);
    return vi.fn();
  }),
}));

vi.mock("@/auth/firebaseConfig", () => ({
  firebaseConfig: {
    apiKey: "test-key",
    authDomain: "test.firebaseapp.com",
    projectId: "test-project",
    storageBucket: "test.appspot.com",
    messagingSenderId: "123456",
    appId: "1:123456:web:abcdef",
  },
}));
