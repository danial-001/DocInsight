# ADR-003: Local development runtime

**Status:** approved  
**Decision ID:** D-006  
**Requirement scope:** Development environment for the specification MVP

## Context and alternatives

The proposed MVP needs PostgreSQL/pgvector, Redis, an API, worker, and frontend. The owner considered Docker Compose for the services and application (A), Docker services with host-based Python/Node (B), and native or WSL setup (C). The recommendation was A for reproducible setup. Its practical costs include container memory use and requiring a working Docker daemon.

## Actual choice

The owner wrote `D-006 A` in the instruction “`D-005 A, D-006 A, D-007 A`or C, I am not sure, I think everything must be with JWT token for that usr ?”. Option A is approved for local development. The owner did not state an additional rationale; none is inferred.

## Consequences and limits

Compose configuration may be proposed for an approved implementation package. The Docker CLI exists locally, but the daemon did not answer during read-only inspection; RAM is unknown. This choice does not authorize installation, startup, deployment, or changes outside an approved package. No Compose file or service exists yet.
