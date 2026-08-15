# Financial OS — Implementation Index

Implementation is organized around observable vertical slices, not technology layers. Every slice has a versioned execution packet, explicit non-goals, requirement IDs, security controls, verification evidence, and a handback contract.

## Current planning baseline

- `sprint-0-1-plan.md` — one-session foundation and receipt-capture delivery plan
- `execution-packets/sprint-0-1-receipt-capture.md` — bounded handoff to the implementation lead
- `execution-packets/sprint-2c-receipt-integrity-discovery.md` — duplicate detection and receipt discovery contract
- `evidence/sprint-2c-receipt-integrity-discovery-2026-08-15.md` — current local verification and remaining release gates

## Gate sequence

1. **Gate A — Plan ready:** three independent reviews of the frozen product, architecture, security, and execution packet.
2. **Gate B — Release candidate ready:** deterministic tests plus independent product, engineering, and security implementation reviews.
3. **Gate C — Private production accepted:** deploy, complete real-iPhone acceptance with non-sensitive evidence, then authorize private receipt use.

No gate is passed by agent consensus alone. The evidence defined in the execution packet controls the decision.
