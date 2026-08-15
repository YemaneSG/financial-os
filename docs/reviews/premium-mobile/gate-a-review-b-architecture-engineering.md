# Premium Mobile Gate A — Architecture and Engineering Review

**Reviewer:** Independent Codex principal architecture subagent
**Mode:** Read-only; no other reviewer output accessed
**Revision 1 verdict:** Approve with conditions
**Revision 2 verdict:** **Approve**

## Independent summary

The architecture correctly separates the operating receipt API from a new
Angular/Capacitor and Supabase/Plaid track. PM-0A proves hosted authorization and
server/browser session semantics; PM-0B proves current native build/deep-link
behavior. No receipt call, financial schema, persistent Plaid Item, matching,
reflection, or live data belongs in PM-0.

## Strengths

- Two independent backends are simpler than a gateway at single-owner scale.
- Firebase UIDs are text and one exact predicate covers Data API and Edge
  Functions.
- Hosted Link is used outside an in-process WebView, and its callback is not
  treated as success or authority.
- File boundaries and receipt-path exclusions are explicit and testable.
- Later exact-money, lifecycle, provenance, owner-decision, and representative
  reflection boundaries remain coherent without speculative infrastructure.

## Revision 1 findings and disposition

| Finding | Revision 2 disposition |
|---|---|
| Current host cannot produce current native evidence | Resolved by PM-0A/PM-0B split; PM-0B still mandatory for completion |
| RLS omitted Supabase-native JWT denial and precise immediate revocation | Resolved with exact issuer/audience/role/sub/active/session-version predicate |
| Hosted Link callback was conflated with connection success | Resolved with subject-bound server session, callback non-authority, and `/link/token/get` |
| Firebase claim overwrite risk | Resolved with dedicated synthetic subject and read-modify-write rollback |
| Missing architecture/threat artifacts | Resolved by Tier-3 architecture and bounded threat model |

## Required execution evidence

- Full Data API and Edge Function identity matrix, including Supabase-native JWT.
- Old-token denial after active/version change.
- Hosted Link cross-subject, forged, stale, duplicate, replay, and expiry tests.
- Secret/log/bundle/grant/private-data scans.
- Path diff proving zero receipt-product changes.
- Xcode 26 real-iPhone return and current Android build/emulator return before PM-0
  completion.

## Residual risks

Sandbox cannot prove every institution OAuth implementation. Provider behavior and
native toolchains remain external dependencies. These do not invalidate PM-0A.

**Verdict: Approve**
