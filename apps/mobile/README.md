# Financial OS Premium Mobile

This directory is the isolated Angular/Capacitor application for the premium
mobile product track.

PM-0 uses synthetic Firebase identities and Plaid Sandbox data only. It does
not call or modify the operating receipt service, connect a real bank, exchange
a Plaid public token, or persist private financial data.

## Local checks

Run from the repository root with the pinned Node 24 and pnpm 11 toolchain:

- `pnpm mobile:lint`
- `pnpm mobile:type-check`
- `pnpm mobile:test`
- `pnpm mobile:build`

`capacitor.config.ts` points to the Angular browser build. The generated `ios/`
and `android/` projects are preparation only; PM-0B requires Xcode 26, a real
iPhone, and an Android SDK/emulator before native evidence can pass.

## Runtime configuration

Firebase and Supabase public client configuration is injected privately at
runtime through `__FINANCIAL_OS_PREMIUM_CONFIG__`. No real project identifier or
credential belongs in source, tests, screenshots, logs, or CI artifacts.

## Native return boundary

The fixed completion URI is token-free and wakes the app only. The client never
uses it as proof that Link succeeded; the exact subject-bound server session
must be refreshed before an outcome is shown. The raw callback URL is discarded
without logging or persistence.

PM-0B still requires an owner-controlled HTTPS Universal/App Link for institution
OAuth return. That verified host is deliberately absent until its domain,
Apple association, Android signing fingerprint, and Plaid allowlist are real.
