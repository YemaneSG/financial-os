I now have sufficient live evidence. Compiling the audit.

---

## CORRECTIONS AND CONFIRMATIONS ADDENDUM

**Sprint:** 2026-08-15-premium-mobile-r1
**Auditor:** Claude Code (read-only, no files modified)
**Audit date:** 2026-08-15
**Sources consulted:** 10 live primary sources (listed at end)

---

### Audit Table

---

#### Claim 1 — Apple minimum-functionality rule: 4.2 vs 4.2.7

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **1a.** "Guideline 4.2.7 (thin-wrapper prohibition)" is cited as the general thin-wrapper rule for an Angular+Capacitor app. | **Corrected** | 4.2.7 is titled **Remote Desktop Clients**. It governs apps that mirror specific software or services on a host device over a local network. Sub-clause 4.2.7(e) — "Thin clients for cloud-based apps are not appropriate for the App Store" — appears inside that remote-desktop context, not as a standalone general rule. An Angular+Capacitor finance app is not a remote desktop client; Apple reviewers would apply the general **4.2** guideline (app must be "useful, unique, or app-like" and not "simply a repackaged website") and possibly 4.2.2 (not primarily web clippings/content aggregators). | **Yes — PRD states "to satisfy App Store guideline 4.2.7"; the correct citation for a non-remote-desktop app is 4.2 (and 4.2.2 where applicable). The native-capability mitigation strategy is still correct — but the stated reason is the wrong sub-guideline.** |
| **1b.** The thin-wrapper risk and the native-capability mitigation (camera, push, biometric) are valid. | **Confirmed** | The general 4.2 rule does require apps to provide genuine utility beyond a repackaged website; adding native capabilities (camera, push notifications, biometrics) is the correct mitigation regardless of which sub-guideline applies. | No — strategy unchanged; only citation changes. |

**Source:** Apple App Store Review Guidelines §4.2 and §4.2.7, https://developer.apple.com/app-store/review/guidelines/, accessed 2026-08-15.

---

#### Claim 2 — Apple legal-entity rule for financial services apps

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **2a.** "Financial services apps must be submitted by the legal entity that provides the services, properly licensed in all jurisdictions." | **Corrected (two errors)** | The live text of 5.1.1(ix) reads: "Apps that provide services in **highly regulated fields (such as banking and financial services** …) or that require sensitive user information **should** be submitted by a legal entity that provides the services, and not by an individual developer." Two corrections: (1) The modal verb is **should**, not must — it is a strong guideline, not an absolute prohibition; (2) The phrase "properly licensed in all jurisdictions" does not appear in the guideline — it is an addition not present in the actual text. | **Minor** — the PRD item should read "should be submitted by a legal entity" and should not assert a licensing mandate that the guideline text does not include. |
| **2b.** Whether a personal finance tracker (as opposed to a bank or lender) falls under "providing services in banking and financial services." | **Still unknown** | 5.1.1(ix) does not define "provides services in banking and financial services." A personal tracker that aggregates a user's own data via Plaid could be reviewed as a financial services app by Apple reviewers. Whether a single-owner personal tool triggers the legal-entity requirement depends on Apple's reviewer interpretation, not a bright-line rule in the text. Requires legal review, not more research. | **Yes — PRD legal review item should note the ambiguity of scope, not present the rule as a certain hard requirement.** |
| **2c.** "For a single-owner personal tool, the developer account submission should be by the individual who owns the financial data." | **Confirmed with caveat** | Reasonable inference — if the app is distributed publicly (App Store), Apple may interpret it as providing a service rather than personal tooling. If distributed only to the developer's own device (TestFlight personal), the guideline may not apply. The scope of distribution is the key variable. | No — already noted as "should be assessed early." |

**Source:** Apple App Store Review Guidelines §5.1.1(ix), https://developer.apple.com/app-store/review/guidelines/, accessed 2026-08-15.

---

#### Claim 3 — Angular + Capacitor: technical packaging vs App Store acceptance

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **3a.** Angular is a named supported framework in Capacitor. | **Confirmed** | Capacitor docs explicitly link to a dedicated Angular guide and name Angular (alongside React and Vue) as a supported framework. The output directory `www` is shown as the Angular-specific example. | No. |
| **3b.** Capacitor produces "genuine Xcode and Android Studio projects, not thin web shells." | **Confirmed (with source precision)** | The App Store deployment page states: "Capacitor apps are normal native apps at the end of the day, the way they are deployed to the App Store is just like any other native app." The getting-started docs reference "your Android and iOS projects" after `npx cap add`. Technical packaging feasibility is confirmed. | No. |
| **3c.** App Store acceptance is confirmed and the thin-wrapper risk is resolved by using Capacitor. | **Corrected** | Capacitor deployment pages do not address thin-wrapper risk or App Store acceptance criteria — they redirect to Apple's own submission guidelines. **App Store acceptance is not guaranteed by the packaging tool**; it depends on what the app does. The correct framing is: Capacitor is technically capable of producing a store-submittable native app; acceptance under 4.2 still depends on the app providing genuine utility beyond a web view. These are separate questions. | **Yes — the feasibility matrix entry "Angular + Capacitor → iOS App Store: Feasible" conflates packaging feasibility with acceptance. It should read: packaging is feasible; acceptance conditional on native-capability evidence (camera/push/biometric).** |
| **3d.** No Angular-specific Plaid SDK; Plaid Link is invoked via native layer or WebView. | **Confirmed** | Plaid docs name iOS, Android, and React Native SDKs. Angular and Capacitor are not mentioned. Web SDK via WebView is an implied alternative for Capacitor apps. | No. |

**Sources:** Capacitor getting-started https://capacitorjs.com/docs/getting-started, Capacitor iOS App Store deployment https://capacitorjs.com/docs/ios/deploying-to-app-store, Plaid Link docs https://plaid.com/docs/link/, all accessed 2026-08-15.

---

#### Claim 4 — Supabase RLS: service-role bypass, anon key, NULL semantics, IS NOT NULL guard

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **4a.** Service-role key bypasses all RLS. | **Confirmed** | Live source confirms: service keys "can be used to bypass RLS." Must remain server-side only. | No. |
| **4b.** "Every RLS policy using `auth.uid() = user_id` **silently passes** for unauthenticated requests when `auth.uid()` returns null, because `null = null` is false in SQL." | **Corrected — two errors** | The live Supabase source states the policy "will **silently fail** for unauthenticated users, because `null = user_id` is always false in SQL." The two errors in the report: (1) **"silently passes" is the opposite of correct** — the policy silently *blocks* (fails to return rows), not passes. Unauthenticated users see *no rows*, which is the desired security outcome. (2) The expression is `null = user_id`, not `null = null`. | **Yes — the report frames this as a security vulnerability ("footgun allows unauthenticated reads if policies are not explicitly guarded"). The live source shows the policy WITHOUT IS NOT NULL already denies unauthenticated access. The security framing in R2 ("allows unauthenticated reads") is incorrect.** |
| **4c.** IS NOT NULL guard is security-critical. | **Corrected** | The live Supabase source characterizes IS NOT NULL as a **clarity and intention-clarity recommendation**, not a security-critical fix for a real data-leak vulnerability. Exact wording: "To avoid confusion and make your intention clear, we recommend explicitly checking for authentication." The IS NOT NULL guard is defense-in-depth / developer-intent clarity — not a patch for an exploitable unauthenticated-read path. | **Yes — PRD must-have controls and R2 risk severity should be updated. The must-have remains good practice (explicit is better than implicit) but should not be cited as a critical vulnerability fix.** |
| **4d.** Anon key is "client-safe publishable" while service key must be server-only. | **Confirmed with precision** | Live source: `anon` role = unauthenticated requests; `authenticated` role = authenticated requests. The anon key is safe on the client *only* when RLS is correctly enabled on every table. Without RLS, the anon key exposes all data. | No — report already notes this dependency. |

**Source:** Supabase Row Level Security docs, https://supabase.com/docs/guides/database/postgres/row-level-security, accessed 2026-08-15.

---

#### Claim 5 — Supabase pricing, Edge Function constraints, storage, portability, Pro-tier urgency

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **5a.** Pro $25/mo, 8GB DB, 100GB storage, 2M edge function invocations; Team $599/mo. | **Confirmed** | Live pricing page matches exactly. Pro overage: $0.125/GB DB, $0.0213/GB storage, $2/million invocations. | No. |
| **5b.** Free plan edge function invocations: 500K/month. | **Still unknown** | The live pricing page did not display the Free plan's edge function invocation count — it returned "Not specified" for that cell. The 500K figure in the report cannot be confirmed from the live source. | **Minor** — the Free tier is not recommended anyway; 500K is unverified. |
| **5c.** Free plan pauses after 1 week of inactivity. | **Confirmed** | Live source: "After 1 week of inactivity." | No. |
| **5d.** No claim in the reports that Pro must be purchased immediately. | **Confirmed (no such claim)** | The report recommends Pro "from the start" as a best practice — it does not assert an immediate commercial obligation. | No. |
| **5e.** Supabase storage file size limits not confirmed. | **Confirmed as unknown** | Report correctly flags this as a follow-up. Live source did not show file size limits. | No. |
| **5f.** Portability: Postgres pg_dump works; managed features (PITR, branching) do not transfer. | **Confirmed** | Consistent with self-hosting documentation. | No. |

**Source:** Supabase pricing, https://supabase.com/pricing, accessed 2026-08-15.

---

#### Claim 6 — Plaid: history limit, token flow, access-token boundary, webhooks, Capacitor/Angular, privacy manifests

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **6a.** 730-day max history via `transactions.days_requested`. | **Confirmed** | Live source: "the maximum value is 730." | No. |
| **6b.** Token flow: link_token → public_token → access_token via /item/public_token/exchange. | **Confirmed** | All three steps confirmed by live Plaid transactions and link docs. | No. |
| **6c.** "access_token must live exclusively in a server-side layer … a non-negotiable architecture constraint." | **Corrected (overstatement)** | Plaid documentation does not explicitly mandate server-side-only storage of the access_token. The code examples show exchange happening on a server endpoint and state tokens "should be saved to a persistent database," but do not declare a security prohibition on client exposure. The server-side-only boundary is a **well-reasoned security inference and best practice** (the client never receives the access_token in Plaid's example flows), not a documented Plaid mandate. Describe it as: "Plaid's example architecture keeps the access_token server-side; placing it on the client is not explicitly prohibited but is a high-severity security risk per standard credential hygiene." | **Yes — "non-negotiable architecture constraint" should be reworded to "strongly implied security best practice" with the same recommended architecture unchanged.** |
| **6d.** SYNC_UPDATES_AVAILABLE webhook drives incremental updates. | **Confirmed** | Named explicitly in live Plaid transactions doc. | No. |
| **6e.** No Angular-specific or Capacitor-specific Plaid SDK; no privacy manifest requirements documented for Plaid iOS SDK. | **Confirmed (no evidence either way for privacy manifest)** | Plaid docs name iOS, Android, React Native — no Capacitor/Angular. Privacy manifest requirements for the Plaid iOS SDK remain unknown from live sources. Report correctly flags as a pre-submission follow-up. | No — already a named unknown. |
| **6f.** Specific webhook verification IPs listed in RESULT-D: 52.21.26.131, 52.21.47.157, 52.41.247.19, 52.88.82.239. | **Still unknown / unverified** | Live Plaid docs fetched did not return these IP addresses. The report correctly notes JOSE/JWT webhook signature verification is the correct approach (not IP allowlisting alone), but the specific IPs listed in RESULT-D could not be confirmed from the accessed page and may be stale training data. Treat as unverified. | **Minor** — the correct architecture (JOSE/JWT signature verification, not IP allowlisting) is already stated. The IPs are an unconfirmed detail. |

**Sources:** Plaid transactions docs https://plaid.com/docs/transactions/, Plaid Link docs https://plaid.com/docs/link/, Plaid quickstart https://plaid.com/docs/quickstart/, accessed 2026-08-15.

---

#### Claim 7 — Google Play: financial-features declaration, Data Safety, privacy policy, account deletion, personal tracker vs regulated service

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **7a.** Google Play Financial Features Declaration Form required. | **Confirmed** | Live source: "Complete the Financial Features Declaration Form in Play Console" is required for all apps with financial features. | No. |
| **7b.** Personal finance tracker vs regulated banking/lending: same requirements? | **Corrected (important distinction)** | Live source: the Financial Services policy imposes loan-specific disclosure requirements (APR, repayment terms, licensing) only on apps **offering or promoting actual financial products** (loans, investments, money management services). A personal finance **tracker** that reads a user's own transaction data and does not offer loans, credit, or investment products "likely falls outside these requirements, though any financial features still require declaration." The report presents Google Play financial policy as an undifferentiated gap — the distinction is now partially resolved. | **Yes — PRD and arch docs should note that a personal tracker's primary obligation is the Financial Features Declaration Form + Data Safety form, not the loan-app disclosure and licensing requirements.** |
| **7c.** Data Safety form mandatory; financial data must be declared. | **Confirmed** | Live source: all developers must complete it. Declared types include payment info, purchase history, credit score, and other financial info. | No. |
| **7d.** Account deletion requirement. | **Confirmed with precision** | Live source: developer must indicate whether they provide a deletion mechanism OR "automatically initiate deletion or anonymization of collected data within 90 days of collection." The report (RESULT-D) says "immediately" — the live source permits a 90-day automatic deletion as an alternative to on-demand deletion. Immediate on-demand deletion is best practice but the 90-day automatic window is also compliant. | **Minor** — PRD "account deletion within 2 taps" is still best practice; the 90-day automatic option is a backup compliance path. |
| **7e.** Google Play thin-wrapper / minimum functionality rule. | **Still unknown** | Neither the financial services policy page nor the developer content policy index returned the minimum functionality rule text for Google Play. No thin-wrapper prohibition analogous to Apple's 4.2 was found. Remains a named gap. | No change — already flagged as an open item. |

**Sources:** Google Play Financial Services policy https://support.google.com/googleplay/android-developer/answer/9876821, Google Play Data Safety https://support.google.com/googleplay/android-developer/answer/10787469, both accessed 2026-08-15.

---

#### Claim 8 — API coexistence layer; FDW cross-cloud joining

| Sub-claim | Verdict | Corrected Wording | PRD/Arch Impact? |
|---|---|---|---|
| **8a.** API proxy coexistence (Option A) is the lowest-risk path. | **Confirmed** | The reasoning is sound: no data migration, existing service unchanged, new Supabase project calls the existing service's API. No source or controlled experiment is needed to accept this as the lowest-risk option — it is a non-destructive, reversible pattern. | No. |
| **8b.** FDW / shared Postgres read-replica (Option B) is described as "moderate complexity" with implied feasibility. | **Corrected — unproven per CONTROL.md standard** | CONTROL.md explicitly states: "Treat FDW/cross-cloud database joining as unproven unless a source or controlled experiment supports it." No live source, Supabase documentation, or controlled experiment was cited for FDW viability. The report presents Option B as a plausible architectural path without evidence. Per the control file's own standard, it must be labeled **unproven inference**. | **Yes — Option B must be relabeled "unproven inference; do not select without a controlled feasibility experiment." Option A remains the recommended path.** |
| **8c.** "Not recommended: migrating the existing service's data into Supabase before the new mobile architecture is validated." | **Confirmed** | Consistent with the CONTROL.md preservation requirement. | No. |

---

### Decision Impact Summary

1. **PRD citation correction (4.2 vs 4.2.7):** The PRD's native-capability requirement is correctly motivated, but must cite guideline **4.2** (minimum functionality / repackaged website) as the controlling rule for an Angular+Capacitor app, not 4.2.7 (which is scoped to remote desktop clients). The mitigation strategy — camera, push, biometrics from day one — is unchanged.

2. **RLS security framing must be corrected:** Risk R2 and the must-have controls table overstate the threat. `auth.uid() = user_id` already blocks unauthenticated access (it silently denies, not silently permits). IS NOT NULL should be retained as a **defense-in-depth clarity practice**, but the PRD must not cite it as patching an exploitable unauthenticated-read vulnerability.

3. **Plaid access_token boundary is best practice, not a documented mandate:** The architecture decision (access_token server-side only) is correct and must be retained, but the PRD should describe it as a strongly implied security best practice rather than a "non-negotiable" contractual Plaid requirement with documented prohibition.

4. **FDW coexistence option must be demoted:** Option B (FDW / shared Postgres replica) has no evidence support and violates the CONTROL.md's own standard. The PRD and architecture notes must mark it as an unproven inference requiring a controlled experiment, and make Option A (API proxy) the sole recommended coexistence path.

5. **Google Play financial policy scope:** A personal finance tracker faces narrower Play Store financial-services obligations than the report's open-ended gap implies — primarily the Financial Features Declaration Form and Data Safety form. Loan-product disclosure and jurisdiction-specific licensing requirements apply only if the app offers financial products. This narrows the compliance surface and reduces the review burden before Play Store submission.

---

### Source List

| # | Title | Publisher | URL | Access Date |
|---|---|---|---|---|
| P1 | App Store Review Guidelines | Apple | https://developer.apple.com/app-store/review/guidelines/ | 2026-08-15 |
| P2 | Row Level Security — Supabase Docs | Supabase | https://supabase.com/docs/guides/database/postgres/row-level-security | 2026-08-15 |
| P3 | Supabase Pricing | Supabase | https://supabase.com/pricing | 2026-08-15 |
| P4 | Plaid Transactions Documentation | Plaid | https://plaid.com/docs/transactions/ | 2026-08-15 |
| P5 | Plaid Link Documentation | Plaid | https://plaid.com/docs/link/ | 2026-08-15 |
| P6 | Plaid Quickstart | Plaid | https://plaid.com/docs/quickstart/ | 2026-08-15 |
| P7 | Capacitor Getting Started | Ionic/Capacitor | https://capacitorjs.com/docs/getting-started | 2026-08-15 |
| P8 | Capacitor iOS App Store Deployment | Ionic/Capacitor | https://capacitorjs.com/docs/ios/deploying-to-app-store | 2026-08-15 |
| P9 | Google Play Financial Services Policy | Google | https://support.google.com/googleplay/android-developer/answer/9876821 | 2026-08-15 |
| P10 | Google Play Data Safety Section | Google | https://support.google.com/googleplay/android-developer/answer/10787469 | 2026-08-15 |

*10 sources. Within 12-source cap. No files modified.*
