# ADR-008: Gmail OAuth sender connection

**Status:** approved design; permission/dependencies/internal store implemented, OAuth/delivery unimplemented  
**Decisions:** D-019 B, D-020 B, D-021 B  
**Owner instructions:** `D-019 B`, `D-020 B`, `D-021 B`

## Context and alternatives

Real email verification is approved under D-015 C. The owner has no domain. D-019 offered dedicated Gmail SMTP with app password (A) or Gmail API OAuth (B); the owner selected B. D-020 offered an owner-run desktop authorization utility (A) or an owner-only web connection page and Django OAuth endpoints (B); the owner selected B. No further owner rationale is inferred.

## Approved direction

Connect only the dedicated application sender. Use Web OAuth client, gmail.send permission, state protection, offline access and backend-only credentials. This does not add Google login or connect ordinary users' mailboxes. External Testing uses the sender as an explicit test user and requires reconnection when its Gmail-scope refresh credential expires after seven days.

Paid provider budget is $0. Google receives sender/recipient information and the verification message/link, not uploaded documents, application passwords or RAG content. Real sends require approved implementation scope and test recipients. No Google setup or delivery has occurred.

## Consequences and unresolved work

Browser reconnection adds routes, an owner authorization boundary, consent/callback handling and credential persistence. Access tokens are short-lived and held in memory; D-021 B approves an encrypted private backend file on a persistent Docker volume, with its encryption key separate in backend environment configuration. No credential database model is planned. File permissions, atomic replacement, backup/restore and concurrent access need review; losing the key requires reconnection. Exact schema, key management, dependency versions, callback URLs, APIs, UI and owner bootstrap require review before implementation. Provider failures must not leak credentials or bypass verification. No next package approved.

## Sources and implementation references

- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://developers.google.com/identity/protocols/oauth2#expiration
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/identity/protocols/oauth2/resources/best-practices

No implementation references exist yet. Account foundation is documented in components/accounts.md; current continuation is in CURRENT_STATE.md and HANDOFF.md.

## Sender administrator direction (D-027 A)

Owner instruction: `D-027 A`. Require an active verified session plus is_superuser for sender administration. Every trusted superuser qualifies; no single-owner UUID allowlist. Explicit trusted CLI superuser provisioning avoids Gmail bootstrap cycle; ordinary signup cannot grant privilege/verification. No real account created. WP-01b-4 (owner: Approved `WP-01b-4`) implemented CanManageEmailSender and verified synthetic permission/CLI checks; sender endpoints/UI/OAuth remain unimplemented. OAuth state/session binding and secrets policy remain required; this permission does not replace them.
## Implemented permission references

backend/apps/accounts/permissions.py: CanManageEmailSender; tests/test_sender_permissions.py:5 tests; tests/test_admin_provisioning.py:6 tests of existing Django command.58 total account tests passed. No production sender route yet, no real superuser created, no Google setup/calls or provider dependency added. README documents owner-run interactive bootstrap. Existing UserManager unchanged.

Subsequent owner confirmation: "Super user created successfully". Aggregate inspection confirmed one account and one active verified superuser. Provisioning is complete; the earlier no-account statements describe package completion. No real login, Google setup or sender delivery verified. D-028 A dependency pins and D-029 A single-key Fernet/file safeguards approved. Owner later explicitly restored container-wide runtime installation, superseding only the initial venv condition; temporary compiler tooling remains isolated. WP-01b-5 installs approved libraries, not a sender adapter or credential store. Subsequent owner approval of WP-01b-6 authorized storage: SenderCredentialStore/private empty volume/lazy config implemented and verified under ADR-010. OAuth/send implementation still needs its own package approval.
