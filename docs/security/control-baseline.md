# Financial OS — Security and Production Control Baseline

**Status:** Proposed Gate A review baseline  
**Baseline:** `planning-baseline-2026-08-12-r1`  
**Applies to:** Day-one receipt-capture release

## 1. Policy

`MUST` controls are release blocking. `SHOULD` controls require a documented reason if deferred. `LATER` controls are triggered by scope expansion.

An exception to a `MUST` control must name:

- the exact unmet control;
- the credible risk being accepted;
- a compensating control;
- an owner and expiration date;
- explicit product-owner approval.

No exception may silently weaken `REL-001` (zero acknowledged receipt loss), owner-only authorization, private storage, secret handling, or the no-tools AI boundary.

## 2. Day-one mandatory controls

| ID | Control | Verification evidence | Maps to |
|---|---|---|---|
| IAM-01 | Verify Firebase identity token server-side for every private request and enforce an exact server-side owner allowlist. | Integration test for missing, invalid, and non-owner tokens | AUTH-001/002, T-01 |
| IAM-02 | Implement owner session-version invalidation and document provider session revocation. | Old token rejected after version increment | AUTH-004, T-02 |
| IAM-03 | Use separate runtime, queue-invoker, CI deploy, and human identities with minimum roles. | IAM policy snapshot reviewed in Gate B | SEC-003, T-09/11/20 |
| NET-01 | Serve client and public API only over HTTPS; worker ingress is private/authenticated. | Deployment configuration and unauthenticated worker negative test | SEC-001/005, T-09 |
| NET-02 | Restrict CORS to the deployed application origin; reject unsupported content types and state changes over GET. | API security integration tests | SEC-004, T-18 |
| OBJ-01 | Enforce Cloud Storage public-access prevention and uniform bucket-level access. | Policy assertion plus anonymous-object negative test | SEC-002, T-05 |
| OBJ-02 | Generate short-lived, method-specific signed capabilities for server-selected random object names; do not log them. | Wrong method/path and expiry tests; log inspection | UPL-001, T-03 |
| OBJ-03 | At finalize, verify object existence, owner/receipt path, ordered count, byte size, allowed type, and decodable image content. | `IT-UPL-002` fixture suite | UPL-002, T-04 |
| OBJ-04 | Do not configure automatic deletion of original evidence in V1; enable recoverability safeguards selected in infrastructure plan. | Lifecycle/versioning configuration test | RET-001, T-12 |
| API-01 | Validate every request/response against versioned schemas; enforce image count/size and request rate limits before expensive calls. | Boundary and abuse tests | SEC-004, T-04/15 |
| API-02 | Use client-generated submission keys plus database uniqueness for idempotent receipt creation. | Concurrent duplicate test | REC-001, T-08 |
| API-03 | Acknowledge only after object verification, durable receipt state, and durable task creation are completed or recoverably recorded. | Failure-injection test across finalize path | UPL-003, QUE-001, REL-001, T-12/19 |
| QUE-01 | Cloud Tasks invokes the worker with a dedicated OIDC identity and exact audience; direct public invocation fails. | Authenticated task succeeds; forged/direct calls fail | SEC-005, T-09 |
| QUE-02 | Set bounded exponential retry, attempt identity, terminal failure, and stale-work reconciliation. | Retry/idempotency/stuck-job tests | QUE-002, STATE-002, REL-003, T-15/19 |
| DB-01 | Use IAM database authentication/connectors and separate least-privilege API/worker database roles; no credential in source. | Connection configuration and grants inspection | SEC-003, T-11 |
| DB-02 | Use migrations, constraints, transactions, fixed-point/decimal money, append-only provenance, and independent processing/verification states. | Migration, invariant, and state-machine tests | VAL-001/002/003, STATE-001, T-07/08 |
| DB-03 | Enable automated backups and point-in-time recovery where available; perform an initial documented restore smoke test before calling production ready. | Backup configuration and restore record | RET-002, REL-001, T-12 |
| AI-01 | Extraction runtime has no tools, browsing, credentials, arbitrary URL fetching, or action authority. | Architecture/config inspection and adversarial fixture | SEC-006, T-06 |
| AI-02 | Treat document content as untrusted data and require a versioned structured response schema. | Prompt contract and prompt-injection test | EXT-001/004, VAL-001, T-06 |
| AI-03 | Publish model output only after deterministic validation; preserve raw output/provenance and never silently repair evidence. | Malformed and inconsistent output tests | VAL-001/002/003, T-07 |
| APP-01 | Render all extracted text as escaped plain text; never inject raw HTML or activate model-generated URLs. | Stored-XSS fixture and CSP check | T-17 |
| APP-02 | Do not persist receipt images, raw text, signed URLs, or tokens in service-worker caches, analytics, or local application logs. | Browser storage/cache inspection | SEC-007, T-02/10 |
| APP-03 | Use a restrictive production Content Security Policy compatible with required Firebase/Google endpoints. | Response-header assertion and browser console review | T-14/17 |
| LOG-01 | Structured logs use an approved-field allowlist and omit images, receipt text, raw model output, tokens, signed URLs, restricted identifiers, and stack details in client errors. | Automated log snapshot plus manual incident-query review | SEC-007, T-10 |
| LOG-02 | Record privacy-safe auth decisions, state transitions, processing attempts, deployment identity, and configuration version. | Trace one synthetic receipt end to end | REL-003, T-19/20 |
| CICD-01 | GitHub Actions uses Workload Identity Federation/OIDC; no long-lived GCP service-account key. | Repository secret and cloud credential inspection | SUP-001, T-13 |
| CICD-02 | Required CI checks cover unit/integration tests, lint/type checks, dependency vulnerabilities, secrets/private-data patterns, migrations, container build, and infrastructure validation. | Protected-branch check evidence | SUP-001, T-13/14 |
| CICD-03 | Production image is built once, identified by immutable digest, and the deployed revision is recorded. | Release evidence includes commit and digest | T-13/20 |
| OPS-01 | Set maximum service instances, queue retry ceilings, budget alerts, and alerts for failures/stuck work. | Configuration assertions and alert smoke test | REL-003, T-15/19 |
| OPS-02 | Keep real evidence out of source, issues, CI artifacts, screenshots, and public portfolio material; use synthetic fixtures publicly. | Private-data scan and release review | PRD §12.2–12.3, T-10/16 |
| OPS-03 | Document access revocation, secret leak, public-data exposure, and restore actions with named commands/console locations once deployed. | Operator runbook walkthrough | T-02/05/10/12 |

## 3. Strongly recommended shortly after day one

| ID | Control | Target |
|---|---|---|
| SHR-01 | Add automated DB/object inventory reconciliation and orphan cleanup in report-only mode first. | Sprint 2 |
| SHR-02 | Run recurring restore drills and record recovery time/data-loss evidence. | Sprint 2 |
| SHR-03 | Establish a private, manually verified receipt evaluation set and regression thresholds. | Sprint 2 |
| SHR-04 | Add automated dynamic security tests against staging and infrastructure policy checks. | Sprint 2 |
| SHR-05 | Add explicit retention review and deletion/export workflows before indefinite storage becomes operationally costly. | Sprint 2–3 |
| SHR-06 | Define dependency remediation service levels based on exploitability and exposure. | Sprint 2 |
| SHR-07 | Alert on owner allowlist/configuration changes and unusual authorization failures. | Sprint 2 |
| SHR-08 | Create an environment-separated staging project if production testing starts to use real data or more integrations. | Before Sprint 3 |

## 4. Scope-triggered controls

| Trigger | Required control expansion |
|---|---|
| Plaid or bank connection | Token vaulting, webhook authenticity/replay defense, provider permission minimization, unlink/revocation, account-data threat-model revision |
| Gmail/Amazon/browser automation | OAuth scope review, token isolation, phishing/content injection defenses, source-specific sandboxing, account revocation runbook |
| Statements/pay stubs | Restricted-identifier detection, quarantine/redaction pipeline, deletion proof, sanitized analytics contract |
| Multiple users or sharing | Tenant-bound authorization on every row/object, invitation lifecycle, audit visibility, data-subject deletion/export |
| Mac Mini synchronization | Device identity, encrypted channel, replay/conflict rules, disk encryption, backup, patching, inbound network policy |
| Tool-using local LLM | Read-only allowlisted finance API, scoped capability tokens, prompt-injection tests, action denial, network isolation |
| Money movement | Separate high-assurance product/security program; explicit confirmation, transaction limits, fraud controls, immutable audit, incident response |

## 5. Approved logging schema

Production application logs may include only fields needed to operate the system, for example:

- UTC timestamp;
- environment, service, version, and trace ID;
- opaque owner ID hash or constant single-owner identifier;
- receipt UUID and processing attempt UUID;
- endpoint template, HTTP status, latency, and byte count;
- state transition and reason code;
- provider/model identifier and token/latency/cost metadata that contains no content;
- exception class and stable internal error code.

They must not include request/response bodies, object capabilities, identity tokens, email addresses, image bytes/URLs, receipt text, model raw output, account numbers, restricted identifiers, or unsanitized stack/context objects.

## 6. Minimum security headers and browser posture

The deployed client should set and verify:

- a restrictive `Content-Security-Policy` tailored to the exact Firebase Auth and API origins;
- `Strict-Transport-Security` where hosting supports it;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: no-referrer` or an equivalently strict policy;
- a restrictive `Permissions-Policy` that permits only required camera behavior;
- frame denial through CSP `frame-ancestors`;
- no service-worker caching of authenticated API responses or private evidence.

Exact directives are implementation configuration, not assumptions; integration tests must assert the deployed headers.

## 7. Incident quick actions

### Lost or stolen phone / suspected session theft

1. Increment the application session version or disable the allowlisted subject.
2. Revoke Google/Firebase refresh tokens.
3. Review authorization and evidence-read audit events from the suspected time window.
4. Re-enable access only after the owner identity and device posture are restored.

### Leaked signed URL

1. Determine object, method, expiry, and access evidence without copying the URL into logs or tickets.
2. If still valid and material, move/rename the object through an authorized recovery workflow or revoke the relevant signing authority if exposure is broad.
3. Confirm the corresponding receipt and object integrity.
4. Fix the disclosure source and shorten capabilities if required.

### Public bucket/service/database exposure

1. Remove public access immediately using known-good infrastructure configuration.
2. Preserve audit evidence and determine exposure window and accessed assets.
3. Rotate affected credentials/identities and validate all access policies.
4. Notify the owner with known facts, residual uncertainty, and recovery steps.

### Secret or deploy identity compromise

1. Disable/revoke the exact secret or federation binding.
2. Stop unauthorized revisions without deleting evidence.
3. inspect audit logs and artifact/deployment history.
4. restore from a trusted commit and immutable artifact; verify data integrity.

### Suspected data loss or corruption

1. Stop destructive reconciliation and preserve current state.
2. Compare receipt, object, state-event, and processing inventories.
3. Restore into an isolated target and verify before cutover.
4. Record loss window, affected receipts, recovery evidence, and prevention change.

## 8. Day-one release security checklist

### Identity and authorization

- [ ] Non-owner valid Google identity receives `403` from every private API family.
- [ ] Missing/invalid token receives `401`; error response contains no private detail.
- [ ] Session invalidation rejects a previously working token/session.
- [ ] Runtime identities and IAM grants have been reviewed against need.

### Storage and database

- [ ] Anonymous bucket/object access fails.
- [ ] Signed capability expiry, method, and object-bound tests pass.
- [ ] Invalid, oversized, and deceptive image fixtures are rejected.
- [ ] Database is not publicly exposed and uses managed/IAM authentication.
- [ ] Automated backup/PITR is enabled and a restore smoke test is recorded.

### Processing and AI

- [ ] Direct worker call fails; queue-authenticated invocation succeeds.
- [ ] Duplicate create/task execution is idempotent.
- [ ] Prompt-injection and malformed-output fixtures cannot bypass schema/deterministic validation.
- [ ] Model runtime has no tools, credentials, or arbitrary network retrieval.

### Browser and privacy

- [ ] Stored-XSS fixture renders inertly.
- [ ] Security headers are present in the deployed response.
- [ ] Browser storage and service-worker cache contain no private evidence or credentials beyond provider-managed session state.
- [ ] Logs and errors from the full test suite contain no forbidden fields/content.

### Delivery and operations

- [ ] CI required checks pass; no secret or real financial-data fixture is present.
- [ ] Deployment used federated short-lived identity and recorded commit/image digest.
- [ ] Failure, stuck-work, and cost alerts are configured and smoke tested.
- [ ] Access-revocation and restore runbooks have been walked through.

## 9. Release decision

Release is allowed only when:

1. every applicable `MUST` control has verification evidence;
2. the three Gate A reviewers approve the design or all blocking findings are resolved;
3. Gate B implementation review finds no open Critical/High release blocker;
4. the owner completes the real-iPhone acceptance flow with a non-sensitive test receipt before private production use.
