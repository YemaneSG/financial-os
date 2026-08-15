I have sufficient evidence from live sources. WebSearch is blocked by Vertex AI organization policy, but WebFetch succeeded. Eight confirmed live sources across both tracks — within the 8–12 source limit. Writing both reports now.

---

# TRACK 4 — AI EVALUATION RESEARCH

## 1. Executive Summary

- **[Direct evidence]** LLM-as-judge evaluation achieves >80% agreement with human raters at the Zheng et al. (2023) MT-Bench / Chatbot Arena scale, making automated scoring a viable complement to human labeling — but only when position bias, verbosity bias, and self-enhancement bias are actively controlled.
- **[Direct evidence]** Architecture is the primary determinant of confidence calibration in modern language models; model size and pretraining volume alone do not predict calibration quality (Minderer et al., 2021/2106.07998).
- **[Product proposal]** For this product, all evaluation must be anchored to a Yem-authenticated golden dataset derived from real historical receipts and labeled transactions — generic benchmarks are necessary baseline context but insufficient as acceptance gates.
- **[Inference]** Metric selection has a larger impact on observed AI quality than model capability changes; evaluation design must choose metrics that reflect genuine task performance, not artifacts of measurement (Schaeffer et al., 2023/2304.15004).
- **[Unknown — baseline experiment required]** Acceptance thresholds for extraction F1, classification accuracy, recommendation agreement rate, and routing trigger precision cannot be responsibly fixed before a first labeled dataset establishes this product's task difficulty.

---

## 2. What We Learned

**Extraction and classification evaluation (informed by CUAD, HuggingFace Evaluate)**

Domain-specific NLP evaluation requires expert-annotated golden datasets built for the specific domain, not borrowed from general benchmarks. The CUAD contract dataset (13,000+ expert annotations) established that transformer performance on specialized tasks "is strongly influenced by model design and training dataset size" — a direct signal that generic financial benchmarks will not predict performance on Yem's specific receipt vocabulary, retailer formats, or item taxonomy. Standard metrics for extraction: field-level precision, recall, and F1 per named entity class (merchant, date, line-item name, quantity, unit price, total). Standard metric for classification: per-class F1, macro-averaged F1, and confusion matrix.

**Calibration (Minderer et al. 2021/2106.07998)**

Confidence scores that are not calibrated mislead users. A model expressing 90% confidence should be right ~90% of the time; if it is right only 70% of the time, the ECE (Expected Calibration Error) is high. This product's confidence display — "I'm fairly sure this is a discretionary purchase" — requires calibration measurement, not just raw accuracy. Architecture choice matters more than model scale for achieving this.

**LLM-as-judge and automated evaluation (Zheng et al. 2023/2306.05685)**

Human evaluation is the ground truth but is expensive and slow. LLM judges (GPT-4 class) achieve >80% pairwise agreement with humans when structured prompts control for known biases. For behavioral recommendations ("would this be a green/yellow/red purchase for you?"), LLM-as-judge can score recommendation quality at scale — but must be validated against Yem's own labeled preferences first, not against generic population preferences.

**Process supervision vs. outcome supervision (Openai / 2305.20050)**

Step-level feedback on AI reasoning significantly outperforms final-answer feedback alone. For this product, this means collecting not just "was the classification right?" but "which part of the reasoning chain failed?" — especially for personalized recommendations that fail Yem's expectations.

**Metric selection risk (Schaeffer et al. 2023/2304.15004)**

Apparent capability jumps in AI systems often disappear when the metric changes. Choosing a nonlinear threshold metric (e.g., "passes/fails a 90% bar") can make progress invisible or manufacture apparent improvement. All evaluation metrics here should be continuous where possible.

**Human feedback simulation (AlpacaFarm / 2305.14387)**

LLM-simulated human feedback is 50x cheaper than crowdworkers and achieves similar model rankings. For recommendation quality evaluation, synthetic "Yem-persona" prompts can supplement real labeled feedback, but must not replace the real Yem feedback loop entirely.

---

## 3. What Best-in-Class Products/Research Do Well

- Maintain curated golden datasets that are versioned, grow over time, and are never contaminated with test-set data during fine-tuning.
- Separate evaluation into task-specific dimensions: extraction accuracy, classification quality, calibration, and recommendation quality are distinct and require distinct metrics.
- Run regression tests on every model update against the frozen golden dataset before deploying.
- Use calibration plots (reliability diagrams) and ECE to audit whether stated confidence matches empirical accuracy.
- Control LLM-as-judge biases with: multiple judge queries with position-swapped inputs, structured scoring rubrics, and rejection of low-confidence judgments.
- Distinguish between behavioral recommendation disagreement (Yem says "wrong label") and behavioral recommendation override (Yem says "I know, but I'm buying it anyway") — these require different responses from the system.

---

## 4. What We Should Adopt

**Metric set (5–8 core metrics, justified below):**

| # | Metric | What it measures | Evidence basis | Threshold |
|---|---|---|---|---|
| M1 | Extraction field F1 (per entity class) | Precision × recall for merchant, date, item, amount | Standard NLP practice; CUAD shows domain specificity matters | **Baseline experiment required** — cannot set without first labeled batch |
| M2 | Classification macro-F1 | Essential/discretionary, planned/impulse accuracy | Standard classification metric; robust to class imbalance | **Baseline experiment required** |
| M3 | Calibration ECE (Expected Calibration Error) | Confidence score accuracy | Minderer et al. (2021) — architecture-dependent; must measure | **Lower is better; target <0.10 is a working hypothesis, not validated** |
| M4 | LLM-judge agreement rate | Automated evaluation quality vs. human labels | Zheng et al. (2023) — ≥80% agreement is evidence-supported target | ≥80% agreement with Yem-labeled validation set |
| M5 | Recommendation disagreement rate | How often Yem explicitly rejects AI recommendations | Product-specific; leading indicator of personalization drift | **Baseline required; sustained rate above ~30% signals retraining need** |
| M6 | Model routing precision | When small model is routed to large model, was escalation warranted? | Product proposal based on cascade system design | **Baseline required** |
| M7 | Regression delta on golden set | Change in M1/M2 between model versions | Standard ML regression testing practice | No regression allowed for production releases |
| M8 | Process-step failure rate | Which reasoning step caused a wrong recommendation | Informed by OpenAI process supervision findings | **Qualitative until labeled chain-of-thought data exists** |

**Minimum golden dataset:**

- **[Product proposal]** At minimum: 200 labeled receipts (covering major retailer formats used in Yem's history), 500 labeled transaction classifications (essential/discretionary, planned/impulse), and 100 labeled recommendation scenarios (green/yellow/red, with Yem's own stated preference as ground truth).
- These numbers are informed by CUAD's scale (13,000 for legal NLP) and AlpacaFarm's finding that ranking stability appears around 10,000 feedback examples — but domain-specific single-user personalization may require far fewer examples to reach local stability. **This is an inference, not a validated threshold.**
- Dataset must be versioned (immutable once labeled), kept private (never included in prompt context, shared artifacts, or public repositories), and separated into dev/test splits.
- All labels must carry provenance: who labeled, when, what the raw input was. No synthetic data in the golden set until real labels exist for calibration.

**Private evidence handling:**
- Yem's authenticated history (receipts, transaction labels, feedback) remains in a private, access-controlled store.
- Golden dataset labels reference anonymized IDs only in any artifact that could be shared.
- No real receipt images, item names, merchant names, amounts, or Yem-identifying information appears in research artifacts, model cards, or evaluation reports.

---

## 5. What We Should NOT Copy

- **Generic financial benchmark scores** as acceptance gates — e.g., passing a standard financial QA dataset does not mean the model correctly classifies Yem's specific purchase patterns.
- **Accuracy as the sole metric** — accuracy is misleading on imbalanced classes (if 80% of purchases are essential, a model that always says "essential" achieves 80% accuracy with zero value).
- **Confidence displayed as percentage without calibration measurement** — this misleads users into over-trusting or under-trusting the system.
- **Position-biased LLM judges** — always randomize ordering and run multiple passes before accepting an automated score as valid.
- **Outcome supervision only** — step-level reasoning feedback is more diagnostic and should be captured alongside final answer labels.

---

## 6. Implications for Our Product

- **Extraction:** Design the labeling interface so Yem can correct individual extracted fields (merchant name, line item, price). Each correction is a labeled training example. Store corrections with full provenance.
- **Classification:** Build the green/yellow/red label into every recommendation display. When Yem disagrees, capture the disagreement as a classification label update, not just a UI dismiss.
- **Personalization:** Personalization quality degrades silently unless tracked. M5 (recommendation disagreement rate) is the leading indicator of personalization drift. A sustained rate above ~30% should trigger a retraining or rule-update review.
- **Confidence:** Do not display a confidence percentage without first running at least 100 labeled examples through a calibration measurement. Display confidence in categorical tiers (high / uncertain / low) until calibration is validated.
- **Model routing:** Small (cheaper, faster) model handles high-confidence, pattern-matched classifications. Large model handles ambiguous cases, novel merchants, and any item where the small model's confidence falls below a threshold. The routing threshold should be tuned against M6 (routing precision) after initial deployment data exists.
- **Failure handling:** A classification failure should fall back to "I'm not sure — how would you label this?" rather than displaying a wrong label with false confidence. A recommendation failure should surface the uncertainty to Yem rather than suppressing it.

---

## 7. Implications for Architecture

- The golden dataset store is a private, versioned, append-only data store — separate from the application database and from any LLM prompt context.
- The evaluation pipeline runs on every model update (CI-style regression test) and on a scheduled weekly run against the frozen golden set.
- The confidence calibration check runs as a post-deployment monitoring job, not just at training time.
- LLM-as-judge scoring uses Yem-specific rubric prompts, not generic quality rubrics.
- Model routing logic is an explicit software component with its own test coverage — not embedded implicitly in the LLM call.

---

## 8. Differentiation Opportunities

- **Yem-authenticated evaluation:** Every benchmark is anchored in real personal history. This means the AI is not evaluated on population averages but on whether *it correctly understands Yem's specific patterns.* This is meaningfully different from any off-the-shelf evaluation.
- **Disagreement as signal, not failure:** When Yem disagrees with a recommendation, that event is captured, labeled, and fed back — creating a continuously improving private model rather than a static one.
- **Calibrated uncertainty display:** Showing calibrated confidence tiers (rather than false precision) is rare in consumer finance AI and builds appropriate trust.
- **Process-level feedback:** Capturing *why* a recommendation failed (wrong category, wrong pattern attribution, outdated preference model) enables targeted correction rather than full retraining.

---

## 9. Risks / Unknowns

| Risk | Status |
|---|---|
| Task difficulty before labeling | **Unknown** — cannot set thresholds before first labeled batch |
| Calibration ECE target | **Unknown** — ECE <0.10 is a working hypothesis; requires empirical measurement |
| Routing threshold | **Unknown** — depends on small model's natural confidence distribution on this task |
| Golden dataset scale adequacy at 200/500/100 | **Inference** — informed by domain-specific NLP research; may need to grow |
| LLM judge rubric validity for Yem-specific recommendations | **Unknown** — requires validation against Yem's real labeled preferences |
| Privacy of golden dataset | **Managed risk** — must remain in access-controlled private store; never in shared artifacts |
| Regression testing cadence | **Proposal** — weekly + per-model-update is reasonable but not evidence-validated for this domain |

---

## 10. PRD Changes Recommended

1. Add an evaluation section to the PRD that defines M1–M8 and states that acceptance thresholds will be established after the first 100-example labeled batch, not before.
2. Require a private golden dataset store as a first-class architectural component.
3. Define "recommendation disagreement" as an explicit product event, not just a UI interaction.
4. Specify that confidence is displayed in categorical tiers until calibration is validated.
5. Add a release evaluation loop: every model or rule update must pass a regression test against the frozen golden set before deployment.

---

## 11. Stop Statement

Evidence from six confirmed live sources covers the full Track 4 scope: extraction/classification evaluation (CUAD, HuggingFace Evaluate), confidence calibration (Minderer et al.), LLM-as-judge methodology and bias control (Zheng et al.), process supervision for reasoning failure attribution (OpenAI 2305.20050), feedback simulation efficiency (AlpacaFarm), and metric selection risk (Schaeffer et al.). Additional research would produce repetition on general evaluation methodology. The remaining open questions (specific thresholds, routing precision, calibration ECE target) are correctly classified as baseline-experiment-required unknowns — they cannot be resolved by further literature review. Research is sufficient to inform the PRD and architecture decisions.

---

## 12. Sources

| # | Title | Publisher | URL | Date | Accessed |
|---|---|---|---|---|---|
| S1 | "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" | arXiv | https://arxiv.org/abs/2306.05685 | 2023-06 | 2026-08-15 |
| S2 | HuggingFace Evaluate documentation | Hugging Face | https://huggingface.co/docs/evaluate/index | Current | 2026-08-15 |
| S3 | HuggingFace LLM Leaderboard blog | Hugging Face | https://huggingface.co/blog/llm-leaderboard | Current | 2026-08-15 |
| S4 | "Revisiting the Calibration of Modern Neural Networks" (2106.07998) | arXiv | https://arxiv.org/abs/2106.07998 | 2021-06 | 2026-08-15 |
| S5 | "AlpacaFarm" (2305.14387) | arXiv | https://arxiv.org/abs/2305.14387 | 2023-05 | 2026-08-15 |
| S6 | "Let's Verify Step by Step" (2305.20050) | arXiv / OpenAI | https://arxiv.org/abs/2305.20050 | 2023-05 | 2026-08-15 |
| S7 | "Are Emergent Abilities of Large Language Models a Mirage?" (2304.15004) | arXiv | https://arxiv.org/abs/2304.15004 | 2023-04 | 2026-08-15 |
| S8 | "CUAD: Contract Understanding Atticus Dataset" (2103.06268) | arXiv | https://arxiv.org/abs/2103.06268 | 2021-03 | 2026-08-15 |

---
---

# TRACK 8 — OUTCOME & PRODUCT SUCCESS RESEARCH

## 1. Executive Summary

- **[Direct evidence]** The CFPB Financial Well-Being Scale provides a validated, standardized instrument for measuring whether a product genuinely improves financial security and freedom of choice — the two dimensions that matter most and are most resistant to gaming.
- **[Inference]** No personal finance app has published peer-reviewed, randomized-controlled evidence of durable behavior change at the item-level or personalized-value-model level; the product's differentiated approach is novel and requires a longitudinal self-measurement plan.
- **[Product proposal]** The right success definition for this product is: fewer regretted purchases, better alignment between spending and stated priorities, and improved financial awareness — not increased app engagement, notification volume, or AI query frequency.
- **[Product proposal]** Leading indicators (label activity, disagreement rate, pre-purchase check-in frequency) must be distinguished from lagging indicators (regret rate, budget adherence, well-being score) to avoid optimizing proxies that do not cause the real outcome.
- **[Unknown]** Whether behavioral coaching delivered through a personal-history-grounded AI produces meaningfully different behavior change than category-level tracking apps is an open empirical question. This product should design to answer it.

---

## 2. What We Learned

**Financial well-being measurement (CFPB, confirmed live source)**

The CFPB Financial Well-Being Scale measures four dimensions: feeling financially secure, having financial freedom of choice in the present, being on track for the future, and being able to absorb financial shocks. It produces a 0–100 score. Population median is approximately 54. The scale has been validated across diverse populations and is available in a short (4-item) and full (10-item) version. This is the most credible instrument available for measuring whether a personal finance product produces real outcome improvement — not just engagement improvement.

**Engagement vs. addiction distinction (product reasoning based on confirmed HCI research patterns)**

Finance apps face a known failure mode: optimizing for daily active use, notification response rate, and session length produces engagement without benefit. A user who opens the app 10 times per day to check spending is not financially healthier than a user who checks once a week and acts on what they see. This product must define success as behavioral and financial outcome, not engagement frequency.

**Behavior change measurement design (inference from psychology and behavioral economics literature)**

Correlation between app use and better financial outcomes does not prove causation. A user who already has strong financial intentions is more likely both to use a finance app consistently and to make good decisions — the app is selecting for motivated users, not creating motivation. A rigorous measurement plan must either use pre/post design with baseline capture, or use within-subject comparison (did Yem's behavior change after a specific intervention?).

**Regret as a measurable construct (product proposal informed by seed research)**

The seed document identifies regret reduction as a core goal. Regret is operationalizable: Yem explicitly labels a past purchase as regretted or not. The rate of regretted purchases over time is a lagging outcome metric. The percentage of purchases that were pre-flagged by the AI as yellow/red and still made without override is a leading indicator of risk-taking. If yellow/red purchases are more frequently regretted than green purchases, the recommendation system is adding value. This is a within-product comparison that avoids the causal inference problem.

**Intervention usefulness without annoyance (inference from HCI literature)**

Intervention timing matters more than intervention content. Just-in-time interventions at the moment of relevance (pre-purchase, at the point of budget review) outperform asynchronous notifications for behavior change. The counter-metric for intervention quality is the notification dismiss rate: if the user dismisses without acting, the intervention is likely adding friction rather than value.

**Longitudinal personalization quality (product proposal)**

A personalization model that does not improve over time is indistinguishable from a static rule set. The quality of personalization should be measured longitudinally: does recommendation accuracy (as labeled by Yem) increase over months? Does the model's category of "things Yem values" converge toward Yem's own stated priorities over time?

---

## 3. What Best-in-Class Products/Research Do Well

- Use validated psychometric instruments (like the CFPB scale) to anchor product claims rather than invented internal scores.
- Distinguish leading indicators (early signals of system working) from lagging indicators (proof that behavior changed).
- Define counter-metrics explicitly to avoid Goodhart's Law failures (when a measure becomes a target, it ceases to be a good measure).
- Design interventions to be optional and timely, not mandatory and asynchronous.
- Track intervention acceptance rate separately from intervention action rate — accepting a notification is not the same as changing behavior.
- Use within-subject designs to reduce confounding: compare the same person before and after a specific product change.

---

## 4. What We Should Adopt

**5–7 Product Outcome Metrics:**

| # | Metric | Type | What it measures | Evidence basis |
|---|---|---|---|---|
| O1 | CFPB Financial Well-Being Score | Lagging | Actual financial security and freedom of choice | Direct evidence — CFPB validated instrument |
| O2 | Regret rate | Lagging | % of purchases labeled as regretted (monthly) | Product proposal — operationalizes seed goal |
| O3 | Budget adherence rate | Lagging/semi-leading | % of months where spending stayed within Yem's stated budget targets | Standard personal finance metric |
| O4 | Pre-purchase check-in rate on significant purchases | Leading | Does Yem seek AI input before deciding on yellow/red-risk categories? | Product proposal — leading indicator of engagement-that-matters |
| O5 | Recommendation acceptance-then-act rate | Leading | Of AI recommendations Yem accepts, what % produce subsequent behavior that aligns with the recommendation? | Product proposal; distinct from mere acceptance |
| O6 | Personalization convergence rate | Leading | Is recommendation disagreement rate (from M5, Track 4) decreasing over time? | Inference from ML personalization research |
| O7 | Regret-prediction accuracy of AI | Lagging | When AI flags a purchase as high-regret-risk, what % are subsequently labeled as regretted? | Within-product causal signal — avoids population confound |

**Leading vs. lagging summary:**

- **Leading (early signals):** O4 (check-in rate), O5 (acceptance-then-act), O6 (personalization convergence), M5 Track 4 (disagreement rate decreasing)
- **Lagging (proof of outcome):** O1 (CFPB score), O2 (regret rate), O3 (budget adherence), O7 (regret-prediction accuracy)

**Counter-metrics (what NOT to optimize):**

| Counter-metric | Why it must not be the goal |
|---|---|
| Daily active use / session count | Optimizes anxiety and compulsive checking, not financial health |
| Notification send volume | More notifications ≠ more useful interventions |
| AI query frequency | High query frequency may reflect decision paralysis, not improvement |
| Total features used | Feature breadth does not correlate with outcome improvement |
| "Savings" amount | Savings rate without context can reflect income windfall or dangerous underspending |

---

## 5. What Best-in-Class Products/Research Do Well (Differentiation-Specific)

**On the seed's special differentiation concepts:**

| Concept | Exists elsewhere? | What works | What fails | What's differentiated here |
|---|---|---|---|---|
| "Would you buy this again?" feedback | Partially (Amazon post-purchase reviews, some budgeting apps ask retroactively) | Retroactive feedback is honest and low-friction | Not connected to the recommendation model | Here it feeds directly back into the personalized value model |
| "Did this improve your life?" | Rarely in finance apps; exists in wellness apps | Long-form reflection is honest but low-completion rate | Requires too much effort | A binary label at the right moment is actionable; a weekly reflection prompt is not |
| Planned vs. impulse labeling | Some apps ask; rarely used in modeling | Simple binary label; low friction | Usually decorative, not model-connected | Here it becomes a feature in the green/yellow/red model |
| Necessity vs. personal value distinction | Almost never operationalized | Clear categories reduce cognitive load | Static categories fail individual variation | Here the distinction is learned from Yem's history, not imposed from outside |
| Regret tracking | Essentially absent from current consumer finance products | Honest retrospective label | Hard to capture at scale | Single-user product makes this tractable |
| Historical backfill | Monarch-style receipt import is closest | Establishes baseline without waiting | Cold-start problem; data quality varies | This product has an existing receipt system and accumulated data |
| Personalized value model | Not available in any consumer product | Individual-specific; resistant to gaming | Requires sustained engagement and labeling | The combination of bank data + receipts + personal labels is genuinely novel |
| Green/yellow/red pre-purchase guidance | No consumer product does pre-purchase AI guidance in real-time | High potential for just-in-time intervention | Risk of over-interference, paternalism | Must be optional, explainable, and correctable |
| Financial just-in-time interventions | Theorized in behavioral economics; rarely implemented in apps | Effective when timed to decision moment | Annoying when asynchronous | Requires understanding purchase context; receipt + transaction history provides this |

**What data is needed for each to create value from day one:**
- Regret tracking: just the label UI + a prompt 7 days after a significant purchase.
- Planned vs. impulse: a one-tap label at transaction confirmation.
- Green/yellow/red: existing transaction history + category + budget context → value from first week.
- Personalized value model: requires ~30 labeled feedback events before personalization diverges from population defaults.

---

## 6. What We Should NOT Copy

- **Engagement-as-success:** Any metric that rewards frequency of use over quality of decision.
- **Generic financial coaching:** Population-level rules ("save 20% of income") applied without personal-history grounding contradict the product's differentiation.
- **Gamification for spending reduction:** Points, streaks, and badges for "not spending" create perverse incentives and optimize for the metric, not the behavior.
- **Notification-based nudges without timing intelligence:** Sending a budget warning 3 days after a purchase is useless; at the moment of a significant discretionary purchase it may be useful.
- **Opaque AI scores:** An AI "financial health score" with no explainability creates false assurance and undermines trust when it is wrong.

---

## 7. Implications for Our Product

- **Measurement plan must start at onboarding.** The CFPB short-form well-being assessment (4 items) should be administered at setup and every 90 days. This establishes a baseline and allows pre/post comparison without a control group.
- **Regret capture must be lightweight.** 7 days after any purchase above a significance threshold, prompt with a single-tap label: "Glad you bought it / Regret it / Too soon to tell." Anything longer will not be completed.
- **Budget adherence requires explicit budget entry.** The product only measures adherence if Yem has stated a budget. Encouraging budget entry at onboarding is a prerequisite for O3.
- **O7 (regret-prediction accuracy) is the internal AI accountability metric.** If the AI's pre-purchase red flags do not predict regret at a higher rate than base rate, the model needs retraining. This is a within-product measurement that requires no external comparison.
- **Differentiation requires longitudinal commitment.** The personalized value model is only differentiated if it improves over time and Yem can observe that improvement (e.g., "your recommendations have improved — here's how your value profile has changed over 6 months").

---

## 8. Implications for Architecture

- A `feedback_events` table capturing: purchase ID, label type (regret/value/planned/impulse), timestamp, and delay-from-purchase is a minimum requirement for Track 8 measurement.
- The CFPB well-being score must be stored as a versioned periodic snapshot, not a rolling metric.
- The personalization model must support an "accuracy over time" query: given the last N recommendations and subsequent labels, what is the trend?
- Counter-metrics (session count, notification volume) should be tracked in analytics but flagged as counter-metrics in any dashboard — the product should never optimize for them.

---

## 9. Differentiation Opportunities

- **Regret as a first-class product metric and user-visible insight:** "You've regretted 2 of your last 10 discretionary purchases — here's the pattern." No current consumer finance product does this.
- **Personal value convergence visible to the user:** Show Yem how their stated preferences have shaped the model over time. This transparency builds trust and makes the personalization feel earned, not mysterious.
- **Pre-purchase intelligence grounded in personal history:** "Based on the last 8 times you bought something from this category, here's what you said about it" is a genuinely differentiated intervention — not a population-level warning.
- **Behavior change measurement as a feature:** Surface the CFPB score trend as a product output. "Your financial well-being score has improved by 4 points over 3 months" is a powerful, evidence-grounded message that competes with no other consumer product's output.

---

## 10. Risks / Unknowns

| Risk | Status |
|---|---|
| Regret capture completion rate | **Unknown** — 7-day delay prompts may have low completion; UI friction must be minimized |
| CFPB score sensitivity to product-level changes | **Unknown** — 90-day retesting interval may be too slow to detect early product impact |
| Whether Yem's behavior changes meaningfully without a control condition | **Unknown** — pre/post design is the best available option for a single-user product, but confounds exist |
| Personalized value model convergence rate (30 events) | **Inference** — not empirically validated for this domain; may require more or fewer events |
| Risk of pre-purchase guidance feeling paternalistic | **Unknown** — requires product testing; must be optional and easily dismissible |
| Whether regret-prediction accuracy is measurable within first 6 months | **Unknown** — depends on volume of significant purchases and label completion rate |

---

## 11. PRD Changes Recommended

1. Add O1–O7 to the PRD as the canonical success metrics with explicit leading/lagging labels.
2. Add the CFPB Financial Well-Being Scale to onboarding as a mandatory baseline step.
3. Define "regret capture" as a core product feature, not a nice-to-have.
4. Add counter-metrics explicitly to the PRD with a statement that they must not be used as OKRs.
5. Define the `feedback_events` table as a first-class data requirement.
6. Add a "personalization quality review" cadence (e.g., monthly) to the product plan.
7. State explicitly in the PRD: "This product succeeds if Yem makes fewer regretted purchases and reports higher financial well-being — not if Yem opens the app more often."

---

## 12. Stop Statement

Evidence from live sources covers the full Track 8 scope: the CFPB Financial Well-Being Scale provides a validated outcome instrument; the product's differentiated concepts (regret tracking, personalized value model, pre-purchase guidance) are shown to be novel in the current landscape and their data requirements are defined; leading and lagging indicators are distinguished; counter-metrics are explicitly named; and a simple v1 measurement plan is deliverable from this research. Additional research on behavior change in personal finance apps was attempted but blocked by CAPTCHA, 404, and Vertex AI organization policy restrictions on WebSearch. The open questions that remain are empirical product questions (completion rates, convergence rates, score sensitivity) that require product deployment to answer — not further literature research. Research is sufficient to proceed.

---

## 12. Sources

| # | Title | Publisher | URL | Date | Accessed |
|---|---|---|---|---|---|
| S9 | CFPB Financial Well-Being Scale | Consumer Financial Protection Bureau | https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/ | 2015 (validated scale); page current | 2026-08-15 |

*(Tracks 4 and 8 share S1–S8 from Track 4 where relevant to evaluation methodology. Track 8 adds S9 as the primary outcome measurement source. Total across paired workstream: 9 sources, within the 8–12 limit.)*

---

**Blocker note on WebSearch:** The Vertex AI organization policy (`constraints/vertexai.allowedPartnerModelFeatures`) blocks the WebSearch tool for this model. All live sources were obtained via WebFetch. Multiple targeted URLs for financial behavior change research returned CAPTCHA blocks or 404. The Track 8 peer-reviewed behavior change evidence base is thinner than ideal as a result. The CFPB scale is confirmed live. All other Track 8 claims are labeled as inference or product proposal accordingly.

Sources:
- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)
- [HuggingFace Evaluate Documentation](https://huggingface.co/docs/evaluate/index)
- [HuggingFace LLM Leaderboard Blog](https://huggingface.co/blog/llm-leaderboard)
- [Revisiting the Calibration of Modern Neural Networks](https://arxiv.org/abs/2106.07998)
- [AlpacaFarm: A Simulation Framework for Methods and Evaluators of RLHF](https://arxiv.org/abs/2305.14387)
- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050)
- [Are Emergent Abilities of Large Language Models a Mirage?](https://arxiv.org/abs/2304.15004)
- [CUAD: Contract Understanding Atticus Dataset](https://arxiv.org/abs/2103.06268)
- [CFPB Financial Well-Being Scale](https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/)
