You are Research Stream B in a tightly controlled product-research sprint.

Read these files first:

1. `research/research_runs/2026-08-15-premium-mobile-r1/CONTROL.md`
2. `research/research_seed/personal_finance_ai_pre_research_seed.md`
3. `research/research_seed/personal_finance_ai_controlled_research_sprint.md`

Return two clearly separated reports: Track 3 (Data & Financial Knowledge Model)
and Track 6 (Technical Feasibility). Follow the full required output format for
each track.

Track 3 must define the minimum useful ontology, not a database schema. Cover:
transaction, receipt, evidence asset, extraction revision, line item, normalized
product, merchant, account, budget context, recurring pattern, personal-value
feedback, behavioral label, provenance, confidence, corrections, reconciliation,
and historical backfill. Identify relationships, minimum metadata, deterministic
versus inferred responsibilities, and deferrals.

Track 6 must investigate only architecture-changing risks relevant to beginning
implementation after this research. Cover:

- Angular as the preferred frontend, and credible native-store packaging paths
  such as Capacitor/Ionic where supported by current official evidence.
- Supabase as the preferred backend/data platform, including Postgres, auth,
  storage, row-level security, edge/server functions, portability, mobile-client
  security boundaries, cost/limits, and production risks.
- Safe coexistence or migration strategy that preserves an already working
  receipt-ingestion service and its accumulated PostgreSQL-backed data without
  interrupting ongoing capture. Do not design the final architecture.
- Plaid transaction ingestion and security boundary; historical coverage;
  receipt-bank matching; retailer/Amazon/Costco/email history possibilities;
  local-first versus cloud-assisted processing; deterministic accounting; and
  future read-only MCP/tool exposure.
- Apple App Store and Google Play technical/distribution constraints that could
  invalidate a thin web wrapper or require native capabilities.

Treat Angular + Supabase as an owner preference that should be made executable,
while explicitly surfacing evidence that would require a guardrail, coexistence
layer, experiment, or reconsideration. Prefer official documentation and primary
technical sources. Label time-sensitive pricing/limits. Produce a feasibility
matrix, top five technical risks, weekend-safe choices, minimum experiments, and
deferrals. Use no more than 12 high-value sources across the paired workstream
unless absolutely necessary. Do not modify any file. Stop at decision
sufficiency and return only the two finished reports.

Live source access is mandatory. If WebSearch/WebFetch is unavailable, stop and
return a blocker; do not substitute training memory or unverified URLs.
