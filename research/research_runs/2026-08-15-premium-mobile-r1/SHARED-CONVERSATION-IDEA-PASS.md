# Shared Conversation Idea Pass — Behavioral Intelligence

**Date:** 2026-08-15
**Input:** Owner-provided shared ChatGPT conversation
**Scope:** Extract, challenge, and enrich the differentiated product ideas without
repeating Tracks 1–8
**Status:** Complete; decision input, not implementation authorization

## 1. Central conclusion

The conversation's strongest idea is not a single feature. Several individual
mechanics now exist in small consumer products: bank-connected purchase swiping,
worth-it/regret reflection, need/want/regret labels, pre-purchase AI scoring,
cooling-off flows, shopping lists, and spending gamification.

The differentiated product hypothesis is the **combined evidence system**:

> Bank truth says what money moved. Receipt evidence says what was bought. The
> owner's time-aware feedback says what the purchase meant. Deterministic
> software assembles that evidence, and AI may later explain it without becoming
> the judge.

No product in this focused pass was confirmed to combine item-level receipt
evidence, versioned multi-axis personal-value labels, representative feedback
sampling, deterministic financial context, explicit abstention, and later
evidence-backed purchase guidance. That is a competitive observation, not a
patent or behavioral-effectiveness claim.

## 2. Ideas recovered from the conversation

1. **A private financial memory, not an AI budget.** The desired progression is
   collection → integration → reflection → action.
2. **Three kinds of truth.** Money movement, item-level purchase content, and
   personal meaning must remain distinct but linked.
3. **Reflection as data creation.** The swipe flow is a low-friction preference-
   elicitation mechanism, not decorative gamification.
4. **Personal value instead of generic morality.** Necessary, discretionary,
   expensive, repeated, and personally valuable are different dimensions.
5. **Historical backfill as a head start.** Existing transactions and receipts
   can establish deterministic patterns on day one; retrospective labels add
   meaning before months of prospective use.
6. **Reactive and proactive intelligence.** The owner can ask questions, while
   the system may later surface narrow, factual observations without waiting for
   a prompt.
7. **Evidence-backed decision support.** Future guidance should cite budget
   capacity, plan status, similar purchases, prior outcomes, and uncertainty;
   it should never merely say buy or do not buy.
8. **Just-in-time support.** A purchase decision point may be more useful than a
   monthly retrospective, but only if the owner is receptive and the product can
   choose to say nothing.
9. **Deterministic tools, interpretive AI.** Code and SQL own arithmetic and
   financial facts; an LLM may translate questions and explain verified results.
10. **Outcome questions beyond category spend.** Examples include the share of
    discretionary spend later rated as worthwhile and the amount associated with
    owner-confirmed regret. These are reflection metrics, not causal claims about
    guaranteed savings.

## 3. What the new pass changed

### A. The swipe queue needs sampling discipline

If the app asks only about expensive, unusual, or suspected low-value purchases,
the resulting labels will overrepresent those cases. Preference-elicitation
research warns that selection bias can propagate into later recommendations.

The v1 reflection queue should therefore mix:

- decision-relevant or uncertain purchases;
- routine and apparently high-value controls;
- a small representative sample across merchants, categories, prices, and time;
- occasional re-evaluation where an outcome may have changed.

Every presentation event should record the subject, selection reason, policy
version, presentation time, skip/completion, and—when randomized—the selection
probability. Missing feedback is missing evidence, not a negative label.

This is the most important architecture addition from this pass.

### B. A future planned-purchase list should be an intent ledger

A shopping list is more than convenience. A controlled online-grocery study
found that list creation reduced items purchased and, in one study, reduced
spend. The result is encouraging but does not prove general effectiveness across
retail contexts.

For this product, a future intent record should preserve:

- what the owner intended to buy;
- when the intent was created;
- target category or item, optional budget, and expiry;
- whether the eventual purchase matched, substituted for, or exceeded the plan.

Absence from a list must not automatically mean impulse. A forgotten necessity,
replacement, gift, or newly discovered need can be unplanned without being
harmful. V1 can collect retrospective plannedness; the prospective intent ledger
belongs after the awareness/reflection release.

### C. Future JITAI design needs a real decision policy

JITAI research identifies decision points, intervention options, tailoring
variables, decision rules, proximal outcomes, and distal outcomes. Applied here:

| Component | Financial OS interpretation |
|---|---|
| Decision point | Owner scans/enters an item, opens a transaction, or encounters a closely related repeat purchase |
| Tailoring variables | Plan status, deterministic affordability, comparable items, prior labels, evidence quality, recent prompt burden, owner receptivity |
| Intervention options | Say nothing; show neutral facts; offer a pause/save-for-later action; show cautious guidance; show an owner-defined hard-limit warning |
| Decision rule | Versioned policy that may abstain and always cites its evidence |
| Proximal outcome
| Owner notices, pauses, saves, skips, or buys with awareness |
| Distal outcome | Lower owner-confirmed regret and better alignment with stated priorities without increasing shame or avoidance |

The 2026 JITAI review highlights a critical distinction: a person can need support
while being unable or unwilling to engage with it. The safest first guidance
surface is therefore **owner-initiated** (scan or ask), not unsolicited checkout
surveillance. “Do nothing” is a first-class intervention option.

### D. Disagreement and override are different learning events

- **Disagreement:** “Your evidence or interpretation is wrong.” This corrects the
  model, source relationship, or policy output.
- **Override:** “I understand the evidence and am buying anyway.” This is a
  decision outcome, not proof that the guidance was wrong.

Both must be recorded separately, with later value/regret evidence linked to the
same decision event. Otherwise the system will learn the wrong lesson.

### E. Gamification should expose progress in knowledge, not demand engagement

Useful feedback is: “Your answers now cover more of your recurring purchases” or
“the model changed because you corrected three items.” Streaks, shame, points for
spending less, and forced daily sessions risk optimizing app use instead of
financial awareness. Short sessions, one question per card, skip, undo, and
visible learning are the appropriate v1 mechanics.

## 4. Focused competitive correction

The earlier bounded competitor set missed several emerging adjacent products.

| Product | Confirmed adjacent mechanism | What remains unconfirmed |
|---|---|---|
| **impause** | Bank connection; swipe right for worth-it and left for regret; trigger/mood patterns; pre-purchase Pause; cooling-off; challenges, XP, and streaks | Item-level receipt linkage, multi-axis/versioned labels, deterministic evidence graph, abstention, and validated outcome effect |
| **enough.** | Purchase reflection using need/want/regret; pattern summaries; judgment-free money mindfulness | Item-level receipts, pre-purchase personalized evidence, and model/evaluation design |
| **Spending Sensei** | Pre-purchase chat, a 1–10 Buy Score, fun-budget context, and Buy/Skip recommendation | Bank/receipt ground truth, correction provenance, and evidence-calibrated personalization |
| **Listonic** | Planned shopping, estimated cost, price tracking, history-based suggestions, and anti-impulse list framing | Whole-financial-history linkage and post-purchase value learning |

This means “swipe regret,” “pre-purchase score,” and “shopping plan” are not
individually novel. Financial OS should not compete by adding more gamification
or making a louder buy/skip judgment. Its stronger wedge is deeper evidence,
item-level personal value, representative labeling, transparent uncertainty, and
learning from corrections and outcomes.

Vendor and App Store claims do not establish behavioral effectiveness. The
existing conclusion still stands: this product must measure its own outcomes.

## 5. Immediate v1 decisions

### Include now

1. Plaid transaction history and receipt evidence through separate authoritative
   sources.
2. Purchase- or line-item-level reflection with independent, editable axes.
3. A reflection exposure event with selection reason and policy version.
4. A queue that includes representative controls instead of only suspicious
   purchases.
5. Skip, unsure/not-yet-known, and later revision.
6. Factual home observations and reflection progress; no predictive colors.

### Do not include now

1. Green/yellow/red guidance.
2. A Buy Score or buy/skip verdict.
3. A planned-purchase/intention system.
4. Push-triggered behavioral intervention.
5. Streaks, XP, leaderboards, or notification targets.
6. LLM-based accounting or authoritative behavioral labels.

The current awareness/reflection v1 remains correct. This pass strengthens its
data-collection design; it does not expand its release scope.

## 6. Minimum future event contracts

These are conceptual requirements for architecture, not full schemas.

### Reflection exposure

- subject type and opaque subject reference;
- policy version and selection reason;
- evidence-availability snapshot;
- presented, skipped, answered, or dismissed time;
- randomized-selection probability when applicable.

### Label event

- axis and value, including unsure/not-yet-known;
- owner-authored time and effective context;
- optional reason;
- previous event reference when revised;
- reflection exposure that elicited it.

### Future decision event

- decision point and owner initiation source;
- prospective intent/plan relationship;
- deterministic financial context;
- comparable purchase and label references;
- intervention option, policy version, confidence band, and abstention reason;
- disagreement, override, purchase/skip, and later outcome as separate events.

## 7. Evaluation plan

1. **Reflection coverage:** Are labels distributed across routine, unusual,
   high-value, low-value, returned, and non-returned purchases?
2. **Burden:** Completion, skip, correction, and session-abandonment rates by
   question and context.
3. **Stability:** Which label axes change with elapsed time? Do not freeze an
   early answer as permanent truth.
4. **Selection-bias check:** Compare label distribution from prioritized prompts
   with the representative control sample.
5. **Later guidance experiment:** Only after sufficient evidence, compare no
   intervention, neutral evidence, and color guidance. Measure immediate action,
   annoyance, later value/regret, and false-positive burden.
6. **Causal restraint:** A future single-owner micro-randomized experiment can
   estimate short-term intervention effects, but only with explicit owner consent
   and low-burden outcomes. Until then, associations are not causal proof.

No fixed label count, notification frequency, regret delay, or traffic-light
threshold is accepted from research alone.

## 8. Evidence classification

### Supported strongly enough to design for

- Personal-informatics stages are iterative; problems in collection and
  integration impair later reflection and action.
- Explicit preference elicitation can help with cold start, but the sample of
  items selected for feedback can bias the learned model.
- JITAIs require explicit decision rules and a no-intervention option; need and
  receptivity are not the same.
- Human-AI systems should support correction, understandable capability limits,
  and appropriate user control.

### Promising but unvalidated in personal finance

- A planned-purchase list reduces later regret outside the studied online-
  grocery contexts.
- Green/yellow/red improves purchase decisions.
- Item-level personal-value learning materially outperforms transaction-level
  regret reflection.
- Historical retrospective labels predict prospective value or regret.
- The product changes behavior rather than merely increasing reflection.

## 9. Sources

1. Ian Li, Anind Dey, and Jodi Forlizzi, “A Stage-Based Model of Personal
   Informatics Systems,” CHI 2010: https://personalinformatics.ianli.com/lab/model
2. Nahum-Shani et al., “Just-in-Time Adaptive Interventions in Mobile Health,”
   *Annals of Behavioral Medicine*: https://pubmed.ncbi.nlm.nih.gov/27663578/
3. Nahum-Shani and Murphy, “Just-in-Time Adaptive Interventions: Where Are We Now
   and What Is Next?”, *Annual Review of Psychology*, 2026:
   https://pubmed.ncbi.nlm.nih.gov/40939059/
4. Klasnja et al., “Micro-Randomized Trials,” *Health Psychology*:
   https://pmc.ncbi.nlm.nih.gov/articles/PMC4732571/
5. Davydenko and Peetz, “Shopping less with shopping lists,” *Journal of Consumer
   Behaviour*: https://doi.org/10.1002/cb.1812
6. Gupta, Oosterhuis, and de Rijke, “A First Look at Selection Bias in Preference
   Elicitation for Recommendation”: https://arxiv.org/abs/2405.00554
7. Amershi et al., “Guidelines for Human-AI Interaction,” CHI 2019:
   https://doi.org/10.1145/3290605.3300233
8. impause App Store listing:
   https://apps.apple.com/us/app/impause-stop-impulse-spending/id6746744026
9. enough. product page: https://enough.app/
10. Spending Sensei App Store listing:
    https://apps.apple.com/gb/app/spending-sensei-ai-budget-app/id6754790513
11. Listonic product page: https://listonic.com/

## 10. Stop statement

The shared conversation has been fully reviewed for product ideas, the ideas have
been compared with Tracks 1–8, material competitors missed by the earlier pass
have been added, and the main new architecture requirement—selection-aware
reflection exposure—has been identified. Additional broad browsing is unlikely
to change the v1 decision. Remaining questions require product use and controlled
experiments, not more desk research.
