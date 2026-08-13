# Financial OS — Security Index

Security is a product property and a release gate, not a separate future phase. The initial control set is deliberately proportional: it protects identity, private financial evidence, system integrity, and recovery while preserving the approved shipping speed.

## Review-baseline documents

- `threat-model.md` — assets, actors, trust boundaries, credible threats, mitigations, and residual risk
- `control-baseline.md` — mandatory controls, verification evidence, incident actions, and release checklist

## Security boundary

- Restricted identifiers and credentials receive the strictest treatment and are minimized.
- Receipts and financial records are private even though cloud processing is accepted.
- Receipt content and model output are always untrusted data.
- No V1 component can initiate a financial transaction or obtain financial-account credentials.

## Status

These documents are a proposed Gate A review baseline. Day-one `MUST` controls are release blocking unless an explicit, owner-approved exception records the compensating control, expiration, and follow-up owner.
