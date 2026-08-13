import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { initializeApp, getApps } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  type User,
} from "firebase/auth";
import { firebaseConfig } from "./firebaseConfig";
import { setTokenProvider } from "@/api/client";

// Initialize Firebase once.
if (getApps().length === 0) {
  initializeApp(firebaseConfig);
}

const auth = getAuth();
const googleProvider = new GoogleAuthProvider();

export type AuthState =
  | { status: "loading" }
  | { status: "unauthenticated" }
  | { status: "authenticated"; user: User }
  | { status: "forbidden"; reason: string };

interface AuthContextValue {
  authState: AuthState;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  signInError: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({ status: "loading" });
  const [signInError, setSignInError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setAuthState({ status: "authenticated", user });
      } else {
        setAuthState({ status: "unauthenticated" });
      }
    });
    return unsubscribe;
  }, []);

  // Wire the API client token provider to Firebase's current user.
  useEffect(() => {
    setTokenProvider(async () => {
      const currentUser = auth.currentUser;
      if (!currentUser) return null;
      try {
        return await currentUser.getIdToken();
      } catch {
        return null;
      }
    });
  }, []);

  const signIn = useCallback(async () => {
    setSignInError(null);
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Sign-in failed. Please try again.";
      // Never expose raw Firebase error details — show a safe message.
      if (msg.includes("popup-closed") || msg.includes("cancelled")) {
        setSignInError("Sign-in was cancelled.");
      } else if (msg.includes("network")) {
        setSignInError("Network error. Check your connection and try again.");
      } else {
        setSignInError("Sign-in failed. Please try again.");
      }
    }
  }, []);

  const signOut = useCallback(async () => {
    await firebaseSignOut(auth);
    setAuthState({ status: "unauthenticated" });
  }, []);

  return (
    <AuthContext.Provider value={{ authState, signIn, signOut, signInError }}>
      {children}
    </AuthContext.Provider>
  );
}

// This module intentionally colocates the provider and its consumer hook.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
