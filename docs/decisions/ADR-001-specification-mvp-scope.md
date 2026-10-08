# ADR-001: Target the specification MVP

**Status:** approved  
**Decision ID:** D-001  
**Requirement scope:** DL-01 through DL-14 and all P0 release requirements

## Context

The original specification proposed a 15-day MVP. The initial review offered a reduced two-to-three-day text-PDF prototype with explicit P0 deferrals. The owner chose to start with the specification MVP instead. The delivery window was subsequently made flexible.

## Alternatives considered

1. Reduced text-PDF prototype, with significant P0 behavior deferred.
2. Scan-first short prototype, with other P0 behavior deferred.
3. Full specification MVP, built through separately approved packages.

## Recommendation and actual choice

The initial recommendation was the reduced vertical slice because of the short window. The owner's actual instruction was: “I think rather than goining with Initial Prototype, we should start working with Specification MVP,”. This selects option 3 and supersedes the short-prototype proposal. The owner did not state an additional rationale; none is inferred.

## Consequences

No P0 deferrals are approved. Intermediate slices are checkpoints, not the completed MVP. The full work includes OCR, revisions, asynchronous jobs, advanced retrieval, conversations, deletion, feedback, limits, and evaluation. Technology, schema, provider, deployment, and package details remain separate decisions. This decision changes scope, not the authorization boundary for implementation.

## Implementation references

No product code exists. `PROTOTYPE_SCOPE.md`, `IMPLEMENTATION_PLAN.md`, and `REQUIREMENT_TRACEABILITY.md` carry the current plan and status.
