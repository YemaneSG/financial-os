# Premium Mobile Financial OS — Tracks 2–8 Consolidation

**Run:** `2026-08-15-premium-mobile-r1`
**Date:** 2026-08-15
**Owner:** Yemane
**Operating lead:** Codex
**Research runtime:** Claude Code through Vertex AI
**Status:** Tracks 2–8 complete; Track 1 and owner decisions remain before PRD or architecture approval

## 1. Outcome

The controlled research supports a credible path to a premium downloadable iOS
and Android Financial OS using Angular, Capacitor, and Supabase as the preferred
direction while the existing receipt-ingestion system continues operating.

It does **not** support a full rewrite, an immediate database migration, a
client-only Supabase design, or immediate implementation against production.
The safest next shape is a new mobile application that coexists with and consumes
the working receipt service through a stable API boundary. Supabase is a candidate
home for new application capabilities, not an automatic replacement for the
existing receipt system or its durable data.

This document consolidates research. It does not amend the current PRD, freeze
the next architecture, authorize a migration, or authorize implementation.

## 2. Research quality and corrections

Four paired Claude Sonnet workstreams covered Tracks 2–8. Two focused evidence
audits then checked architecture-changing claims and weak HCI evidence.

The audits made these material corrections:

1. Apple's relevant rule for a packaged web application is the general App Store
   Review Guideline **4.2, Minimum Functionality**. A report incorrectly treated
   4.2.7 as the general thin-wrapper rule; 4.2.7 is scoped to remote desktop
   clients. Capacitor makes native packaging possible but does not guarantee App
   Store acceptance.
2. Supabase `auth.uid() = user_id` with no authenticated user evaluates false and
   denies rows; it does not silently expose them. An explicit authentication
   guard remains useful for clarity and defense in depth. Missing RLS or exposure
   of a service-role key is the real high-severity risk.
3. Plaid's example architecture keeps its persistent access credential on the
   server. Server-only handling remains the required project security design,
   but the source does not state it as a literal contractual prohibition.
4. Cross-cloud FDW or shared-replica access is unproven. It is not a recommended
   coexistence path without a controlled experiment. The API boundary is the
   only supported starting recommendation.
5. Actual Budget's browser API via Web Workers is confirmed. The raw report's
   WebAssembly/IndexedDB implementation description was not confirmed.
6. Fixed notification frequency, a 20–30-label personalization threshold, a
   seven-day regret prompt, and green/yellow/red effectiveness in personal
   finance are hypotheses, not established evidence.

Raw reports remain preserved. Where a raw report conflicts with an audit, the
audit and this consolidation control the later handoff.

## 3. Decision-changing findings

### A. Product position

- Receipt capture is necessary infrastructure, not the premium differentiator.
  Monarch now documents receipt scanning, although its itemization, correction,
  matching, and email-ingestion depth could not be verified from accessible
  primary sources.
- The strongest differentiated hypothesis is the combination of transaction
  truth, receipt line items, budget context, explicit personal-value feedback,
  regret or repurchase feedback, and future guidance grounded in the owner's own
  history.
- No product in the bounded comparison set was confirmed to combine all of those
  mechanisms. This is a competitive signal, not proof that the product will
  change behavior.
- Copilot provides the most relevant premium mobile benchmark: a restrained
  information hierarchy, native-feeling interaction, and narrow event-triggered
  alerts. Its feature set should not be copied wholesale.
- Cleo's chat-first, humor-led model is not the target product direction and its
  current primary sources were inaccessible. Claims about its item-level depth
  remain unknown.

### B. Mobile application direction

- Angular plus Capacitor is technically capable of producing normal iOS and
  Android projects with access to native APIs.
- Store acceptance depends on the delivered utility and quality, not the wrapper.
  The app must feel designed for the device and provide lasting utility beyond a
  repackaged website. Receipt camera capture is a meaningful native capability;
  push or biometric features should be added when product or security needs
  justify them, not as decorative review theater.
- The platform choice must be proven on a real iPhone and Android device before
  architecture is frozen. Camera behavior, HEIC/HEIF, multi-image capture,
  lifecycle pause/resume, authentication return, deep links, and accessibility
  are decision evidence.

### C. Supabase direction

- Supabase is feasible as a candidate managed application platform for the
  expected personal scale, but it does not eliminate server-side responsibilities.
- RLS must be enabled and tested for every client-reachable financial table.
  Publishable/anonymous keys are usable in clients only with correct grants and
  RLS. Service-role credentials, Plaid credentials, and LLM credentials remain
  server-only.
- Edge/server functions are appropriate for bounded token exchanges, webhooks,
  and short deterministic operations. Long-running receipt extraction should
  remain an asynchronous worker concern unless a later experiment proves another
  safe runtime.
- A paid Supabase plan may be operationally appropriate, but purchasing or
  creating production resources is not required to accept the architectural
  hypothesis. Begin with a bounded synthetic-data proof.
- PostgreSQL portability is valuable, but managed Supabase features and operating
  assumptions still require explicit exit and backup evidence.

### D. Preservation and coexistence

- The existing receipt system remains authoritative for receipt evidence,
  revisions, validation, corrections, and durable acknowledgement during the new
  application's development.
- The lowest-risk starting point is a client-independent API adapter: the new
  application reads and invokes authorized receipt capabilities through the
  existing service contract.
- No existing receipt row, object, migration, contract, production service, or
  accumulated evidence should move merely to align brands or providers.
- Direct FDW, shared-database, dual-write, replication, and data-migration options
  are future architecture candidates only after controlled experiments and
  explicit rollback evidence.

### E. Financial truth and AI boundary

- Transactions, balances, budgets, reconciliations, arithmetic, and authoritative
  state transitions must be deterministic.
- AI may extract, classify, interpret, propose, explain, or converse. It must not
  become the ledger, calculate authoritative totals, or directly mutate financial
  truth.
- Inferred values require model/version provenance, confidence, and correction.
  User corrections and personal-value feedback are durable first-party evidence,
  not temporary chat context.
- A future tool/MCP layer should expose typed, allowlisted operations over the
  deterministic core. The final tool list and authorization model belong to the
  architecture phase, not this research run.

### F. Trust and interaction

- The strongest supported principles are user control, visible system status,
  easy correction, explicit uncertainty, explanations grounded in authenticated
  personal history, and quiet-by-default proactivity.
- Recommendations are advisory. Override must be immediate and must not require a
  justification. An optional explanation can follow after the override.
- The system needs an explicit insufficient-evidence state. It must not produce a
  personalized color signal merely because the UI expects one.
- Green/yellow/red is a reasonable low-cognitive-load hypothesis but is not
  validated for personal finance. It must be tested against a textual observation
  and no-intervention control.
- Notification frequency, prompt timing, and personalization activation are
  configurable experiment variables, not hardcoded research conclusions.

### G. Evaluation and outcomes

- Model evaluation must use a private, versioned golden set grounded in the
  owner's authenticated receipts, corrections, transaction labels, and feedback.
  Public artifacts reference only opaque fixture IDs and aggregate results.
- Core evaluation dimensions are extraction field quality, classification
  macro-F1, confidence calibration, recommendation disagreement, routing quality,
  and regression between model versions.
- Proposed dataset counts in the raw research are starting hypotheses. No fixed
  sample size becomes a release requirement before a baseline labeling study.
- Product success is fewer regretted purchases, better alignment with stated
  priorities, improved budget adherence, and improved financial awareness or
  well-being—not sessions, notification volume, time in app, or AI query count.
- No competitor in the bounded set supplied credible causal evidence that its
  coaching changes financial behavior. This product must measure its own outcome
  rather than borrow an engagement claim.

## 4. Research dispositions

### Validated product signals

1. A premium mobile experience must be device-quality, restrained, accessible,
   and useful beyond a packaged website.
2. Existing receipt capture and durable data are assets to preserve and reuse.
3. Receipt line items plus user-authenticated value feedback create a promising
   differentiated data asset.
4. Financial truth must remain deterministic and separable from AI.
5. Corrections, overrides, and confidence must be first-class product concepts.
6. Privacy declarations, account deletion, data minimization, server-only secrets,
   and tested authorization are v1 concerns rather than later hardening.

### Hypotheses to test

1. Personal-value feedback reduces future regretted purchases.
2. Item-level coaching is materially more useful than transaction/category-level
   coaching.
3. Green/yellow/red improves decisions without increasing friction or shame.
4. Opportunity-triggered reflection outperforms a fixed calendar prompt.
5. Personalized guidance begins outperforming generic observations after a
   discoverable amount of labeled history.
6. Quiet, event-triggered proactivity is more useful than a conversational or
   notification-heavy primary interface.
7. The owner will consistently provide enough low-friction feedback for the
   personal model to improve.

### Rejected for the immediate path

1. Rewrite or migrate the working receipt system before the new client proves its
   coexistence path.
2. Direct mobile access to service-role, Plaid, LLM, or provider credentials.
3. LLM-authored accounting, balances, budgets, or authoritative state changes.
4. Treat competitor feature lists as proof of behavioral outcomes.
5. Make a chat interface the primary product surface merely because AI is used.
6. Add gamification, streaks, or high-frequency notifications as engagement goals.
7. Hardcode the raw reports' unsupported label-count, frequency, timing, or
   dataset-size numbers.

### Deferred

1. Amazon, Costco, and broad email/order ingestion.
2. Full product normalization across retailers.
3. Investment tracking and other broad wealth-dashboard features.
4. Production MCP/tool exposure.
5. Full database migration or cross-cloud database joining.
6. Local-first replication and a self-hosted Supabase transition.
7. Any public multi-user expansion not explicitly approved in the next PRD.

## 5. Minimum experiments before architecture freeze

### EXP-01 — Mobile shell proof

Build a disposable Angular + Capacitor prototype with synthetic data. Prove on a
real iPhone and Android device:

- native camera capture;
- HEIC/HEIF and JPEG behavior;
- ordered multi-image capture;
- background/resume and failed-upload recovery;
- authentication return/deep link;
- device-safe navigation, focus, text scaling, contrast, and touch targets.

**Pass condition:** The evidence supports one shared mobile codebase without
regressing the current capture experience or relying on a remote website shell.

### EXP-02 — Supabase authorization proof

Use synthetic data in a disposable non-production project or local environment.
Prove:

- authenticated owner sees only authorized rows;
- anonymous and wrong-user access fail;
- service-role credentials never enter a client bundle;
- all client-reachable tables have explicit grants and RLS;
- deletion and export behavior are auditable;
- logs omit financial content and credentials.

**Pass condition:** Automated negative tests establish the authorization boundary.

### EXP-03 — Receipt coexistence proof

Create a read-only prototype adapter against a synthetic or isolated instance of
the existing receipt API. Do not change production contracts or data. Measure:

- authentication compatibility;
- list/detail/search latency;
- image access and capability handling;
- error and offline behavior;
- whether the mobile client can reuse the current durable receipt path unchanged.

**Pass condition:** The new client retrieves and displays receipt data without a
database migration, dual write, or production change.

### EXP-04 — Personal feedback prototype

After Track 1 supplies the behavioral vocabulary, test a small feedback flow over
private, authenticated history:

- planned vs. impulse;
- would buy again;
- value or regret;
- optional reason;
- correction and visible learning confirmation.

Do not assume a label-count threshold. Measure completion, usefulness, and whether
the vocabulary fits the owner's real decision patterns.

**Pass condition:** The feedback can be completed quickly, produces stable labels,
and the owner finds the resulting reflection useful before AI advice is added.

### EXP-05 — Guidance-format comparison

Using synthetic or owner-controlled private scenarios, compare:

- factual observation only;
- green/yellow/red plus personal-history explanation;
- no intervention.

Measure comprehension, override rate, annoyance, and later regret feedback.

**Pass condition:** A guidance format demonstrates value without moralizing,
blocking, or false certainty.

## 6. Owner decisions needed after Track 1

These are product-authority questions. The architecture model should not invent
answers:

1. **Distribution:** public App Store/Play Store product, private/unlisted personal
   distribution, or an App-Store-quality build without public availability?
2. **Initial user model:** remain single-owner, or deliberately design the new
   product for future multi-user use? The current security and data model are
   single-owner.
3. **Supabase responsibility:** new capability store and application backplane,
   or intended eventual system of record? Research recommends the former until
   migration evidence exists.
4. **Bank connectivity timing:** is Plaid in the first premium-app release, or a
   subsequent bounded slice after the mobile shell and receipt coexistence pass?
5. **First behavioral promise:** awareness/reflection, post-purchase learning, or
   pre-purchase intervention? Track 1 should determine which genuinely helps.
6. **Coaching posture:** observational, gently proactive, or explicitly requested
   only? Defaults and notification scope follow this choice.
7. **Commercial and legal posture:** personal tool, portfolio product, or consumer
   financial service? App Store entity, privacy, support, and regulatory review
   differ materially.

## 7. Inputs to the later PRD

The new PRD should include, at minimum:

- product outcome and primary user;
- distribution and platform targets;
- preserved receipt capability and coexistence requirement;
- minimum v1 behavioral loop informed by Track 1;
- deterministic financial truth and AI advisory boundary;
- data provenance, inference, correction, and feedback rules;
- native-quality and accessibility requirements;
- privacy, deletion, export, secrets, logging, and store-disclosure controls;
- success metrics and counter-metrics;
- explicit non-goals and experiment-driven thresholds;
- migration prohibition until evidence and rollback exist.

It should not embed a full schema or final service topology.

## 8. Inputs to the later Fable/Opus architecture pass

The architecture model should receive:

1. both research seeds;
2. this consolidation;
3. the two evidence audits;
4. Track 1 findings;
5. the owner decisions in Section 6;
6. an inventory of the existing receipt API/data/contracts;
7. the existing security and durability invariants that must survive coexistence;
8. results from EXP-01 through EXP-03, or explicit approval to make those the
   first architecture-validation tasks.

The architecture brief must require options and tradeoffs, choose the smallest
reversible topology, define coexistence before migration, identify authority for
each data domain, and produce bounded implementation slices. It must not assume
that selecting Supabase means moving existing receipt data.

## 9. Remaining unknowns

- Monarch itemization, matching, correction, confidence, and email-ingestion
  depth; hands-on testing is the minimum follow-up.
- Cleo's current primary product evidence; its inaccessible sources do not block
  the selected direction.
- Apple reviewer interpretation of legal-entity guidance for a publicly
  distributed personal finance tracker.
- Exact Google Play minimum-functionality treatment for a packaged web client.
- Current Plaid SDK privacy-manifest requirements and production commercial fit.
- Supabase runtime/storage limits relevant to the final receipt workload.
- Whether personal-history coaching produces causal behavior improvement.
- The label vocabulary, intervention timing, and tone established by Track 1.

## 10. Stop statement

Tracks 2–8 are sufficient to proceed to owner synthesis and the Track 1 merge.
Every architecture-changing research question has either a supported disposition,
a correction, a bounded experiment, or a named unknown. Additional broad research
is unlikely to change the next decisions.

Do not begin the Fable/Opus architecture pass until Track 1 findings and the owner
decisions in Section 6 are available. Do not begin implementation until the new
PRD, architecture, security amendments, decision register, and bounded execution
packet are explicitly approved.

## 11. Source artifacts

- `RESULT-A-TRACK-2.md`
- `RESULT-B-TRACKS-3-6.md`
- `RESULT-C-TRACKS-4-8.md`
- `RESULT-D-TRACKS-5-7.md`
- `AUDIT-E-PLATFORM.md`
- `AUDIT-F-COMPETITIVE-HCI.md`

The source URLs and access dates are retained in those artifacts. No private
financial evidence, real receipt content, secrets, tokens, or production resource
identifiers are included in this consolidation.
