# Premium Mobile Financial OS — Controlled Research Run R1

**Run date:** 2026-08-15
**Owner:** Yemane
**Operating lead:** Codex
**Research runtime:** Claude Code through Vertex AI
**Status:** Tracks 2–8 complete; consolidated with evidence corrections

## Outcome

Produce decision-ready evidence for a premium, downloadable iOS and Android
Financial OS while the existing receipt-ingestion application and its durable
data continue operating unchanged.

The research must make the next PRD and architecture pass faster. It must not
silently become the PRD, architecture, migration plan, or implementation.

## Inputs

- `research/research_seed/personal_finance_ai_pre_research_seed.md`
- `research/research_seed/personal_finance_ai_controlled_research_sprint.md`
- Owner direction from 2026-08-15: treat Angular and Supabase as the preferred
  application direction; target App Store and Play Store distribution; retain
  the working receipt system and accumulated data; permit research to challenge
  assumptions when evidence identifies a material risk.

Existing canonical documents are boundary context only during research. They
remain authoritative for the working application until the owner explicitly
approves a replacement PRD, architecture, decision register, and execution
packet.

## Non-goals

- Modify or deploy the existing application.
- Change production data, schemas, contracts, cloud resources, or credentials.
- Rewrite the PRD, freeze an architecture, or begin implementation.
- Perform an open-ended market scan or copy a competitor.
- Introduce real owner financial content, identifiers, receipt data, tokens,
  provider identifiers, or production resource names into research artifacts.

## Workstreams

| Stream | Tracks | Model | Effort | Budget cap | Research cap |
|---|---|---|---|---:|---:|
| A | 2 — competitive study + differentiation | Sonnet | high | $2.25 | 30 min |
| B | 3 — data model + 6 — technical feasibility | Sonnet | high | $1.75 | 30 min |
| C | 4 — AI evaluation + 8 — product outcomes | Sonnet | high | $1.50 | 30 min |
| D | 5 — human-AI interaction + 7 — trust/privacy/safety | Sonnet | high | $1.75 | 30 min |

**Maximum Claude API spend:** $7.25.
**Maximum research wall clock:** 120 minutes from launch.
**Target machine-research convergence:** 30 minutes from launch.

**Machine-research stop:** 2026-08-15 11:58 CDT / 16:58 UTC.
**Absolute run stop:** 2026-08-15 13:28 CDT / 18:28 UTC.

This run covers Tracks 2–8 only. Track 1 is owned and conducted separately by
Yemane, and consumes no Claude research budget. The global cap includes the four
Claude workstreams, evidence checking, and initial consolidation of Tracks 2–8.
A workstream stops earlier when its stop rule is satisfied. An uncertain question
becomes a named follow-up experiment; it does not extend the run.

## Source and evidence rules

- Use no more than 8–12 high-value sources per workstream unless a narrow claim
  cannot otherwise be verified.
- Prefer primary sources for technical, platform, privacy, security, pricing,
  and product-capability claims.
- Time-sensitive claims must include a source date or access date.
- Every material finding must be marked as observed fact, reasoned inference,
  proposal, or unknown.
- Competitor marketing claims are evidence of positioning or documented
  capability, not proof of internal architecture or effectiveness.
- Never invent inaccessible implementation details. State the evidence limit.
- Use short paraphrases; do not reproduce copyrighted source text.

## Required output for each track

1. Executive Summary — maximum five bullets
2. What We Learned
3. What Best-in-Class Products/Research Do Well
4. What We Should Adopt
5. What We Should NOT Copy
6. Implications for Our Product
7. Implications for Architecture
8. Differentiation Opportunities
9. Risks / Unknowns
10. PRD Changes Recommended
11. Stop Statement
12. Sources — title, publisher, URL, publication/update date when available,
    and access date

Paired workstreams return separate numbered outputs for each assigned track.

## Completion gate

The Tracks 2–8 research run is complete only when:

- Tracks 2–8 have returned or a named blocker is recorded;
- every assigned question is answered, labeled unknown, or converted into the
  minimum follow-up experiment;
- decision-changing findings are separated from background information;
- duplicated findings are removed;
- product ideas are classified as validated signal, hypothesis, future idea, or
  rejected/deferred;
- technical constraints and migration/coexistence risks are explicit;
- Angular, Supabase, mobile packaging, App Store/Play Store distribution, and
  preservation of the working receipt/data path have an evidence-based
  disposition;
- each track includes a stop statement.

Track 1 is a required input to the later whole-product merge, but is not a
completion dependency for this controlled Claude research run.

## Hard stop and escalation

Stop the run immediately if research exposes private data, credentials, real
production identifiers, or a need to modify the working system. Stop an
individual stream when it reaches its 30-minute or budget cap. At 120 minutes,
stop all remaining research, label gaps, and return the smallest follow-up
experiment.

No architecture or implementation work is authorized by this control file.

## Run log

- 11:28 CDT — Four streams launched.
- 11:33 CDT — Stream A disclosed that `dontAsk` permission mode blocked live
  WebSearch/WebFetch and returned a memory-based report. That report was rejected
  as final evidence. Streams B–D were stopped under the same constraint.
- Recovery rule — Relaunch with only `Read`, `WebSearch`, and `WebFetch` tools in
  bypass-permissions mode. Shell and file-write tools remain unavailable. If live
  sources are still inaccessible, the stream must return a blocker rather than a
  memory-based substitute.
- Recovery budget caps — A $1.50, B $1.35, C $1.10, D $1.35 ($5.30 total),
  reserving $1.95 of the original aggregate cap for the rejected/aborted attempt.
  The original machine and absolute stop times do not move.
- Owner authorized up to double the original budget after the first reports
  returned. The operating lead approved only a focused $3.25 addendum: $1.75 for
  a platform/security claim audit and $1.50 for competitive/HCI evidence gaps.
  The expanded ceiling is not a target, and the wall-clock stop does not move.
- Tracks 2–8 and both evidence audits returned before the machine-research stop.
  The decision-ready consolidation is `CONSOLIDATED-TRACKS-2-8.md`. Track 1
  remains owner-controlled and is required before the whole-product PRD and
  architecture merge.
