# Execution Packet — {{WORK_ITEM_NAME}}

**Status:** Draft | Approved | In progress | Complete  
**Packet owner:** {{OWNER}}  
**Implementation lead:** {{LEAD_OR_TOOL}}  
**Date:** {{DATE}}  
**Repository revision:** {{COMMIT_OR_ARTIFACT_VERSION}}

## 1. Outcome

When this work is complete, the user or operator can:

> {{ONE_SENTENCE_OBSERVABLE_OUTCOME}}

## 2. Why now

{{WHY_THIS_IS_THE_NEXT_SMALLEST_VALUABLE_SLICE}}

## 3. Canonical inputs

Read these exact artifacts before planning:

- `{{PRD_PATH_AND_SECTION}}`
- `{{ROADMAP_PATH_AND_SECTION}}`
- `{{ARCHITECTURE_OR_ADR_PATH}}`
- `{{SECURITY_OR_DATA_POLICY_PATH}}`
- `{{OTHER_REQUIRED_SOURCE}}`

The packet and listed canonical artifacts are authoritative. Conversation history is supporting context only.

## 4. Accepted decisions

- {{DECISION_1}}
- {{DECISION_2}}
- {{DECISION_3}}

## 5. Scope

- {{IN_SCOPE_1}}
- {{IN_SCOPE_2}}
- {{IN_SCOPE_3}}

## 6. Non-goals

- {{NON_GOAL_1}}
- {{NON_GOAL_2}}
- {{NON_GOAL_3}}

Do not implement non-goals unless a newly discovered condition makes the approved outcome unsafe or impossible. Stop and escalate that condition before expanding scope.

## 7. Constraints and invariants

- {{CONSTRAINT_OR_INVARIANT_1}}
- {{CONSTRAINT_OR_INVARIANT_2}}
- {{CONSTRAINT_OR_INVARIANT_3}}

## 8. Acceptance evidence

| Requirement | Verification method | Required evidence |
|---|---|---|
| {{REQUIREMENT_1}} | {{TEST_OR_DEMO}} | {{OUTPUT_OR_ARTIFACT}} |
| {{REQUIREMENT_2}} | {{TEST_OR_DEMO}} | {{OUTPUT_OR_ARTIFACT}} |
| {{REQUIREMENT_3}} | {{TEST_OR_DEMO}} | {{OUTPUT_OR_ARTIFACT}} |

Completion requires every row to pass or have an owner-approved exception.

## 9. Data and security considerations

**Data classes involved:** {{DATA_CLASSES}}

**Trust boundaries changed:** {{BOUNDARIES_OR_NONE}}

**Secrets or credentials involved:** {{DETAILS_OR_NONE}}

**Required controls:**

- {{CONTROL_1}}
- {{CONTROL_2}}

**Prohibited data in source control, logs, or fixtures:**

- {{PROHIBITED_DATA}}

## 10. Operational considerations

**Deployment impact:** {{IMPACT}}

**Observability:** {{HEALTH_SIGNAL_LOG_METRIC_OR_ALERT}}

**Fallback:** {{MANUAL_OR_TECHNICAL_FALLBACK}}

**Rollback:** {{ROLLBACK_PATH}}

**Migration or backfill:** {{PLAN_OR_NONE}}

## 11. Parallel work plan

| Workstream | Owner/agent | Files or boundary owned | Inputs | Deliverable | Dependencies |
|---|---|---|---|---|---|
| {{WORKSTREAM_1}} | {{OWNER_1}} | {{BOUNDARY_1}} | {{INPUT_1}} | {{OUTPUT_1}} | {{DEPENDENCY_1}} |
| {{WORKSTREAM_2}} | {{OWNER_2}} | {{BOUNDARY_2}} | {{INPUT_2}} | {{OUTPUT_2}} | {{DEPENDENCY_2}} |

Do not parallelize shared schema, contract, or migration edits without one explicit integration owner.

## 12. Required checks

- [ ] Unit tests
- [ ] Integration or contract tests
- [ ] Formatting and static analysis
- [ ] Secret and private-data scan
- [ ] Dependency or supply-chain check when applicable
- [ ] Security review proportional to changed risk
- [ ] Product behavior demonstrated
- [ ] Documentation and decision records updated
- [ ] Deployment, fallback, and rollback verified proportionally

Remove checks that genuinely do not apply and record why.

## 13. Stop and escalate conditions

Stop implementation and return to the packet owner if:

- An accepted requirement conflicts with another canonical artifact.
- A material assumption is false or cannot be validated.
- Safe implementation requires expanding a stated non-goal.
- Real secrets or prohibited private data are discovered in the repository or output.
- A migration, destructive operation, or external side effect lacks authority.
- Acceptance evidence cannot be produced as written.

## 14. Handback contract

The implementation lead returns:

1. Concise outcome summary
2. Exact files and behavior changed
3. Verification commands and results
4. Acceptance-evidence table with pass, fail, or exception
5. Deployment or preview location when applicable
6. Known limitations and residual risks
7. Changed assumptions or newly required decisions
8. Suggested next smallest slice

Do not report completion based solely on generated code.

## 15. Approval

**Packet approved by:** {{OWNER}}  
**Date:** {{DATE}}  
**Conditions:** {{NONE_OR_CONDITIONS}}
