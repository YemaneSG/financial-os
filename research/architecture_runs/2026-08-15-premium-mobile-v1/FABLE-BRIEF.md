# Claude Fable Architecture Brief — Premium Mobile Financial OS v1

You are the principal architect for a fast, bounded architecture pass. Produce a
decision-ready architecture for a new greenfield premium mobile application. Do
not implement code, modify files, deploy resources, or change the operating
receipt collector.

## Read first

Read these artifacts completely:

1. `docs/product/premium-mobile-app-PRD.md` — authoritative for the new app.
2. `research/research_runs/2026-08-15-premium-mobile-r1/CONSOLIDATED-TRACKS-2-8.md`
3. `research/research_runs/2026-08-15-premium-mobile-r1/RESULT-G-TRACK-1-BEHAVIORAL-SIGNALS.md`
4. `research/research_runs/2026-08-15-premium-mobile-r1/AUDIT-E-PLATFORM.md`
5. `research/research_runs/2026-08-15-premium-mobile-r1/AUDIT-F-COMPETITIVE-HCI.md`
6. `docs/security/control-baseline.md` — apply its durable/privacy/security floor
   where relevant; do not inherit its old frontend/provider choice as a new-app
   requirement.
7. `contracts/openapi.yaml` — existing receipt API boundary.
8. `docs/architecture/implementation-contracts.md` — existing receipt invariants
   and ceilings only.
9. `src/financial_os/routers/receipts.py`, `src/financial_os/routers/search.py`,
   `src/financial_os/schemas/receipt.py`, and relevant auth/config code only as
   needed to understand current integration capability.

## Frozen owner decisions

- The current receipt collector is a separate operating production track. It
  continues collecting and enriching data. Do not replace, migrate, fork, or
  redesign it in this architecture.
- The new application is greenfield and lives alongside the collector.
- Angular + TypeScript + Capacitor is the mobile client direction.
- Supabase is the default platform for new application data and bounded backend
  functions, not an automatic replacement for existing receipt infrastructure.
- Plaid Transactions is in the first release and is the main new data source.
- V1 is private and single-owner, optimized for the fastest useful build in the
  owner's hands; controlled friends-and-family follows later.
- V1 behavioral experience is awareness and reflection, not pre-purchase
  guidance.
- Core experience: Home, Activity, Reflect, Connections/Settings.
- Reflection is a fast swipe-oriented but accessible flow over purchases and
  receipt line items: serving/not serving, buy again, plannedness, necessity,
  use, value/regret, skip, optional reason.
- Financial truth and calculations are deterministic. LLMs interpret and propose;
  they never become the ledger or mutate authoritative truth directly.
- Keep the design simple, reversible, and implementation-ready. Avoid microservices,
  event buses, Kubernetes, Redis, or speculative scale infrastructure.

## Preferred identity simplification

Current official Supabase documentation supports Firebase Auth as a first-class
third-party authentication provider. Prefer one existing Firebase owner session
for both systems:

- existing receipt API continues verifying the same Firebase token;
- Supabase is configured to trust the registered Firebase project JWT;
- the mobile Supabase client supplies the current Firebase ID token;
- RLS restricts every financial row to the exact owner identity and registered
  issuer/audience;
- no separate Supabase login UX in v1;
- document custom role claim, token refresh, revocation, and negative tests.

If evidence in the repository makes this unsafe or infeasible, explain precisely
and choose the next-smallest alternative. Do not emit any real provider IDs.

## Plaid constraints

- Begin with Sandbox; Trial/live follows provider enablement.
- Transactions, incremental sync, pending/posted lifecycle, webhook verification,
  connection revocation, and idempotency are required.
- Plaid secrets and persistent credentials remain server-side and outside client
  bundles and logs.
- No money movement, Auth/ACH transfer, lending, or investment features.

## Required architecture output

Return one concise but implementation-ready document with:

1. **Executive decision** — chosen topology and why it is the smallest safe path.
2. **System context diagram** — new app, Supabase, Plaid, existing receipt API,
   existing receipt database/storage, AI provider boundary.
3. **Component topology** — mobile modules, server/edge functions, Postgres
   schemas/domains, scheduled/background work, adapter boundaries.
4. **Domain authority table** — exact system of record for accounts/connections,
   transactions, receipts, receipt revisions/items, matches, owner feedback,
   inferred signals, guidance/outcomes, auth identity.
5. **Identity and authorization flow** — Firebase-to-Supabase third-party auth,
   owner-only RLS, receipt API authorization, issuer/audience/role checks,
   revocation, negative tests.
6. **Plaid lifecycle** — Link token, public-token exchange, access credential
   handling, transaction sync cursor, webhooks, reconciliation, retries, failure
   states, disconnect.
7. **Receipt integration** — use current endpoints where sufficient; list any
   minimal additive adapter/contract delta separately. Do not change frozen
   contracts silently.
8. **Transaction/receipt matching** — deterministic candidate inputs, confirmed /
   rejected / unresolved states, owner correction, provenance, idempotency.
9. **Minimum data model** — concepts, ownership, key invariants, relationships,
   and money types; no exhaustive DDL.
10. **Behavioral evidence model** — separation of source facts, deterministic
    facts, inferred candidates, owner labels, future guidance, outcomes;
    versioning, confidence, abstention, correction scope.
11. **Mobile architecture** — Angular boundaries, state/query management,
    Capacitor/native responsibilities, secure session handling, caching/offline
    boundary, accessible swipe alternatives.
12. **AI boundary** — what v1 needs, if anything; cheapest model routing and
    deterministic-first design; do not add AI merely because future guidance uses
    it.
13. **Security and privacy** — threat boundaries, secrets, RLS, logging, deletion,
    export, receipt capabilities, App Store/Play disclosures.
14. **Reliability and operations** — sync/idempotency, backups, migration order,
    observability, cost controls, rollback, receipt-collector independence.
15. **Alternatives rejected** — especially direct receipt DB access, full receipt
    migration, dual auth UX, client-side Plaid secrets, and speculative services.
16. **ADRs required** — a short list with proposed decisions.
17. **Bounded implementation slices** — ordered for fastest owner value. The first
    slice must put an installable Angular/Capacitor shell with owner auth and Plaid
    Sandbox activity into the owner's hand; subsequent slices add receipt adapter,
    matching, reflection, and live Plaid acceptance.
18. **Acceptance evidence per slice** — executable proof, not completion claims.
19. **Stop/escalate conditions** — provider access, auth incompatibility, receipt
    contract delta, data-loss path, or store/distribution blocker.

## Quality rules

- Clearly label observed repository fact, owner decision, architecture decision,
  inference, and open experiment.
- Do not include real account data, receipt content, provider/project identifiers,
  credentials, signed URLs, or production resource names.
- Do not ask broad discovery questions already answered in the PRD.
- Make a decision. Do not return a menu of equally weighted architectures.
- Prefer the simplest topology that preserves the receipt collector and can be
  implemented today.
- End with a stop statement explaining why the architecture is sufficient to
  begin the first implementation slice.
