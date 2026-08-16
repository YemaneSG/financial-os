# Premium Mobile PM-0A — Hosted Authorization Evidence

**Date:** August 15, 2026
**Issue:** `#15 — Prove Firebase owner authorization through Supabase`
**Status:** Hosted authorization and signed-token lifecycle matrix complete
**Data boundary:** Dedicated synthetic subject only; no financial data

## Hosted resources and controls

- Created one isolated free Supabase development project in the owner-approved
  East US (Ohio) region.
- Left the unrelated existing Supabase project unchanged.
- Enabled the Data API, disabled automatic exposure of new tables, and enabled
  automatic RLS for new public tables.
- Registered the existing Firebase project as a third-party identity provider.
- Did not upgrade a plan or modify the receipt product's real owner account.
- Created one deterministic synthetic Firebase subject and set only
  `role = authenticated` and a bounded `session_version` custom claim.
- Provisioned exactly one enabled Firebase provider relationship and one active
  owner relationship in the private Supabase schema. No private identifier is
  recorded in this artifact.

## Hosted verification

| Check | Result |
|---|---|
| Source-controlled migration | Pass — applied successfully in the isolated project |
| Aggregated pgTAP matrix | Pass — `all_passed = true`, `assertion_count = 26`, no failures |
| Provider relationship | Pass — exactly one enabled provider |
| Owner relationship | Pass — exactly one active owner at session version 7 |
| Edge Function deployment | Pass — caller-scoped function deployed with no service-role client |
| Legacy Supabase JWT gate | Disabled intentionally; it accepts only Supabase legacy-signed JWTs, not registered Firebase JWTs |
| Function authentication boundary | Firebase bearer is forwarded unchanged to the registered Data API integration, then the common owner RPC evaluates exact issuer/audience/role/subject/version |
| Anonymous invocation | Denied fail-closed with fixed `authorization_unavailable` response; no data or internal detail |
| Unsupported HTTP method | Denied with 405 before authorization work |
| Valid Firebase owner token | Pass — Edge boundary returned 204 with an empty body |
| Stale session version | Pass — prior token denied with fixed 403 `owner_required` |
| Refreshed session version | Pass — newly issued token returned 204 |
| Inactive owner | Pass — issued token denied immediately with fixed 403; restoration returned 204 |
| Disabled Firebase relationship | Pass — issued token denied with fixed 403; restoration returned 204 |
| Direct Data API/RLS | Pass — valid token returned exactly the one synthetic proof row |
| Final synthetic-owner state | Pass — private owner row inactive and the synthetic Firebase subject deleted |
| Temporary sign-in path | Pass — Email/Password was enabled only to mint the synthetic integration token, then disabled after deletion |
| Secret/private-data handling | No credential, token, private identifier, or project reference entered repository evidence |
| Receipt isolation | Existing receipt application and authorization unchanged |

The Supabase SQL editor presents only the final result set of a multi-statement
pgTAP script. For an unambiguous hosted verdict, the same 26 assertion calls
were recorded in a transaction-local result table; the final aggregate returned
`true`, `26`, and an empty failure collection. The transaction rolled back its
synthetic provider/owner test fixtures.

Cloud Shell could administer Firebase users and custom claims but could not sign
a custom token: the default signer was absent and the available user lacked
signing permission on an existing service account. No IAM permission was granted.
Instead, Email/Password was enabled temporarily, the dedicated synthetic subject
received a generated synthetic address and one-time random password, and the
Identity Toolkit issued its Firebase ID tokens. The subject was deleted and the
provider disabled immediately after the matrix. Tokens, password, address, keys,
project identifiers, and subject identifiers were not copied into evidence.

## Credential hygiene observation

A generated database password appeared in transient pre-submission browser-tool
output while the project form was being inspected. It was immediately replaced
with a newly generated value before project creation. The exposed candidate was
never submitted, stored, or made valid for the hosted project.

## Remaining PM-0A evidence

- Plaid Sandbox credentials and the subject-bound Hosted Link server/browser
  session matrix remain outstanding.

This artifact claims completion only for the hosted Firebase/Supabase
authorization requirement. It does not claim full PM-0A or native PM-0B
completion.
