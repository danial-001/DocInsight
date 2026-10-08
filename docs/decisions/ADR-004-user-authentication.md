# ADR-004: User identity and browser authentication

**Status:** approved  
**Decision ID:** D-007  
**Requirement scope:** DL-01 and every owner-scoped API and private-file operation

## Context and alternatives

The specification proposes a custom user model and same-origin Django session cookies with CSRF protection. The owner considered a custom email-based user with sessions (A), Django's default username-based user with sessions (B), and a custom email-based user with JWT authentication (C). The owner asked whether users must have JWTs. Django sessions were explained as a way for the browser to identify the user to the server; neither sessions nor JWTs replace per-object authorization.

## Actual choice

The owner wrote: “We can go with D- 007 A, Ram is 24 GB, and Docker Desktop can be opend”. Option A is approved. No additional rationale is inferred.

## Consequences and limits

The design uses a custom email-based Django user and same-origin session authentication with CSRF protection for browser mutations. The user model must be defined before the first migration. Exact fields, email normalization, account creation/seed behavior, session settings, API error responses, and permission rules still need approval. Standard DRF `SessionAuthentication` returns 403 for unauthenticated denial, while the source specification proposes 401; the API contract review must resolve this. No user model, migration, or login flow exists yet.

## Current implementation reference

D-011 selected AbstractBaseUser/PermissionsMixin; WP-01b-1 implemented User. D-012 A approved standard403 with codes. WP-01b-2 (owner: Approved `WP-01B-2`) implemented sessions/CSRF and verified-account login/session lookup under backend/apps/accounts and config. D-013 supplies fixed eight-hour expiry, D-016 local login throttle and D-017 separate verification/suspension.27 model/API tests passed. Earlier unresolved statements describe the original decision checkpoint; account provisioning, email and UI remain unimplemented. See API_CONTRACT.md and components/accounts.md.