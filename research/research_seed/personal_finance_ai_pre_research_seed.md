# Personal AI Finance Assistant — Pre-Research Seed

**Date:** 2026-08-15
**Purpose:** Seed document for structured product research before updating the PRD.

## Core Research Direction

The product is evolving from a finance tracker into a private, personalized financial intelligence and behavior-change system.

The research should stay structured and evidence-driven. The eight research tracks previously identified remain the overall framework, but the first two are now assigned clear working methods.

## 1. Problem & Behavioral Research

**Method:** Direct question-and-answer research between Yem and ChatGPT.

This track should focus on Yem's actual financial behavior, motivations, friction points, spending patterns, regret patterns, decision-making, and what kinds of interventions would genuinely help.

The goal is to understand:
- What causes purchases that do not align with Yem's priorities.
- Which purchases create lasting value.
- Which purchases are regretted.
- How planned vs. impulsive purchases differ.
- What information would have changed a purchase decision.
- When intervention would be useful versus annoying.
- What signals can help distinguish necessity, personal value, habit, and impulse.
- How historical purchase feedback can personalize future guidance.

This research should be conducted as a controlled interview, one question at a time.

## 2. Competitive Research

**Method:** Delegate a controlled study to a strong research model such as Claude Opus or Sonnet through Vertex AI.

Do not perform a broad market scan.

Limit the primary comparison set to **3–4 products/projects maximum** so the research stays deep and comparable.

### Initial comparison set

1. Monarch Money
2. Cleo
3. Copilot Money
4. Actual Budget / relevant open-source AI or MCP ecosystem

### Study dimensions

For every product, examine the same questions:
- What problem is the product fundamentally solving?
- What financial data does it ingest?
- How is transaction enrichment performed?
- Where is AI used?
- Where is deterministic software used?
- How are calculations kept trustworthy?
- How are corrections and user feedback handled?
- How proactive is the system?
- How does it surface patterns or anomalies?
- How does it personalize recommendations?
- How does it manage uncertainty?
- How does it handle privacy and sensitive financial data?
- What parts of the product are especially polished?
- What mechanisms are worth adapting?
- What weaknesses or gaps create opportunities for this project?

The goal is to study **mechanisms and architecture**, not merely collect feature lists.

## Specific Competitive Research Notes

### Monarch Money

Priority research area: **Receipt upload and receipt-processing workflow.**

Yem considers Monarch's receipt-upload experience mature and robust and wants to study:
- Capture flow
- Upload UX
- Image handling
- Extraction
- Transaction matching
- Verification
- Error handling
- Correction UX
- Itemization
- Data enrichment
- Confidence handling
- Overall robustness

The intent is to compare Monarch's implementation against the receipt-capture system already built for this project and identify production-quality patterns worth adopting.

### Copilot Money

Priority research area: **UI / UX and interaction design.**

Yem likes Copilot's interface and wants its design approach included in the controlled study.

Research should examine:
- Information hierarchy
- Dashboard structure
- Transaction presentation
- Mobile-first interaction patterns
- Visual simplicity
- Conversational/assistant surfaces
- Proactive financial insights
- How the UI avoids overwhelming the user

### Cleo

Priority research area: **AI enrichment, behavioral intelligence, and proactive coaching.**

Research should focus on:
- How transaction meaning is inferred
- Essential vs. discretionary classification
- Behavioral recommendations
- Personalization
- Confidence and model escalation
- Proactive intervention
- Feedback loops

### Actual Budget / Open Source

Priority research area: **Deterministic financial core + AI tool layer.**

Research should focus on:
- Local-first architecture
- Ledger/accounting model
- Data ownership
- APIs
- MCP integrations
- Deterministic calculations
- LLM/tool separation
- How an AI assistant can safely query financial data without becoming the accounting engine

## Research Principle

The project should not copy competitors.

The research objective is:

> Understand the best current mechanisms, identify why they work, keep deterministic financial truth separate from AI interpretation, and combine those lessons with the project's unique item-level and behavioral-personalization approach.

## Unique Product Direction to Preserve

The emerging differentiation is the combination of:
1. Bank transaction data.
2. Item-level receipt and purchase data.
3. Budget context.
4. Historical personal-value feedback.
5. Behavioral pattern detection.
6. Personalized future purchase guidance.
7. Deterministic accounting and calculations.
8. LLM interpretation and conversational access.
9. Future MCP/tool exposure.
10. Proactive coaching based on the user's own authenticated history.

The product should learn from the user rather than treating generic population assumptions as truth.

## Next Research Actions

- Conduct **Problem & Behavioral Research** as a structured Q&A between Yem and ChatGPT.
- Prepare a **controlled competitive-research prompt** for Opus/Sonnet covering the 3–4 selected products with identical evaluation criteria.
- Continue capturing research decisions before merging them into the main PRD.
