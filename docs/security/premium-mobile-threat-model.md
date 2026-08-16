# Premium Mobile — Slice 0 Threat Model

**Status:** Gate A revision 2
**Date:** August 15, 2026
**Scope:** Synthetic PM-0A/PM-0B proof only

## Assets

- Firebase identity/session and private owner subject
- Supabase project and database grants
- Plaid Sandbox client secret and short-lived Link session
- native callback association and application bundle
- receipt-service isolation boundary

No real bank transaction, Plaid Item access token, receipt evidence, or reflection
data belongs in Slice 0.

## Trust boundaries

```text
Device -> Firebase -> Supabase Data API/RLS
Device -> Supabase Edge Function -> Plaid
Device -> Hosted Link browser -> application callback
Supabase private server path -> project secrets/database
Premium app -> existing receipt API (untouched and unused in Slice 0)
CI/hosted native builder -> signed build artifact -> test device
```

## Threats and required controls

| Threat | Control and evidence |
|---|---|
| Valid but non-owner Firebase token | Exact issuer, audience, role, text subject, active, and session-version predicate; negative Data API and Edge Function tests |
| Supabase-native token with matching subject | Exact Firebase issuer/audience denial test |
| Stolen already-issued ID token | Immediate private active/version check on every request; provider refresh revocation plus device-loss runbook |
| Custom-claim overwrite weakens another application | Dedicated synthetic subject; private read-modify-write/rollback record; never touch receipt allowlist |
| Edge Function uses service role before owner authorization | First call the common active-owner predicate with caller JWT; administrative client is inaccessible before success |
| Legacy Edge gateway rejects Firebase tokens or bypass is mistaken for trust | Disable only the incompatible legacy-secret check; pass the unchanged bearer to the registered Data API verifier and common predicate; fail closed on any verifier error |
| Forged or replayed mobile callback | Callback is UI-only; short-lived server session bound to subject; server checks exact Link session; single-use/expiry/cross-subject tests |
| Link or public token leaks through URI/log | No token in callback; redact URLs/query strings; device console, crash, cache, screenshot, bundle, and CI scans |
| Plaid secret reaches client | Edge Function project secret only; bundle and source scan; client cannot enumerate secrets |
| Dependency or CI compromise | Frozen lockfile, pinned supported majors, minimal workflow permissions, credential-free PR checks, secrets only in approved integration environment |
| Synthetic project accidentally becomes production | Explicit owner/account/region/purpose, no-live-data banner, billing ceiling/no-upgrade rule, resource register, teardown/retention decision |
| Receipt service is modified accidentally | Path boundary and diff test over receipt code/contracts/migrations/infra; no receipt call in PM-0 |
| Obsolete native build appears release-ready | PM-0B requires Xcode 26/iOS 26 and approved Android target; Xcode 15.2 output is non-release evidence only |

## Residual risk

Sandbox does not prove every institution OAuth path; cloud/native toolchain remains
an external dependency; hosted provider behavior can change; a synthetic proof
does not validate future Vault, sync, backup, deletion, or live-data controls.
