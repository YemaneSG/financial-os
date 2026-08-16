# Premium Mobile PM-0B — Native Return Preparation

**Date:** August 16, 2026
**Status:** Credential-free local preparation complete; current native builds and
device returns pending
**Boundary:** Synthetic Plaid Sandbox only; no real financial data, token exchange,
persistent Item, production deployment, or receipt-service change

## Outcome prepared

- One fixed custom-scheme completion URI is declared on iOS and Android.
- The app accepts only the exact token-free completion URI. It reduces an
  approved return to `completion` or `oauth-return`, discards the raw URL, and
  does not log or persist query/fragment material.
- The callback displays only a neutral checking state. It is not proof of Plaid
  success; the subject-bound server session remains authoritative.
- The server uses mobile Hosted Link mode only when a privately supplied HTTPS
  redirect passes strict structural validation. Without that value, it remains
  in the already-proven PM-0A browser mode.
- Credential-free GitHub lanes compile Android and an unsigned iOS simulator app
  on macOS 26/Xcode 26 only when premium-mobile inputs change.

## Corrected integration defect

The PM-0A server configuration and generated native projects used different
custom schemes. The mismatch was found before a device claim and corrected to
one exact URI across server configuration, iOS, Android, client policy, and
tests.

## Local verification

| Check | Result |
|---|---|
| Mobile lint | Pass |
| Mobile TypeScript | Pass |
| Mobile unit tests | Pass — 17/17 |
| Mobile production build | Pass |
| Edge authorization/Hosted Link tests | Pass — 25/25 |
| Capacitor native synchronization | Pass — iOS and Android |
| iOS plist and shared-scheme XML | Pass |
| Generated bundle credential scan | Pass |
| Tracked private-data scan | Pass |
| Diff/whitespace check | Pass |
| Receipt isolation | Pass — no receipt client, API, domain, contract, migration, or infrastructure file changed |

The first hosted Android compile reached Capacitor and failed before application
compilation because the workflow selected JDK 17 while Capacitor Android requires
source release 21. The workflow was corrected to JDK 21; no product or security
contract changed. The first macOS 26/Xcode 26 unsigned simulator build passed.

## Remaining acceptance evidence

1. Obtain green GitHub Android and macOS 26/Xcode 26 builds.
2. Select one owner-controlled HTTPS host and publish the exact Apple association
   and Android Digital Asset Links documents for the signed app.
3. Register the HTTPS redirect with Plaid and privately configure the Edge
   Function for native mode.
4. Recreate one bounded synthetic owner subject and server-held Sandbox session.
5. Demonstrate success, cancel, interruption, cold start, resume, forged return,
   and replay behavior on a real iPhone and Android emulator.
6. Inspect device logs, crash output, navigation state, preferences, cache,
   screenshots, bundle, and CI output for callback or credential leakage.

PM-0 is not complete until the real-iPhone and Android-emulator rows pass.
