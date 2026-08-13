# Financial OS — Gate A Synthesis and Disposition

**Artifact version:** `planning-baseline-2026-08-12-r1`  
**Date:** August 12, 2026  
**Operating lead:** Codex  
**Decision:** **Proceed with conditions to Wave 0/Wave 1; production release remains blocked on listed controls**

## 1. Review execution

The original Claude supervisor orchestration produced no reports within the owner's time boundary and was terminated. The gate was recovered using three isolated direct Sonnet processes. Product and architecture completed full frozen-packet reviews. At the owner's explicit direction, the security review was replaced by a strict three-minute, security-critical-artifact review.

| Review | Model/tool | Scope | Verdict |
|---|---|---|---|
| A — Product and delivery | Claude Sonnet 4.6 / Claude Code | Full 14-artifact frozen packet | Approve with conditions |
| B — Architecture and engineering | Claude Sonnet 4.6 / Claude Code | Full 14-artifact frozen packet | Approve with conditions |
| C — Security, production, reliability | Claude Sonnet 4.6 / Claude Code | Owner-authorized timebox; five security-critical artifacts | Approve with conditions |

All reviewers were isolated and did not receive another reviewer's conclusions. Review C is intentionally narrower than the original Gate A protocol; that limitation is accepted by the owner for this gate and does not waive the implementation security checklist or release review.

## 2. Decision rationale

No reviewer found the product incoherent, the architecture fundamentally unsafe, or the one-day vertical slice unbuildable. The design may proceed into preflight and contract implementation.

The security reviewer labeled two implementation gaps High. They do not require redesign and do not prevent Wave 0/Wave 1 work; they are accepted as mandatory production-release conditions. They may not be waived silently. Gate B/C remains closed until they are implemented and tested.

## 3. Mandatory conditions before Wave 1 parallel build

| ID | Condition | Owner | Evidence |
|---|---|---|---|
| P-01 | Benchmark the pinned extraction model and set minimum schema-adherence and arithmetic-computable thresholds. | Operating/implementation lead | Dated benchmark and pass/fail decision |
| P-02 | Complete real-iPhone camera/library/direct-upload spike and adopt an explicit HEIC policy. | PWA/receipt leads | Device result, MIME contract, end-to-end test |
| P-03 | State canonical precedence: PRD/roadmap/architecture/security/execution packet supersede early handoff source documents. | Claude supervisor | Contract-readback confirms no Actual Budget/Plaid/rental day-one scope |
| A-01 | Specify concurrent task idempotency and the successful duplicate-delivery response. | Receipt lead | Concurrent duplicate test: two 2xx, one current revision |
| A-02 | Specify migration as a one-shot pre-deploy job/step; services never migrate concurrently at startup. | Platform lead | Migration/deploy contract and concurrency test |
| A-03 | Define canonical ordered `asset_manifest_hash` algorithm. | Receipt lead | Cross-path deterministic hash tests |
| A-04 | Measure cold-start effect on the ten-second capture target; set one warm API instance if evidence requires it. | Platform lead | p50/p95 decision and cost record |
| S-01 | Bind finalized/processed evidence to immutable GCS object generation and content hash so signed-URL overwrite cannot substitute evidence. | Receipt/platform leads | Replacement/replay negative tests |
| S-02 | Freeze and test a Firebase-compatible CSP with no `unsafe-inline` or `unsafe-eval`. | PWA/platform leads | Deployed header assertion and stored-XSS test |

## 4. Mandatory conditions before production release

- Enforce a worker-side extraction input ceiling and terminal cost circuit breaker.
- Generate `client_submission_key` with `crypto.randomUUID()` or equivalent CSPRNG.
- Add allowlist-change alerting or record an explicit owner-approved, expiring exception.
- Satisfy every applicable `MUST` in `docs/security/control-baseline.md`, including restore evidence.
- Resolve and test all conditions in Section 3.
- Complete Gate B implementation reviews and real-iPhone Gate C acceptance.

## 5. Accepted advisory improvements

These must not delay the first production slice unless evidence elevates them:

- define the implementation session as Waves 1–4, after preflight;
- pre-authorize a lightweight Option B fallback decision if GCP preflight is blocked;
- use enough Wi-Fi/cellular timing runs to compute credible median and p95;
- constrain non-authoritative category suggestions to a versioned vocabulary;
- add stronger allowlist/auth anomaly monitoring after initial release.

## 6. Rejected scope expansion

No reviewer justified pulling Plaid, transaction matching, Amazon/email ingestion, correction UI, analytics, SwiftUI, Actual Budget, rental itemization, or the Mac Mini runtime into day one.

## 7. Final gate status

**Gate A result:** Conditional approval to begin platform preflight and contract implementation.

**Not authorized by this decision:** private-data production use, publication, destructive cloud changes, or declaring the application complete.

**Next action:** Claude implementation supervisor executes Wave 0, records P-01/P-02/A-04 evidence, freezes Wave 1 contracts including all remaining conditions, then launches the three bounded implementation workstreams.

This synthesis preserves all reviewer reports verbatim. Conditions are not recommendations to debate again; they are inputs to the implementation packet and release checklist.
