You are a read-only evidence auditor for a controlled research sprint. Read:

1. `research/research_runs/2026-08-15-premium-mobile-r1/CONTROL.md`
2. `research/research_runs/2026-08-15-premium-mobile-r1/RESULT-B-TRACKS-3-6.md`
3. `research/research_runs/2026-08-15-premium-mobile-r1/RESULT-D-TRACKS-5-7.md`

Return a corrections-and-confirmations addendum only. Do not repeat the reports
and do not design the final architecture. For each audited claim, give:

- claim;
- verdict: confirmed / corrected / rejected / still unknown;
- current primary source URL and date/access date;
- precise corrected wording;
- whether the correction changes a PRD or architecture decision.

Audit these claims specifically:

1. Apple's minimum-functionality rule: distinguish general guideline 4.2 from
   any 4.2.x sub-guideline; do not call 4.2.7 a general thin-wrapper rule unless
   the current source literally supports it.
2. Apple's legal-entity rule for apps handling sensitive financial data and its
   implications for a single-owner app versus a publicly distributed service.
3. Angular + Capacitor support for native iOS/Android projects. Separate
   technical packaging feasibility from App Store acceptance.
4. Supabase RLS: service-role bypass, client-safe publishable/anon keys, what
   `auth.uid()` returning NULL actually does under SQL semantics, and whether an
   explicit `IS NOT NULL` guard is security-critical or clarity/defense-in-depth.
5. Supabase pricing/limits, Edge Function constraints, storage, portability, and
   any claim that the Pro plan must be purchased immediately.
6. Plaid history limit, token flow, server-only secrets/access-token boundary,
   webhooks, Link support in a Capacitor/Angular application, and any special
   mobile-SDK/privacy-manifest implications.
7. Google Play financial-features declaration, Data Safety, privacy policy, and
   account-deletion requirements. Separate a personal finance tracker from
   regulated banking/lending services.
8. Whether an API coexistence layer is supported as the lowest-risk way to keep
   the existing receipt system operating. Treat FDW/cross-cloud database joining
   as unproven unless a source or controlled experiment supports it.

Use only live primary sources from Apple, Google, Capacitor/Ionic, Supabase, and
Plaid. If a source cannot be fetched, say unknown. Never substitute training
memory. Do not modify files. Stop after the audit table, a five-bullet decision
impact summary, and a source list (12 sources maximum).
