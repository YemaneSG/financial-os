# Gate A Review C — Security, Production, and Reliability

**Reviewer:** Claude Code (claude-sonnet-4-6), independent  
**Date:** 2026-08-12  
**Timebox:** three minutes  
**Authorization:** owner-authorized time-boxed security review  
**Artifacts reviewed:**
- `docs/product/PRD.md` §6, §12–13
- `docs/architecture/system-architecture.md` §5–6, §9–11
- `docs/security/threat-model.md`
- `docs/security/control-baseline.md`
- `docs/implementation/execution-packets/sprint-0-1-receipt-capture.md`

This reviewer did not read other Gate A reviewer reports.

---

## Verdict: Approve with Conditions

The plan is architecturally sound. Threat coverage is comprehensive, STRIDE-informed, and honestly residual-rated. The MUST-control framework, invariant set, and acceptance-evidence table establish a credible release gate. No finding below makes the plan fundamentally unsafe to proceed to implementation; two HIGH conditions must be resolved before or at release, and three MEDIUM conditions are attached.

---

## Control Adequacy Summary

| Domain | Assessment |
|---|---|
| Owner auth | **Adequate.** Server-side Firebase token verification + immutable owner allowlist enforced on every private request (IAM-01). Session-version revocation documented (IAM-02). Residual medium risk for stolen-device window is explicitly accepted and within acceptable single-owner posture. |
| Private evidence | **Adequate.** Uniform bucket-level access prevention, server-selected random object names, short-lived signed capabilities, finalize-time object verification (OBJ-01–03). HIGH-1 below adds a generation-check gap. |
| Durable acknowledgement | **Adequate.** API-03 and REL-001 require finalization to complete object verification, durable DB state, and durable task creation before the `Receipt saved` acknowledgement. Reconciliation sweep covers stranded transitions. |
| Queue/worker auth | **Adequate.** Cloud Tasks OIDC with exact audience; dedicated invoker identity; private worker ingress; negative test required (QUE-01, T-09). |
| AI untrusted-data boundary | **Adequate.** No tools, browsing, credentials, or URL-fetch authority in extractor (AI-01). Structured versioned schema required; deterministic validation before any result is published; raw output preserved (AI-02, AI-03). |
| Secrets and logs | **Adequate.** Workload Identity Federation / no long-lived keys (CICD-01). Secret Manager for runtime secrets. LOG-01 allowlist schema is specific and correct. Prohibited-field list in execution packet is comprehensive. |
| Backup and restore | **Adequate as specified.** DB-03 is a MUST control requiring documented restore smoke test before production. Execution packet §11 repeats this. Adequate only if this gate is enforced — not waivable. |
| CI identity | **Adequate.** Federated OIDC, protected default branch, required checks including secret/private-data scanning (CICD-01–03, T-13). |
| Failure and cost controls | **Adequate.** Max Cloud Run instances, retry ceilings, dead-letter terminal failure, billing budget alerts, stuck-work age metrics (OPS-01, QUE-02, T-15). MEDIUM-1 below notes a gap in the worker layer specifically. |

---

## HIGH Findings (must resolve before release)

### HIGH-1 — OBJ-03 does not require GCS object-generation verification at finalize

**Threat:** T-03 / REL-001 / OBJ-03  
**Scenario:** The API issues a short-lived signed PUT capability to a server-selected random path. Between capability issuance and finalization, the same signed URL can be used to overwrite the object with different content (e.g., a minimal valid JPEG covering a larger payload). OBJ-03 verifies existence, path, byte size, content type, and decodability — but does not require capturing the GCS object generation at URL issuance and asserting it at finalize. The finalization verification can therefore pass on substituted content that satisfies all listed checks.  
**Required fix:** At signed-capability issuance, record the expected GCS object generation (initially 0 / absent, meaning "not yet written"). At finalization, verify the actual generation matches the post-upload expected generation and matches what is recorded per-asset in PostgreSQL. Worker processing should also pin and verify the generation before reading evidence. Add generation verification to OBJ-03 and the asset data model.

### HIGH-2 — CSP strategy for Firebase Auth SDK not specified; unsafe-inline risk

**Threat:** T-14 / T-17 / APP-03  
**Scenario:** APP-03 requires a "restrictive CSP compatible with required Firebase/Google endpoints" but does not specify how to handle Firebase Auth's JavaScript SDK, which historically cannot be satisfied by a strict `script-src` without either (a) `unsafe-inline`, (b) `unsafe-eval`, or (c) explicit nonce/hash-based loading. An implementation that reaches for `unsafe-inline` to make Firebase work silently negates stored-XSS protection (T-17). Given that the worker extracts and the PWA renders arbitrary merchant text, this is a concrete risk.  
**Required fix:** Before implementation, confirm the exact Firebase Auth SDK loading model for the chosen version and document the CSP directive set that satisfies it without `unsafe-inline` or `unsafe-eval` (nonce/strict-dynamic or enumerated hashes). The deployed CSP must be integration-tested as part of the day-one security checklist.

---

## MEDIUM Conditions (at most three)

### MEDIUM-1 — Worker-layer AI input size ceiling is not a MUST control

API-01 enforces image count and byte limits at intake. However, retried processing tasks read evidence directly from GCS and re-invoke the extractor without an explicit MUST-level re-validation of total input size or token budget. A maximal-size multi-image receipt that repeatedly retries (including via the reconciliation sweep) could generate unbounded AI cost per attempt. OPS-01 and T-15 address this at the aggregate level but not per-extraction call.  
**Condition:** Add a MUST worker-layer control requiring an explicit per-extraction input size ceiling (image count × pixel count or byte total) verified before the extractor is invoked, and a per-extraction circuit-breaker that marks the receipt terminal rather than retrying on cost-limit breach.

### MEDIUM-2 — Client submission key entropy requirement is unspecified

The execution packet requires the PWA to generate "a random client submission ID" but does not specify cryptographic randomness. A non-CSPRNG source increases collision probability and could allow a client to predict or induce key collisions against the uniqueness constraint.  
**Condition:** Specify that `client_submission_key` must be generated with `crypto.randomUUID()` (or equivalent CSPRNG UUID v4) and add this to the PWA acceptance criteria and unit fixture.

### MEDIUM-3 — Owner allowlist and session-version change alerting deferred to Sprint 2

SHR-07 defers alerting on allowlist and authorization-failure anomalies to Sprint 2. During the initial deployment period the only signal for an accidental or unauthorized allowlist expansion is manual IAM log inspection. Given that allowlist expansion immediately grants access to all private financial evidence, this is the highest-consequence silent misconfiguration.  
**Condition:** Either promote allowlist-change alerting to a day-one OPS control or produce explicit owner approval documenting acceptance of the unmonitored gap for the Sprint 0–1 window, consistent with the exception format in control-baseline §1.

---

## Notes on Residual Risk

- **Stolen device / session theft (T-02):** Residual medium risk is correctly accepted. Application session-version revocation is adequate for single-owner posture; provider session revocation is documented as a separate manual step, which is an inherent latency gap but proportionate.  
- **Hallucinated or manipulated AI output (T-07):** Residual medium is correctly accepted. Independent verification state, needs-review promotion, and append-only revision history prevent silent financial-fact mutation.  
- **Permanent V1 evidence retention:** Accepted per PRD §12.6. Access controls, object versioning, and the later retention review (SHR-05) are the correct mitigations.  
- **PII in receipt images (T-16):** Scope-triggered for pay stubs and statements. Day-one receipt scope does not commonly contain SSNs or full account numbers; the scope-triggered control table is correctly structured.

---

*Signed: Claude Code, independent Security/Production/Reliability reviewer, Gate A.*  
*This was an owner-authorized three-minute time-boxed security review of the artifacts listed above.*  
*No other files were modified.*
