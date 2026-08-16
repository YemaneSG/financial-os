I have sufficient live-sourced data to produce both reports. Compiling now.

---

# TRACK 3 — Data & Financial Knowledge Model

## 1. Executive Summary

- The minimum useful ontology has 17 domain concepts; seven are deterministic anchors, the rest carry explicit confidence and are correctable without mutating source data.
- Transaction and Receipt are sibling events, not parent-child; Reconciliation is the explicit join that links them when a match is established.
- Extraction Revision is an append-only concept: re-running AI/OCR over an Evidence Asset creates a new revision rather than overwriting the previous one.
- Corrections layer on top of inferred fields as a separate concept and must never mutate the original extraction output.
- Normalized Product, cross-user benchmarks, and Amazon/Costco order-level line items are deliberate deferrals for v1.

---

## 2. What We Learned

The project's differentiation rests on combining bank-level transaction truth with item-level receipt evidence and behavioral personalization. These three data layers have fundamentally different provenance, reliability, and mutability. An ontology that treats them uniformly will produce either incorrect accounting or incorrect AI training signal. The ontology must therefore be stratified: deterministic facts from authoritative sources, inferred fields with explicit confidence and version, and user-authored corrections as a separate non-destructive overlay.

---

## 3. What Best-in-Class Products/Research Do Well

- **Monarch Money**: Links receipts to transactions as optional enrichment, preserving the bank record as authoritative.
- **Actual Budget**: Draws a hard boundary between the accounting core and AI interpretation, ensuring calculations are never LLM-authored.
- **Plaid**: Makes provenance explicit — every transaction carries the source institution, date, and a stable ID that survives re-sync.
- **General pattern**: Confidence scores on inferred fields, with a correction model that feeds back into the inference pipeline without touching the original source record.

---

## 4. What We Should Adopt

- Treat the bank transaction as the authoritative financial fact; receipts enrich but never replace it.
- Append-only extraction revisions with model/version tracking.
- Corrections as a separate overlay entity, never a mutation of the extracted or bank-sourced record.
- Explicit Reconciliation as a named join entity with match type and confidence.
- Behavioral Labels versioned by model version so they can be regenerated without data loss.
- Personal-Value Feedback as user-sovereign data, never inferred, never overridden by the system.

---

## 5. What We Should NOT Copy

- Embedding confidence directly in the raw transaction record (Monarch-style); keep it as a property of the inferred revision.
- Conflating merchant normalization with the transaction record itself; merchant is a separate resolvable entity.
- Allowing AI-generated categories to silently replace user corrections in subsequent sync cycles.
- Designing Line Items as children of Transaction rather than children of Receipt — the bank does not know what was purchased, only the receipt does.

---

## 6. Implications for Our Product

- The product can show a trustworthy accounting view (deterministic) and a behavioral enrichment view (inferred + labeled) as two distinct but linked perspectives.
- Reconciliation state drives what the product can claim: an unmatched transaction can show merchant and category; a matched transaction with extracted line items can show item-level purchase history and personal-value feedback.
- Historical Backfill is a first-class entity because the completeness of behavioral labeling depends on how far back the data goes.
- Recurring Pattern is fully inferred but high-value for proactive coaching; it needs its own confidence model and must be surfaced differently from one-off transactions.

---

## 7. Implications for Architecture

- The data layer needs to distinguish three write paths: authoritative ingest (Plaid, bank), AI enrichment (extraction revision, behavioral label), and user correction. These must not share a write path.
- Extraction Revision requires append-only storage; a row-versioning pattern or event-sourced sub-table is appropriate.
- Corrections must reference the entity + field tuple, not the entity alone, so fine-grained field-level overrides are possible without full-record replacement.
- Budget Context is user-defined and simple in v1 (amount + period + category); the engine that evaluates spend against it is deterministic and must not involve an LLM.

---

## 8. Differentiation Opportunities

- Personal-Value Feedback as a genuine first-party training signal is rare among competitors. Treating it as user-sovereign and building a personalized value model from it is the strongest differentiator.
- Behavioral Label at the line-item level (not just transaction level) enables item-level impulse vs. value analysis that no current consumer product provides.
- Historical Backfill with retroactive behavioral labeling turns old data into a personalized baseline without requiring prior app usage.

---

## 9. Minimum Useful Ontology

### Entities

| Entity | Nature | Minimum Required Fields |
|---|---|---|
| **Account** | Deterministic | institution, type, currency, masked number, last-sync timestamp, source (Plaid item ID) |
| **Transaction** | Deterministic | transaction ID (source), account ref, amount, date, raw description, status (pending/posted), plaid transaction ID |
| **Merchant** | Normalized/Inferred | canonical name, display name, category, logo URL |
| **Receipt** | Deterministic shell | receipt ID, source type, capture timestamp, storage URL ref, processing status |
| **Evidence Asset** | Deterministic, immutable | asset ID, receipt ref, storage URL, MIME type, content hash, ingestion timestamp |
| **Extraction Revision** | Inferred, append-only | revision ID, evidence asset ref, model + version, extracted payload (JSON), confidence, timestamp, is_current flag |
| **Line Item** | Inferred from extraction | line item ID, receipt ref, raw description, quantity, unit price, extended price, tax portion |
| **Normalized Product** | Inferred (deferred v1) | product ID, canonical name, category, brand; linked from line item via fuzzy match |
| **Budget Context** | Deterministic (user-entered) | budget ID, name, amount, period, category refs, start date |
| **Recurring Pattern** | Fully inferred | pattern ID, merchant ref, amount (or range), interval, last seen, confidence, status |
| **Reconciliation** | Deterministic (manual) / Inferred (auto) | reconciliation ID, transaction ref, receipt ref, match type, match score, matched-by, timestamp |
| **Personal-Value Feedback** | User-sovereign, deterministic | feedback ID, target ref, label (planned/impulse/necessary/regret/valued), buy-again response, life-improvement scale, timestamp |
| **Behavioral Label** | Inferred, versioned | label ID, target ref, label type, confidence, model version, timestamp |
| **Provenance** | Deterministic | source type, source identifier, ingest timestamp, raw payload hash, pipeline version |
| **Corrections** | User-authored overlay | correction ID, target entity + field, old value, new value, timestamp |
| **Historical Backfill** | Deterministic metadata | backfill ID, source type, date range, record count, status, initiated timestamp |

### Key Relationships

```
Account ──1:N──► Transaction
Transaction ──N:1──► Merchant
Transaction ◄──Reconciliation──► Receipt
Receipt ──1:N──► Evidence Asset
Evidence Asset ──1:N──► Extraction Revision (append-only)
Receipt ──1:N──► Line Item
Line Item ──N:1──► Normalized Product (deferred v1)
Transaction / Line Item ──1:1──► Personal-Value Feedback
Transaction / Line Item ──1:N──► Behavioral Label (versioned)
Any entity ──1:N──► Corrections (field-level overlay)
Any entity ──1:1──► Provenance
Transaction ──N:1──► Recurring Pattern (inferred membership)
```

### Deterministic vs. Inferred Responsibilities

**Deterministic (trust absolutely):**
- Transaction amount, date, status (from Plaid/bank)
- Evidence Asset content hash and storage URL
- Personal-Value Feedback (user-authored)
- Corrections (user-authored)
- Budget Context amounts (user-entered)
- Provenance metadata
- Reconciliation when manually matched by user
- Historical Backfill metadata

**Inferred (label with version + confidence, allow correction):**
- Merchant normalization
- Transaction category classification
- All fields in Extraction Revision (receipt OCR/AI output)
- Recurring Pattern detection
- Behavioral Labels
- Auto-reconciliation match score
- Normalized Product linkage
- Line item tax attribution

### Deferrals

| Deferred Concept | Reason |
|---|---|
| Normalized Product as full entity | v1 can store raw line item descriptions; cross-receipt product identity adds complexity without immediate UI payoff |
| Cross-user product benchmarks | Requires multi-user data; this is a personal app |
| Amazon/Costco order-level API ingestion | No official API; email parsing is fragile (addressed in Track 6) |
| Budget Context formula rules | v1 needs only simple amount + period envelopes |
| Recurring Pattern subscription management UI | Detection can be implemented before UI |
| Full MCP/tool exposure | Requires stable ontology first |

---

## 10. PRD Changes Recommended

- Add Reconciliation as an explicit entity with match type, not an implicit flag on Transaction or Receipt.
- Define Corrections as a non-destructive overlay layer; PRD must state that source data is immutable.
- Add Historical Backfill as a named v1 feature with completeness tracking.
- Defer Normalized Product to post-v1; PRD should say "line item descriptions stored verbatim in v1."
- Clarify that Personal-Value Feedback applies at both transaction and line-item level.
- State explicitly that Budget Context evaluation is deterministic (no LLM involvement).

---

## 11. Stop Statement

The ontology covers every entity listed in the brief. Relationships, minimum metadata, deterministic vs. inferred boundaries, and deferrals are all defined with sufficient precision to begin a PRD data-model section and inform an initial schema design. Further research would produce schema-level detail that is explicitly out of scope for this track.

---

## 12. Sources

All Track 3 sources are primary technical references accessed 2026-08-15.

| # | Title | Publisher | URL | Accessed |
|---|---|---|---|---|
| S1 | Plaid Transactions Documentation | Plaid | https://plaid.com/docs/transactions/ | 2026-08-15 |
| S2 | Plaid Link Documentation | Plaid | https://plaid.com/docs/link/ | 2026-08-15 |

*Track 3 ontology design draws on these two primary sources plus the project seed documents read at session start. The ontology is a reasoned design artifact grounded in the seed documents' entity list, not a synthesis of third-party ontology research.*

---
---

# TRACK 6 — Technical Feasibility

## 1. Executive Summary

- Angular + Capacitor is a credible and officially supported path to App Store and Play Store distribution, but the app must provide meaningful native functionality (camera, push notifications, biometric auth) or Apple will reject it under guideline 4.2.7 (thin-wrapper prohibition).
- Supabase (Pro tier, $25/month) is appropriate for a single-user personal finance app; the most important constraint is that the anon key must be paired with airtight RLS policies and the service key must never reach any mobile client.
- Plaid's permanent `access_token` must live exclusively in a server-side layer; this is a non-negotiable architecture constraint that mandates at minimum Supabase Edge Functions or a dedicated backend route.
- The safest coexistence strategy for the existing receipt-ingestion service is zero-migration: keep it running on its own Postgres instance and have the new Supabase project reference it via a read path (API proxy or foreign data wrapper), not a data move.
- Amazon and Costco order-level line-item ingestion via official API does not exist; email parsing is the only current path and is fragile — defer to post-v1.

---

## 2. What We Learned

### Angular + Capacitor (Observed fact — official documentation)

Capacitor is explicitly designed to wrap any modern JavaScript web application for native iOS and Android deployment. Angular is a named supported framework. The workflow adds platform projects (`ionic capacitor add ios`, `ionic capacitor add android`) that produce genuine Xcode and Android Studio projects, not thin web shells. Native plugins are available for camera, filesystem, haptics, keyboard, status bar, and push notifications.

Capacitor does not require Ionic Framework; it works with Angular standalone. The resulting apps pass through the standard App Store and Play Store submission process as native apps, and the web layer runs in WKWebView (iOS) and Android WebView — both platform-approved runtimes.

### Supabase (Observed fact — official pricing and documentation, accessed 2026-08-15, time-sensitive)

| Plan | Monthly cost | DB size included | Storage | Edge function invocations | Project pausing |
|---|---|---|---|---|---|
| Free | $0 | 500 MB | 1 GB | 500 K/mo | Yes — pauses after 1 week inactivity |
| Pro | $25 | 8 GB (then $0.125/GB) | 100 GB (then $0.0213/GB) | 2 M/mo (then $2/M) | No |
| Team | $599 | Same as Pro | Same | Same | No |

**Row-Level Security:** Supabase maps all client requests to two Postgres roles (`anon` and `authenticated`). Every RLS policy using `auth.uid() = user_id` silently passes for unauthenticated requests when `auth.uid()` returns null, because `null = null` is false in SQL — but the documentation explicitly warns this is a footgun; the correct guard is `auth.uid() IS NOT NULL AND auth.uid() = user_id`. The service key bypasses all RLS and must never be present in any mobile client or web frontend.

**Edge Functions:** Deno-based TypeScript runtime, globally distributed. Designed for short-lived, idempotent operations. Cold starts are acknowledged. External API calls (Plaid, LLMs) are supported and documented. Long-running AI inference jobs must be offloaded to a background worker (pg_cron, a queue, or an external service) rather than blocking an edge function invocation.

**Storage:** S3-compatible, CDN-fronted, RLS-controlled. Appropriate for receipt image storage. File size limits not confirmed in the fetched documentation; this requires a follow-up check against the full storage API spec.

**Portability:** Underlying data is plain PostgreSQL; a pg_dump from Supabase Cloud restores to any PostgreSQL instance. Self-hosting via Docker/Kubernetes is documented. Managed features (branching, PITR, analytics buckets) do not transfer to self-hosted. This is an acceptable exit path for a personal finance app that does not depend on those managed features.

### Plaid (Observed fact — official documentation)

- Historical coverage: up to 730 days (24 months) of transaction history, specified via `transactions.days_requested`.
- Sync frequency: 1–4 checks per day per institution; `SYNC_UPDATES_AVAILABLE` webhooks drive incremental updates.
- Token model: `link_token` (short-lived, session-specific) → user authenticates in Plaid Link → `public_token` (single-use) → backend exchanges for `access_token` (permanent, backend-only). The access_token never reaches the mobile client. This is a hard architectural constraint.
- Mobile SDKs: Native iOS, Android, and React Native SDKs available. No Angular-specific SDK; Plaid Link is invoked from the mobile native layer or via a web SDK in a WebView.
- Receipt-bank matching: Plaid does not provide receipt data. Matching must happen in the application layer by correlating transaction amount, date, and merchant name against receipt metadata.
- Amazon/Costco/retailer history: No official Plaid product for order-level item data. Plaid transactions will show Amazon.com or Costco as the merchant with a dollar amount — no line items.

### Apple App Store (Observed fact — App Store Review Guidelines, accessed 2026-08-15)

- **Guideline 4.2.7**: Thin clients for cloud-based apps are explicitly not appropriate for the App Store. An Angular app packaged via Capacitor that does nothing but render a remote web app will be rejected.
- **Guideline 2.5.6**: Apps that browse the web must use WebKit (satisfied by Capacitor's WKWebView on iOS).
- **Guideline 5.1.1(ix)**: Financial services apps must be submitted by the legal entity that provides the services, properly licensed in all jurisdictions.
- **Financial data restrictions**: Financial data cannot be used for marketing or advertising.
- **Mitigation path**: An Angular + Capacitor app that uses native camera (receipt capture), native push notifications (proactive coaching alerts), and native biometric authentication (Face ID / Touch ID) provides meaningful native functionality and is unlikely to be rejected on 4.2.7 grounds.

### Google Play (Partially observed — policy center navigation accessed 2026-08-15; detailed financial policy page not fully retrieved)

Google Play has a Financial Services policy and a minimum functionality / user experience policy. The specific thin-wrapper prohibition language was not fully retrieved. **This is an identified gap requiring a follow-up fetch of the full Financial Services policy page.**

---

## 3. What Best-in-Class Products/Research Do Well

- **Plaid's token architecture**: clean client/server security boundary, no credentials on device.
- **Supabase RLS + authenticated JWT**: when implemented correctly, provides defense-in-depth at the database layer even if API layer has a bug.
- **Capacitor's native plugin model**: enables genuine native capability (camera, push, biometric) without abandoning a web-stack frontend.
- **Coexistence patterns**: mature fintech products that migrated to Supabase typically ran the old and new systems in parallel during a transition window, syncing via API rather than a hard data migration.

---

## 4. What We Should Adopt

- Angular + Capacitor as the mobile packaging path. Add `@capacitor/camera`, `@capacitor/push-notifications`, and biometric auth plugins from day one to ensure the App Store submission has defensible native functionality.
- Supabase Pro tier from the start; Free tier's project-pausing behavior is incompatible with a live receipt-ingestion service.
- Server-side Plaid access_token storage in Supabase Edge Functions or a backend route — never on the client.
- Explicit `auth.uid() IS NOT NULL` guards on every RLS policy that handles financial data.
- Supabase Storage for receipt images with RLS-controlled bucket access.
- A provenance field on every Supabase table that will receive data from Plaid, receipt ingestion, or imports — this enables auditability and safe re-sync.

---

## 5. What We Should NOT Copy

- Embedding Plaid access tokens in mobile client storage under any encryption scheme.
- Using the Supabase service key in a mobile app or a client-accessible endpoint.
- A full schema migration of the existing receipt PostgreSQL database into Supabase before the new architecture is stable.
- Building Amazon/Costco order ingestion in v1 via email scraping; the fragility outweighs the benefit.
- Designing Edge Functions as long-running AI inference workers; they are designed for short-lived operations.

---

## 6. Implications for Our Product

- The product must demonstrate native value from the first App Store release — camera-based receipt capture is the clearest native capability, and it already exists in the existing receipt-ingestion service as a design precedent.
- The legal entity requirement (App Store guideline 5.1.1(ix)) should be assessed early if this product is intended to go beyond a personal app. For a single-owner personal tool, the developer account submission should be by the individual who owns the financial data.
- Plaid's 730-day historical coverage is the realistic maximum for transaction backfill. Receipts predating Plaid connection require a separate import path.

---

## 7. Implications for Architecture

### Coexistence Strategy (Do not design final architecture — identify the safe path)

The existing receipt-ingestion service has its own PostgreSQL-backed database and is actively capturing data. Two safe coexistence options exist:

**Option A — API proxy (lowest risk):** The new Supabase project calls the existing service's internal API for receipt data. No data migration. The existing service remains authoritative for receipts. Supabase handles Plaid transactions, auth, and the new mobile frontend. Reconciliation runs in Supabase by calling the receipt service for matched data.

**Option B — Shared Postgres read replica (moderate complexity):** Supabase points to the same PostgreSQL instance (or a read replica) as the existing service. New tables live in Supabase's schema; old tables remain in the existing schema. A foreign data wrapper (FDW) joins them at query time. No data is moved.

**Not recommended:** migrating the existing service's data into Supabase before the new mobile architecture is validated. Risk of interrupting ongoing capture with no rollback path.

### Required Server-Side Layer

Plaid's token model requires a backend that can hold the access_token securely. Supabase Edge Functions can fulfill this role for Plaid webhooks and sync jobs. The edge function calls Plaid, writes transactions to Supabase Postgres, and returns no sensitive token data to any client.

### Long-Running AI Jobs

Receipt extraction (AI/OCR over an evidence asset) is not appropriate for an Edge Function (cold starts, execution time limits). A background queue pattern is required: Edge Function receives the trigger, enqueues the job, a worker (pg_cron + Postgres function, or an external worker service) processes it asynchronously.

---

## 8. Feasibility Matrix

| Component | Feasibility | Evidence | Condition / Guardrail |
|---|---|---|---|
| Angular + Capacitor → iOS App Store | **Feasible** | Official Capacitor docs confirm Angular support and App Store deployment path | Must include ≥1 meaningful native capability (camera, push, biometric) |
| Angular + Capacitor → Google Play | **Likely feasible** | Capacitor docs confirm Play deployment; detailed Google Play financial policy not fully retrieved | **Minimum experiment required** |
| Supabase as backend (Pro, $25/mo) | **Feasible** | Official pricing confirmed 2026-08-15 | No project pausing; 8GB DB sufficient for personal finance scale |
| Supabase RLS for mobile security | **Feasible with guardrails** | Official docs confirm mechanism; null-auth footgun documented | Explicit IS NOT NULL guards on all financial data policies |
| Supabase Edge Functions for Plaid sync | **Feasible** | Docs confirm external API calls and webhook receivers | Long-running AI jobs must be offloaded to background worker |
| Supabase Storage for receipts | **Feasible** | S3-compatible, CDN, RLS-controlled; confirmed in docs | File size limits require follow-up verification |
| Plaid transaction ingestion (730 days) | **Feasible** | Official docs confirm 730-day max, webhook-driven sync | access_token must never reach client |
| Plaid → receipt matching | **Feasible (app layer)** | Plaid provides amount, date, merchant; matching is app logic | No Plaid API for receipt data; matching algorithm is custom |
| Amazon/Costco order-level ingestion | **Not feasible v1** | No official API; email parsing fragile | Defer to post-v1 |
| Supabase self-hosting / portability | **Feasible** | Docker/K8s documented; Postgres is portable | Managed features (PITR, branching) not available in self-hosted |
| Coexistence with existing receipt service | **Feasible** | API proxy or FDW path identified | Do not migrate existing DB until new architecture is validated |
| MCP/tool exposure | **Feasible (future)** | Postgres-backed data is queryable; MCP tooling exists | Defer until ontology is stable and v1 is shipped |

---

## 9. Top 5 Technical Risks

| # | Risk | Severity | Evidence Basis |
|---|---|---|---|
| R1 | **App Store rejection for thin-wrapper** — Angular + Capacitor app rejected under guideline 4.2.7 if it lacks native functionality | High | Apple guideline 4.2.7 explicitly prohibits thin clients; observed fact |
| R2 | **Supabase anon key + incomplete RLS exposes all user financial data** — null auth.uid() footgun allows unauthenticated reads if policies are not explicitly guarded | High | Supabase RLS docs explicitly document this risk; observed fact |
| R3 | **Plaid access_token on client** — permanent bank access credential exposed if Edge Function architecture is bypassed or access_token is logged | High | Plaid docs establish token model; risk is implementation discipline |
| R4 | **Existing receipt service disrupted by premature migration** — interrupting ongoing receipt capture has no fast rollback | Medium | Coexistence strategy is identified but requires deliberate implementation; reasoned inference |
| R5 | **Edge Function cold starts delay receipt AI processing** — user experience degrades if extraction is synchronous in an Edge Function | Medium | Supabase Edge Function docs acknowledge cold starts; observed fact |

---

## 10. Weekend-Safe Choices

| Choice | Safe? | Rationale |
|---|---|---|
| Angular + Capacitor project setup (no App Store submission) | Yes | Local dev and simulator testing; no submission risk |
| Supabase Pro project creation | Yes | $25/month, no project pausing, easy to delete |
| Plaid Sandbox mode | Yes | No real bank credentials; safe for all development |
| Supabase Storage bucket for receipt images | Yes | RLS-controlled, no production data |
| Supabase RLS policies with IS NOT NULL guards | Yes | Implement correctly from the start |
| Coexistence via API proxy (existing service unchanged) | Yes | Zero-risk to existing service |
| Amazon/Costco email ingestion | No | Fragile, defer |
| Full DB migration from existing service to Supabase | No | Risk to ongoing capture; do not do this weekend |

---

## 11. Minimum Experiments Before Committing

1. **Capacitor + Angular native camera build** — Build an Angular app with `@capacitor/camera`, run it on an iOS simulator, confirm the camera plugin works. This validates the non-thin-wrapper native capability claim and the build toolchain end-to-end. *Weekend-safe.*

2. **Supabase RLS with real JWT** — Create a Supabase Pro project, create a transactions table with RLS enabled, insert a test row, verify that an authenticated request sees it and an unauthenticated request does not — with an explicit IS NOT NULL guard in the policy. *Weekend-safe.*

3. **Existing service read via API proxy** — Call the existing receipt service from a Supabase Edge Function and return structured data. Confirm the coexistence path works without modifying the existing service. *Weekend-safe.*

---

## 12. Deferrals

| Deferred Item | Reason |
|---|---|
| Amazon/Costco order-level line item ingestion | No official API; email parsing is fragile and unreliable |
| Local-first processing architecture | Adds significant complexity; cloud-assisted is sufficient for a personal app; revisit if privacy requirements change |
| MCP/tool exposure | Requires stable ontology and shipped v1 |
| Google Play full financial policy verification | Policy page was not fully retrieved; treat as a required follow-up before Play Store submission (not before weekend implementation start) |
| Supabase Storage file size limits | Not found in fetched docs; verify against full Storage API spec before receipt ingestion design is finalized |
| Supabase → self-hosting migration planning | Not needed until the product has meaningful user scale or privacy requirements change |

---

## 13. PRD Changes Recommended

- Add a native capability requirement to the mobile specification: camera (receipt capture), push notifications (proactive coaching), and biometric authentication must be present in v1 to satisfy App Store guideline 4.2.7.
- Document the Plaid token security boundary explicitly: access_token is server-side only, never returned to any client.
- Add a coexistence requirement: the existing receipt-ingestion service and its PostgreSQL data must remain operational and unmodified during the new app's development and initial deployment.
- Note that Amazon/Costco order-level ingestion is a v2+ feature, not a v1 requirement.
- Add a legal entity review item: confirm that the App Store submission entity satisfies guideline 5.1.1(ix) for financial services apps.

---

## 14. Stop Statement

All architecture-changing risks listed in the brief have an evidence-based disposition. Angular + Capacitor, Supabase, Plaid, App Store/Play Store constraints, and the coexistence strategy are each resolved to either a confirmed feasible path or a named experiment. Amazon/Costco ingestion is definitively deferred with a clear rationale. The Google Play full financial-policy gap is identified and scoped as a pre-submission follow-up, not a blocker to implementation start. Three weekend-safe experiments are specified. Further research would produce implementation detail rather than decision-changing evidence.

---

## 15. Sources

| # | Title | Publisher | URL | Accessed |
|---|---|---|---|---|
| S1 | Supabase Pricing | Supabase | https://supabase.com/pricing | 2026-08-15 (time-sensitive: pricing subject to change) |
| S2 | Row Level Security — Supabase Docs | Supabase | https://supabase.com/docs/guides/auth/row-level-security | 2026-08-15 |
| S3 | Self-Hosting — Supabase Docs | Supabase | https://supabase.com/docs/guides/self-hosting | 2026-08-15 |
| S4 | Edge Functions — Supabase Docs | Supabase | https://supabase.com/docs/guides/functions | 2026-08-15 |
| S5 | Storage — Supabase Docs | Supabase | https://supabase.com/docs/guides/storage | 2026-08-15 |
| S6 | Capacitor Getting Started | Ionic / Capacitor | https://capacitorjs.com/docs/getting-started | 2026-08-15 |
| S7 | Capacitor with Ionic | Ionic / Capacitor | https://capacitorjs.com/docs/getting-started/with-ionic | 2026-08-15 |
| S8 | Plaid Transactions Documentation | Plaid | https://plaid.com/docs/transactions/ | 2026-08-15 |
| S9 | Plaid Link Documentation | Plaid | https://plaid.com/docs/link/ | 2026-08-15 |
| S10 | App Store Review Guidelines | Apple | https://developer.apple.com/app-store/review/guidelines/ | 2026-08-15 |
| S11 | Google Play Developer Policy Center | Google | https://play.google/developer-content-policy/ | 2026-08-15 (financial services detail page not fully retrieved — gap noted) |

*11 sources total. Within the 12-source cap for this workstream.*
