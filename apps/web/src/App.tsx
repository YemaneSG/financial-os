import type { ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/auth/AuthProvider";
import { SignInScreen } from "@/auth/SignInScreen";
import { CapturePage } from "@/receipts/CapturePage";
import { ReceiptsDiscovery } from "@/receipts/ReceiptsDiscovery";
import { ReceiptDetailPage } from "@/receipts/ReceiptDetail";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { ErrorBoundary } from "@/components/ErrorBoundary";

function RequireAuth({ children }: { children: ReactNode }) {
  const { authState } = useAuth();

  if (authState.status === "loading") {
    return <LoadingSpinner label="Checking session…" />;
  }

  if (authState.status === "unauthenticated" || authState.status === "forbidden") {
    return <SignInScreen />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RequireAuth>
            <CapturePage />
          </RequireAuth>
        }
      />
      <Route
        path="/receipts"
        element={
          <RequireAuth>
            <ReceiptsDiscovery />
          </RequireAuth>
        }
      />
      <Route
        path="/receipts/:receiptId"
        element={
          <RequireAuth>
            <ReceiptDetailPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <div className="app-shell">
            <AppRoutes />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}
