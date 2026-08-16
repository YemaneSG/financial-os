# Financial OS Premium Mobile Application — PRD v1

**Status:** Architecture briefing baseline — owner direction captured 2026-08-15
**Owner:** Yemane
**Product scope:** New greenfield mobile application
**Existing receipt collector:** Separate operating product; retained unchanged
**Implementation authorization:** Not granted by this document alone

## 1. Product statement

Build a private, premium, downloadable personal finance application that combines
live bank transactions, item-level receipt evidence, and lightweight personal
feedback so the owner can understand which purchases serve their life and which
do not.

The first release creates awareness and reflection. It does not attempt
pre-purchase coaching. The system begins learning from explicit owner feedback so
future guidance can be grounded in authenticated personal history rather than
generic assumptions.

## 2. Product separation

The working receipt collector remains an independent production system.

- It continues capturing and enriching receipt data.
- Its current database, storage, contracts, durability, and deployment remain
  authoritative for receipts.
- The new application does not replace it, migrate it, or dual-write its data.
- The new application consumes authorized receipt data through a stable API or
  adapter boundary.
- Receipt capture can remain in the existing collector during this release.

## 3. Primary user and distribution

- V1 has one owner and no public registration.
- Optimization target: get a useful build into the owner's hands as quickly as
  possible, then polish through daily use.
- First delivery channel: private development/TestFlight-style distribution.
- Next distribution stage: unlisted or otherwise controlled friends-and-family
  access for feedback.
- Public multi-user launch is a later product decision, not a v1 requirement.

## 4. Product outcomes

V1 succeeds when the owner can:

1. Authenticate from the downloadable mobile application.
2. Connect primary bank and credit-card accounts through Plaid.
3. Import available historical and current transactions without unexplained
   duplication.
4. See a calm, useful summary of spending and recent activity.
5. See item-level receipt evidence from the existing receipt service where it is
   available.
6. Confirm or reject receipt-to-transaction matches.
7. Rapidly reflect on purchases or line items through a swipe-oriented flow.
8. Build a durable personal-value dataset for later behavioral learning.

## 5. V1 experience

### 5.1 Home

One restrained financial pulse rather than a dense dashboard:

- current-period spending;
- recent account activity;
- account and Plaid synchronization status;
- unusual or changed spending presented as factual observations;
- count of purchases or items ready for reflection;
- a clear action to continue reflection.

The home screen does not provide green/yellow/red purchase advice in v1.

### 5.2 Activity

- Unified list of Plaid transactions across connected in-scope accounts.
- Merchant, amount, date, account alias, pending/posted state, category candidate,
  and receipt-match state.
- Search and filters by date, merchant, amount, account, category, and match state.
- Transaction detail with deterministic facts, enrichment, provenance, and linked
  receipt evidence.
- Pending-to-posted transitions do not create duplicate spending.
- Transfers and credit-card payments are distinguishable from expenses.

### 5.3 Reflect

A fast, swipe-oriented review experience inspired by the low-friction interaction
quality of premium mobile finance products without copying their interface.

The unit of reflection can be a purchase or an individual receipt line item.
Each card shows enough factual context to identify the purchase and may ask one
small question at a time.

Initial feedback axes:

- serving me / not serving me / unsure;
- would buy again / would not buy again / unsure;
- planned / unplanned / prompted in the moment / unsure;
- necessary / preferred but optional / discretionary / mixed / unsure;
- used as intended / partly used / unused / not yet known;
- value or regret outcome, when the owner has enough experience to answer.

Rules:

- Swipe actions must have visible labels and accessible non-swipe alternatives.
- Skip is always available.
- No explanation is required to record or change a label.
- An optional short reason can be added afterward.
- Each answer is independently editable and versioned.
- A label is first-party evidence for that purchase at that time, not an eternal
  rule about the merchant or category.
- The reflection queue mixes decision-relevant or uncertain subjects with a
  representative control sample. It must not learn only from purchases already
  suspected to be unusual or low-value.
- Each presented subject records its selection reason, queue-policy version,
  presentation outcome, and randomized selection probability when applicable.
- Missing or skipped feedback is missing evidence, not a negative label.
- No streaks, shame, moralizing, or engagement-for-engagement's-sake.

### 5.4 Connections and settings

- Connect, reconnect, and remove Plaid Items.
- Show synchronization health and last successful update.
- Owner-only session controls and sign out.
- Privacy explanation and cloud-provider boundaries.
- Data export and deletion entry points.
- Feedback and notification controls.

## 6. Bank connectivity

Plaid Transactions is part of the first release, not a later enhancement.

Requirements:

- Start implementation with Plaid Sandbox.
- Move to Plaid Trial/live access as soon as the owner account is enabled.
- Request the maximum useful history supported by the approved Plaid plan and
  participating institution, up to the current product ceiling.
- Use Link for owner-authorized connection.
- Keep Plaid client secrets and persistent access credentials exclusively in a
  server-side boundary controlled by the application.
- Process transaction updates through idempotent synchronization and verified
  webhooks or scheduled reconciliation.
- Store source identifiers and synchronization provenance.
- Preserve pending/posted lifecycle and removals/modifications from incremental
  sync.
- Support connection revocation from the application.
- Do not enable money movement, transfers, lending, or credential collection.

## 7. Receipt integration

V1 treats the existing receipt API as an external domain service.

Minimum consumed capabilities:

- receipt list and search;
- receipt detail and current structured revision;
- line items and totals;
- processing, verification, and duplicate state;
- controlled evidence-image access when needed;
- stable receipt identifiers and purchase dates.

Matching requirements:

- Produce deterministic or scored receipt-to-transaction candidates using amount,
  date, normalized merchant, and available evidence.
- Keep confirmed, rejected, and unresolved match states distinct.
- Never silently merge or delete receipt or transaction evidence.
- A user-confirmed match is first-party evidence and remains auditable.
- Matching may be implemented in the new application platform or an adapter, but
  it must not require changing the receipt collector's database in v1.

## 8. Behavioral signal contract

The application separates six layers:

1. **Source facts:** Plaid transactions and receipt-service evidence.
2. **Deterministic facts:** counts, totals, dates, frequencies, return facts, and
   rolling baselines produced by versioned code.
3. **Inferred candidates:** normalized merchant/product, recurrence, anomaly,
   replacement, match, or behavioral candidates with confidence and provenance.
4. **Owner labels:** plannedness, necessity, use, value, regret, repurchase intent,
   and correction events.
5. **Guidance decisions:** future advisory output such as green/yellow/red/no
   signal, with policy version and cited evidence.
6. **Outcomes:** later owner response, override, use, value, or regret evidence.

V1 implements layers 1–4 and captures the evidence required for layer 6. It does
not ship predictive guidance.

Important boundaries:

- Repetition does not prove habit or value.
- A return does not prove regret.
- High spending does not prove high value.
- A generic category does not prove personal necessity.
- Missing or ambiguous evidence produces abstention, not an invented label.

## 9. Deterministic and AI responsibilities

### Deterministic software owns

- balances, sums, budgets, and arithmetic;
- pending/posted transaction lifecycle;
- transfers and credit-card-payment rules;
- idempotent ingestion and synchronization;
- receipt/transaction evidence preservation;
- confirmed relationships and owner labels;
- frequency, recurrence, and baseline calculations;
- access control and legal state transitions.

### AI may

- normalize merchant or item descriptions;
- propose categories or behavioral candidates;
- interpret patterns;
- explain why an item was surfaced for reflection;
- summarize owner-authenticated history;
- later formulate advisory guidance from deterministic facts and explicit labels.

AI output is non-authoritative, versioned, correctable, and permitted to abstain.
It never directly changes financial truth or calculates authoritative amounts.

## 10. Technology direction

### Mobile client

- Angular and TypeScript.
- Capacitor for iOS and Android packaging and access to required native APIs.
- Native-quality navigation, camera/device behavior where used, lifecycle handling,
  safe-area support, text scaling, accessibility, and performance.

### New application platform

- Supabase is the selected default for new application PostgreSQL data, bounded
  storage needs, and server/edge functions where they fit.
- Prefer reusing the existing Firebase owner identity through Supabase's supported
  Firebase third-party-auth integration so one login authorizes both the receipt
  API and the new Supabase data boundary. Validate this path before introducing a
  second identity system.
- The architecture pass may retain an additional worker or adapter when workload
  duration, secret isolation, receipt compatibility, or reliability requires it.
- Selecting Supabase does not authorize moving the existing receipt database.

## 11. Authentication and authorization

V1 uses the smallest safe single-owner design:

- one allowlisted owner identity;
- no public registration;
- no roles, invitations, teams, or multi-user administration;
- reuse the existing Firebase owner session where the architecture proof confirms
  Supabase third-party-auth compatibility;
- Supabase verifies the Firebase JWT and applies RLS to new application data;
- one mobile login session is presented to the owner, not separate Firebase and
  Supabase login experiences;
- RLS and explicit grants for every client-reachable financial table;
- anonymous and non-owner access fails;
- service-role, Plaid, LLM, and provider secrets never enter the client bundle;
- native deep-link return is tested for the chosen sign-in method;
- revocation and forced reauthentication are supported.

Authentication is required before live Plaid or owner financial data is used.
Synthetic and Sandbox prototypes may temporarily run without owner authentication
only when they contain no real financial data or live credentials.

## 12. Privacy and safety floor

- Private financial content is encrypted in transit and at rest using approved
  managed-service controls.
- Logs contain no transaction descriptions, receipt text, account values, tokens,
  credentials, raw model output, or owner identifiers.
- Plaid credentials and provider secrets remain server-side.
- Cloud LLM input is minimized and sent only through an approved, documented
  boundary.
- Store privacy disclosures reflect actual data collection and providers.
- The owner can disconnect Plaid and initiate export/deletion.
- The application gives no investment, tax, legal, credit, or money-movement
  instruction in v1.
- Behavioral reflection is observational and owner-controlled, not a diagnosis or
  financial-advisor representation.

## 13. V1 quality requirements

- Demonstrated on a real iPhone and an Android device.
- Clear loading, empty, offline, partial-sync, and error states.
- Idempotent Plaid ingestion and retry.
- No unexplained duplicated transactions.
- Accessible interaction without relying exclusively on swipe or color.
- Smooth reflection flow with immediate persistence and undo/edit.
- Factual explanations expose provenance and uncertainty.
- Private evidence remains out of source control, CI artifacts, screenshots, and
  research documents.
- The receipt collector continues operating throughout development and release.

## 14. Initial success evidence

The first useful owner build must demonstrate:

1. Owner authentication.
2. Plaid Sandbox connection followed by Trial/live connection when enabled.
3. Import and display of available transaction history.
4. Stable incremental synchronization with no duplicates.
5. Read-only receipt retrieval through the existing API boundary.
6. At least one receipt-to-transaction candidate and explicit owner disposition.
7. Completion of a multi-item reflection session with versioned feedback.
8. A home view that summarizes factual awareness without predictive coaching.
9. Negative authorization tests and absence of secrets in the client build.

## 15. Explicit non-goals

- Replacing or migrating the existing receipt collector
- Public registration or public multi-user launch
- Green/yellow/red pre-purchase guidance
- Autonomous or blocking financial advice
- Money movement, transfers, lending, or investment execution
- Investment portfolio tracking
- Full tax or accounting product
- Amazon, Costco, or broad email/order ingestion
- Full cross-retailer product catalog normalization
- Social feeds, streaks, leaderboards, or addiction-oriented engagement
- Production MCP/action exposure

## 16. Delivery order

1. Freeze this concise product contract for the architecture pass.
2. Produce one architecture decision and bounded implementation slices.
3. Prove the Angular/Capacitor device shell and Supabase owner boundary with
   synthetic data.
4. Implement Plaid Sandbox ingestion and transaction activity.
5. Add the receipt API adapter and match candidates.
6. Add the reflection flow and home awareness surface.
7. Move to Plaid Trial/live owner acceptance when provider access is enabled.
8. Polish and distribute the private owner build; then prepare controlled
   friends-and-family feedback.

These are delivery gates, not separate long planning phases. Documentation should
remain concise and implementation-focused.

## 17. Architecture questions to resolve now

The architecture pass must decide:

1. Exact Firebase-to-Supabase third-party-auth configuration, owner claim, token
   refresh, revocation, and mobile return flow; use a separate Supabase identity
   only if the proof fails.
2. Server-side Plaid token storage, webhook verification, sync, and reconciliation.
3. Which data domains live in Supabase and which remain behind the receipt API.
4. The smallest receipt-adapter boundary compatible with existing owner
   authorization.
5. Transaction/receipt candidate-matching ownership and deterministic rules.
6. Versioned event/envelope design for inferences and owner feedback.
7. Selection-aware reflection exposure design that supports representative
   controls and later bias evaluation.
8. Background job mechanism for sync and later inference.
9. Offline/cache boundary for private mobile data.
10. TestFlight/private distribution path and later unlisted friends-and-family
   transition.

## 18. Research basis

- `research/research_seed/personal_finance_ai_pre_research_seed.md`
- `research/research_seed/personal_finance_ai_controlled_research_sprint.md`
- `research/research_runs/2026-08-15-premium-mobile-r1/CONSOLIDATED-TRACKS-2-8.md`
- `research/research_runs/2026-08-15-premium-mobile-r1/RESULT-G-TRACK-1-BEHAVIORAL-SIGNALS.md`
- `research/research_runs/2026-08-15-premium-mobile-r1/AUDIT-E-PLATFORM.md`
- `research/research_runs/2026-08-15-premium-mobile-r1/AUDIT-F-COMPETITIVE-HCI.md`
- `research/research_runs/2026-08-15-premium-mobile-r1/SHARED-CONVERSATION-IDEA-PASS.md`

## 19. Stop statement

This PRD is sufficient for architecture. Additional broad research or prolonged
product documentation is not required before the architecture pass.

Implementation must still wait for the architecture decision, security boundary,
and a bounded execution packet that explicitly separates the new application from
the operating receipt collector.
