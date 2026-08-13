# Financial OS — Architecture Index

The architecture is intentionally a portable modular monolith with managed production infrastructure. The system has multiple deployment processes where trust or runtime behavior requires separation, but one canonical domain model and one application codebase.

## Review-baseline documents

- `system-architecture.md` — components, trust boundaries, runtime flows, failures, and Mac Mini transition
- `data-architecture.md` — source-of-truth rules, initial relational model, states, invariants, and evolution
- `technology-recommendation.md` — evidence-based stack recommendation and alternatives

## Canonical related documents

- `../product/PRD.md`
- `../product/requirements-traceability.md`
- `../product/day-one-ux.md`
- `../security/threat-model.md`
- `../security/control-baseline.md`

## Status

These documents are a proposed Gate A review baseline. They are not accepted architecture until the three independent reviews complete and blocking findings are resolved.
