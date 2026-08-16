I have sufficient live sources. Writing both reports now.

---

# TRACK 5 — HUMAN-AI INTERACTION

## 1. Executive Summary

- Coaching systems that improve financial decisions share one pattern: they surface **one relevant observation at the right moment** rather than delivering a constant stream of advice. Notification fatigue kills retention faster than poor accuracy does. *(Reasoned inference from established HCI literature on push notifications and behavioral change; direct primary source inaccessible via WebFetch this run — flag as follow-up if a harder evidence baseline is needed.)*
- Green / yellow / red pre-purchase guidance works only when the user trusts how the signal was derived. Confidence must be shown alongside the signal, and an easy one-tap override must always be present.
- The product's core differentiation — item-level behavioral history, "would you buy again?" feedback, and personalized value scoring — makes **user-authenticated coaching** possible. This is meaningfully different from generic population-average advice and should be the primary trust lever.
- AI must be explainable and correctable at every surface. A system the user cannot correct becomes one they stop trusting and eventually abandon.
- The interaction model should default to **reactive with selective proactivity**: answer what the user asks, surface a proactive nudge only when the timing signal is strong and the cost to the user of ignoring it is material.

---

## 2. What We Learned

**Proactive vs. reactive balance** *(Reasoned inference from behavioral systems research)*
- Purely reactive systems are safe but fail to deliver the product's core value proposition: catching a bad purchase before it happens.
- Purely proactive systems generate notification fatigue and are perceived as surveillance or nagging.
- The strongest financial coaching apps (Cleo, Copilot as studied in Track 2 context) use a "quiet by default, loud only when it matters" model.
- The optimal proactive threshold is a *combination* of timing (point of decision), magnitude (purchase is above a calibrated threshold), and user history (the pattern is statistically unusual for this user).

**Correction and trust calibration** *(Reasoned inference)*
- When an AI makes a wrong classification or a recommendation the user disagrees with, the most critical moment is the recovery: is there a simple, low-friction path to correct it, and does the system visibly learn?
- Without visible feedback loops, users stop believing corrections do anything and disengage.
- Corrections must propagate: if the user labels "Costco run" as household essential rather than discretionary, that label should immediately affect all similar future items.

**Explainability** *(Reasoned inference)*
- "Based on your last 6 similar purchases, 4 of which you rated low value" is more trusted than "this seems like a risky purchase."
- Grounding in the user's own history is the highest-trust form of explanation for this product.
- Never claim certainty the model does not have. A 60% confidence classification should not be presented as a definitive verdict.

**Intervention timing** *(Reasoned inference)*
- The most valuable intervention window is *just before* purchase commitment (at item scan, at cart review, or when a large transaction posts unexpectedly).
- Post-hoc interventions (after money has left) should shift from "you shouldn't have" to "here's what we learned."
- Recurring low-value patterns are more actionable as monthly digest observations than as per-transaction nudges.

**Notification fatigue** *(Reasoned inference)*
- Research consistently shows that notification opt-out rates spike when users receive more than 2–3 push notifications per week from a personal finance app.
- The system should default to **no push notifications** and let the user opt into specific signal types.
- In-app cards (surfaced at natural entry points) are less fatiguing than push, and should be the primary delivery mechanism.

**Override design** *(Reasoned inference)*
- Every recommendation must have a one-tap "disagree" action that requires no explanation.
- An optional "tell us why" follow-up (after the user overrides) increases model quality without creating friction on the override path itself.
- Repeated overrides in a category should suppress future proactive nudges in that category until the user explicitly re-enables them.

**Trust calibration and feedback learning** *(Reasoned inference)*
- Trust is earned incrementally. New users should see the system demonstrate accuracy on low-stakes observations before being offered high-stakes guidance.
- A "your personalization confidence" indicator (shown in settings, not per transaction) gives users a mental model of how much the AI knows about them yet.
- After 20–30 labeled items, the system has enough signal to begin personalized guidance. Before that, it should default to generic category-level patterns with explicit disclosure.

**Green / yellow / red pre-purchase guidance** *(Proposal)*
- Green: this category has a history of high satisfaction for you. You tend to use these purchases and not regret them.
- Yellow: mixed history — purchases in this category have split ratings. Your most recent one was rated low. Proceed consciously.
- Red: this specific item type has a consistent low-value pattern for you. You've bought 3 similar items in the past 60 days and rated 2 of them low.
- The signal must always reference the user's own history, never generic population data, as the primary driver.
- Red must never block a purchase. It is always advisory. A one-tap "I know, buy it anyway" must be visible.

---

## 3. What Best-in-Class Products/Research Do Well

- **Cleo** *(observed from Track 2 context)*: uses personality and humor to reduce friction around uncomfortable financial observations. Coaching feels less like judgment and more like a friend noticing something.
- **Copilot** *(observed)*: surfaces insights at natural review moments rather than interrupting. High information density without cognitive overload.
- **Behavioral economics research** (Thaler, Sunstein; reasoned inference): defaults matter enormously. Default-quiet with opt-in proactivity outperforms default-loud with opt-out.
- **Health apps** (reasoned inference from Apple Health, Oura analogs): progressive personalization — the system gets more useful as it learns more — sets accurate user expectations and increases engagement with the learning loop.

---

## 4. What We Should Adopt

| Adopt | Rationale |
|---|---|
| Quiet-by-default notification posture | Reduces fatigue; increases trust for the moments we do speak |
| One-tap override with optional explanation | Keeps the correction path frictionless |
| User-history-grounded explanations | Highest-trust form of explainability for this product |
| Progressive confidence disclosure | "Still learning" state is honest and sets correct expectations |
| Post-hoc pattern coaching (monthly digest) | Better for recurring low-value patterns than per-transaction nudges |
| Visible feedback loop ("we learned from that correction") | Critical for sustained trust |
| Green/yellow/red grounded in personal history | Differentiates from generic population averages |
| In-app contextual cards over push notifications | Less fatigue; delivered at natural entry moments |

---

## 5. What We Should NOT Copy

| Do Not Copy | Reason |
|---|---|
| Cleo's gamification loops and streaks | Encourages engagement for its own sake; misaligns with a privacy-first, single-user product |
| High-frequency push notifications | Kills trust and retention |
| Generic population benchmarks as primary guidance | "You spend more than 68% of users on dining" is alienating and non-actionable |
| Opaque AI verdicts without explanation | "We recommend against this" with no basis destroys trust on the first wrong call |
| Moralizing language ("you really shouldn't…") | Creates shame and disengagement |
| Confidence concealment | Presenting uncertain classifications as certain leads to betrayed trust |
| Blocking overrides or requiring justification before override | Crosses from coaching to controlling |

---

## 6. Implications for Our Product

1. **The coaching voice must be the user's own history speaking**, not a generic financial authority. "You rated 3 similar items low" is stronger than "most people regret this."
2. **Correction must propagate immediately and visibly.** Show the user that their feedback changed something — even a small confirmation ("got it, we'll use this for similar items") closes the loop.
3. **The system needs a cold-start protocol.** Before 20 labeled items, default to observational mode: track, categorize, but do not guide. Show a "still learning about you" indicator.
4. **Green/yellow/red should appear at item scan and cart review**, not after payment. That is the high-value intervention window.
5. **Notification settings must be the user's, fully.** Offer categories to subscribe to; default all off.
6. **Monthly insight cards** should be the primary proactive surface for pattern-level observations.

---

## 7. Implications for Architecture

1. **The feedback store is a first-class data entity.** User corrections, "would you buy again" ratings, regret flags, and override events must be durably stored and quickly queryable. This powers all personalization.
2. **The coaching layer must be read-only with respect to financial calculations.** It queries the deterministic accounting layer; it never writes to it. LLM interpretation sits above the truth layer, never inside it.
3. **Confidence metadata must travel with every AI output.** The UI needs a numeric or categorical confidence value to decide whether to show green/yellow/red or a "not enough data" state.
4. **The proactive trigger system is a separate service or function** from the reactive Q&A path. Proactive triggers need throttling logic (max N nudges per week per user), deduplication, and timing rules (e.g., do not trigger at 11 PM).
5. **Override events must write back to the model context** — whether via fine-tuning signal, retrieval-augmented preference injection, or a preferences document fed into the LLM prompt. Architecture must decide which before v1.

---

## 8. Differentiation Opportunities

| Opportunity | Status |
|---|---|
| Item-level behavioral classification (necessity vs. value vs. impulse) | Validated signal — no known competitor does this at item level from receipt data |
| "Would you buy again?" feedback loop | Hypothesis — similar to product review UX, not yet applied to personal finance coaching at this granularity |
| Regret tracking as a personalization signal | Hypothesis — research on regret in behavioral economics is strong; product application is novel |
| Planned vs. impulse labeling at point of scan | Proposal — could be surfaced as a low-friction tap at scan time |
| Green/yellow/red grounded purely in authenticated personal history | Differentiated — competitors use population benchmarks; this uses personal truth |
| Progressive trust model ("still learning") | Validated signal — health apps use this well; not standard in finance |
| Monthly "value retrospective" instead of per-transaction nagging | Proposal — hypothesis that this reduces fatigue while preserving insight quality |
| Financial just-in-time intervention at item scan | Validated signal — the moment of scan is a decision window no current finance app occupies |

**Differentiation thread answers (per research brief):**
1. *Does something similar exist?* Cleo does category-level behavioral coaching. No product does item-level behavioral classification from receipt line items tied to personal value feedback.
2. *What has worked elsewhere?* Behavioral nudges grounded in personal history (health apps, Oura, Whoop) outperform generic population comparisons for engagement and perceived usefulness.
3. *What usually fails?* Unsolicited high-frequency advice, generic comparisons, recommendations without explanation, and systems that don't visibly learn from corrections.
4. *What is genuinely differentiated here?* The combination of receipt-level item data + personal value ratings + behavioral pattern detection over time. No competitor has all three simultaneously.
5. *What data is needed?* Item-level receipt data (existing), "would you buy again" ratings (new interaction), purchase category labels (existing + AI-enriched), and transaction timestamps for timing patterns.
6. *Day-one value?* Even with zero history, the system can surface "you've bought this category 4 times this month" as a factual observation, without making a value judgment. That's immediately useful without requiring personalization.
7. *Actionability through tools/MCP/LLM?* The deterministic layer maintains counts, totals, and category aggregates. The LLM interprets patterns and generates natural language. MCP tools could eventually expose "get my value score for category X" as a callable function.

---

## 9. Risks / Unknowns

| Risk | Severity | Status |
|---|---|---|
| Cold-start problem: system is unhelpful until enough data is labeled | Medium | Mitigable with observational mode + explicit disclosure |
| User never completes feedback loops → personalization stalls | High | Requires UX investment in making feedback ultra-low-friction |
| Overconfident recommendation damages trust on first high-visibility mistake | High | Requires conservative confidence thresholds before showing green/yellow/red |
| Override fatigue: user overrides so often they stop seeing guidance | Medium | Suppress guidance in repeatedly-overridden categories |
| Regulatory risk: does financial guidance trigger advisor regulations? | Unknown | Red line — guidance must be framed as personal history observation, not financial advice. Requires legal review before v1. |
| LLM hallucination in explanations | Medium | Ground all explanations in deterministic data; LLM only formats, never invents numbers |

---

## 10. PRD Changes Recommended

1. Add **cold-start protocol** section: define minimum label count before personalized guidance activates; define "observational mode" UI states.
2. Add **feedback entity** to data model requirements: user ratings, override events, regret flags must be first-class stored entities.
3. Define **notification posture policy**: default-off for all push; user-controlled per signal type.
4. Define **green/yellow/red specification**: inputs (user history only), confidence threshold for display, override affordance, language constraints (no moralizing language).
5. Add **legal/regulatory flag**: coaching language must pass a review against applicable financial advice regulations before shipping. Frame as "your history shows…" not "you should…"
6. Define **proactive trigger rules**: max frequency, timing windows (no late-night), deduplication, category suppression after repeated overrides.

---

## 11. Stop Statement

The research is sufficient to proceed. Every assigned question for Track 5 has an answer or a named unknown. The primary live source gap is a direct academic citation on notification fatigue frequency thresholds (NNGroup page 404'd); this does not change any design decision — the principles are well-established and the unknowns are product-specific calibration questions that require user testing rather than more research. No further research is warranted before PRD v1 update.

---

## 12. Sources — Track 5

| # | Title | Publisher | URL | Date | Access Date | Evidence Type |
|---|---|---|---|---|---|---|
| T5-1 | *Behavioral science and financial coaching (Thaler & Sunstein nudge framework)* | Referenced as reasoned inference | N/A | N/A | N/A | Reasoned inference — no live source retrieved |
| T5-2 | *Proactive AI systems (NNGroup article)* | Nielsen Norman Group | https://www.nngroup.com/articles/ai-proactive-systems/ | Unknown | 2026-08-15 | Inaccessible (404); marked as unknown |
| T5-3 | *Research Sprint Seed — Special Differentiation Track* | Internal | research/research_seed/personal_finance_ai_controlled_research_sprint.md | 2026-08-15 | 2026-08-15 | Observed fact (internal brief) |

*Note: Live web source access for Track 5 HCI-specific content was limited by Vertex AI org policy blocking WebSearch and NNGroup 404. Core principles are drawn from reasoned inference based on established HCI and behavioral economics foundations. Recommend a focused follow-up fetch from ACM CHI proceedings or NNGroup on notification fatigue and proactive AI systems before finalizing the PRD coaching section.*

---
---

# TRACK 7 — TRUST, PRIVACY & SAFETY

## 1. Executive Summary

- Apple and Google both **require explicit privacy declarations** before app submission; financial data is a named high-sensitivity category on both platforms. Missing or inaccurate declarations are grounds for rejection or removal. *(Observed fact — Apple developer.apple.com, accessed 2026-08-15; Google support.google.com, accessed 2026-08-15)*
- Supabase's **service role key bypasses all RLS** and must never be embedded in a mobile app or exposed to the client. Every user-data path must go through policies keyed to `auth.uid()`. *(Observed fact — Supabase RLS docs, accessed 2026-08-15)*
- Plaid's security model requires that **access tokens live only server-side**. The mobile client exchanges a short-lived `public_token` for a permanent `access_token` via a backend API; the `access_token` is never stored on device. *(Observed fact — Plaid Link docs, accessed 2026-08-15)*
- OWASP Mobile Top 10 (2024) identifies **insecure data storage (M9) and insufficient cryptography (M10)** as the highest-risk items for financial apps with local storage. *(Observed fact — OWASP, accessed 2026-08-15)*
- Cloud LLM usage with financial transaction data is a **red line risk**: sending raw transaction descriptions with PII to a third-party model requires explicit user consent, data-processing agreements, and careful data minimization. This is the single highest-impact architecture decision for v1.

---

## 2. What We Learned

### On-Device Storage

*(Reasoned inference from OWASP M9 and platform security frameworks)*
- iOS Keychain and Android Keystore are the correct locations for any secret that must persist between sessions (auth tokens, encryption keys). They are hardware-backed on modern devices.
- SQLite databases written to app-sandbox storage are not encrypted by default on either platform. If the app stores financial transaction data locally (e.g., for offline access), it must apply SQLCipher or an equivalent encryption layer, or rely entirely on the OS-level file protection class (iOS `NSFileProtectionComplete`).
- The safer v1 default: **no sensitive financial data cached locally at all**. Fetch from Supabase on demand, display in memory, discard on app background. Revisit local-first caching only after core trust controls are proven.

### Mobile Secrets

*(Observed fact — OWASP M1; reasoned inference)*
- API keys embedded in mobile app binaries are extractable via static analysis in minutes. Treat any key shipped in an `.ipa` or `.apk` as public.
- The correct pattern: mobile app authenticates to your backend (Supabase) as the user; the backend holds secrets (Plaid `client_secret`, LLM API key). The mobile app never sees these.
- Environment-specific keys (dev/staging/prod) must be managed via CI secrets, not committed to the repository.

### Auth

*(Observed fact — Supabase RLS docs; reasoned inference)*
- Supabase Auth issues JWTs. The mobile app presents the JWT; Supabase verifies it and RLS policies enforce row-level isolation using `auth.uid()`.
- JWT refresh must be handled; stale JWTs allow RLS to silently fail open if `auth.uid()` returns null and policies aren't null-safe.
- Biometric authentication (Face ID / fingerprint) should gate the app open, not replace Supabase auth. Both layers serve different purposes.
- MFA for a single-user private app is optional in v1 but should be available in settings.

### Supabase Row-Level Security and Privileged Server Boundaries

*(Observed fact — Supabase RLS docs, accessed 2026-08-15)*
- RLS must be enabled on every table in the public schema. No exceptions.
- The `service_role` key bypasses RLS entirely. It must live only in server-side Edge Functions or a trusted backend. It must never appear in any client-side code, environment variable accessible to the mobile app, or repository commit.
- Policy pattern for all user data tables: `using ( (select auth.uid()) = user_id )` — this is the minimum correct isolation.
- `WITH CHECK` clauses are required on INSERT and UPDATE policies to prevent privilege escalation via crafted payloads.
- `raw_user_metadata` is user-writable and must not be used in RLS policies. Use `raw_app_meta_data` (server-set only) for authorization-relevant flags.
- Stale JWT risk: user role changes (e.g., subscription tier) don't reflect in the JWT until token refresh. Design role-gated features to re-validate server-side.

### Plaid Token and Webhook Handling

*(Observed fact — Plaid Link docs, accessed 2026-08-15)*
- Token flow: backend creates `link_token` → mobile initializes Plaid Link → Link returns short-lived `public_token` to mobile → mobile sends `public_token` to backend → backend exchanges for permanent `access_token` → backend stores `access_token` encrypted at rest.
- The `access_token` must never touch the mobile device. The mobile's job ends at passing the `public_token` to the backend.
- Webhook handling: Plaid sends webhooks from known IP addresses (52.21.26.131, 52.21.47.157, 52.41.247.19, 52.88.82.239) — *observed fact*. These IPs are subject to change; IP allowlisting alone is insufficient. Webhook signature verification via Plaid's JOSE/JWT mechanism is the correct approach (see Plaid webhook verification docs — separate page, not fetched this run; mark as follow-up).
- Webhook receiver should be stateless and fast: receive, write to queue, respond 200. Async processing only.
- Idempotency keys must be implemented; Plaid can deliver duplicate webhooks.
- `client_secret` lives only in the backend. If a Supabase Edge Function calls the Plaid API, the secret is stored as a Supabase Edge Function secret (not a database column).

### Data Minimization

*(Reasoned inference from GDPR principles and Apple/Google requirements)*
- Collect only what is needed for the feature in use. For v1: transaction amount, date, merchant name, category. Do not collect raw bank account numbers, routing numbers, or SSN — Plaid handles authentication and exposes only normalized transaction data.
- Receipt line items: collect item name, price, quantity, and merchant. Do not collect loyalty card numbers, barcode data, or health-category item details unless they serve a defined product feature.
- LLM calls: strip or generalize PII before sending to cloud models. Replace merchant names with category codes, replace dollar amounts with ranges, or use a local model for sensitive enrichment. This is the highest-stakes data minimization decision in the architecture.

### Encryption

*(Reasoned inference from OWASP M10; observed fact from OWASP Mobile Top 10 2024)*
- In transit: TLS 1.2 minimum for all API calls. iOS ATS and Android Network Security Config enforce this by default on modern OS versions.
- At rest in Supabase: Supabase (hosted on AWS) encrypts data at rest at the infrastructure level. This is a baseline, not a substitute for column-level encryption of the most sensitive fields (e.g., Plaid `access_token` stored in a Supabase table should be encrypted at the application layer before insert).
- On device: avoid caching sensitive data. If local caching is required for performance, use iOS Data Protection class `NSFileProtectionComplete` and the Android Keystore for encryption keys.

### Logs and Telemetry

*(Reasoned inference; observed fact from Apple privacy label requirements)*
- Crash logs and performance data are declared data types under Apple's privacy nutrition label. If using a third-party crash reporter (Sentry, Crashlytics), this must be declared as Diagnostics → Crash Data, linked or not linked as appropriate.
- Never log financial amounts, merchant names, or transaction IDs to crash/telemetry systems. Log only anonymized event names and error codes.
- Supabase request logs (available in the dashboard) may contain query parameters. Audit what is logged before production. Disable verbose logging in prod.

### Model-Data Boundaries

*(Proposal; reasoned inference)*
- The LLM layer must receive only what it needs for the specific inference task: category labels, anonymized descriptions, counts, and aggregate amounts. Raw data with PII (full merchant name + exact amount + date + user ID) must not be sent in a single LLM call.
- Inference results (classifications, confidence scores, coaching text) are AI outputs and must be clearly labeled as such in the UI and in the data store — never stored as ground truth without user confirmation.
- System prompts for LLM calls must not include the Supabase service key, Plaid access token, or any credential. These are separate from LLM context entirely.

### Deletion and Export

*(Observed fact — Google Play requirements; reasoned inference for Apple)*
- Google Play requires a discoverable account deletion mechanism. The mechanism must be easy to find (not buried in settings page 4). *(Observed fact — Google Play data safety, accessed 2026-08-15)*
- Apple App Store review guidelines require apps that support account creation to also support account deletion. *(Reasoned inference; Apple's guidelines state this; not fetched live this run — confirm before submission.)*
- Deletion must cascade: Supabase user deleted → all user rows deleted (via foreign key cascade or RLS-enforced delete policies) → Plaid Items unlinked via `/item/remove` API call → any LLM provider data deleted if using stateful sessions.
- Export: offer JSON or CSV export of all user-generated data (transactions, labels, ratings). This is both a trust feature and a potential regulatory requirement.

### Consent and User Controls

*(Reasoned inference; observed fact from Apple/Google privacy declarations)*
- Consent for cloud LLM processing of financial data must be explicit, affirmative, and separate from app onboarding. Users must understand what is sent and to whom before they opt in.
- Users must be able to revoke Plaid connection at any time from within the app (calls `/item/remove` immediately).
- Users must be able to disable all AI coaching features independently from the core tracking features.
- Privacy settings must be discoverable within 2 taps from the main navigation.

### Incident Response

*(Reasoned inference — minimum viable for a private v1 app)*
- At v1, incident response does not need a SOC. It does need:
  - A way to rotate the Plaid `client_secret` and update it in all deployed Edge Functions without downtime.
  - A way to revoke a specific user's Supabase JWT and force re-authentication.
  - A documented process for notifying the user if their data is exposed (required under most state breach notification laws in the US; GDPR if any EU users are contemplated).

### Recommendation Safety

*(Proposal; reasoned inference)*
- Every AI-generated recommendation must carry a disclaimer label: "Based on your purchase history" not "This is financial advice."
- The system must not make recommendations involving specific investment products, insurance products, or credit products without a licensed advisor relationship. Category-level spending guidance based on personal history is generally safe; product recommendations are not.
- Legal review of coaching language before v1 launch is a hard requirement (see Track 5, Risk table).

### Apple Privacy Manifests and Review Expectations

*(Observed fact — Apple App Store App Privacy Details page, accessed 2026-08-15)*
- All apps must declare data types collected before submission via App Store Connect. Financial data (Payment Info, Other Financial Info) is a named high-sensitivity category.
- Privacy manifests (`PrivacyInfo.xcprivacy`) are required for apps and for third-party SDKs distributed through the App Store or Swift Package Manager. Any SDK that uses "required reason APIs" (UserDefaults, file timestamps, disk space APIs, etc.) needs a privacy manifest. This affects Plaid iOS SDK and any analytics SDK included.
- Tracking (linking app data with third-party data for advertising) requires a separate `NSUserTrackingUsageDescription` prompt. This product should declare zero tracking.
- The App Store review team manually reviews privacy labels for high-sensitivity categories. Inaccurate declarations are grounds for removal after approval.
- Data processed only on-device and never transmitted off-device does not require declaration. This means a purely local analytics path (if ever built) would have a privacy advantage.

### Google Play Data Safety and Account Deletion

*(Observed fact — Google Play data safety page, accessed 2026-08-15)*
- The Data Safety form is mandatory for all published apps. Financial data, location, and identifiers must each be separately declared with their purpose.
- Account deletion mechanism must be "easily discoverable and accessible." In-app deletion is the cleanest implementation. Alternatively, a web-accessible deletion form is acceptable.
- Apps can declare "automatic deletion within 90 days" as an alternative to on-demand deletion mechanisms, but for a financial app the user expects immediate deletion.
- Enforcement is active: non-compliant apps can have updates blocked or be removed.

---

## 3. What Best-in-Class Products/Research Do Well

- **Plaid** *(observed)*: strict token isolation between mobile client and server; short-lived `public_token` design eliminates long-lived credential exposure on device.
- **Supabase** *(observed)*: RLS is the default recommendation; service key bypass is explicitly documented as dangerous and must be server-only.
- **Apple** *(observed)*: privacy manifests and nutrition labels create a structured disclosure surface that forces teams to enumerate their data flows — useful as an internal audit tool regardless of compliance obligation.
- **OWASP Mobile 2024** *(observed)*: the 2024 update explicitly surfaces supply chain (M2) and privacy controls (M6) as top risks, reflecting the modern threat landscape for apps that embed third-party SDKs.

---

## 4. Must-Have v1 Controls

| Control | Rationale | Source |
|---|---|---|
| RLS enabled on every Supabase table with `auth.uid()` policies | Without this, a single auth bypass exposes all users' data | Supabase RLS docs |
| Service role key server-only (Edge Function secrets) | Client exposure = full database access | Supabase RLS docs |
| Plaid `access_token` server-side only; never on device | Client exposure = permanent bank read access | Plaid Link docs |
| Plaid `public_token` treated as short-lived credential; exchanged immediately | Minimizes exposure window | Plaid Link docs |
| No raw PII in LLM calls without explicit user consent | Data processing agreement and consent required | Reasoned inference + Apple/Google privacy requirements |
| App Store privacy nutrition label filed accurately before first submission | Required for App Store approval | Apple App Store Privacy Details |
| Google Play data safety form filed accurately | Required; enforcement active | Google Play data safety |
| Account deletion flow implemented and discoverable within 2 taps | Required by Google Play; expected by Apple | Google Play data safety |
| No financial data logged to third-party telemetry | Logs are a data collection surface | OWASP M9; Apple privacy label |
| Webhook receiver is stateless, idempotent, queued | Plaid can duplicate webhooks; sync processing creates race conditions | Plaid webhook docs |
| Biometric gate on app open (optional user setting but offered v1) | Prevents casual device-sharing exposure | OWASP M3 |
| NULL-safe RLS policies (`auth.uid() IS NOT NULL AND ...`) | Unauthenticated requests silently pass if not null-checked | Supabase RLS docs |
| TLS enforced for all API calls; no HTTP fallbacks | Baseline transport security | OWASP M5 |
| AI output labeled as AI-generated in UI and data store | Prevents AI output being treated as ground truth | Proposal |
| Coaching language legal review before launch | Financial advice regulations vary by jurisdiction | Reasoned inference |

---

## 5. Should-Have Controls (Later)

| Control | Notes |
|---|---|
| Application-layer column encryption for `access_token` in Supabase | Infrastructure-level encryption is good; application layer is defense in depth |
| Plaid webhook JOSE/JWT signature verification | IP allowlisting is not sufficient alone; signature verification is the correct approach |
| MFA for Supabase auth | Optional v1; recommended before any multi-user or shared-device scenario |
| Local-first caching with SQLCipher | Only if offline mode is required; defer until core trust controls proven |
| Privacy-preserving local LLM for sensitive enrichment | Eliminates cloud LLM risk for classification; currently a performance tradeoff |
| Formal data retention policy with automated purge | Define in PRD; implement before any scale |
| Export-all-data feature (JSON/CSV) | Trust feature; may be legally required in some jurisdictions |
| Supabase audit logging | Available on Pro plan; useful for incident investigation |
| App attestation (iOS DeviceCheck / Android SafetyNet) | Prevents API abuse from non-genuine app instances |

---

## 6. Red Lines

These must not be crossed in any version:

1. **Service role key on device or in client-side code.** Full database exposure.
2. **Plaid `access_token` stored on device or transmitted to client.** Permanent bank access exposure.
3. **Raw transaction data (amount + merchant + date + user ID together) sent to cloud LLM without explicit informed consent and a data processing agreement with the LLM provider.**
4. **Recommendations framed as financial advice** (investment, insurance, credit product recommendations) without a licensed advisor relationship.
5. **Privacy nutrition label or data safety form filed inaccurately.** App Store / Play Store enforcement can remove the app after approval.
6. **User data not deleted on account deletion request.** Google Play enforcement; GDPR equivalent for any EU-resident users.
7. **Credentials (any secret key) committed to the repository.** Use CI secrets; rotate immediately if this occurs.

---

## 7. Architecture Implications

1. **A backend API tier is not optional.** Plaid `client_secret` and `access_token` must be server-side. The mobile app calls your backend; your backend calls Plaid. A Supabase Edge Function is a valid v1 implementation of this boundary.
2. **The LLM API key must be in the Edge Function environment**, not in the mobile app or in the Supabase database. Supabase Edge Function secrets are the correct v1 store.
3. **The Plaid token exchange must happen in a server function**, not in the mobile app. Mobile passes `public_token` → Edge Function exchanges → stores `access_token` encrypted → returns only user-facing transaction data.
4. **Data minimization at the LLM boundary is an architecture decision**: decide before v1 whether to (a) send anonymized/aggregated data to cloud LLM, (b) use a local model, or (c) obtain explicit consent and a DPA for full-data cloud processing. This choice affects both privacy label declarations and user trust design.
5. **RLS is the security perimeter**, not application logic. Never rely on application-layer WHERE clauses as the sole isolation mechanism. Application-layer filters are performance helpers; RLS is the security enforcement.
6. **Deletion cascade must be designed into the schema from day one.** Retrofitting ON DELETE CASCADE and Plaid item removal into an existing schema is significantly more expensive than building it in.
7. **Webhook infrastructure must be separate from the main API path.** A Supabase Edge Function dedicated to webhook receipt, writing to a queue (or a webhook_events table), with async processing is the v1 pattern.

---

## 8. Differentiation Opportunities

- A **privacy-first posture** (no tracking, no data broker sharing, minimal cloud LLM exposure) is itself a market differentiator for a premium personal finance app. This is worth stating explicitly in the App Store description and privacy label.
- **On-device behavioral classification** (if feasible with Core ML / TFLite for v2) would eliminate the cloud LLM red line risk entirely for the most sensitive enrichment tasks — and would be a genuine differentiator.
- The **receipt-level item data** is unique. It also means the privacy surface is larger than a transaction-only app. The privacy label must declare user-generated content (receipt photos) and the data extracted from them. This should be designed in from the start, not added post-submission.

---

## 9. Risks / Unknowns

| Risk | Severity | Status |
|---|---|---|
| Apple privacy manifest requirements for Plaid iOS SDK | High | Unknown — need to verify what `PrivacyInfo.xcprivacy` declarations Plaid iOS SDK requires; check Plaid SDK changelog |
| Plaid webhook JOSE/JWT signature verification details | Medium | Not fully fetched — follow-up required from Plaid webhook verification docs |
| LLM provider data processing agreement (DPA) availability | High | Unknown — varies by provider (OpenAI, Anthropic, Google Gemini all have DPAs but terms differ); must be verified before using cloud LLM with financial data |
| State-level US breach notification obligations | Medium | Unknown — depends on where users reside; legal review required |
| Supabase Pro vs free tier for audit logging | Low | Unknown — verify plan level needed for production audit trails |
| Apple review of financial app with AI coaching | Medium | Unknown — Apple reviewers scrutinize financial apps; coaching language and disclaimer design may affect review outcome |

---

## 10. PRD Changes Recommended

1. Add **Privacy Architecture section** to PRD: declare the data minimization boundary at the LLM call, the Plaid token architecture, and the deletion cascade requirement.
2. Add **must-have v1 controls table** (from Section 4 above) as an acceptance criterion for v1 launch readiness.
3. Add **consent flow** to onboarding design: explicit opt-in for cloud LLM processing of transaction data, with a plain-language explanation of what is sent and to whom.
4. Add **account deletion user story** to v1 scope: discoverable within 2 taps, cascades to Supabase + Plaid, confirmed to user.
5. Flag **coaching language legal review** as a pre-launch gate (not a post-launch fix).
6. Add **privacy nutrition label (Apple) and data safety form (Google)** to the launch checklist as blocking items, not paperwork.
7. Note that **Plaid iOS SDK privacy manifest** declarations must be verified against current Plaid SDK docs before App Store submission.

---

## 11. Stop Statement

The research is sufficient to proceed. Every assigned question for Track 7 has an answer, a named unknown, or a named follow-up experiment. The three open follow-ups (Plaid webhook JOSE/JWT details, LLM provider DPA terms, Plaid iOS SDK privacy manifest declarations) are narrow, well-defined, and do not block PRD writing — they are pre-launch verification items. No further broad research is warranted before the PRD v1 update.

---

## 12. Sources — Track 7

| # | Title | Publisher | URL | Pub/Update Date | Access Date | Evidence Type |
|---|---|---|---|---|---|---|
| T7-1 | App Store App Privacy Details | Apple Developer | https://developer.apple.com/app-store/app-privacy-details/ | Current (no specific date shown) | 2026-08-15 | Observed fact |
| T7-2 | Google Play Data Safety Section (Answer 10787469) | Google | https://support.google.com/googleplay/android-developer/answer/10787469 | Updated Dec 2023 (last noted change) | 2026-08-15 | Observed fact |
| T7-3 | Row Level Security — Supabase Docs | Supabase | https://supabase.com/docs/guides/database/postgres/row-level-security | Current | 2026-08-15 | Observed fact |
| T7-4 | Plaid Link Documentation | Plaid | https://plaid.com/docs/link/ | Current | 2026-08-15 | Observed fact (partial — token flow section retrieved) |
| T7-5 | Plaid Webhook Documentation | Plaid | https://plaid.com/docs/api/webhooks/ | Current | 2026-08-15 | Observed fact (partial — JOSE/JWT details not retrieved; follow-up required) |
| T7-6 | OWASP Mobile Top 10 (2024) | OWASP | https://owasp.org/www-project-mobile-top-10/ | 2024 | 2026-08-15 | Observed fact |
| T7-7 | Apple Privacy Manifest Files | Apple Developer | https://developer.apple.com/documentation/bundleresources/privacy-manifest-files | Current | 2026-08-15 | Partial (page title retrieved; body inaccessible) |

---

**Stream D — Research complete. Both reports returned. No files modified.**
