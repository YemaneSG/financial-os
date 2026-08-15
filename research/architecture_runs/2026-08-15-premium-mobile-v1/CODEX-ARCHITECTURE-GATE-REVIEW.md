# Premium Mobile v1 — Architecture Gate Review

**Date:** 2026-08-15
**Reviewer:** Codex operating lead
**Artifact reviewed:** `OPUS-ARCHITECTURE-PROPOSAL.md`
**Verdict:** **Approve with conditions as a technical direction; reject for
implementation under the current repository authority.**

Claude Sonnet was requested as the independent second reviewer. Its authentication
provider required interactive reauthentication (`invalid_rapt`), so no Sonnet
verdict was produced or inferred. This review is labeled accurately and is not
presented as an independent Claude review.

## Release-blocking authority conflict

The proposal is for a new, separate product track, but the current canonical
contract authorizes only the existing receipt PWA:

- `AGENTS.md:22` says Plaid was rejected from Wave 1.
- `AGENTS.md:30-36` defines the authorized product as the private iPhone receipt
  PWA and authorizes nothing outside its capture flow.
- `AGENTS.md:86` prohibits Plaid, Android, bank connectors, matching, and analytics
  without a current owner-approved execution packet.
- `docs/product/premium-mobile-app-PRD.md:48` requires Plaid immediately and
  `:228` requires Android packaging, while `:6` explicitly says that the document
  alone does not authorize implementation.
- No execution packet in `docs/implementation/execution-packets/` covers the new
  premium application.

This is not a technical rejection of the new application. It is a document-authority
conflict. The existing receipt collector must remain untouched, and no part of
Slice 0 may begin until the owner accepts a canonical separate-track decision and
bounded execution packet.

## Findings

### P0 — Create explicit separate-track authority before implementation

Add an accepted owner decision to the canonical decision register, amend the
roadmap to show the premium app as an independent track, and approve a Slice 0
execution packet with new-app-only file boundaries. State explicitly that the old
Wave 1 Plaid/Android rejection still governs the receipt collector and does not
govern the newly authorized product track. Do not modify frozen receipt contracts.

### P1 — Freeze the Plaid secret and webhook controls in the packet

`OPUS-ARCHITECTURE-PROPOSAL.md:180` says only “encrypted/server-only” for the
persistent Plaid credential. Before any live credential exists, decide the exact
managed vault or envelope-encryption mechanism, key custody, access grants,
rotation, revocation, backup/restore behavior, and log prohibitions. Define Plaid
webhook authenticity verification, replay/deduplication, cursor transactionality,
and failure recovery as acceptance tests. These controls are triggered by
`docs/security/control-baseline.md:74`.

### P1 — Prove owner-only Firebase-to-Supabase authorization

The proposed text UID, private owner allowlist, RLS, and Firebase `role` claim are
the right shape. Slice 0 must additionally prove session-version invalidation,
token refresh/revocation, issuer/audience/project rejection, zero default grants
to private schemas, explicit grants only to reviewed views/RPCs, and non-owner
denial for every client-readable table and function. No real project identifier or
owner UID may enter repository evidence.

### P1 — Treat mobile Hosted Link return as an evidence gate

Hosted Link is a credible first path, not yet a proven path. Test the external
authentication browser, universal/app link return, interrupted flow, institution
OAuth, resume, and reconnect on a real iPhone and representative Android target.
Stop before building the product shell if this proof fails.

### P1 — Extend the security baseline for the separate application

The current Tier-1 baseline says it applies to the receipt-capture release. Create
a short premium-app addendum covering bank-data classification, local mobile
storage/cache, account masking, export/deletion, device loss, provider revocation,
database grants, webhook ingress, backup/PITR availability, and restore evidence.
No live owner financial data is allowed before those applicable MUST controls are
accepted and tested.

### P2 — Avoid speculative future schema

Do not create `guidance_events` or `outcome_events` in v1. The concepts belong in
the research/architecture record, but physical tables should wait for an approved
future guidance packet and evidence that the contracts are needed.

### P2 — Keep reflection sampling observable without forcing experimentation

Every exposure needs selection reason, policy version, completion/skip outcome,
and—only when truly randomized—selection probability. Missing feedback remains
missing evidence. V1 can use deterministic representative controls; a randomized
behavioral experiment requires a later explicit owner decision and protocol.

## Minimum owner actions

1. Accept the premium mobile app as a separate canonical product track alongside
   the unchanged receipt collector.
2. Approve the architecture direction and authorize creation of the Slice 0
   packet—not production deployment or live-data use.
3. Approve the premium-app security addendum before Plaid Trial/live data.

After actions 1 and 2, the bounded synthetic Slice 0 proof may begin. Live Plaid
credentials, production resources, owner financial data, frozen-contract changes,
and friends-and-family access remain separately gated.
