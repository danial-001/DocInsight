# ADR-002: Application stack

**Status:** approved  
**Decision ID:** D-005  
**Requirement scope:** Foundation for DL-01 through DL-14

## Context and alternatives

The specification proposes Django/DRF for the API and React/TypeScript/Vite for the browser. The owner considered that option (A), FastAPI with the same frontend (B), and Django-rendered pages (C). The recommendation was A because it follows the specification's API and interactive workspace design while using Django's authentication and ORM facilities. It requires both Python and Node toolchains.

## Actual choice

The owner wrote `D-005 A` in the instruction “`D-005 A, D-006 A, D-007 A`or C, I am not sure, I think everything must be with JWT token for that usr ?”. Option A is approved: Django/DRF and React/TypeScript/Vite, with compatible dependency versions pinned in lockfiles. The owner did not state an additional rationale; none is inferred.

## Consequences and limits

This approves the stack and pinning approach, not exact package versions, installation, scaffolding, app boundaries, data model, API contracts, frontend state architecture, or implementation of WP-01. Research and propose the exact significant dependencies and versions before installation. No product code exists yet.
