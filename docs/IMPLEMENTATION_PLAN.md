# Implementation plan

Status vocabulary: `proposed`, `approved`, `in progress`, `verified`, `blocked`, `deferred`. A proposed package cannot be implemented until its unresolved choices and package scope are approved. Estimates will be refined after environment inspection and decisions; there is no fixed delivery deadline.

| ID | Objective and requirement IDs | Dependencies | Status |
| --- | --- | --- | --- |
| WP-00 | Documentation baseline and traceability for DL-01–DL-14 | Owner approval of documentation structure and package | verified |
| WP-01a | Reproducible Django/React/Compose framework shell; foundation for DL-01–DL-14, no requirement completed | D-005 through D-009 | in progress |
| WP-01b-1 | User schema and six app shells; partial DL-01 | Approved WP-01b-1; D-010/D-011/D-017 | verified |
| WP-01b-2 | Session authentication API; partial DL-01 | Owner: Approved `WP-01B-2`; D-007/D-011/D-012/D-013/D-016/D-017 | verified |
| WP-01b-3 | Verification-token persistence and lifecycle services; partial DL-01 | Owner: Approved `WP-01b-3`; D-017 A/D-018 B/D-023 B | verified |
| WP-01b-4 | Sender-admin permission and trusted bootstrap checks; partial DL-01 | Owner: Approved `WP-01b-4`; D-027 A | verified |
| WP-01b-5 | Approved Gmail dependencies and reproducible lock/build; DL-01 support | Owner: Approved `WP-01b-5`; D-008 B; D-028 A with owner-approved container-wide runtime amendment | verified |
| WP-01b-6 | Encrypted sender credential-store service and private local volume; DL-01 support | Owner: Approve `WP-01b-6`; D-021 B/D-029 A/D-030 A | verified |
| WP-01b-7 | Internal committed OAuth attempt lifecycle; DL-01 support | Owner: `D-033 A; Approved WP-01b-7`; D-027/D-030/D-031 B/D-032 A/D-033 A | verified |
| WP-01b-8 | Encrypted attempt-bound S256 verifier lifecycle; DL-01 support | D-035 A/D-036 B; owner: `D-036 B; Approved WP-01b-8` | verified |
| WP-01b | Authentication, collection ownership, initial schema and private file foundation; DL-01, DL-02, DL-03 | WP-01a; D-007; app boundaries, schema, API and storage decisions | proposed |
| WP-02 | Validated upload, asynchronous PDF/image extraction and OCR, page preview and jobs; DL-03, DL-04 | Parser/OCR, limits, worker, state and retry decisions | proposed |
| WP-03 | Extraction confirmation, source-aware chunks and safe index publication; DL-05, DL-06, DL-11 | Revision, chunking, embeddings, pgvector and concurrency decisions | proposed |
| WP-04 | Collection-scoped retrieval, cited answer, abstention and source viewer; DL-07, DL-08, DL-09, DL-14 | Retrieval, model/provider, citation, source viewer and API decisions | proposed |
| WP-05 | Follow-up conversation, feedback, deletion and race handling; DL-10, DL-12, DL-13 | History, provenance, deletion and quota decisions | proposed |
| WP-06 | Complete frontend paths, accessible states and operational hardening; DL-01–DL-14 | Frontend routes/state/hooks, deployment and security decisions | proposed |
| WP-07 | Reproducible baseline-versus-advanced evaluation, acceptance, documentation and demo; DL-01–DL-14 | Evaluation design and all implementation packages | proposed |

The sequence favors a real end-to-end path by WP-04. Later packages are still required for the full specification MVP. Each row is a planning envelope, not permission for a large uninterrupted build; it can be split into smaller approved work packages after decisions.

## WP-01a proposal — framework and database shell

The following foundation versions were approved under D-008 and resolved during WP-01a: Python image `3.13.15-slim-bookworm`; Django `5.2.17`; Django REST framework `3.18.1`; `psycopg[binary]` `3.3.6`; Node image `24.16.0-bookworm-slim`; React and React DOM `19.3.0`; React type packages `19.3.0`; TypeScript `6.0.3`; Vite `8.3.2`; `@vitejs/plugin-react` `6.1.1`. Python lock-tool alternatives are uv `0.12.22` and pip-tools `7.6.1`. D-009 proposes PostgreSQL 17 with pgvector `0.8.6` as the local database image; PostgreSQL 18 with the same extension is the alternative. These are candidate pins verified from package/release listings, not an installed compatibility test. The selected lockfile and build checks will test the actual combination.

- **Objective:** Verify that the approved Django/React stack can run together under Docker Compose before creating domain migrations.
- **Relevant requirements:** Technical foundation for DL-01–DL-14; no DL behavior is claimed complete.
- **Approved dependencies:** D-005 Django/DRF plus React/TypeScript/Vite with pinned lockfiles; D-006 Compose; D-007 custom email user with sessions/CSRF (implementation belongs to WP-01b).
- **Unresolved decisions:** None within WP-01a. D-008 B and D-009 A approved; WP-01a explicitly approved. Exact app boundaries, user schema, API routes, and frontend navigation remain for later packages.
- **Expected files:** `compose.yaml`, `.env.example`, `.gitignore`, `backend/Dockerfile`, `backend/pyproject.toml`, `backend/uv.lock` or a pip-tools equivalent, `backend/manage.py`, `backend/config/` settings and boot files, `frontend/Dockerfile`, `frontend/package.json`, `frontend/package-lock.json`, Vite/TypeScript configuration, and a minimal `frontend/src/` boot screen; relevant documentation updates.
- **Included:** Reproducible containers for the database, backend, and frontend; minimal startup configuration with no secrets committed; framework boot, database connectivity, and build verification. The frontend screen will state that product functionality is not yet implemented.
- **Excluded:** Custom-user migration, auth endpoints, collection/document models, Redis/Celery, OCR, RAG, provider calls, domain API routes, and public deployment.
- **Acceptance:** Compose configuration validates; PostgreSQL starts with the vector extension available; Django system check and database connection pass; the frontend builds and loads locally; documented fresh-start commands work. Successful checks must be recorded from actual runs.
- **Verification:** `docker compose config`, database readiness and extension-availability query, `python manage.py check`, frontend type/build check, and local browser smoke check. If Docker Desktop is unavailable, record the blocked step rather than changing runtime architecture.
- **Dependencies and risks:** Docker Desktop must be running. First image pulls require network and disk space. Version resolution may reveal incompatibilities; those will be brought back for a decision if they change the approved set.
- **Estimated effort:** 3–5 focused hours after approval, subject to image downloads and environment access.

## WP-00 record

- **Objective:** Persist the working agreement and create an honest, navigable project record.
- **Included:** `AGENTS.md`, `README.md`, and the requested `docs/` structure; initial requirement status, decisions, risks, and handoff.
- **Excluded:** dependencies, scaffolding, migrations, product code, provider calls, deployment, and Git operations.
- **Acceptance:** no proposed architecture is presented as approved; every DL requirement is traceable; current state and handoff identify the next action.
- **Verification:** manually cross-check documents against the source specification and repository; no application tests exist yet.
- **Risk:** documentation can become stale unless updated with every later package.
- **Effort:** initially estimated at 1–2 focused hours; actual time not recorded.
- **Approval:** owner replied `1. Approved` to the documentation structure and WP-00 question.

## WP-01a implementation record

Approved by “Approved: D-009 A and WP-01a”. Actual pip files replace pyproject/uv alternatives. Framework files and locks implemented; command acceptance checks passed. Browser check blocked by tool metadata error, so package stays in progress. No app boundaries, custom-user schema, domain migrations or next package approved. See TESTING_AND_EVALUATION.md and components/development-foundation.md.

## WP-01b-1 proposal — User schema and six app shells

Status: verified. Owner approval: `Approved WP-01b-1`. Requirement DL-01 foundation, not complete user isolation. Depends on approved D-005–D-011, D-013 field details, D-016 password rules, D-017 A. WP-01a browser acceptance still blocked; this backend-only package can proceed independently if explicitly approved, without claiming WP-01a verified.

Objective: implement the approved custom user safely before other application foreign keys, and introduce all six Django app shells.

Expected paths: backend/apps/__init__.py; each accounts/collections/documents/retrieval/conversations/jobs __init__.py and apps.py; accounts/models.py, managers.py, validators.py, migrations/0001_initial.py, tests/test_models.py and supporting package files; backend/config/settings.py; docs/components/accounts.md, DATA_MODEL, ARCHITECTURE, traceability/testing/development/current-state/handoff and interview notes. Supporting small functions documented in accounts component.

Included: AbstractBaseUser/PermissionsMixin User, UUID, normalized required email max254 with exact and Lower(email) uniqueness, optional first/last names max150 default empty, timezone max64 defaultUTC with IANA validation, date_joined awareUTC defaultnow, email_verified_at nullable defaultNone, is_active true/is_staff false, Django password/last_login/permissions. Explicit UserManager creates users/superusers with validation/hashing. Ordinary users default unverified; privileged flags cannot be passed to ordinary create_user. create_superuser is an explicit trusted administrative provisioning operation, marks its email verified and requires active/staff/superuser flags. Reject >128 passwords before hashing; enforce approved validators for provided passwords. Missing ordinary password produces unusable password (cannot log in), not an empty password. Register AUTH_USER_MODEL before generating migrations; enable Django auth/contenttypes plus six shells. No new dependencies.

Migrations: generate/review initial custom-user and built-in auth/contenttype schema, verify plan; apply additive migrations only after checking current database state. If unexpected tables or migration history exist, pause affected work; do not reset/delete. Migration tests use a separate Django-owned test database, not the application database. No account deletion feature or domain foreign-key/deletion choices included.

Excluded: Django admin UI/forms, seed_demo, sessions/login/logout/register endpoints, token model/verification delivery, frontend changes, collections/document/job schema, pgvector activation, providers, public deployment. All remain full-MVP work, not deferrals.

Acceptance/checks: Django system check; migrations build from empty dedicated test DB, makemigrations --check --dry-run reports no drift; tests UUID and defaults, email normalization and case-duplicate DB rejection including bypass path, timezone/invalid email validation, password hash/no plaintext/weak-or-overlong rejection, unusable-password behavior, superuser flag checks, default unverified and independent suspension/verification state. Query migrated local schema without displaying secrets. No claim of cross-user object isolation or complete login behavior. Tests should assert contracts and failures, not mirror implementation.

Risk/effort: migration/model label choices are expensive to reverse; email lowercasing is explicit approved product policy. Docker access needed. No external paid calls. Estimate 2–4 focused hours. Unresolved provider/token/API details are excluded and do not block this package; owner must approve explicit superuser provisioning semantics and package implementation/migration scope together. Next proposal after completion: authentication/registration API package following token/provider decisions.

## WP-01b-2 proposal - Session authentication API

Status: verified. Owner instruction: Approved `WP-01B-2`. Implemented the scope below; 27 account tests passed, system/drift checks passed, additive sessions migration applied and proxy smoke passed. No next package approved. No separate permissions.py needed: standard IsAuthenticated plus verified-account backend supplies the approved gate.

- Objective: enable the approved cookie session lifecycle and verified/active account checks before building owner-only Gmail connection. Relevant requirement DL-01 authentication foundation; domain object isolation remains incomplete.
- Approved decisions: D-007 sessions/CSRF, D-011 User, D-012 403/code distinction, D-013 endpoint/error/cookie contract, D-016 login throttle and password limits, D-017 verification/suspension separation. D-020 owner-connect flow motivates sequencing but is excluded here.
- Unresolved decisions: none within this package. Gmail authorization/permissions/bootstrap, encryption dependency/pins/file details and registration/token schema remain excluded for separate review.
- Expected files: backend/config/settings.py and urls.py; backend/apps/accounts/{authentication.py,permissions.py,serializers.py,services.py,views.py,urls.py,throttles.py,tests/test_auth_api.py}; backend/config/{middleware.py,exceptions.py}; relevant API, architecture, accounts component, data model, traceability, testing, development log, current state, handoff and interview documents. File split may be consolidated if cohesive; no frontend files or external dependency additions.
- Components: serializers validate login data and represent safe user fields; views handle HTTP and CSRF-protected mutations; services coordinate credential checks and Django login/logout; authentication/permissions enforce verified active status on login and existing sessions; built-in Django database sessions persist state. Shared error handling supplies approved envelope and request IDs; login throttle owns only the approved local request limit. Tests exercise HTTP behavior, not helper implementation.
- Included: GET /api/v1/auth/csrf (token/cookie), POST /auth/login (email/password, user/fresh token), GET /auth/me (safe user), POST /auth/logout (204; repeat valid-CSRF logout 204). Canonical email matching, fixed eight-hour expiry without renewal, session/CSRF rotation, no-store auth responses, host-only HttpOnly SameSite=Lax session cookie, Secure exception only for local HTTP. Enable built-in sessions app and session/auth middleware; generate UUID request IDs and safe errors. Unverified/inactive/invalid credentials all generic 400 invalid_credentials; protected missing/invalid sessions 403 authentication_required, CSRF failures 403 csrf_failed, genuine permission failures 403 permission_denied; validation 400 and login throttle 429/Retry-After/rate_limited. Bound login password length at 128 before hashing; use approved LocMemCache 10/minute/REMOTE_ADDR throttle (not durable/atomic abuse protection).
- Migrations: inspect current schema/history, review built-in Django session migration plan and apply additive session migration only. No new domain model or reset; pause if unexpected schema/history appears. API tests use a dedicated Django-owned test database with synthetic users; no production user provisioning or credentials printed.
- Excluded: signup, email verification/resend/delivery, Gmail OAuth/storage, admin/forms/demo seed, owner-connect authorization policy, React UI and new dependencies, collections/private documents/RAG, deployment/push. These remain required future work, not MVP deferrals. Synthetic test users are not real registration or email delivery.
- Acceptance: verified active users can log in, fetch only their own safe profile and log out. Unknown/wrong/unverified/inactive accounts share credential failure contract. Suspension or loss of verification blocks existing sessions. Fixed expiry and rotation are demonstrable; missing/invalid CSRF blocks login/logout; no password/hash in responses, all auth responses no-store, errors contain matching request IDs. Throttle returns agreed 429 behavior and ignores spoofed forwarded IP. Logout invalidates prior session.
- Verification: Django check; migration-plan review; account model plus API tests using enforce_csrf_checks=True and controlled expiry/clock; inspect cookie attributes and response contracts; independent clients for session separation; makemigrations --check --dry-run. Test expired session, unusable password, overlong password and CSRF rotation. Confirm basic endpoints through local proxy without logging tokens/passwords. Frontend visual/browser acceptance is outside this API package and the earlier WP-01a browser gate stays unverified.
- Dependencies/risks: Docker/database availability; correct middleware ordering and explicit anonymous CSRF enforcement; local proxy may group throttle IPs. Existing model tests previously passed, no new tests run for this proposal. No provider calls or costs. Estimated 3-5 focused hours including verification and documentation; not a promised deadline.
- Next proposed package: review registration/verification schema and API, then a small implementation package. Owner-only sender setup and UI follow their remaining decisions; no implicit authorization from approval of this package.
## WP-01b-3 proposal - Verification-token persistence and lifecycle

Status: verified. Owner instruction: Approved `WP-01b-3`. Token model/lifecycle,20 new tests and additive migration implemented. Full47-test account suite, system/drift checks and local constraint inspection passed. No HTTP/provider/UI implementation or next package approved.

Objective: implement approved token schema and internal issuance/consumption rules independently of still-unresolved Gmail/API/UI details. Relevant DL-01 verified-account foundation plus owner-added D-015 C; not completed real email verification. Depends on WP-01b-1/2 and D-017 A/D-018 B/D-023 B. D-024 A inline delivery remains design only and excluded here.

Unresolved decisions: none inside this package. Provider dependency pins/setup, exact timeouts/diagnostics/failure responses, HTTP registration/verification/resend contracts and frontend link transport remain outside scope for later review. No P0 feature deferred.

Expected files: backend/apps/accounts/models.py (EmailVerificationToken), migrations/0002_emailverificationtoken.py, verification.py (issue_verification_token, consume_verification_token and small domain errors), tests/test_verification.py; docs/decisions/ADR-009-email-verification-tokens.md, DATA_MODEL.md, components/accounts.md, ARCHITECTURE.md, API_CONTRACT.md (internal capability only), REQUIREMENT_TRACEABILITY.md, TESTING_AND_EVALUATION.md, DEVELOPMENT_LOG.md, IMPLEMENTATION_PLAN.md, CURRENT_STATE.md, HANDOFF.md and INTERVIEW_GUIDE.md as relevant. No frontend, dependency or auth-route changes.

Components: model stores digest and lifecycle state with approved constraints; issuance service accepts an existing user identity, locks User first, checks unverified state/cooldown, revokes outstanding old record and creates a one-hour token. Raw token comes from32 random bytes and is returned only to trusted calling code in memory for eventual delivery, never stored/logged/HTTP-returned. Consumption service accepts a raw token, identifies/locks User then rechecks token state/expiry under transaction, marks used and sets email_verified_at. Neither service sends email, creates/logs in accounts or accepts HTTP requests. Django transactions/PostgreSQL enforce concurrency; standard-library secrets/hashlib supply token generation/hash, no dependencies.

Included schema: UUID id; required ForeignKey User PROTECT; unique lower-case64-hex SHA256 token_digest; created_at/expires_at awareUTC; nullable consumed_at/revoked_at. DB checks expiry after creation and not both consumed/revoked; partial unique user constraint where both null (at most one outstanding row, including expired until revoked); user/created_at index. Digest format validated by model/service. Retain issuance history, no automatic cleanup/account deletion authorized.

Included lifecycle: one-hour expiry; one successful use; resend revokes old outstanding row (including expired),60-second issuance cooldown even after uncertain future send failure. Already verified users receive internal no-issuance result with no changes; unknown/expired/used/revoked/malformed links share safe internal invalid-link error, no plaintext echo. Successful proof may set verification on an inactive account but never changes is_active, preserving suspension. No automatic login. If verification is already present, consume performs no second success. No database locks held around any external operation (none exist here). Use consistent User-first lock order for issuance/consumption, recheck eligibility after locking; old link cannot verify a different account.

Migrations: inspect local table/history state, generate/review only additive token model migration and plan; apply after expected schema confirmed. No reset, deletion or data rewrite. Concurrency checks use Django-owned test_docinsight only after confirming it is not unrelated existing work; database created/migrated/destroyed by tests.

Acceptance: issued secret absent from stored data; one-hour server expiry; no issuance for verified user; cooldown; latest link only; one successful consumption; invalid links leave account/token unchanged; suspension preserved; DB unique/check/PROTECT rules enforced; failed operation rolls back token replacement; competing resends produce at most one issued outstanding link and competing confirmations at most one success.

Verification: account regression tests plus focused token tests; TransactionTestCase with independent DB connections and bounded thread synchronization for actual PostgreSQL resend/consume concurrency; migration plan/schema inspection; Django system check and makemigrations --check --dry-run. Test expiry boundary (now >= expires_at invalid), rollback, duplicate digests, outstanding constraint including expired records, timestamp/state checks and protected user deletion. No provider/email fixture needed: these are internal lifecycle tests, not simulated delivery or inbox success. No browser check applicable; WP-01a browser gate remains unverified.

Excluded: registration/verification/resend HTTP endpoints, per-IP HTTP throttles (existing approved policies unchanged), Gmail OAuth/storage/delivery, delivery diagnostics/automatic retries, admin/seed, confirmation UI, retention/cleanup, public release and all document pipeline work. Real delivery still required in later package; no claim of completed registration/end-to-end verification from this internal slice.

Dependencies/risks: Docker/PostgreSQL availability; lock ordering and concurrency deadlocks; token table PROTECT blocks implicit user deletion pending explicit future cleanup design; issuance history growth. No provider costs/calls/dependencies. Estimate2-4 focused hours including tests/docs, not a deadline. Next: review result, resolve precise registration/verify/resend/delivery contracts, then propose their package; owner Gmail setup can be separately scoped after remaining approvals.
## WP-01b-4 proposal - Sender-admin permission and trusted bootstrap checks

Status: verified. Owner instruction: Approved `WP-01b-4`. CanManageEmailSender and11 new tests implemented; full58 account tests, system check and no-drift check passed. Existing manager/command reused without changes. No real account provisioning, migration, provider or production-route changes. No next package approved.

Objective: establish the approved sender-administration authorization boundary and verify existing trusted CLI provisioning before adding OAuth credentials/endpoints. Relevant DL-01 and D-020 B owner-only sender direction. Depends on verified WP-01b-1/2/3, D-007/D-011/D-012/D-017 and D-027 A. Unresolved choices: none inside package; Gmail dependencies/pins/file details/timeouts/diagnostics/endpoint/UI contracts remain excluded.

Expected files: backend/apps/accounts/permissions.py (CanManageEmailSender), tests/test_sender_permissions.py, tests/test_admin_provisioning.py; docs/components/accounts.md, API_CONTRACT.md (no new production API), ARCHITECTURE.md, TESTING_AND_EVALUATION.md, REQUIREMENT_TRACEABILITY.md, DEVELOPMENT_LOG.md, IMPLEMENTATION_PLAN.md, DECISION_LOG.md, CURRENT_STATE.md, HANDOFF.md, INTERVIEW_GUIDE.md and README.md as relevant. No migrations, packages or frontend files. Existing manager touched only if command integration reveals ordinary bugs within approved provisioning semantics.

Component explanation: DRF permission accepts request.user and returns whether authenticated/active/verified/superuser; owns only sender-admin eligibility, relies on existing backend/session/CSRF for identity. Future OAuth endpoints will reuse it; no sender route introduced here. Django's existing createsuperuser command already uses UserManager.create_superuser, deliberately hashes/validates password and marks trusted admin verified. Reuse this built-in command; no redundant custom bootstrap service/management command.

Included: CanManageEmailSender permission and tests using a test-only protected DRF view plus real session authentication/CSRF. Deny anonymous, ordinary verified, staff-only, unverified and suspended users; allow only verified active superuser. Dropping superuser flag or eligibility blocks subsequent requests. Keep errors403 authentication_required versus permission_denied/csrf_failed consistent with existing contract; no privilege flags added to current user responses. Verify built-in createsuperuser integration using only synthetic credentials in isolated test DB, including normalization/hash/verified-active flags and weak-password/duplicate rejection without mutating existing accounts. Document owner-run interactive docker compose exec backend python manage.py createsuperuser (TTY, no -T). Never request passwords in chat/CLI arguments or print them.

Real owner provisioning: not performed automatically. Owner subsequently confirmed "Super user created successfully"; aggregate inspection found one account and one active verified superuser. Do not seed/reset/promote the existing account or invent account email. Real login remains unverified. D-028/D-029 now approved; WP-01b-5 proposed below. OAuth/delivery contracts remain later review.

Acceptance: permission verified against role/status matrix and real session request behavior; ordinary/staff users cannot act as sender admin, revocation takes effect next request, allowed mutations still require CSRF. Built-in command synthetic integration passes approved manager validation/trusted behavior; documented interactive setup needs no Gmail connection and preserves existing accounts. No production sender route or functional Connect Gmail feature claimed from this slice.

Verification: confirm separate test DB absent/owned, run account regression plus focused permission/CLI integration tests; Django check and migration drift check (no migration expected). All fixtures synthetic, not real email identity proof or delivered email. No browser/provider checks apply; WP-01a browser gate remains unverified. Only tests write accounts, test DB removed by Django.

Excluded: real owner account creation, Django admin UI, seed_demo, signup/verify/resend HTTP, sender/OAuth endpoints, credentials/encryption/file storage, Google project setup/calls/sends, React UI, new dependencies, domain data/features, push/deployment. These remain full-MVP work; no P0 deferral.

Risk/effort: every superuser receives sender access; ordinary registration must never grant that flag (D-025 contract). Guard is not attached to a real sender endpoint until that endpoint is approved/implemented, so current acceptance is foundation only. Docker/PostgreSQL needed; no provider cost. Estimate1-2 focused hours including checks/docs. After owner review, propose Gmail integration dependency/storage/API/delivery decisions and a separate package.


## WP-01b-5 - Gmail dependencies and reproducible container installation

Status: verified. Owner instruction: Approved `WP-01b-5`. Owner subsequently explicitly confirmed returning to the previous container-wide runtime installation, superseding only the runtime-venv condition. Objective: install/verify approved Gmail dependencies and reproduce their hash lock. Relevant DL-01 support and specification sections4/9/14 reproducible dependencies; email verification is an owner-approved extension, not a newly completed DL requirement. Lock/build/import/pip/Django/drift checks and all58 account tests passed; live administrator preserved. No new product route/behavior, migration or provider call. No next package approved.

Approved decisions: D-005/D-006 Docker Django stack; D-008 B pip-tools exact/hash locks; D-028 A google-auth2.61.0/google-auth-oauthlib1.5.0/requests2.34.2/cryptography50.0.2 and explicit container-wide runtime amendment recorded in DECISION_LOG.md. D-029 A approved but storage implementation excluded. No unresolved choice inside this package; materially incompatible pins require owner review, not silent substitution.

Expected changed files: backend/Dockerfile, backend/requirements.in and requirements.txt; a small scripts/Compile-BackendRequirements.ps1 helper if needed for repeatable container-based lock generation; README.md, docs/components/development-foundation.md, docs/decisions/ADR-005-foundation-dependencies.md and ADR-008-gmail-oauth-sender.md, DECISION_LOG.md, REQUIREMENT_TRACEABILITY.md, TESTING_AND_EVALUATION.md, DEVELOPMENT_LOG.md, CURRENT_STATE.md, HANDOFF.md and this plan. Tool lock changes only if resolution requires corresponding approved tool dependencies; preserve pip-tools7.6.1. No model/migration/product HTTP/frontend change.

Included: install approved runtime packages with hash-locked pip requirements into dedicated backend image's main Python, retaining previous /usr/local layout outside /app bind mount. Use a separate temporary container /opt/lock-venv for pip-tools and dependencies when compiling locks; no host-global pip or Windows venv installation. Optional trusted public CA bundle is mounted read-only for tooling and as a temporary BuildKit mount for image downloads; verification never disabled. Rebuild/recreate backend only, preserving database/files/owner account. Explain container runtime versus isolated compiler environment in foundation documentation.

Excluded: Fernet credential service/volume/key generation, Google project/consent/OAuth endpoints, real token refresh/email calls, registration HTTP/UI, frontend dependencies, database migrations, worker setup and deployment. Installing libraries alone is not working Gmail integration. No fake delivery substituted.

Acceptance after owner amendment: runtime dependencies import from container /usr/local Python and site-packages, not a host location or runtime venv. Tooling compiler runs from isolated venv. Approved exact pins and hash lock consistent; pip check/system/no-drift checks pass; backend healthy and existing account regression suite passes; owner account preserved. No secrets emitted. No new behavior tests needed for package installation itself.

Verification: inspect lock diff and dependency versions; build backend with hashed install; inspect interpreter/pip/site-package locations and imports; run pip check, manage.py check, makemigrations --check --dry-run and test apps.accounts in dedicated Django-owned test DB after safety precheck. Confirm backend health and aggregate live account eligibility after recreate without identity/credential output. Record actual results and blocked/unrun checks; browser acceptance remains separately blocked.

Dependencies/risks: Docker/network access, Linux wheels for approved Python3.13, compatible transitive resolution, image rebuild may briefly interrupt local backend. Container packages must be readable/executable by app UID10001. No paid service cost; local build/download overhead only, no claimed performance benefit. Estimated effort1-2 focused hours including verification/docs. Next proposed scope after completion: credential-store service once its remaining integration boundaries are ready, followed by separately reviewed OAuth endpoint/state and email-delivery contracts.

## WP-01b-6 proposal - Encrypted sender credential store

Status: verified. Owner instruction: Approve `WP-01b-6`. Focused27/full85 tests and Compose/build/system/pip/no-drift/permissions checks passed. No next package approved. Objective: reusable backend-only encrypted file storage for the eventual Gmail sender, with safe concurrent operations. Relevant DL-01 support/owner-added verified registration and specification section10 secrets; no complete DL requirement delivered by this internal slice.

Approved dependencies: D-019 B dedicated sender/data exposure, D-020 B web direction, D-021 B encrypted private volume, D-028 A installed libraries, D-029 A Fernet/file safeguards, D-030 A record/limits/generation-checked short writes/empty marker. Unresolved inside this package: none. Remaining OAuth/API/provider/UI choices are explicitly excluded. No new library/provider/database-schema decision inside this proposal. Owner separately approved this package; D-030 alone did not authorize implementation.

Component explanation: implemented apps/accounts/sender_store.py receives configured private directory, separate Fernet key, expected client ID and validated credential/operation input. Returns a decrypted record only to trusted backend callers or safe domain errors. Owns schema validation/encryption/filesystem permissions/atomic persistence/coordination, depends on installed cryptography and Linux standard-library file APIs. Does not authenticate users, run OAuth, refresh access tokens, send messages or own account models. Future protected services call it after authorization. Models/serializers/views/tasks and React hooks are not added by this package.

Expected files: backend/apps/accounts/sender_store.py, tests/test_sender_store.py, backend/config/settings.py (optional store configuration), backend/Dockerfile (app-owned private directory), compose.yaml (backend-only named sender volume/config), .env.example (dummy/blank key only), docs/components/gmail-sender-store.md, ADR-008 and decision log/architecture/API-contract notes (no routes), README, plan/traceability/testing/development/current-state/handoff/interview/checkpoint documents. No dependency-lock change/migration/frontend/product endpoint. Implemented interfaces: SenderCredentialStore.read/replace/clear, SenderCredential and SenderState; see component documentation.

Included: strict encrypted record per approved D-030, single-key Fernet, stable Linux advisory lock with bounded acquisition, private directory0700/files0600, same-directory encrypted temporary file plus fsync/atomic replacement and safe failure cleanup. Failed/corrupt/unknown records preserved; no plaintext fallback or blind reset. Mount named sender volume only into backend at /var/lib/docinsight/sender; image initializes directory for existing app UID10001. Inspect any existing volume before writes; do not chmod/reset unknown stored credentials. Missing key leaves sender service explicitly unconfigured without breaking existing account API startup. Do not generate/alter real .env keys here; provide owner setup/recovery instructions for separately approved real connection. Synthetic tests pass temporary keys directly, never write real Google credentials. A clear operation, if selected, is exercised only on synthetic test data; no actual disconnect/deletion/reset.

Excluded: Google client JSON mount/project/consent/identity checks, HTTP sender status/connect/callback/disconnect, network refresh/send, public signup/resend/confirm, delivery diagnostics, UI/hooks, paid calls, key rotation/backup automation, real credential/key provisioning, document/private-media feature or deployment. No simulated provider/inbox delivery; synthetic storage fixtures explicitly labelled.

Acceptance: encrypted roundtrip and persistence between independent store instances; credential/key absent from plaintext files/error/repr output; private permissions and backend-only mount verified; approved generation-checked write outcomes preserved; tamper/wrong/missing key/client mismatch/oversize/schema errors safe and leave existing bytes unchanged; pre-publication write failure preserves old valid file; two-second lock timeout bounded; existing58 account regressions/system/no-drift pass and live administrator unchanged. Stale refresh/reconnect after clear cannot restore credentials; concurrent conditional writers have one winner. Initial missing record differs from generation-bearing empty marker. Process failure/power-loss guarantees must be described narrowly; no exactly-once network/delivery claim.

Verification: tests with synthetic secrets in isolated temporary directories and separate processes for real Linux lock behavior, bounded synchronization/deadlines, failure injection before atomic replacement, restart-style reread. Inspect new empty runtime volume permissions/mount without putting fixtures in production credentials.enc. Backend rebuild/recreate if needed preserves other volumes; run compose quiet config check/system/no-drift and account regressions after safe test-DB precheck. Record unrun/blocked outcomes; no Google/browser requirement in this internal package. Do not perform whole-host crash or real secret/log tests.

Risks/dependencies/effort: Linux container APIs (not native Windows backend execution), named-volume ownership, key loss, malformed stored records, process coordination and uncertain post-replace durability failures. Key remains separate environment configuration; image/host compromise still exposes decryptable credentials. Estimated2-4 focused hours including tests/docs, no provider fee. Actual store integration still depends on later OAuth/delivery contracts. Next: owner review result, approve protected OAuth API/state contract and real Google setup package.

## WP-01b-7 proposal — internal OAuth attempt lifecycle

Status: verified. Owner instruction: `D-033 A; Approved WP-01b-7`. Model/service/migration and27 new tests implemented; focused27/full112, Django/no-drift and schema/postchecks passed. No next package approved.

**Objective/requirements:** implement temporary connection proof and one committed claim before future Google exchange; DL-01 support and specification sections6/7/9/10. This is not complete Gmail connection or full DL-01 acceptance.

**Approved dependencies:** verified WP-01b-1 through6; D-020 B web direction, D-027 A administrator boundary, D-030 A store generations, D-031 B dedicated attempts and D-032 A ten-minute/exact-session/single-use/latest-pending policy.
**Unresolved inside package:** none after D-033 A approval. Provider/API choices remain excluded, not implicitly approved.

**Expected product files:** backend/apps/accounts/models.py (OAuthConnectionAttempt); migrations/0003_oauthconnectionattempt.py (expected next additive migration, verify actual numbering); oauth_attempts.py (create_oauth_attempt/claim_oauth_attempt and small immutable results/safe errors); tests/test_oauth_attempts.py. Reuse existing User/session/store interfaces; no lock/dependency/frontend/settings changes expected.
**Expected documentation:** ADR-011, components/gmail-oauth-attempts.md, DATA_MODEL.md, API_CONTRACT.md (internal only), ARCHITECTURE.md, plan/decision/traceability/testing/development/current-state/handoff/interview/checkpoint docs and README as relevant.

**Component explanation:** model stores digests/session binding/client context/expiry/lifecycle/generation and enforces DB constraints. Service accepts trusted current user/session/state/client/generation inputs, checks live session/account, coordinates short committed transactions and returns either ephemeral issuance secret or claimed context. Depends on Django/PostgreSQL and standard-library secrets/hashlib; no provider adapter. Future protected views will call it, future exchange operates afterward and honors stored generation. No serializers/views/tasks/hooks introduced.

**Included:** approved D-033 A design; validate live session authentication/expiry/account eligibility; unique pending slot across sessions; new start supersedes prior pending; one atomic claim, safe expiry/replay/mismatch errors; generation/client snapshot; secrets hidden from repr/error/persisted fields. Services require outermost commit and cannot be used inside an outer transaction. No Google code stored. Existing claimed attempts remain claimed; new start does not cancel in-flight work.

**Excluded:** sender HTTP/status/connect/callback/disconnect or errors, CSRF endpoint integration, PKCE/provider transport/real Google project/configuration/authorization/exchange/send, real key generation/store writes, React/auth UI, signup delivery, cleanup/retention automation, paid calls, dependency upgrades and document features. No fake Google provider introduced.

**Acceptance criteria:**
1. Approved fields, constraints/indexes/deletion policy exist; only additive migration, existing administrator/schema/data preserved.
2. Random raw state is returned only in trusted memory; DB has digest not secret, no raw session key or provider credentials; static errors/result repr do not expose secrets.
3. Current active/verified/superuser and exact live authenticated DB session required at start and claim; expired/deleted/rotated/wrong-user/password-invalidated session and changed role rejected.
4. Ten-minute boundary enforced; pending replacement includes expired unmarked prior rows; other admins unaffected; invalid/mismatched caller cannot burn another valid attempt.
5. Duplicate concurrent claims yield exactly one successful claim. Concurrent starts leave at most one pending state; claim-versus-start has a valid serialized result with no revival.
6. Failed issuance rolls back supersession; successful claim committed before return and cannot be undone by later provider failure; nested transaction calls rejected. Captured UUID/None and client ID preserved/checked.
7. Existing account regression suite/system/no-drift checks pass. Synthetic fixtures do not claim Google/inbox success.

**Verification plan:** inspect local table/migration/aggregate counts and confirm separate test DB safety; generate/review additive migration and migrate plan; apply only expected new table once approved. Unit/schema/session integration and TransactionTestCase real PostgreSQL concurrency checks with bounded synchronization/independent connections; constraints, deletion-policy, rollback, commit/nesting tests. Full account suite, Django check, migration drift and live aggregate postcheck. No browser/provider check appropriate to internal-only slice; prior browser gate stays unverified.

**Dependencies/risks:** Docker/PostgreSQL, safe User→Session→Attempt lock order, commit boundary, session invalidation, retained metadata/deletion policy. History growth without cleanup documented; no complete audit/provisioning/delivery claim. Generation is an input snapshot, not a database/file distributed transaction; future publication must still use store CAS. Estimated2-4 focused hours including docs/checks, refined if session/concurrency work proves larger. No new service fee.

**Next action:** owner review of verified package, then small-batch protected OAuth API/transport/provider decisions and a separate package. No next implementation approved.

## WP-01b-8 proposal — internal PKCE verifier lifecycle

**Status:** verified. Owner instruction: `D-036 B; Approved WP-01b-8`. D-036 B resolved the shape constraint. D-034 A/D-035 A approved via owner instruction `D-034 A, D-035 A`; directions alone do not authorize code.

**Objective/requirements:** extend existing internal attempts with encrypted, attempt-bound S256 verifier lifecycle; DL-01 support/specification sections6/9/10. No actual Google authorization/exchange or complete Gmail connection.

**Approved dependencies:** verified WP-01b-7/model/session/transaction/store foundations, D-028 installed cryptography, D-029 A/D-033 A/D-035 A. D-034 callback direction informs future use but no callback here.
**Unresolved:** none within WP-01b-8; D-036 B approved. Callback/provider/HTTP choices remain outside this package.

**Expected product files:** backend/apps/accounts/models.py; migrations/0004_<pkce-name>.py (verify actual numbering); new oauth_pkce.py; oauth_attempts.py; tests/test_oauth_pkce.py; tests/test_oauth_attempts.py updated with synthetic configured keys and lifecycle assertions. No dependencies/settings/Compose/frontend/HTTP changes expected. Existing optional GMAIL_CREDENTIAL_ENCRYPTION_KEY used lazily, real .env untouched.

**Expected docs:** ADR-012/011 and existing gmail-oauth-attempts component (supporting crypto helpers explained there, no redundant component file), DATA_MODEL/API/ARCHITECTURE/plan/decision/traceability/testing/development/current-state/handoff/interview/checkpoints/README as relevant.

**Components/interfaces:** model adds encrypted verifier field/selected constraint. oauth_pkce.py owns random verifier/S256 transform and strict context-bound Fernet envelope validation only, no persistence/HTTP/provider. oauth_attempts.py keeps account/session/lock/commit rules and coordinates encrypted-field creation/clear; issuance gains challenge/method, claim gains repr-hidden raw verifier. Inputs/outputs/key/error/expiry/supersession and rollback behavior per D-036. Missing config fails only attempted OAuth operations; existing session API starts.

**Included:** D-036 once approved; field/additive migration; bounded/versioned attempt-bound ciphertext; same10-minute/session/admin/latest-pending/single-claim rules; clear ciphertext on claim/supersession; no fallback without PKCE; retained history. Helpers use existing cryptography/standard library only.

**Excluded:** authorization URL builder/client JSON/config/provider endpoints/actual Flow exchange, callback HTTP/routes/CSRF/log redaction/result UI, Gmail identity/scope changes, refresh/send/public signup, real key creation/store writes, key rotation/retention automation/deployment/paid calls. D-034 implementation remains later. No fake Google provider introduced.

**Acceptance:**
1. Approved field/constraint migrate additively, preserve current account/history; pause if B encounters legacy pending rows, no silent invalidation/reset.
2. Known RFC7636 S256 example and generated independent verifier/challenge format pass; no plain fallback.
3. Persisted field/rows have no plaintext verifier/state/session key; issuance has challenge not verifier, claimed repr hides verifier. Wrong key/tamper/unknown envelope/version/size/mismatched row fail safely without consuming state.
4. Successful claim clears ciphertext atomically and returns correct verifier after commit; supersession clears prior ciphertext. Failures roll back claim/clear/supersession. Expiry does not auto-delete rows.
5. Two competing callbacks reveal one verifier to one successful claim; concurrent starts/start-versus-claim/logout remain consistent; other-user attempts unaffected.
6. Missing/malformed key leaves existing account API startup/behavior available; tests use synthetic keys only, runtime real key remains unset.
7. Full account suite/system/no-drift and migration/schema/live-preservation checks pass; no Google success claim.

**Verification:** fresh table/history/test-DB aggregate precheck and nonsecret optional-key configuration presence check; inspect generated migration/plan, apply approved additive change. Helper tests against known standard example plus encrypted envelope validation; updated TransactionTestCase independent PostgreSQL races and rollback/commit visibility checks. Full accounts regressions, Django/system/no-drift, schema inspection/postcheck. No browser/provider/network check appropriate to this internal-only scope; existing browser gate remains separately unverified.

**Dependencies/risks/effort:** Docker/PostgreSQL and approved Fernet; lazy key dependency, legacy pending state, ciphertext context binding, safe transient secret handling and transaction cleanup. Same key means compromise exposes both decryptable stores; no new backup/rotation policy. Clearing DB column is logical removal, not secure erasure from WAL/backups/in-memory copies. Estimate2-4 focused hours including verification/docs, no provider cost. No extra abstractions or installed packages.

**Next action:** review verified WP-01b-8, then small-batch callback/API/provider/config/identity/timeouts/log redaction decisions and a separate WP-01b-9 proposal. No next implementation approved.

## WP-01b-8 verification

Owner instruction: `D-036 B; Approved WP-01b-8`. D-036 B approved; WP-01b-8 verified. Fresh aggregate precheck: users1, eligible administrators1, OAuth attempts0/pending0, test database0. Implement encrypted S256 lifecycle and DB shape constraint only; no provider or HTTP integration. Focused38/full123 passed; migration0004 applied, Django/no-drift checks passed. Exact result in TESTING_AND_EVALUATION.md.
