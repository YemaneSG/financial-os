# Independent Review — {{GATE_OR_ARTIFACT_NAME}}

**Review ID:** {{REVIEW_ID}}  
**Reviewer charter:** {{PRODUCT_DELIVERY_OR_ARCHITECTURE_ENGINEERING_OR_SECURITY_PRODUCTION}}  
**Reviewer model/tool:** {{MODEL_AND_TOOL}}  
**Date:** {{DATE}}  
**Verdict:** Approve | Approve with conditions | Reject

## 1. Independence declaration

- I reviewed the artifacts listed below in an independent context.
- I did not receive or inspect another reviewer's conclusions before forming this verdict.
- I treated prior recommendations as claims to evaluate, not facts to inherit.
- I did not modify the reviewed artifacts.

If any statement is false, explain:

{{EXPLANATION_OR_NONE}}

## 2. Review scope and immutable evidence packet

**Repository revision or artifact version:** {{COMMIT_OR_VERSION}}

**Artifacts reviewed:**

- `{{ARTIFACT_1}}`
- `{{ARTIFACT_2}}`
- `{{ARTIFACT_3}}`

**Explicitly out of scope:**

- {{OUT_OF_SCOPE_1}}
- {{OUT_OF_SCOPE_2}}

## 3. Independent understanding

In your own words, state:

- The user problem
- The proposed outcome
- The smallest release
- The system or implementation approach
- The critical constraints

{{INDEPENDENT_SUMMARY}}

## 4. Assumptions and unknowns

| ID | Assumption or unknown | Material impact | Evidence currently available | Required validation |
|---|---|---|---|---|
| A-1 | {{ITEM}} | {{IMPACT}} | {{EVIDENCE}} | {{VALIDATION}} |

## 5. Strengths

List only strengths supported by evidence.

| ID | Strength | Evidence | Why it matters |
|---|---|---|---|
| S-1 | {{STRENGTH}} | {{EVIDENCE}} | {{IMPACT}} |

## 6. Findings

Severity definitions:

- **Blocking:** The gate cannot safely or credibly proceed.
- **High:** Must be resolved before this gate unless the owner explicitly accepts the risk.
- **Medium:** Important but can proceed with an owned, testable follow-up.
- **Advisory:** Useful improvement that must not block the stated outcome.

| ID | Severity | Finding | Evidence | Consequence | Required change | Verification |
|---|---|---|---|---|---|---|
| F-1 | {{SEVERITY}} | {{FINDING}} | {{EVIDENCE}} | {{CONSEQUENCE}} | {{CHANGE}} | {{HOW_TO_PROVE_FIXED}} |

Do not write “best practice” as evidence. State the failure, requirement, standard, test, measurement, or reasoning that supports the finding.

## 7. Adversarial checks performed

Record important concerns that were actively evaluated, including those that did not become findings.

| Concern tested | Evidence examined | Conclusion |
|---|---|---|
| {{CONCERN}} | {{EVIDENCE}} | {{CONCLUSION}} |

## 8. Residual risks

| Risk | Likelihood | Impact | Current control | Owner |
|---|---|---|---|---|
| {{RISK}} | {{LIKELIHOOD}} | {{IMPACT}} | {{CONTROL}} | {{OWNER}} |

## 9. Verdict rationale

**Verdict:** {{APPROVE_OR_CONDITIONAL_OR_REJECT}}

**Rationale:**

{{EVIDENCE_BACKED_RATIONALE}}

**Conditions, if any:**

| Condition | Owner | Deadline/gate | Verification |
|---|---|---|---|
| {{CONDITION}} | {{OWNER}} | {{WHEN}} | {{PROOF}} |

## 10. Sign-off

This verdict applies only to the artifact versions listed in this review. Material changes invalidate affected conclusions and require targeted re-review.

**Reviewer:** {{REVIEWER_IDENTIFIER}}  
**Timestamp:** {{TIMESTAMP}}
