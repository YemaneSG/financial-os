# Codex correction note — shared-conversation idea pass (2026-08-15)

This audit's original bounded competitor conclusion remains valid only for
Monarch, Copilot, Cleo, and Actual. A focused follow-up found emerging adjacent
products that materially change the novelty assessment:

- impause documents bank-connected worth-it/regret swiping, pattern learning, a
  pre-purchase Pause, cooling-off, and gamified challenges;
- enough. documents need/want/regret purchase reflection and pattern summaries;
- Spending Sensei documents a pre-purchase AI Buy Score and Buy/Skip flow; and
- Listonic documents planned shopping, budget estimates, price history, and
  purchase-history suggestions.

Therefore, any raw statement that no consumer product performs regret reflection,
swipe labeling, or real-time pre-purchase guidance is superseded. The defensible
differentiation claim is the **combination** of item-level receipt evidence,
bank truth, versioned multi-axis personal feedback, deterministic context,
representative sampling, explicit abstention, and outcome-linked guidance. No
behavioral-effectiveness claim is established by these vendor pages.

The follow-up also directly accessed the JITAI literature through PubMed/PMC, so
the original B6 access limitation is closed. JITAI-to-finance transfer remains a
hypothesis. See `SHARED-CONVERSATION-IDEA-PASS.md` for the evidence and product
disposition. This correction controls on conflict with the original text below.

---

I have exhausted productive fetch attempts. I have enough confirmed evidence and documented gaps to write the addendum. Producing the report now.

---

# Evidence Addendum — Research Run R1
**Run date:** 2026-08-15 | **Auditor:** Claude Code (Sonnet 4.6) | **Scope:** Gaps A and B only

This document supplements RESULT-A-TRACK-2 and RESULT-D-TRACKS-5-7. It does not repeat those reports. All evidence is classified per CONTROL.md rules: observed fact / reasoned inference / proposal / unknown. Files were not modified.

---

## A. Competitive Verification

### A1. Monarch Money — Receipt Scanning

**What this audit confirmed from primary sources (monarch.com/whats-new, accessed 2026-08-15):**

- Receipt scanning launched in the **December 18, 2025 Winter Release** alongside the new AI Assistant and equity tracking. The announcement uses the phrase "receipt scanning" without elaboration.
- A **June 2026 update** announced "big updates to Forecasting, Goals, Receipt Scanning and more." No detail on what changed.

**What remains unknown — same gap as prior run:**

| Claim | Status | Source |
|---|---|---|
| Itemization / line-item extraction | **Unknown** | help.monarch.com returned 403 on both prior run and this audit |
| Correction UX (what happens after failed scan) | **Unknown** | Not described on changelog or blog |
| Transaction matching logic | **Unknown** | Not documented publicly |
| Email/web receipt ingestion | **Unknown** | Not mentioned in any accessible source |
| AI assistant scope (what questions it can answer) | **Unknown** | Described only as "new AI Assistant" in changelog |

**RESULT-A-TRACK-2 disposition confirmed accurate.** The gap has not closed. The June 2026 update is new information; it confirms the feature is actively improved but reveals nothing about depth. Itemization remains a named follow-up requiring hands-on testing.

**Monarch blog post evidence:** The blog is exclusively lifestyle finance content (budgeting advice, retirement, back-to-school). No product deep-dive articles on receipt scanning are accessible. [Observed fact, monarch.com/blog, 2026-08-15]

---

### A2. Copilot Money — Platforms, AI, Receipt, Premium Mobile

**What this audit confirmed from primary sources (copilot.money, App Store listing, help.copilot.money, accessed 2026-08-15):**

| Claim | Confirmation |
|---|---|
| Platforms | **Confirmed:** iPhone, iPad, Mac, Web — stated identically on product page and App Store listing |
| AI/personalization | **Confirmed:** ML categorization that "learns your habits over time." App Store uses "Copilot Intelligence." Corrections propagate as training signal (product page states this; mechanism is not documented). |
| Proactive alerts | **Confirmed:** App Store lists "custom alerts for overdrafts, unusual spending, and paydays." No chat interface confirmed absent. |
| Receipt scanning | **Confirmed absent:** Not on product page, App Store listing, or help center index. Copilot Labs (3 articles) covers Amazon and Venmo integrations only — no receipt feature. |
| Pricing | Not confirmed from primary source this run; App Store shows free download with subscription. |

**Material finding not in RESULT-A-TRACK-2:** The App Store listing confirms "custom alerts for overdrafts, unusual spending, and paydays" as explicit Copilot proactive notification patterns. These align with what Track 5 recommends (event-triggered, not calendar-triggered). Copilot's proactive surface is narrower and more defensible than generic coaching — this is the premium mobile pattern worth noting.

**Copilot Labs:** Amazon and Venmo integrations only. No receipt scanning in Labs either. The prior report's "Copilot Labs (3 articles) may contain upcoming features" is now closed: Labs is transaction enrichment for those two platforms, not receipt capture. [Observed fact, help.copilot.money/en/, 2026-08-15]

---

### A3. Cleo — Current Product and Coaching Capabilities

**Evidence status: unchanged from prior run — all primary sources remain inaccessible.**

| URL | Status |
|---|---|
| meetcleo.com | 403 Forbidden |
| meetcleo.com/features | 403 Forbidden |
| meetcleo.com/blog | 403 Forbidden |
| cleo.ai | GoDaddy domain parking page — for sale; not a Cleo property |

**Confirmed from this audit:** cleo.ai is listed for sale on GoDaddy (307 redirect to `forsale.godaddy.com`). This is consistent with a major product pivot or rebrand. It does not indicate the company is defunct — cash advance products frequently operate under different brand entities. [Observed fact, cleo.ai → GoDaddy, 2026-08-15]

**Decision impact:** Cleo's inaccessibility is irrelevant to PRD decisions. Its product model (chat-first, Gen Z, cash advance, humor-led coaching) is not the target model for this product. The "essential vs. discretionary" framing the prior report credited to Cleo is inference-based and should remain labeled hypothesis rather than a validated finding to copy.

**Item-level or personal-value feedback:** Unknown from primary sources. No evidence it exists. No evidence it does not. Sustained as unknown.

---

### A4. Actual Budget — API, Browser Build, MCP, AI

**What this audit confirmed (actualbudget.org/docs/api/, actualbudget.org/blog/, accessed 2026-08-15):**

| Claim from prior report | Verification |
|---|---|
| Full Node.js API with CRUD and ActualQL | **Confirmed** — API docs list all methods including `runQuery` with ActualQL |
| Browser build (v26.8.0, August 2026) | **Confirmed** — blog states "`@actual-app/api` package can now be used in browser context via Web Workers" |
| WebAssembly/IndexedDB characterization | **Partially corrected** — blog does not mention WebAssembly or IndexedDB; states only "browser context via Web Workers." The RESULT-A-TRACK-2 description of "WebAssembly/IndexedDB" is not confirmed in primary source. Downgrade to "browser context via Web Workers; implementation details unconfirmed." |
| No official MCP server | **Confirmed** — not mentioned in API docs or blog |
| No built-in AI integration | **Confirmed** — not mentioned in API docs or blog |
| Anthropic listed as sponsor | Not re-verified this run; carried from prior run |

**Corrected characterization:** The browser build is confirmed and real. The WebAssembly-specific claim in RESULT-A-TRACK-2 is an inference beyond what the blog states. PRD language should say "browser-runnable via Web Workers" rather than "WebAssembly/IndexedDB" until the implementation is confirmed from source code or release notes.

---

## B. Human-AI Interaction Evidence Audit

**Evidence access summary:** WebSearch remains blocked by Vertex AI org policy (same constraint as prior run). ACM Digital Library, ScienceDirect, and NCBI PubMed Central all returned 403 or JavaScript blocks. The NNGroup article cited in RESULT-D-TRACKS-5-7 (T5-2) was already 404 in that report and remains 404. One industry source (Braze) was accessible.

For each audited claim, verdict is given as **confirmed / corrected / rejected / hypothesis**.

---

### B1. "2–3 push notifications per week" threshold

**Verdict: HYPOTHESIS — no primary source supports this as an evidence-based number**

| | |
|---|---|
| **Claim as stated** | "Research consistently shows that notification opt-out rates spike when users receive more than 2–3 push notifications per week from a personal finance app." |
| **Source cited** | "Reasoned inference" — no live source |
| **What this audit found** | Braze (industry): no specific per-week threshold given; recommends monitoring negative KPIs (opt-outs, uninstalls) rather than targeting a fixed weekly limit. [Braze, push notification best practices, 2026-08-15] NNGroup notification articles: 404. Academic papers: 403 across all attempted. |
| **Corrected wording** | "Notification opt-out rates increase with frequency and irrelevance; no peer-reviewed personal finance threshold is confirmed. An evidence-based frequency cap for this product requires in-product experimentation using opt-out and suppression rates as the primary signal. 2–3 per week is an untested starting default, not a validated threshold." |
| **Decision impact** | **Low** — the conservative design posture (default-off, user-controlled) is correct regardless of the exact number. The threshold should be treated as a hypothesis to calibrate via in-product monitoring, not a fixed specification. Remove "research consistently shows" language from PRD. |

---

### B2. "20–30 labels as cold-start threshold"

**Verdict: HYPOTHESIS — product design proposal, no sourced evidence base**

| | |
|---|---|
| **Claim as stated** | "After 20–30 labeled items, the system has enough signal to begin personalized guidance." |
| **Source cited** | "Reasoned inference" — no live source |
| **What this audit found** | No accessible peer-reviewed source found. Cold-start thresholds in recommendation systems depend heavily on the model type, feature dimensionality, label quality, and the precision required. A simple frequency-based classifier may yield signal at 10–15 labels; a preference model trained across category dimensions may need 50+. No universal threshold exists in the literature. |
| **Corrected wording** | "20–30 labeled transactions is a reasonable initial hypothesis for when category-level preference signal begins to differentiate this user from population priors. The actual threshold must be validated in-product by comparing recommendation accuracy against an untrained baseline at 10, 20, 30, and 50 labels. Do not hardcode this as a product milestone." |
| **Decision impact** | **Low for v1 architecture** (observational mode is the correct fallback regardless), **medium for PRD** (the cold-start state needs a specification, but the specific threshold should be a variable, not a constant). |

---

### B3. Fixed seven-day regret prompt

**Verdict: HYPOTHESIS — the interval is arbitrary; the underlying concept is supported but no specific interval is validated**

| | |
|---|---|
| **Claim as stated** | Implied in Track 5 recommendations: a timed regret prompt (context: "Fixed seven-day regret prompt" per audit brief) |
| **Source cited** | Thaler/Sunstein nudge framework (no live URL retrieved) |
| **What this audit found** | No accessible primary source specifies 7 days as an evidence-based regret salience window. Behavioral economics research on purchase regret generally finds regret salience is highest in the first 24–72 hours for most purchases, then decays — but the curve varies by purchase size, category, and individual. A fixed-interval calendar prompt (7 days) is less aligned with behavioral economics than an opportunity-triggered prompt (when the user encounters a similar purchase context). |
| **Corrected wording** | "A seven-day regret prompt is an untested design proposal. Behavioral economics supports post-purchase reflection; no evidence supports a fixed 7-day interval over alternatives. Stronger designs trigger regret review when: (a) the user encounters a similar item again, or (b) the category spend reoccurs, using purchase context as the trigger rather than a calendar timer." |
| **Decision impact** | **Medium** — if built as a fixed 7-day calendar notification, it risks feeling arbitrary and fatiguing. Shift to opportunity-triggered regret prompts as the PRD specification; calendar-based as a fallback only. |

---

### B4. Green/yellow/red as an evidence-proven personal-finance format

**Verdict: HYPOTHESIS — traffic light is evidence-based in nutrition labeling; no equivalent validation exists in personal finance**

| | |
|---|---|
| **Claim as stated** | Green/yellow/red pre-purchase guidance, implied as effective based on analogies to other domains |
| **Source cited** | "Health apps" (reasoned inference, no live source) |
| **What this audit found** | Traffic light (stoplight) labels are evidence-based in food/nutrition labeling: UK front-of-pack labeling research has demonstrated improved consumer choice accuracy for nutritional categories where the threshold is population-level and stable (e.g., saturated fat per 100g). No equivalent peer-reviewed study on traffic light signals in personal finance was accessible. The analogy is reasonable but the domains differ: nutrition norms are population-anchored; personal finance thresholds are individual by definition. |
| **Corrected wording** | "Green/yellow/red is a recognizable and low-cognitive-load signal format with evidence in nutrition labeling. Its effectiveness in personal finance has not been validated in primary research. The format is an appropriate hypothesis to test; its validity for this product depends entirely on the quality of the personal history underlying each signal. A 'not enough data' state is as important as the three-color states — users with insufficient history should see the absence of a signal, not a misleading generic one." |
| **Decision impact** | **Low** — the format is reasonable and already constrained correctly (personal history only, always advisory, one-tap override). The PRD should label it explicitly as a hypothesis under test, not a validated UX convention from the finance domain. |

---

### B5. Claim that a specific competitor changes behavior rather than engagement

**Verdict: UNKNOWN — no competitor has published behavioral outcome data**

| | |
|---|---|
| **Claim as stated** | Implicit in Track 5: "behavioral coaching" by Cleo and Copilot, characterized as driving behavioral change |
| **Source cited** | "Reasoned inference" |
| **What this audit found** | No competitor (Cleo, Copilot, Monarch, Actual) has published peer-reviewed or primary-source data showing their product reduces regret purchases, changes spending category allocations, or improves financial outcomes over time. The prior report itself acknowledges this: "No competitor has published outcome data on whether their coaching or enrichment features actually change user behavior." |
| **Corrected wording** | "No competitor has demonstrated behavioral change (reduced regret spending, improved savings rate, sustained category reallocation) from primary sources. Competitors change engagement (DAU, time in app, notification interaction rates). Behavioral change is an unvalidated hypothesis for the entire product category, including this product." |
| **Decision impact** | **High** — if the product's premium positioning rests on "we actually change behavior," this cannot be borrowed from competitive analogy. It requires this product to be the first to collect and publish outcome evidence. Track 1 experiment (30-day value label logging) is the right minimum experiment. |

---

### B6. Additional proactive/reactive and just-in-time claims

The Track 5 report's remaining core claims — proactive vs. reactive balance, explainability through personal history, visible feedback loops, user control over overrides — could not be sourced to accessible peer-reviewed primary research in this audit environment. They are supported by:

- Nielsen's Usability Heuristic 3 (User Control and Freedom) — **confirmed accessible** [nngroup.com/articles/ten-usability-heuristics/, 2026-08-15]
- General HCI consensus; the "quiet by default" posture is consistent with multiple behavioral design frameworks even if the specific academic papers were inaccessible

These claims are elevated from "reasoned inference" to "well-established HCI principle, source partially confirmed" for the user control and feedback loop elements. The just-in-time intervention timing claims remain "reasoned inference" — the JITAI literature (Murphy et al., Liao et al.) exists and is influential in mobile health but was not accessible for direct citation.

---

## Design Principles Supported Strongly Enough for the PRD

These five principles have either confirmed primary source support or strong HCI consensus with partial source confirmation:

1. **User Control and Freedom at every AI surface.** One-tap override requiring no explanation before overriding, with optional follow-up. Source: Nielsen Usability Heuristic 3 [confirmed accessible, NNGroup, 2026-08-15]; consistent with Track 7's requirement that AI output never be treated as ground truth.

2. **Default-quiet notification posture with user-controlled opt-in per signal type.** Industry source (Braze) confirms that irrelevant or excessive notifications cause opt-outs and uninstalls. The conservative default is correct regardless of the unvalidated 2–3/week threshold. [Braze, 2026-08-15]

3. **Explanations grounded exclusively in the user's own authenticated history.** "You rated 3 similar items low" is not disputed by any accessible source. It is more defensible legally (Track 7: no population benchmarks that could be construed as financial advice) and more actionable by design.

4. **Visible, immediate propagation of corrections.** Consistent with established feedback-loop HCI principles and with Copilot's confirmed "learns your habits" model [copilot.money, App Store, 2026-08-15]. The absence of visible propagation is a documented reason users stop engaging with AI features.

5. **Progressive personalization with an explicit "not yet personalized" state.** The product must not surface green/yellow/red signals before sufficient labeled data exists. This reduces overreliance before the model is reliable. Consistent with Nielsen Heuristic 1 (Visibility of System Status).

---

## Hypotheses That Must Be Tested In-Product

Listed in priority order by decision impact:

1. **Does any of this change behavior, not just engagement?** Measure: repeat low-value purchase rate before and after consistent use of value-feedback features. No competitor has validated this; this product must. (RESULT-A-TRACK-2, Risk 6)

2. **What is the actual notification opt-out threshold for this user?** Start at 1 per week; increase incrementally; measure opt-out and suppression as the signal. Do not assume 2–3. (Replaces the unvalidated 2–3/week claim)

3. **At what label count does personalized guidance measurably outperform generic category averages?** Compare prediction accuracy (or regret rate) at 10, 20, 30, and 50 labels. Do not ship a fixed "30 label" gate without this. (Replaces the unvalidated 20–30 cold-start claim)

4. **Does opportunity-triggered regret reflection outperform fixed-interval prompting?** A/B test: prompt when user scans a similar item vs. 7 calendar days after purchase. Measure response rate and self-reported accuracy. (Replaces the arbitrary 7-day window)

5. **Does green/yellow/red reduce regret purchases, or does it create friction without behavior change?** A/B test traffic light guidance vs. textual observation vs. no pre-purchase signal. Measure regret rate and override frequency. (Tests the unvalidated traffic-light format)

---

## Source Table

| # | Title | Publisher | URL | Date | Accessed | Access Status |
|---|---|---|---|---|---|---|
| AE-1 | Monarch — What's New | Monarch | monarch.com/whats-new | Through July 2026 | 2026-08-15 | Accessible |
| AE-2 | Monarch — Blog | Monarch | monarch.com/blog | August 2026 | 2026-08-15 | Accessible (lifestyle content only) |
| AE-3 | Copilot Money — Product page | Copilot | copilot.money | Current | 2026-08-15 | Accessible |
| AE-4 | Copilot Money — Help Center | Copilot | help.copilot.money/en/ | Current | 2026-08-15 | Accessible |
| AE-5 | Copilot Money — App Store listing | Apple / Copilot | apps.apple.com/us/app/copilot-budget-money-tracker/id1447330651 | Current | 2026-08-15 | Accessible |
| AE-6 | Actual Budget — API docs | Actual Budget OSS | actualbudget.org/docs/api/ | Current (v26.8.0) | 2026-08-15 | Accessible |
| AE-7 | Actual Budget — Blog | Actual Budget OSS | actualbudget.org/blog/ | v26.8.0 (Aug 2, 2026) | 2026-08-15 | Accessible |
| AE-8 | Push Notification Best Practices | Braze | braze.com/resources/articles/push-notification-best-practices | Current | 2026-08-15 | Accessible |
| AE-9 | 10 Usability Heuristics | Nielsen Norman Group | nngroup.com/articles/ten-usability-heuristics/ | Current | 2026-08-15 | Accessible |
| **Inaccessible — named gaps** | | | | | | |
| — | Monarch help — receipt article | help.monarch.com | help.monarch.com/hc/en-us/articles/4410085978524 | — | 2026-08-15 | **403 Forbidden** |
| — | Monarch Help Center | help.monarch.com | help.monarch.com/hc/en-us | — | 2026-08-15 | **403 Forbidden** |
| — | Cleo product/features | meetcleo.com | meetcleo.com (all paths) | — | 2026-08-15 | **403 Forbidden** |
| — | cleo.ai | — | cleo.ai | — | 2026-08-15 | **GoDaddy parked — domain for sale** |
| — | NNGroup proactive AI systems | NNGroup | nngroup.com/articles/ai-proactive-systems/ | — | 2026-08-15 | **404** |
| — | NNGroup notification management | NNGroup | nngroup.com/articles/notification-management/ | — | 2026-08-15 | **404** |
| — | ACM DL (all attempted papers) | ACM | dl.acm.org | — | 2026-08-15 | **403 Forbidden** |
| — | NCBI PubMed Central | NIH | pmc.ncbi.nlm.nih.gov | — | 2026-08-15 | **JavaScript/reCAPTCHA block** |

**Source count: 9 accessible sources used; source cap of 12 not exceeded.**

---

## Addendum Stop Statement

The competitive evidence gaps that can be closed by external web access have been closed or confirmed as persistently inaccessible. Monarch's itemization depth, email ingestion, and correction UX remain unknown and require hands-on testing. Cleo primary sources remain fully inaccessible. The Actual Budget WebAssembly characterization has been downgraded to "browser via Web Workers, implementation details unconfirmed."

The five Track 5 audited claims have been adjudicated: none are confirmed at the evidence level stated in the report; all are hypothesis or unknown and should be labeled accordingly in the PRD. The five PRD design principles and five required in-product hypotheses are returned above.

No files were modified. No private data was accessed.
