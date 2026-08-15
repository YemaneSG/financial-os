# Premium Mobile PM-0A — Scaffold Evidence

**Date:** August 15, 2026
**Issue:** `#14 — Initialize isolated Angular/Capacitor proof and CI`
**Status:** Local acceptance complete; credential-free GitHub CI pending
**Data boundary:** Synthetic configuration only; no real financial data

## Outcome

An isolated Angular 22 and Capacitor 8 application now builds from the repository
workspace without changing the operating receipt product. iOS and Android project
files are generated for the later PM-0B lane. Their existence is not native build
or device-return evidence.

## Frozen toolchain and primary dependencies

| Component | Version |
|---|---:|
| Node | 24.19.0 locally; CI uses supported Node 24 |
| pnpm | 11.19.0 |
| Angular framework | 22.1.2 |
| Angular CLI/build | 22.1.4 |
| Capacitor core/CLI/platforms | 8.5.0 |
| Capacitor App | 8.1.1 |
| Capacitor Browser | 8.0.4 |
| Supabase JavaScript | 2.112.3 |
| Firebase JavaScript | 12.17.1 |

Exact transitive versions and integrity values are frozen in `pnpm-lock.yaml`.
Package build scripts are denied by default. The inspected pinned build helpers
`@firebase/util`, `@parcel/watcher`, `esbuild`, `lmdb`, `msgpackr-extract`, and
`protobufjs` are the explicit allowlist.

## Local verification

| Check | Result |
|---|---|
| Frozen install | Pass — workspace lockfile installs without change |
| ESLint | Pass |
| TypeScript | Pass |
| Unit tests | Pass — 2 files, 4 tests |
| Angular production build | Pass — 190.29 kB initial raw bundle, 52.33 kB estimated transfer |
| Capacitor configuration/plugin discovery | Pass |
| iOS project generation | Pass; build/device evidence deferred to PM-0B |
| Android project generation | Pass; build/emulator evidence deferred to PM-0B |
| Private-data scan | Pass |
| Built-bundle credential-pattern scan | Pass — no matches |
| Receipt protected-path diff | Pass — no changes under receipt client/API/domain/tests/migrations/contracts/infra |
| Production dependency licenses | Pass — permissive 0BSD, Apache-2.0, BSD-3-Clause, ISC, and MIT only |

The workspace advisory audit reports three pre-existing moderate React Router
advisories, all through `apps/web`; it reports no path through the new mobile
workspace. The execution packet forbids changing the receipt product in this
slice, so those findings remain an existing-track maintenance item rather than a
PM-0A scaffold change.

## Host-specific observation

Angular's optional native LMDB disk cache aborts under the current Intel macOS
13 host during production optimization. The crash report identifies the LMDB
`EnvWrap` native path. Disabling the Angular CLI disk cache makes the production
build deterministic and green; this does not change application output. Linux CI
provides an independent build lane.

## Remaining before issue completion

- Push this scaffold and receive a successful credential-free GitHub CI run.
- Record the resulting commit and run link in this evidence file.

PM-0A as a whole remains open. Firebase/Supabase authorization and Plaid Hosted
Link session proof are tracked separately and require private external sessions.
