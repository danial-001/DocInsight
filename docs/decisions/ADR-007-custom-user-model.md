# ADR-007: Custom user foundation and schema

**Status:** approved  
**Decision:** D-011  
**Owner instruction:** `D-011 B`

## Context and alternatives

D-007 approved custom email identity and sessions/CSRF. Before first migrations, choose the user foundation. A offered AbstractUser with username removed; B offered AbstractBaseUser plus PermissionsMixin. A was recommended for less custom code. The owner requested an explanation of differences and selected B; no additional rationale inferred.

## Approved design

Use AbstractBaseUser plus PermissionsMixin with UUID primary key, required email (maximum 254), optional first/last names, is_active/is_staff, inherited is_superuser/groups/permissions, password hash/last_login, explicit creation timestamp and timezone preference. Canonicalize email by trimming surrounding whitespace and lowercasing the full address; unique email plus Lower(email) uniqueness prevents case-only duplicate accounts. Manager implements create_user/create_superuser with Django password hashing. Login uses matching normalization. Timezone is an IANA name (maximum 64, default UTC), validated with zoneinfo; timestamps use aware UTC.

## Consequences and implementation limits

B permits explicit user field design but requires more manager/admin/form integration and verification. No added external dependencies or provider costs. Changing the user foundation after relationships/migrations exist is expensive; adding optional profile fields later is simpler.

No user implementation exists. Exact remaining field lengths/default details belong in the package design; account provisioning, session settings, API contract and migration execution still await approval. No account-deletion feature authorized. This decision approves design, not a work package.

## Implemented foundation

WP-01b-1 owner approval `Approved WP-01b-1`; actual User, UserManager, validators and initial migration in backend/apps/accounts/.13 tests passed and schema applied. Names max150/defaultempty, date_joined UTC now, status defaults and verification field set per approved D-013/D-017 and package. Admin/provisioning UI, endpoints and sessions remain future packages. See accounts component for limits and validation boundaries.
