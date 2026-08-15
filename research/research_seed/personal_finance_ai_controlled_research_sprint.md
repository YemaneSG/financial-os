# Personal AI Finance Assistant — Controlled Research Sprint Brief

**Purpose:** Run a world-class but tightly bounded research sprint that directly improves PRD v1 and architecture decisions for an Apple App Store-quality personal finance copilot.

## Research Philosophy

This is not an open-ended literature review.

The goal is to answer only the questions needed to:
1. Improve PRD v1.
2. Make architecture decisions.
3. Identify the strongest differentiated product ideas.
4. Start implementation immediately afterward.

## Global Stop Rule

Each research agent must stop when ALL of the following are true:

- Every assigned research question has a supported answer.
- Each major finding has at least one credible source.
- No more than 8–12 high-value sources are used unless absolutely necessary.
- The agent has identified the top 3–5 actionable product implications.
- The agent has identified the top 3 architecture implications, if relevant.
- The agent has identified the top 3 unresolved risks or unknowns.
- Additional research is producing repetition rather than changing decisions.

**Do not continue researching for completeness. Stop when additional evidence is unlikely to change PRD or architecture decisions.**

## Timebox

Recommended maximum per agent: **20–30 minutes of focused research effort**.

If a topic is still uncertain after the timebox:
- state the uncertainty,
- identify the minimum follow-up experiment,
- stop.

## Required Output Format for Every Agent

1. **Executive Summary** — max 5 bullets.
2. **What We Learned** — concise findings.
3. **What Best-in-Class Products/Research Do Well**
4. **What We Should Adopt**
5. **What We Should NOT Copy**
6. **Implications for Our Product**
7. **Implications for Architecture**
8. **Differentiation Opportunities**
9. **Risks / Unknowns**
10. **PRD Changes Recommended**
11. **Stop Statement** — explain why the research is sufficient to proceed.

---

# Research Track 1 — Problem & Behavioral Research

**Owner:** Yem + ChatGPT
**Method:** Structured interview, one question at a time.
**Goal:** Understand real spending behavior, regret, value, impulse, planning, and useful intervention timing.

This track should produce:
- behavioral patterns,
- trigger conditions,
- high-value vs low-value purchase signals,
- useful intervention moments,
- candidate feedback labels,
- first personalized behavior model.

---

# Research Track 2 — Competitive Product Study

**Recommended model:** Claude Opus or Sonnet

**Primary products only:**
1. Monarch Money
2. Cleo
3. Copilot Money
4. Actual Budget / relevant open-source MCP ecosystem

## Controlled Comparison Questions

For every product:
- What problem does it fundamentally solve?
- What data does it ingest?
- How does it enrich transactions?
- Where is AI used?
- Where is deterministic software used?
- How are corrections handled?
- How proactive is it?
- How does personalization work?
- How is uncertainty handled?
- What is particularly polished?
- What should we adopt?
- What should we avoid?

## Special Focus Areas

### Monarch
Study:
- receipt capture,
- image upload,
- receipt extraction,
- itemization,
- transaction matching,
- verification,
- correction,
- email/web receipt ingestion.

### Copilot
Study:
- mobile UI,
- information hierarchy,
- transaction UX,
- proactive insights,
- assistant surfaces,
- visual simplicity.

### Cleo
Study:
- transaction enrichment,
- behavioral intelligence,
- essential vs discretionary logic,
- proactive coaching,
- personalization,
- confidence/model escalation.

### Actual Budget / Open Source
Study:
- local-first design,
- deterministic accounting,
- API/tool boundaries,
- MCP,
- data ownership,
- LLM vs deterministic responsibility.

---

# Research Track 3 — Data & Financial Knowledge Model

**Recommended model:** Sonnet

Goal: define the minimum useful financial ontology for PRD v1.

Research:
- transaction → receipt → line item → product relationships,
- bank/receipt reconciliation,
- recurring purchases,
- categories,
- budget linkage,
- personal-value labels,
- provenance,
- confidence,
- historical backfill.

Deliver:
- recommended domain entities,
- key relationships,
- minimum metadata required,
- what should be deterministic vs inferred,
- what can wait until later.

Do not design a full database schema.

---

# Research Track 4 — AI Evaluation Research

**Recommended model:** Sonnet

Goal: determine how we know the AI is good enough.

Research:
- golden datasets,
- human-verified labels,
- confidence calibration,
- extraction/classification benchmarks,
- behavioral recommendation evaluation,
- regression testing,
- model routing/escalation.

Special requirement:
Design evaluation around **Yem-authenticated history** rather than generic benchmarks alone.

Deliver:
- 5–8 core evaluation metrics,
- minimum golden dataset,
- acceptance thresholds where appropriate,
- failure handling,
- evaluation loop for future releases.

---

# Research Track 5 — Human-AI Interaction

**Recommended model:** Sonnet or Opus

Goal: design an assistant that coaches without annoying, controlling, or overreaching.

Research:
- proactive vs reactive interaction,
- user correction,
- explainability,
- confidence,
- intervention timing,
- notification fatigue,
- recommendation overrides,
- trust calibration.

Special focus:
How should green / yellow / red recommendations be explained?

Deliver:
- interaction principles,
- do/don't rules,
- recommended recommendation format,
- override/feedback flow,
- proactive intervention guidelines.

---

# Research Track 6 — Technical Feasibility

**Recommended model:** Sonnet

Goal: identify only the technical risks that could affect architecture this weekend.

Research:
- Plaid transaction ingestion,
- receipt-bank matching,
- historical transaction coverage,
- historical receipt/order ingestion,
- Amazon / Costco / retailer data possibilities,
- local-first vs cloud-assisted processing,
- MCP/tool exposure,
- deterministic accounting boundaries.

Deliver:
- feasibility matrix,
- top 5 technical risks,
- weekend-safe architecture choices,
- experiments required before committing,
- what to postpone.

Do not produce a full implementation plan.

---

# Research Track 7 — Trust, Privacy & Safety

**Recommended model:** Sonnet

Goal: identify minimum production-minded protections for a private financial application.

Research:
- local storage,
- cloud LLM use,
- bank credentials/token handling,
- Plaid security model,
- App Store privacy expectations,
- logging,
- encryption,
- data deletion,
- user control,
- recommendation safety.

Deliver only:
- must-have controls for v1,
- should-have controls later,
- red lines,
- privacy architecture implications.

Keep it weekend-actionable.

---

# Research Track 8 — Outcome & Product Success Research

**Recommended model:** Sonnet

Goal: define whether the product actually improves financial behavior.

Research:
- financial awareness,
- regret reduction,
- better purchase decisions,
- budget adherence,
- intervention usefulness,
- engagement without addiction,
- long-term personalization quality.

Deliver:
- 5–7 product outcome metrics,
- leading indicators,
- lagging indicators,
- what NOT to optimize,
- simple v1 measurement plan.

Avoid vanity metrics.

---

# Special Differentiation Research Track

This thread must be woven into Tracks 2, 4, 5, and 8.

Study whether similar ideas exist, what can be learned, and how to improve them:

- item-level behavioral classification,
- "would you buy this again?" feedback,
- "did this improve your life?" feedback,
- planned vs impulse labeling,
- necessity vs personal-value distinction,
- regret tracking,
- historical backfill,
- personalized value model,
- green/yellow/red pre-purchase guidance,
- proactive coaching,
- user-authenticated behavioral learning,
- recommendation updates after user disagreement,
- financial just-in-time interventions.

For each concept answer:

1. Does something similar exist?
2. What has worked elsewhere?
3. What usually fails?
4. What is genuinely differentiated here?
5. What data is needed?
6. How can it create value from day one?
7. How does it eventually become actionable through deterministic tools / MCP / LLM interpretation?

---

# Merge Phase

After all research tracks return:

1. Extract only decision-changing findings.
2. Remove duplicate findings.
3. Separate:
   - validated product ideas,
   - hypotheses,
   - future ideas,
   - technical constraints.
4. Compare against the old PRD.
5. Produce PRD v1.
6. Produce architecture v1.
7. Begin implementation.

Research continues later only when new product questions arise.

**Research is not a blocker after this sprint.**
