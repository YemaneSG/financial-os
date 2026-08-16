# Track 1 — Behavioral Signal Research

**Run:** `2026-08-15-premium-mobile-r1`
**Date:** 2026-08-15
**Owner:** Yemane
**Research role:** bounded background research
**Status:** Complete
**Scope boundary:** research only; the existing receipt collector, its data,
contracts, database, infrastructure, and production path remain untouched

## 0. Outcome, non-goals, and acceptance evidence

### Outcome

Identify which personal-spending signals a future Financial OS can derive from
bank transactions, item-level receipts, merchant history, repeat purchases,
returns/refunds, purchase frequency, category patterns, and historical user
feedback. The result must be decision-ready for the future PRD and architecture
pass without designing the full architecture.

### Non-goals

- Do not change or replace the working receipt-ingestion system.
- Do not choose a database schema, model vendor, fixed classifier threshold, or
  final green/yellow/red policy.
- Do not treat competitor marketing as proof that coaching changes behavior.
- Do not infer private facts about the owner or include real receipt, transaction,
  identity, provider, or production data.
- Do not turn broad category norms into claims about what the owner personally
  needs, values, regrets, or buys impulsively.

### Acceptance evidence

This report is complete when it distinguishes automatic signals from user labels,
day-one learning from longitudinal learning, deterministic facts from inference,
and validated mechanisms from hypotheses; identifies minimum evolution-friendly
architecture capabilities; cites no more than 8–12 strong sources; and ends with
an explicit stop statement.

## 1. Executive summary

- Historical transaction and receipt data can immediately establish objective
  baselines: merchants, products, amounts, cadence, recency, repeat rate,
  cumulative spend, refunds, category mix, and deviations from the owner's own
  history. It can produce **candidates**, not truths, for recurrence,
  replacement, necessity, impulse, regret, and habit.
- Intent and lived outcome are not present in bank or receipt records. Plannedness,
  felt necessity, automaticity, usefulness, regret, and willingness to repurchase
  require lightweight user feedback. A return is not regret; repetition is not
  habit; a grocery-store charge is not necessarily an essential basket.
- Item-level evidence is the key differentiator. It can separate a mixed merchant
  basket, identify repeated products, connect a return to an item, and let future
  guidance learn that one product was valuable while another product in the same
  transaction was not.
- Green/yellow/red should be a versioned advisory policy over cited evidence, with
  an explicit **insufficient evidence / no signal** state. Red should initially be
  reserved for owner-defined constraints or unusually strong, corroborated
  personal evidence—not generic judgments about categories.
- The architecture needs append-only observations, user-label events, versioned
  inferences, temporal feature snapshots, provenance/confidence, and recorded
  guidance outcomes. It does not need a final behavioral model now, and it must
  not couple the future app to the existing receipt database.

## 2. Evidence classification used in this report

| Label | Meaning |
|---|---|
| **Observed fact** | Directly documented by a primary source or computable exactly from source records. |
| **Research-supported boundary** | A distinction supported by peer-reviewed research and applicable here with stated limits. |
| **Proposal** | A recommended product or architecture choice derived from the evidence. |
| **Hypothesis** | Plausible and testable, but not established for this product or owner. |
| **Unknown** | Evidence is insufficient; a product experiment or owner input is required. |

Competitor sources in this report establish that a mechanism exists or how the
vendor describes it. They do not establish causal behavior change or reveal
undocumented implementation details.

## 3. What the system can infer automatically

### 3.1 Direct observations and deterministic features

The following are computable without interpreting the owner's psychology, once
source normalization and relationship quality are adequate:

| Signal | Inputs | Deterministic output | Important boundary |
|---|---|---|---|
| Merchant/product occurrence | Normalized merchant; receipt line item or normalized product candidate | Count, first/last seen, recency, dates, accounts, source coverage | Entity/product normalization may itself be inferred and must carry confidence. |
| Purchase frequency | Occurrence series | Inter-purchase intervals, purchases per window, rolling frequency, interval variance | Posting date may differ from purchase date; missing sources bias the rate. |
| Repeat purchase | Linked occurrences of the same normalized merchant/product | Repeat count, time since prior purchase, cumulative units and spend | “Same product” requires a versioned identity decision; same merchant is much weaker. |
| Monetary significance | Exact minor-unit amounts | Transaction amount, item amount, cumulative spend, share of observed spend, personal percentile | “High spend” is not “high value.” Value requires user evidence. |
| Category pattern | Versioned category assignment | Spend/count mix by category and time window | Category assignment may be inferred; mixed baskets require item-level evidence. |
| Cadence consistency | Dated occurrences | Candidate weekly/monthly/annual cadence, expected window, amount variability | Regularity is recurrence evidence, not evidence of necessity or habit automaticity. |
| Return/refund event | Credit transaction, receipt/order evidence, source relationship | Amount, date, source, full/partial status; confirmed link when a source ID proves it | Amount/date/merchant matching alone yields a candidate link, not a confirmed one. |
| Change from personal baseline | Current and prior windows | Difference from rolling personal baseline by merchant/product/category | A deviation is unusual, not automatically harmful, fraudulent, or regretted. |
| Coverage/quality | Source manifests and linkage states | Missing periods, unmatched evidence, confidence coverage, stale feed | No behavior signal should outrank data-quality uncertainty. |

Plaid documents that transaction feeds can supply date, amount, description,
merchant and category, can later modify or remove transactions, and can expose
recurring-stream status, frequency, first/last dates, amounts, and category. It
also recommends at least 180 days of history for its recurring product. These are
useful feasibility signals, not requirements for our own algorithm. [S1]

### 3.2 Automatically inferred candidates

These outputs are useful if they remain named hypotheses with evidence,
confidence, provenance, and a correction path.

| Target | Candidate inference | Evidence that may raise confidence | Evidence that must not be treated as proof |
|---|---|---|---|
| **High-value repeat purchase** | A product/merchant with high repeat rate and/or meaningful cumulative spend, potentially valuable to the owner | Item identity; stable repurchase; low return rate; later “worth it” and “buy again” labels | High price, high frequency, or no return alone |
| **Impulse purchase** | A purchase worth asking about because it is new, off-pattern, discretionary-candidate, clustered with other unplanned purchases, or outside a stated plan | Explicit “unplanned” label; short consideration time; user-confirmed trigger; repeated pattern under similar context | Transaction speed, time of day, merchant/category, or later regret alone |
| **Necessity** | A recurring or replenished expense that may be necessary | Owner label; goal/obligation context; repeated stable essential-purpose evidence; item detail | A generic “essential” category, recurrence, or grocery merchant alone |
| **Low-value/regretted purchase** | A purchase worth follow-up because it was returned, quickly replaced, not repurchased, or resembles previously regretted items | “Not worth it,” “regret,” “unused,” or “would not buy again” feedback and reason | Return/refund, price, or lack of repetition alone |
| **Habit pattern** | Repeated behavior in a stable temporal, merchant, category, or situational context | Longitudinal repetition plus user report that the action occurred automatically or without deliberation | Frequency alone; a recurring bill is usually a commitment, not necessarily a habit |
| **Replacement purchase** | A later item may replace an earlier item in the same product family | Explicit replacement link/reason; plausible elapsed time; prior failure/end-of-life feedback | Same category or similar product name alone; it may be replenishment, upgrade, gift, or duplication |
| **Unusual spending** | Amount, frequency, merchant, item, category, timing, or basket composition deviates from a personal/contextual baseline | Multiple personal baselines; seasonal/context filters; calibrated uncertainty; owner confirmation | Population averages or a single global threshold |

### 3.3 Why the strongest signals are composite

No single source answers the behavioral question:

- Bank transactions establish money movement, but their descriptions are sparse
  and ambiguous. Cleo's current engineering account explicitly describes this
  ambiguity and uses multiple enrichment layers and confidence per attribute.
  Its “essential” flag is a vendor taxonomy outcome, not proof of a particular
  user's necessity. [S4]
- Receipts establish item composition and purchase-time evidence, but do not
  establish whether the purchase was planned or valuable later.
- Merchant history establishes recurrence and context, but cannot distinguish a
  routine necessity from a routine indulgence.
- Returns/refunds establish a reversal or adjustment, but not why it happened.
- User feedback establishes personal intent or outcome, but can be delayed,
  inconsistent, missing, or change with context.

The strongest behavioral signal is therefore an evidence bundle: financial event
+ item evidence + historical comparison + explicit user evidence + current
budget/goal context. The system should retain the components rather than collapse
them into one opaque label.

## 4. Labels the user should provide later

The proposed labels are independent axes, not one exclusive taxonomy. The owner
should be able to answer one useful question without completing all of them. The
exact vocabulary and number of choices remain a usability hypothesis.

| Axis | Candidate low-friction choices | When to ask | Why it cannot be safely inferred |
|---|---|---|---|
| Plannedness | Planned / unplanned / reminded in the moment / unsure | Soon after purchase or during later review | Intent occurs before/during purchase and is absent from financial records. |
| Necessity to this owner | Necessary / preferred but optional / discretionary / mixed / unsure | For high-impact or ambiguous items, then reuse carefully | Generic category norms do not encode the owner's obligations or circumstances. |
| Personal value | Worth it / neutral / not worth it / not yet known | After enough time to experience the outcome | Price and repetition do not measure life value. |
| Repurchase intent | Yes / maybe / no / not applicable | Post-use or when a similar purchase recurs | A repeat may be accidental or obligatory; no repeat may simply mean durable use. |
| Regret | None / some / strong / not yet known | At an opportunity-triggered follow-up, not a fixed universal delay | Regret is a post-decision cognitive/affective evaluation, not a transaction field. [S9] |
| Use/outcome | Used as intended / partly used / unused / consumed / gifted / returned | Post-use or on detected return/replacement | Returns and elapsed time cannot establish actual use. |
| Return/refund reason | Defect / size-fit / duplicate / changed mind / price adjustment / service recovery / other | When a return/refund is detected and the reason matters | Return events have multiple meanings. |
| Relationship to prior item | Replenishment / replacement / upgrade / duplicate / gift / unrelated | When a plausible prior item exists | Similarity and time alone cannot identify the relationship. |
| Habit automaticity | Intentional routine / often without thinking / situational / not a pattern | Only after a stable repeated pattern appears | Habit research distinguishes repeated behavior from automatic cue-response. [S8] |
| Guidance feedback | Helpful / wrong / too strong / mistimed / already knew / not relevant | Immediately after an advisory or later outcome | Dismissal alone does not identify whether content, timing, or inference failed. |

Optional reasons should be short, user-authored, and never mandatory. Structured
choices support learning; optional text preserves nuance. A correction to merchant,
category, amount, or product identity is **not** automatically a value/preference
label and must be stored separately.

Rook's impulse-buying research centers the subjective onset of an urge and action
without deliberation, and explicitly distinguishes swift habitual behavior from
impulsive behavior. That makes plannedness/urge a user-evidence question, not a
transaction classifier target. [S7]

## 5. What can be learned on day one from historical data

“Day one” means immediately after historical data has been imported and normalized
well enough for analysis. It does not mean that every source is complete.

### 5.1 Available on day one

1. **Personal merchant/category baseline:** observed counts, spend, recency,
   seasonality candidates, and changes by historical window.
2. **Repeat merchant and repeat product candidates:** merchant-level from bank
   history; item-level only where receipt/order evidence and product normalization
   exist.
3. **Recurring stream candidates:** regular timing, amount range, likely current
   status, and next expected window. Plaid's documented recurring mechanism and
   Monarch/Copilot user-editable recurrence/rules show this mechanism is feasible.
   [S1][S2][S3]
4. **Unusual-spending candidates:** deviation from the owner's own merchant,
   category, amount, frequency, and time-window distributions. Research on unusual
   PFM category spend supports uncertainty-aware personal/category forecasts and
   also notes that human expenses are intermittent and erratic. [S6]
5. **Cumulative significance:** which merchants/products/categories account for
   the largest observed spend or purchase count, without calling them valuable.
6. **Return/refund candidates:** credits or receipt/order events that may link to
   prior purchases, with confirmed vs inferred relationship status.
7. **Data-quality boundaries:** missing periods, unmatched evidence, stale feeds,
   mixed baskets, low-confidence merchant/category/product resolution, and source
   coverage.
8. **Imported user truth, if it already exists:** prior corrections, rules, and
   explicit labels can be applied as historical first-party evidence with their
   original time and semantics.

Personalized financial categorization has been deployed at large scale in another
financial context, and Copilot documents category prediction using transaction
features and the user's prior review history. These support technical feasibility,
not a claim that our owner-specific value labels will generalize or that a fixed
review count is adequate. [S3][S5]

### 5.2 Not knowable on day one without user evidence

- Whether a purchase was planned, prompted by an urge, or made after deliberation.
- Whether the owner regarded it as necessary at that time.
- Whether it improved the owner's life or was “worth it.”
- Whether a return indicates regret, defect, fit, duplication, or price adjustment.
- Whether repetition reflects automatic habit, obligation, convenience, or a
  deliberate routine.
- Whether a similar later item is a replacement, replenishment, upgrade, gift, or
  duplicate.
- Whether green/yellow/red improves decisions or merely adds friction, shame, or
  false certainty.

The correct day-one product behavior is therefore **descriptive first**: “This is
unusual relative to your history” or “You bought this four times,” with cited
evidence and optional feedback—not “This was impulsive” or “This is bad.”

## 6. What requires months of feedback

There is no supported universal month count or label count. Readiness should be
earned per signal through evidence sufficiency and evaluation, not elapsed time.

| Longitudinal learning | Why time/feedback is required | Activation evidence |
|---|---|---|
| Personal value by product/merchant/context | Value appears after use and may change by purpose or life context | Repeated outcome/repurchase feedback with stable semantics and held-out accuracy |
| Regret predictors | Regret is a later evaluation and may be purchase-specific | Follow-up labels across varied purchases, including non-regretted controls |
| Impulse-pattern candidates | Intent/urge labels are needed to distinguish off-pattern from merely new or planned | Enough owner-confirmed planned and unplanned examples to calibrate precision and abstention |
| Habit candidates | Repetition and stable context must be paired with experienced automaticity | Stable occurrence series plus explicit automaticity feedback |
| Replacement cycles | Product identity, elapsed life, and replacement reason must be learned | Confirmed relationship events across product families |
| Seasonal and life-change baselines | Travel, holidays, moves, pay changes, health events, and merchant drift can look anomalous | Multiple comparable periods or explicit context annotations |
| Guidance effectiveness | Advice can affect decisions differently by timing, framing, and receptivity | Recorded decision points, guidance/no-guidance comparison, overrides, usefulness, and later outcome |
| Label drift | The owner's priorities and meanings can change | Time-stamped labels, contradiction handling, and recent-vs-historical evaluation |

Copilot currently reports enabling its personalized category suggestions after 30
reviewed transactions. That is an observed product rule, not evidence that 30 is
valid for this different task, label vocabulary, owner, or outcome. [S3]

## 7. Future green/yellow/red guidance

### 7.1 Proposed semantics

Color is a compact summary of a full advisory record. It must never be the only
explanation.

| State | Proposed meaning | Example qualifying evidence | Product behavior |
|---|---|---|---|
| **No signal / insufficient evidence** | The system lacks enough relevant, reliable personal evidence | New product; incomplete source coverage; unresolved identity; conflicting labels | Show facts or ask one optional question; do not force a color. |
| **Green** | Evidence is consistent with the owner's stated plan/constraints and positive prior outcomes | Budget capacity is deterministic; comparable item was repeatedly “worth it”/“buy again”; no conflicting current goal | “Looks aligned” plus the two or three strongest factors; never “approved” or “safe.” |
| **Yellow** | Evidence is mixed, novel, off-pattern, or uncertain enough to merit reflection | Unusual amount/frequency; new merchant/product; prior outcomes mixed; category near owner-defined budget; likely impulse candidate without confirmation | Ask a short reflective question, show uncertainty, and make dismissal effortless. |
| **Red** | Strong corroborated personal evidence or an explicit owner-defined constraint indicates likely misalignment | Owner-defined hard limit; repeated confirmed regret/not-buy-again for close comparables plus current budget/goal conflict | Advise pause with evidence; do not block; allow immediate override without justification. |

At launch, red should be conservative. Inference alone should normally stop at
yellow until the owner has defined the rule or enough outcome evidence has been
calibrated. A safety or fraud alert is a separate product concept and should not
reuse the behavioral color semantics.

### 7.2 Guidance decision flow

1. Validate source freshness, identity/link confidence, and coverage.
2. Compute deterministic context: price, budget capacity, frequencies, prior
   facts, and exact owner-defined rules.
3. Retrieve only relevant, time-valid personal labels and inferred candidates.
4. Apply a versioned guidance policy that can abstain.
5. Store the evidence snapshot, policy version, color/no-signal state, explanation,
   and uncertainty.
6. Record view, override, optional feedback, actual purchase outcome, and later
   value/regret feedback as separate events.
7. Evaluate whether the guidance improved a defined proximal outcome before
   promoting or changing its policy.

JITAI research is from mobile health rather than personal finance, so transfer is
a **design hypothesis**. Its useful general structure is decision points,
tailoring variables, intervention options (including no intervention), decision
rules, and proximal/distal outcomes; it also warns that fatigue and receptivity
matter. [S10]

### 7.3 What the explanation must say

Every color should be expandable into:

- **Observed:** “This item is 2.1× your usual amount in this product family.”
- **Personal evidence:** “You marked two similar purchases ‘not worth it.’”
- **Current constraint:** “It would put the owner-defined category budget over by
  a deterministic amount.”
- **Uncertainty:** “Product match is medium confidence; one comparable purchase
  had a different purpose.”
- **Action:** “Pause,” “compare,” “continue,” or “no recommendation.”
- **Control:** “Not relevant,” “wrong match,” “buy anyway,” or “don't ask again in
  this context.”

The explanation should not claim emotion, motive, or moral status that the owner
did not provide.

## 8. Deterministic, inferred, and user-confirmed boundaries

| Layer | May contain | Authority |
|---|---|---|
| Source observation | Raw transaction/receipt/order event, source IDs, original descriptions, image-derived fields with extraction provenance | Evidence, not automatically normalized truth |
| Deterministic derived fact | Exact sums/counts/windows, state transitions, confirmed relationships, budget arithmetic, rule evaluation | Authoritative only within its explicit inputs and definitions |
| Inferred attribute | Merchant/category/product identity, recurring stream, candidate match, anomaly, replacement candidate, behavior candidate | Non-authoritative; confidence, model/rule version, evidence, and abstention required |
| User-confirmed label | Plannedness, necessity, value, regret, use, repurchase intent, relationship reason | First-party evidence for that target and time; not an eternal universal truth |
| Guidance decision | Green/yellow/red/no-signal plus reasons and policy version | Advisory output; never financial truth or permission |
| Outcome/evaluation | Purchase/skip, override, return, later label, usefulness response | Evidence for evaluating the policy; not automatically proof of causality |

Deterministic software should calculate all monetary values, time windows,
frequencies, and rule conditions. Models may normalize, classify, rank, detect,
and explain, but model output must not overwrite source facts or user labels.

### Required provenance and confidence

Each inferred or guidance record needs, at minimum:

- target entity and inference type;
- proposed value and explicit abstention capability;
- evidence references and evidence time window;
- source coverage/freshness state;
- feature-definition version;
- rule/model/prompt version and calculation time;
- calibrated confidence or evidence band, not invented precision;
- competing hypotheses or ambiguity reason where material;
- top contributing factors suitable for an explanation;
- state: proposed, user-confirmed, user-rejected, superseded, or expired;
- links to the user feedback that confirmed/rejected it;
- policy version and outcome links when used for guidance.

Confidence should be evaluated per inference type. A merchant-normalization score
does not transfer to “necessity,” and confidence in recurrence does not imply
confidence in habit or value.

## 9. Failure modes and false-positive risks

| Failure mode | Likely false conclusion | Required mitigation |
|---|---|---|
| Pending transaction becomes posted, modified, or removed | Duplicate purchase or artificial frequency spike | Preserve source lifecycle and deduplicate before behavior features. [S1] |
| Sparse bank description or merchant alias | Wrong merchant/category/product history | Raw description preservation, versioned normalization, confidence, correction. |
| Mixed basket at Amazon, Costco, grocery, or marketplace | Entire transaction labeled necessary or discretionary | Prefer receipt/order line items; otherwise mark basket mixed/unknown. |
| Missing receipts/accounts/cash history | Understated frequency or false “new/unusual” claim | Coverage indicator in every behavior query and guidance decision. |
| Return, refund, rebate, reimbursement, or price adjustment | False regret or reversal | Represent event type and relationship separately; ask reason when useful. |
| Bulk purchase, inflation, sale, or family/gift purchase | False unusual-spend or impulse alert | Compare quantity/unit price where available; allow context/recipient labels. |
| Travel, holiday, move, illness, or pay-cycle change | False anomaly/habit break | Context windows, seasonal baselines, change-point handling, easy dismissal. |
| Replenishment confused with replacement | False product-lifespan model | User-confirmed relationship reason; do not infer from time alone. |
| Repetition confused with habit | False claim of automatic behavior | Require stable context plus user automaticity evidence. [S8] |
| High frequency/spend confused with value | Reinforce an expensive low-value pattern | Separate monetary significance from personal value. |
| No repeat confused with dissatisfaction | Penalize durable or rarely needed products | Use repurchase applicability and product lifecycle context. |
| Feedback sampling bias | Learn only from extreme purchases or annoying prompts | Sample some neutral controls, track prompt eligibility and non-response. |
| Label drift or contradictory labels | Treat old preference as current truth | Time-stamp labels, retain contradictions, weight recency only through a versioned policy. |
| Color compression | Shame, false certainty, or automation bias | No-signal state, explanation, advisory language, immediate override. |
| Too many interventions | Alert fatigue and reduced trust | Quiet default, explicit intervention budget, measure receptivity/usefulness. [S10] |

## 10. Minimum architecture capabilities needed now

This is a capability checklist, not a full schema or topology.

1. **Source-neutral identity and relationship graph.** Stable internal references
   must connect transaction, receipt, receipt asset, line item, merchant candidate,
   product candidate, return/refund, and later feedback without requiring the new
   application to read the old receipt database directly. The existing receipt
   system remains behind an API boundary.
2. **Append-only evidence and lifecycle.** Preserve source observations, normalized
   revisions, inferred attributes, user labels, corrections, and guidance outcomes
   as distinguishable time-stamped records. Never overwrite one class with another.
3. **Versioned inference envelope.** All merchant/category/product resolution,
   recurrence, anomaly, similarity, replacement, and behavior candidates share a
   common provenance/confidence/status contract while allowing type-specific
   evidence.
4. **Multi-axis feedback events.** Store plannedness, necessity, value, regret,
   usage, repurchase intent, return reason, and guidance feedback independently.
   Taxonomy versions must coexist so vocabulary can evolve without rewriting
   history.
5. **Temporal feature definitions and snapshots.** Support reproducible rolling
   windows, personal baselines, seasonality/context, feature versions, and
   point-in-time reconstruction so training and evaluation do not leak future
   information.
6. **Configurable policy and abstention.** Green/yellow/red/no-signal thresholds,
   evidence requirements, intervention eligibility, and prompt budgets must be
   versioned configuration—not fixed columns or hardcoded universal constants.
7. **Explanation and outcome linkage.** A guidance decision must retain the exact
   evidence/features/policy used and later link to override, purchase/skip, return,
   usefulness, value, and regret outcomes.
8. **Evaluation split and privacy boundary.** Support private owner-authenticated
   golden labels, time-based train/evaluation splits, calibration by signal type,
   and aggregate/opaque public reporting. No raw private evidence enters source or
   public artifacts.
9. **Correction propagation with explicit scope.** A user can correct one event,
   establish a future rule, or confirm an entity relationship; the system must not
   silently propagate a one-off preference to all similar purchases.
10. **Data-quality gate.** Coverage, source freshness, unresolved identity, and
    relationship confidence must be queryable inputs to every inference and
    guidance decision.

### Top three architecture implications

1. Behavioral intelligence should be an evidence-and-feedback layer over source
   domains, not new columns that mutate transaction or receipt truth.
2. The contract must support versioned, typed inference plus abstention now; the
   eventual model can change without schema churn or historical relabeling.
3. Guidance is its own auditable decision/outcome loop, not a color stored on a
   purchase and not an LLM-generated authoritative field.

## 11. What best-in-class mechanisms do well

- **Plaid:** exposes sparse-but-useful transaction attributes, source update
  lifecycle, recurring stream attributes, and confidence on some enriched fields.
  [S1]
- **Monarch:** lets users create explicit deterministic rules from statement,
  merchant, amount, category, and account criteria; previews and retroactive
  application make propagation visible. [S2]
- **Copilot:** uses prior transaction reviews for personalized category suggestions,
  abstains from showing its own prediction when confidence is insufficient, and
  keeps correction close to the suggestion. [S3]
- **Cleo:** describes a layered cost-aware enrichment pipeline, per-attribute
  confidence, recurring-sequence analysis, and a user/domain-expert golden set.
  Its own report also shows why sparse transaction data has irreducible ambiguity.
  [S4]
- **Research:** demonstrates feasibility of personalized transaction categorization
  [S5], uncertainty-aware unusual-category detection [S6], and structured adaptive
  intervention design that includes doing nothing [S10].

These are mechanisms to adapt, not proof that any competitor reduces regret or
improves long-term financial behavior.

## 12. What we should adopt and not copy

### Adopt

1. Personal baselines before population judgments.
2. Layered deterministic-first inference with escalation only when needed.
3. Per-attribute confidence, abstention, and easy correction.
4. User-visible, scoped propagation rules rather than silent learning.
5. Item-level feedback tied to the exact evidence and later outcome.
6. Intervention policies with decision points, tailoring evidence, an explicit
   no-intervention option, and measurable outcomes.

### Do not copy

1. Generic essential/discretionary labels as if they represented the owner's
   actual necessity.
2. A fixed review count, confidence threshold, regret delay, or notification
   frequency from another product.
3. Opaque “AI insight” claims without source coverage, evidence, or uncertainty.
4. Chat personality, color, or alert volume as evidence of behavior change.
5. Automatic propagation of one correction or value judgment to every similar
   transaction.
6. Competitor-reported accuracy as a benchmark when taxonomy, dataset, and metric
   differ; Cleo itself warns that its before/after accuracy figures are not
   apples-to-apples. [S4]

## 13. Product implications and differentiation opportunities

### Top five actionable product implications

1. Launch the behavioral layer as **reflection and learning**, not predictive
   judgment: facts first, one optional feedback question, visible learning.
2. Make “worth it?” and “would buy again?” item-level when evidence exists; avoid
   forcing one label onto a mixed basket.
3. Treat “planned,” “necessary,” “habit,” and “regret” as user-confirmable axes
   with unknown states, not model-generated facts.
4. Introduce green/yellow/red only after a no-signal state, explanation, override,
   and evaluation loop exist.
5. Preserve data coverage and confidence in the interface so the owner knows when
   a conclusion is based on complete item history versus a sparse bank description.

### Differentiation opportunities

- **Evidence-to-outcome memory:** connect a bank charge to receipt items, then to
  later use/value/regret and the next related decision.
- **Personal value, not merchant morality:** learn that two items from the same
  merchant or category can have opposite value.
- **Replacement/replenishment graph:** make product relationships explicit rather
  than treating all repeat purchases alike.
- **Learning confirmation:** after feedback, show exactly which future inference
  can change and what will not be generalized.
- **Measured restraint:** make “no recommendation” a premium trust feature and
  evaluate whether interventions help rather than optimizing notification volume.

## 14. Validated findings, hypotheses, and unknowns

### Validated or strongly supported for decision-making

1. Transaction history can supply the objective inputs needed for personal
   merchant/category/amount/cadence baselines, subject to provider coverage and
   mutable transaction lifecycle. [S1]
2. Personalized transaction categorization from prior user decisions is technically
   feasible; both deployed research and current products document it. [S3][S5]
3. Unusual spending should be contextual and uncertainty-aware; personal financial
   expenses can be intermittent and difficult to forecast. [S6]
4. Impulse, habit automaticity, and regret include subjective or experiential
   components not encoded in a transaction record. [S7][S8][S9]
5. Feedback, correction, confidence, and abstention are first-class mechanisms in
   credible current product implementations, though their causal outcomes remain
   unproved here. [S2][S3][S4]
6. Adaptive intervention design requires explicit decision points, tailoring
   variables, intervention options, outcomes, and the ability to deliver nothing.
   Transfer from health to personal finance remains a design inference. [S10]

### Hypotheses to test

1. Item-level “worth it / buy again” feedback predicts future owner value better
   than transaction/category history alone.
2. Return/refund plus a negative outcome label is a strong predictor of future
   regret for a closely matched item; return/refund alone is not.
3. A restrained yellow reflection prompt helps on uncertain or unusual purchases
   without producing shame or fatigue.
4. Red guidance based on explicit owner constraints and repeated corroborated
   regret improves decisions without becoming controlling.
5. Opportunity-triggered follow-up produces more useful labels than a universal
   fixed delay.
6. Personalized item/product history materially outperforms merchant/category
   history for mixed retailers.

### Unknowns requiring owner research or minimum experiments

1. Which feedback vocabulary feels natural to the owner and can be answered
   consistently with low friction.
2. Which purchases deserve item-level feedback and when the owner is receptive.
3. How much and what diversity of labeled history is needed for each inference to
   beat a descriptive baseline at acceptable precision/calibration.
4. Whether green/yellow/red improves comprehension or introduces moral judgment,
   false certainty, or automation bias.
5. Which contexts should suppress guidance entirely and what intervention budget
   is tolerable.
6. Whether purchase guidance changes later regret, budget alignment, or personal
   value; no bounded competitor evidence establishes this causal effect.
7. How accurately products can be normalized across receipts/retailers and whether
   that accuracy is sufficient for replacement and repurchase learning.

### Minimum follow-up experiments

1. **Feedback vocabulary test:** apply the candidate axes to a small, private,
   owner-selected historical sample; measure ambiguity, completion time, and
   contradictions. Do not set a production label count from this test.
2. **Signal replay:** replay historical data point-in-time and compare rule-based
   merchant/category/item baselines against owner labels, including abstention and
   false-positive review.
3. **Guidance format test:** compare factual observation, color-plus-explanation,
   and no intervention on synthetic/private scenarios; measure comprehension,
   usefulness, annoyance, override, and later outcome.
4. **Timing test:** randomize only safe reflection opportunities among prompt now,
   prompt later, and no prompt; record proximal usefulness and fatigue. Any causal
   language waits for an adequately designed experiment.

## 15. PRD changes recommended for the later merge

1. Define the first behavioral promise as **personal reflection and evidence-backed
   learning**, unless the owner explicitly selects pre-purchase intervention.
2. Require separate source facts, deterministic derived facts, inferences,
   user-confirmed labels, guidance decisions, and outcomes.
3. Require an insufficient-evidence/no-signal state and prohibit forced colors.
4. Require item-level feedback when item evidence exists and transaction-level
   fallback when it does not.
5. State that high spending is not high value; repetition is not habit; a return
   is not regret; and generic essentiality is not personal necessity.
6. Require visible provenance, confidence/ambiguity, correction, scoped learning,
   override, and deletion/export controls for behavioral data.
7. Make guidance effectiveness, false-positive burden, regret reduction, and
   owner usefulness outcomes; do not optimize alerts, colors shown, AI messages,
   or time in app.
8. Keep thresholds, label counts, prompt timing, and color policy experimental and
   versioned until private owner evidence supports them.

## 16. Top unresolved risks

1. **Semantic overreach:** the app may present intent or value as fact when only a
   spending proxy exists.
2. **Sparse/biased learning:** missing sources and selectively answered prompts may
   produce confident but unrepresentative models.
3. **Intervention harm:** color and proactive prompts may create shame, fatigue,
   or misplaced reliance without improving outcomes.

## 17. Stop statement

This bounded Track 1 research is sufficient for the PRD and architecture briefing.
Every requested behavioral target now has an automatic-signal boundary, proposed
user evidence, day-one versus longitudinal disposition, guidance role, provenance
requirement, false-positive analysis, and minimum evolution-friendly architecture
capability. The remaining questions are owner-specific product experiments, not
gaps that broader desk research is likely to resolve. Additional research would
mostly repeat mechanisms or introduce unsupported thresholds, so this track stops
here. No application, production system, receipt service, data, contract, schema,
infrastructure, or existing research artifact was changed.

## 18. Sources

All sources were accessed 2026-08-15. Product sources establish documented
capability or vendor-reported mechanism, not independent effectiveness.

1. **[S1] Plaid, “Transactions API Reference.”** Current documentation; publication
   date not stated. Transaction attributes, mutable transaction lifecycle,
   confidence fields, and recurring stream structure/status.
   https://plaid.com/docs/api/products/transactions/
2. **[S2] Monarch Money, “Transaction Rules.”** Updated 2026-06-12. Visible,
   user-authored matching and propagation rules across statement/merchant/amount/
   category/account inputs.
   https://help.monarch.com/hc/en-us/articles/360048393372-Transaction-Rules
3. **[S3] Copilot Money, “Copilot Intelligence for Spending.”** 2025-03-21.
   Personalized category suggestions based on reviewed transactions, transaction
   features, confidence behavior, and correction flow. The documented 30-review
   activation is a competitor implementation choice, not our threshold evidence.
   https://help.copilot.money/en/articles/8182433-copilot-intelligence-for-spending
4. **[S4] Cleo, “How Cleo learns what your transactions actually mean.”**
   2026-01-28. Vendor engineering account of sparse transaction ambiguity,
   layered enrichment, per-attribute confidence, sequence-based recurrence,
   essentiality taxonomy, and labeled evaluation data.
   https://web.meetcleo.com/blog/how-cleo-learns-what-your-transactions-actually-mean
5. **[S5] Lesner, Ran, Rukonic, and Wang, “Large Scale Personalized Categorization
   of Financial Transactions.”** Proceedings of AAAI, published 2019-07-17.
   Deployed personalized financial categorization in a small-business context.
   https://doi.org/10.1609/aaai.v33i01.33019365
6. **[S6] Brando, Rodríguez-Serrano, and Vitrià, “Detecting Unusual Expense
   Categories for Financial Advice Apps.”** KDD Workshop on Anomaly Detection in
   Finance, 2019-08. Uncertainty-aware unusual-expense detection over personal
   category histories and limits of forecasting intermittent spending.
   https://www.bbvaaifactory.com/publications/Anomaly_Detection_in_Finance.pdf
7. **[S7] Rook, “The Buying Impulse.”** *Journal of Consumer Research* 14(2),
   1987-09, pp. 189–199. Subjective impulse onset, urge, deliberation, and the
   distinction between swift habitual and impulsive behavior.
   https://doi.org/10.1086/209105
8. **[S8] Gardner, Abraham, and Lally, “Towards parsimony in habit measurement:
   Testing the convergent and predictive validity of an automaticity subscale of
   the Self-Report Habit Index.”** *International Journal of Behavioral Nutrition
   and Physical Activity* 9:102, published 2012-08-30. Habit automaticity and its
   self-report measurement boundary.
   https://doi.org/10.1186/1479-5868-9-102
9. **[S9] Keaveney, Huber, and Herrmann, “A model of buyer regret: Selected
   prepurchase and postpurchase antecedents with consequences for the brand and
   the channel.”** *Journal of Business Research* 60(12), 2007-12, pp. 1207–1215.
   Buyer regret as a post-decision evaluation with cognitive/affective context;
   field context was luxury automobile purchases, so generalization is limited.
   https://doi.org/10.1016/j.jbusres.2006.07.005
10. **[S10] Nahum-Shani et al., “Just-in-Time Adaptive Interventions (JITAIs) in
    Mobile Health: Key Components and Design Principles for Ongoing Health
    Behavior Support.”** *Annals of Behavioral Medicine* 52(6), published online
    2017-12-12; issue 2018-06, pp. 446–462. Decision points, tailoring variables,
    intervention options including no intervention, decision rules, outcomes,
    receptivity, and fatigue. Application to finance is a hypothesis.
    https://doi.org/10.1007/s12160-016-9830-8
