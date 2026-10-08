# Decision log

Statuses: `proposed`, `approved`, `rejected`, `superseded`, `deferred`. An approved target scope does not approve its proposed implementation. No approval date or owner rationale has been inferred.

| ID | Title | Status | Owner instruction / current choice | Consequences and references |
| --- | --- | --- | --- | --- |
| D-001 | Target full specification MVP | approved | “I think rather than goining with Initial Prototype, we should start working with Specification MVP,” | All P0 requirements remain in scope; the earlier reduced prototype proposal is superseded. See `decisions/ADR-001-specification-mvp-scope.md`. |
| D-002 | Documentation structure and WP-00 | approved | `1. Approved` in reply to approval of the proposed structure and documentation-only WP-00 | Create the requested documents before product code; keep actual statuses. |
| D-003 | Prototype answer path | superseded | No choice was made among the prototype-only hosted/local/extractive options. | The full MVP needs a new provider/model and budget decision. |
| D-004 | Delivery cadence | approved | “Don't bother for the deadline, we will try to give it maximum hours and see it we can complete it at the finest” | No fixed deadline or authorized P0 cuts; plan and estimates remain reviewable. |
| D-005 | Backend/frontend stack and pinning approach | approved | `D-005 A` in the owner's instruction | Django/DRF API and React/TypeScript/Vite UI; pin compatible versions in lockfiles. Foundation versions approved under D-008; later dependencies still need approval. See `decisions/ADR-002-application-stack.md`. |
| D-006 | Local development runtime | approved | `D-006 A` in the same instruction | Docker Compose for local services and application. Daemon availability and RAM remain unresolved; no installation or startup was approved. See `decisions/ADR-003-local-runtime.md`. |
| D-007 | User identity and browser authentication | approved | “We can go with D- 007 A, Ram is 24 GB, and Docker Desktop can be opend” | Custom email-based Django user and same-origin session/CSRF authentication. This does not approve schema fields or implementation. See `decisions/ADR-004-user-authentication.md`. |
| D-008 | Foundation dependency versions and lock tooling | approved | “D-008: B I need pip packages” | Use the approved foundation pins with pip-tools 7.6.1, compiled requirements files, and pip installation; frontend uses package-lock.json. Installation authorized within WP-01a. See ADR-005. |
| D-009 | Local database engine and vector extension | approved | “Approved: D-009 A and WP-01a” | PostgreSQL 17 with pgvector 0.8.6, with a localhost port for desktop pgAdmin. No domain schema or migration approved. See ADR-006. |

## Pending decision areas

These are **proposed topics, not approved choices**. Present no more than a small relevant batch before each dependent package:

- Exact significant dependency versions and lockfiles after D-005; Django app/service boundaries, database schema, constraints and deletion behavior.
- PostgreSQL/pgvector availability and embedding dimensions.
- Parser/OCR engine, supported limits, worker architecture, states, retry and concurrency.
- Embedding, reranking, generation provider/models, content exposure and budget.
- Chunking, retrieval/fusion, context budgets, follow-ups and abstention.
- Revision/index publication, API contracts/errors, citation mapping and viewer behavior.
- Frontend routes/layout/state/hooks, evaluation design/metrics, deployment and release.

For each substantial approved choice, create an ADR with context, alternatives, recommendation, exact owner choice, owner-provided rationale if any, consequences, and implementation references. Use this log for smaller choices and supersessions.

## D-010 — First Django app boundary

**Status: approved.** Owner instruction: `D-010:B`. Relevant: DL-01 and specification section 9.

A (recommended): introduce `apps/accounts` for user model/manager, auth serializers/views and account rules; introduce `config/api` only for shared error/request-ID plumbing when its contract is approved. Collection/document/job/retrieval/conversation apps remain future decisions. Keep HTTP handling in views, validation in serializers and data constraints in model/manager; use a service only where coordination warrants it.

B: introduce all six candidate domain app shells now, although most remain empty.

A reduces current files and review time while preserving the specification's domain separation. B establishes directory names early but adds empty structure and decides future boundaries prematurely. Neither adds provider cost or changes runtime performance; both use approved Django dependencies. App paths are easy to change before migrations; model app labels are more expensive to change after migrations. Owner selected B. Introduce all six app shells in the next approved package; no domain models or package implementation authorized by this decision alone.

## D-011 — Custom user implementation and schema

**Status: approved.** Owner instruction: `D-011 B`. Relevant: DL-01, specification sections 6/7, approved D-007.

A (recommended): subclass Django AbstractUser, remove username, use email as login identifier and a UUID primary key. Retain Django password hash, optional first_name/last_name, is_active/is_staff/is_superuser, last_login/date_joined and permission/group relationships. Add timezone (IANA name, max_length 64, default UTC, validated with zoneinfo). Required email max_length 254; strip surrounding whitespace and lowercase entire address as explicit product policy. Store canonical email with unique=True plus a database Lower(email) uniqueness constraint preventing case-only duplicates even through alternate write paths. Custom manager owns create_user/create_superuser and password hashing; login canonicalizes email identically. Timestamps remain timezone-aware UTC; timezone is a display preference. No account-deletion feature/behavior authorized here.

B: subclass AbstractBaseUser plus PermissionsMixin with the same UUID/email/timezone policy and core auth/status fields, defining names and creation timestamp explicitly. Greater customization but more manager/admin/form integration to maintain. Neither option changes providers or adds dependency cost; A takes less implementation/review time, expected comparable authentication performance. Changing base/model shape after foreign keys exist is costly; adding optional profile fields later is simpler.

Owner selected B: AbstractBaseUser plus PermissionsMixin with the proposed UUID/email/timezone and account-field rules. Approval does not authorize migrations, account provisioning, session/API settings or a work package. References: Django authentication customization documentation.

## D-012 — Unauthenticated API response

**Status: approved.** Owner instruction: `D-012 A`. Relevant: DL-01; specification section 7; approved D-007 sessions/CSRF.

A (recommended): standard DRF SessionAuthentication. Protected requests without a valid session return HTTP 403 with error.code=authentication_required. CSRF failures return 403 with csrf_failed; genuine permission denial uses permission_denied. This explicitly proposes changing the specification's unauthenticated HTTP 401 contract, not deferring isolation. Future React behavior distinguishes codes rather than using status alone. Shared JSON envelope follows specification; exact endpoints/payloads/session settings need separate review.

B: retain specification 401 by adding a small session-authentication adapter providing a documented WWW-Authenticate: Session challenge. CSRF and actual permission failures stay 403. Frontend may distinguish expired/missing sessions by status. Session is an application-defined challenge; browser login still uses our login endpoint, not JWT or Basic credentials.

A uses standard framework behavior and less custom code; B preserves specification status and needs adapter/header regression checks. Neither adds dependencies/provider costs; no material performance difference expected. Both are reversible before clients depend on the API, less convenient afterward. Owner selected A: standard session-auth 403 with authentication_required; specification status-code variation approved. No implementation package approved.

## D-013 — Authentication endpoint and session contract

Status: approved. Owner instruction: `D-013 A`. Fixed 8-hour session plus shared endpoint/session contract approved. Relevant DL-01 and specification section 7; depends on D-007/D-011/D-012.

Common proposed contract: GET /api/v1/auth/csrf returns csrf_token and establishes cookie; POST /api/v1/auth/login takes email/password, returns 200 user plus fresh csrf_token; GET /api/v1/auth/me returns current user; POST /api/v1/auth/logout returns 204 and invalidates session (repeat logout with valid CSRF also 204). User representation: id,email,first_name,last_name,timezone. JSON error envelope: error.code,message,field_errors,request_id, with generated UUID request ID also in X-Request-ID. Invalid login/inactive account use same 400 invalid_credentials response; validation 400; anonymous protected endpoint 403 authentication_required; CSRF 403 csrf_failed. Password never echoed; auth responses Cache-Control no-store. CSRF enforced explicitly for login/logout including anonymous requests; unsafe authenticated requests require X-CSRFToken. No redirect responses. Database session storage; HttpOnly session cookie; SameSite=Lax, host-only; Secure false only local HTTP, required for later HTTPS deployment. No new dependencies or frontend implementation. Names max150, optional empty strings; date_joined aware UTC; is_active true, is_staff false by default. Login rotates session key and CSRF token; logout clears session. PermissionsMixin supplies permissions/groups.

A recommended: fixed 8-hour expiry from login, no per-request renewal, persistent cookie until expiry/logout. B: same contract with fixed 14-day expiry. A reduces unattended session lifetime but requires more frequent login; B is more convenient with longer retained sessions. Equal code complexity/cost/performance; expiry setting easily reversible, endpoint contracts need client coordination. Owner choice pending.

## D-014 — MVP account provisioning

Status: approved. Owner instruction: `D-014 B`. Public registration plus admin and demo seed approved as scope; verification/abuse policies still unresolved. Relevant DL-01 and seeded demo account requirement.

A recommended: account creation via management commands and Django admin; repeatable seed_demo command creates two synthetic ordinary users using runtime passwords without logging them, preserves existing users, never resets passwords silently. Adapt user admin forms for AbstractBaseUser. No public registration/password-reset/email-delivery feature in this package. Later public signup requires its own proposal.

B: include public registration now with password validation plus demo seed/admin. More endpoint/UI/test and abuse-control design required; account verification/email policy must be decided before implementation. Neither option needs paid provider calls to create local accounts. A is smaller and sufficient for seeded MVP; B is additional product scope. Adding registration later does not require replacing the approved user model. Owner choice pending.

## D-015 — Registration verification policy

Status: approved. Owner instruction: `D- 015 C`. Require real email verification; provider/integration details still need approval. Relevant DL-01, approved D-014 B.

A recommended for local development: account becomes usable immediately, email ownership unverified, no verification email/token implementation. Address serves as login identifier only; no claim of verified identity. Before any public release, revisit policy with owner. This is not approval for public deployment.

B: require an email verification link before login, using a local development inbox/console delivery. Exercises a real verification-token flow but simulated delivery does not prove real email delivery; must be labelled. Requires pending-account state, expiring single-use token/resend API and delivery adapter, plus schema/package review.

C: require verification delivered through a real email provider. Same token/state design plus explicit provider, credentials, budget and content-exposure approval before integration or calls.

A is quickest, no new dependencies/provider cost, but email ownership is not established and others may register an address first. B adds implementation/testing but no real-delivery evidence. C adds external reliability/cost and more decisions. Adding verification later needs account-state/migration and existing-account policy review. Owner choice pending.

## D-016 — Initial password and request-limit policy

Status: approved. Owner instruction: `D- 016 A`. Shared password policy and local DRF cache throttles approved. Relevant DL-01 and D-014 B; distinct from provider quotas.

Common password proposal: Django similarity, common-password and numeric-only validators plus minimum 12 characters; validate registration, admin creation and demo seed. Reject passwords over 128 characters before expensive hash work. Login generic credential failures; no raw credentials logged. Seed passwords supplied through runtime environment, preserve existing users without resetting passwords.

A recommended local foundation: built-in DRF cache throttles, registration 5/hour/IP and login 10/minute/IP, HTTP429 with Retry-After and rate_limited error. LocMemCache for current single-process dev server; use REMOTE_ADDR only, ignoring forwarded client-IP claims. Not durable, resets on process restart and non-atomic under concurrency; Vite proxy may group local requests under one address. No claim of brute-force/DDoS prevention. Shared storage/edge controls reviewed before public deployment.

B: same password policy with durable atomic PostgreSQL rate counters now. Adds rate-counter schema, transactions, cleanup and concurrency testing requiring a detailed schema review; survives app restarts and supports multiple processes, adds DB writes/maintenance. Neither option adds paid providers. A is quicker with weaker durability; B more work with stronger counter guarantees. Owner choice pending.

## D-017 — Separate email verification from account suspension

Status: approved. Owner instruction: `D-017 A`. Independent email_verified_at and is_active approved. Relevant DL-01, D-011 B and D-015 C.

A recommended: nullable email_verified_at (aware UTC) on User, independently retain is_active for suspension. Registration creates active but unverified users; login rejects if either inactive or unverified. Successful verification sets email_verified_at without changing suspension. Ordinary seed/admin accounts need explicit marking as trusted when created; no implicit bypass for ordinary users. Permissions also reject unverified users with existing sessions. Exact verification token/delivery/endpoint design remains later approval.

B: use is_active=false for unverified registration, true after verification; no separate verified timestamp. Requires extra rules to prevent verification from reactivating a suspended account and offers no separate ownership-verification record. Simpler schema, less clear account state. Both have negligible expected performance difference, no dependencies/provider costs. A adds one field and checks, distinguishes states and is easier to audit; changing B later requires deciding which existing accounts count as verified. Owner choice pending.

## Email provider research and approval boundary

Owner has no domain. Prior discussion proposed a dedicated Gmail account for low-volume real delivery; provider choice and $0 budget are not inferred from D-015 C alone. Gmail requires eligible app-password access/2-Step Verification. Brevo documents temporary sender rewriting plus normal domain/activation requirements. SMTP2GO permits single sender verification but its current FAQ rejects free-address signup. No accounts created, credentials accessed or emails sent. Provider/content-exposure/budget and token lifecycle will be approved before integration.

## WP-01b-1 implementation references

Owner approved `Approved WP-01b-1`, including initial additive migrations and explicit trusted-superuser provisioning. D-010/D-011/D-017 implemented in backend/apps/ and accounts model/manager/migration. D-016 password validation implemented; registration/login throttles not yet implemented. D-012/D-013/D-014/D-015 HTTP/session/registration/email behavior remains approved design, unimplemented. See components/accounts.md and TESTING_AND_EVALUATION.md.

## D-018 — Verification link lifecycle

Status: approved. Owner instruction: `D-018 B`. One-hour lifetime plus shared single-use/resend/confirmation rules approved. Relevant DL-01 and D-015 C/D-017 A.

Common proposal: unpredictable 32-byte random token, store only SHA256 digest; server expiry; one successful use; resend revokes earlier unused link, no automatic login after verification. Verification sets email_verified_at only, never is_active. Email link opens a confirmation page; explicit CSRF-protected POST consumes token so email scanners/GET do not activate accounts. Resend requested by email gives generic response whether account exists/already verified. Minimum60 seconds between sends for an eligible account; local DRF resend5/hour/IP. These controls are local basic limits, not durable abuse prevention. Token table/constraints and endpoint payloads will be presented before implementation.

A recommended: 24-hour link lifetime. B: 1-hour lifetime. A gives more time for delayed email/demo; B reduces lifetime of stolen unused links but causes more expiry/resends. Same code complexity/cost/performance, configuration easy to change. Extra resends consume mail quota. Unknown/expired/consumed/revoked tokens share safe invalid_verification_link response. No account cleanup or deletion policy approved here. Owner choice pending.

## D-019 — Real email provider and budget

Status: approved. Owner instruction: `D-019 B`. Gmail API with OAuth; shared dedicated sender, $0 paid budget and content-exposure boundaries approved. Relevant D-015 C; owner has no domain.

A recommended for low-volume demo: dedicated Gmail account via Django built-in SMTP backend with TLS, owner-managed app password in ignored environment configuration, $0 paid-service budget. No paid upgrade/provider or normal Gmail password. Google requires 2-Step Verification and eligible app-password access; confirm account availability before dependent integration. App password is a broad account credential, so dedicated mailbox preferred; never paste secret into chat. Google receives recipient email, sender details and verification-message body/link; no uploaded document, password or RAG content. Tests use explicit in-memory simulated delivery, distinct from real SMTP acceptance check; no simulated delivery described as real. Actual sends limited to owner-approved test recipients in implementation package. A local link can be used on same development computer; another device cannot access that computer's localhost link without separately approved reachable setup.

B: Gmail API with OAuth for same dedicated account, same $0 paid budget/content exposure; additional Google project/consent/credential lifecycle and potentially dependencies, to be approved separately. Google prefers Google sign-in/OAuth when supported. A less integration work, B revocable scoped authorization and more setup/maintenance. Both subject to Google account limits and delivery failures; no inbox success guaranteed. Neither is public deployment approval. Owner choice pending.

Sources checked: https://support.google.com/accounts/answer/185833?hl=en ; https://docs.djangoproject.com/en/5.2/topics/email/ . Account policy confirmed in docs, account eligibility/inbox delivery not tested.

## D-020 — Owner authorization for Gmail sender

Status: approved. Owner instruction: `D-020 B`. Relevant DL-01/D-019 B; this connects the application sender, not end-user Gmail accounts or Google login.

Common proposal: dedicated sender account only, gmail.send permission (no inbox reading), OAuth app in External Testing with owner-added sender as test user, offline access for refresh capability, secrets only in ignored local credential configuration mounted read-only into backend, never browser/source/logs. Access tokens short-lived/in-memory; durable refresh credential requires local protected storage. No automatic production consent publishing or public deployment. External Testing refresh tokens expire after7 days for this Gmail scope; reauthorization is a documented operational step. Token revocation/errors return safe email-unavailable behavior; exact API delivery failure semantics still await review.

A recommended local foundation: explicit owner-run local OAuth authorization utility, using installed/desktop OAuth client and loopback redirect, then backend uses mounted credentials. No sender-connect product screen. Utility may run as separate approved tooling container with published loopback callback port; browser consent occurs on host. B: owner-only Django sender-connect/callback endpoints with Web OAuth client, state protection and secure backend token persistence, with admin UI. More integration/routes/authorization/storage complexity but browser-based reconnection. Exact dependency pins/storage paths/callbacks will be proposed in package; not approved by this choice alone.

A less code/time/cost and no new public route, but owner uses setup command. B easier reconnect UX, more maintainability/security/test work. Both use approved Google provider, $0 paid budget, same Gmail send data exposure, no expected material send-speed difference. A can later be replaced by B without changing verification token schema. Owner selected B: owner-only sender-connect UI with Django OAuth endpoints and Web OAuth client. Storage, schema, exact dependencies and package approval remain unresolved. See ADR-008.

Sources: https://developers.google.com/workspace/gmail/api/auth/scopes ; https://developers.google.com/identity/protocols/oauth2 ; https://developers.google.com/identity/protocols/oauth2/native-app . gmail.send is sensitive; External Testing7-day refresh expiry. Consent/project/account availability not tested. No Google account/project created or messages sent.

## D-021 - Gmail refresh credential storage

Status: approved. Owner instruction: `D-021 B`. Relevant DL-01, D-019 B and D-020 B. Owner selected encrypted private backend file on a persistent Docker volume; PostgreSQL credential storage not selected.

OAuth refresh credentials let the backend obtain short-lived send access without repeated consent. They must be recoverable, so verification-token hashing is unsuitable. Both options encrypt the refresh credential, keep the separate encryption key in ignored backend environment configuration (not Django SECRET_KEY), keep access tokens in memory, exclude credentials from logs/API/browser, and require reconnection if key/credential is lost or revoked. Encryption protects a stolen stored record without its key, not a compromised running backend with access to both.

A recommended: encrypted PostgreSQL record. Adds a sender configuration model/migration and a cryptography dependency subject to exact-version approval. Fits the approved web reconnection flow and shared backend access; DB transactions support atomic replacement. Database backups must retain the corresponding key separately. More initial schema review; no paid service or expected material send latency change. Reversible by decrypting and moving credentials through a separately reviewed migration or simply reconnecting.

B: encrypted file on a private persistent backend Docker volume. Avoids sender credential DB model initially but still needs encryption dependency, persistent mount, file permissions, atomic replacement and backup rules. Suitable for a single sender/process; coordination across processes/deployment is less convenient. Similar provider cost and expected send performance; moving later requires migration or reconnection.

Owner selected B for storage direction. No owner rationale inferred. Exact schema/constraints/deletion, dependency pins and key rotation remain for review; neither option approves product implementation or provider calls.

Sources: https://developers.google.com/identity/protocols/oauth2/resources/best-practices ; https://cryptography.io/en/latest/fernet/ . Google recommends secure token storage and encryption at rest for server-side storage. No dependency installed.
## WP-01b-2 approval and implementation record

Owner instruction: Approved `WP-01B-2`. Package implemented and verified within previously approved D-007/D-011/D-012/D-013/D-016/D-017. Session API plus additive Django session migration; no new product/architecture/provider decisions or dependencies.27 account tests passed and proxy/check/drift gates passed. See IMPLEMENTATION_PLAN.md and TESTING_AND_EVALUATION.md. No next package approved. D-018/D-019/D-020/D-021 verification/Gmail directions remain unimplemented.
## D-022 - Registration response and duplicate-email behavior

Status: approved. Owner instruction: `D-022 B`. Relevant DL-01, specification account scope and owner-added D-014 B public registration; D-015 C, D-016 A, D-017 A and D-018 B apply. Generic202 response and shared registration rules selected; no implementation package approved.

Common proposal: POST /api/v1/auth/register, CSRF required even anonymous; required email/password with approved normalization/password validators, optional first_name/last_name/timezone using existing model limits/defaults. Never allow client privilege, suspension or verification fields to set account state. New users active/unverified; no automatic login. Registration throttle5/hour/REMOTE_ADDR as approved. Duplicate requests never overwrite password/profile/status or auto-send another email; separate resend flow owns resend controls. Concurrent duplicate creates use DB uniqueness and converge on selected duplicate response. Delivery failure behavior remains a separate unresolved contract, not silently approved here.

A:201 on new account,409 email_in_use for any existing account. Clear frontend feedback and less response-path coordination; reveals whether an email is registered. B recommended: identical202 generic acknowledgement for accepted valid new/existing-address requests; no user ID/status or existence disclosure in success body. Suggested message: "If registration can proceed, check your email for verification instructions. If you already have an account, sign in or request another verification email." Existing credentials unchanged. This only reduces disclosure through the normal success response; no timing or delivery-failure indistinguishability guarantee. Actual mail-delivery failures and response behavior must be resolved before implementation.

Both require same validation/provider budget; B adds duplicate/concurrency response tests and less direct UX, A simpler but discloses membership. Expected normal response work similar excluding provider calls; delivery architecture still unresolved. Switching response contract later needs coordinated API/UI updates, no different schema. Neither implements account recovery/password reset; pending-address recovery/retention remains a known limitation for review. Owner selected B; no additional rationale inferred.

## D-023 - Verification-token schema and concurrency

Status: approved. Owner instruction: `D-023 B`. Relevant DL-01, D-015 C, D-017 A, D-018 B; extends spec account schema. Separate issuance records plus common fields/constraints/PROTECT and transaction rules selected; no implementation package approved.

Common proposed EmailVerificationToken model in accounts: UUID id; required User relation with PROTECT (no implicit deletion of token history), unique token_digest CharField64 containing lower-case SHA256 hex, created_at awareUTC, expires_at awareUTC, consumed_at/revoked_at nullable awareUTC. Constraint expires_at > created_at; consumed_at and revoked_at cannot both be set. Token material32 random bytes with only digest stored; one-hour lifetime already approved. No plaintext token in model/API response/log. Creation time records issuance, not successful email delivery. User deletion/retention/cleanup feature remains unapproved; PROTECT requires explicit future deletion policy, not perpetual retention approval.

A: OneToOne user/token, replace digest/lifecycle fields on resend. Old links become unknown after replacement; minimal rows, simple current-state access, no issuance history. B recommended: ForeignKey user/token, retain each issuance; resend explicitly revokes earlier unconsumed/unrevoked row. Partial unique constraint on user where consumed_at and revoked_at null ensures at most one outstanding row (including expired rows until explicitly revoked). Index(user,created_at) supports latest issuance/cooldown checks. Token digest is globally unique; no token row is exposed publicly. History shows issued/consumed/revoked states, not proof of mail delivery.

Both serialize issuance and consumption by locking User first in a short transaction; token rows then read/locked in consistent order. Verify rechecks digest/expiry/unused/unrevoked/eligibility under lock, marks one use and sets email_verified_at without changing is_active or logging in. An expired outstanding row is revoked before replacement under B. A60-second issuance cooldown implements approved resend limit even after an uncertain delivery failure; delivery-specific retry rules still require review. No Google call or long operation while holding database locks. Test two simultaneous resends/consumes and rollback; issuance alone must not send or pretend delivery.

B adds rows, constraints and retention/cleanup considerations; clearer history and explicit revocation. A fewer rows and simpler storage, less diagnosis. Neither adds dependency/provider cost; short transactions serialize requests for the same account, not unrelated users. Reversing A to B cannot recover overwritten history; B to A discards history and requires separately approved migration/deletion. Owner selected B, including common fields/constraints/PROTECT and transaction design; no additional rationale inferred. Email delivery architecture/API failure handling, verification confirmation frontend route/token transport and package implementation remain unresolved and excluded.
## D-024 - Email delivery execution and failure acknowledgement

Status: approved. Owner instruction: `D-024 A`. Relevant DL-01 and owner-added verified registration, D-018/D-019/D-022/D-023. Inline email delivery direction selected; exact delivery limits/diagnostics/API still need review. No implementation/package approval.

A recommended for current low-volume registration: send during the HTTP request after committing account/token state; no database lock during Google calls. Bound provider request timeouts, no automatic send retries after ambiguous timeout (Google may already have accepted). Individual send failure leaves account unverified and receives the same generic202 acknowledgement as other accepted new/existing requests; no claim that email was sent/delivered. Owner-visible safe delivery diagnostics and user resend recover failures; exact diagnostic storage and timeout limits need review. A global sender-not-configured/unavailable preflight can return503 uniformly before account lookup for otherwise valid requests; exact availability checks/contracts remain unresolved. Successful provider acceptance is not inbox delivery. Resend retains approved generic responses, cooldown and latest-link rules.

B: durable background delivery job; HTTP acknowledges after account/job transaction, worker creates token just before each send (raw token in memory, not queued plaintext/recoverable payload). Adds durable delivery-job schema/status, dispatch/recovery, concurrency and explicit retry/supersession decisions; broker/worker/dependencies require separate approval. Process crashes and ambiguous sends still need safe recovery, cannot promise exactly-once inbox delivery. A new send attempt may require a new link and invalidate prior one under approved latest-link rules. Exact queue/retry/cooldown design not approved by selecting mode alone.

A fewer components and faster review/implementation, but registration waits for Google and crashes/timeouts need user resend; switching to jobs later requires delivery-state/schema/API coordination. B faster acknowledgement and recoverable durable work, more infrastructure/schema/testing and operating resources. Neither changes $0 paid provider budget, Gmail quotas or real-delivery requirement. Both use real approved provider only once integration/package/test recipients are approved; simulated tests labelled. Owner selected A inline delivery direction; no additional rationale inferred. Exact limits/schema/API and package approval follow. No P0 ingestion worker requirement is deferred by choosing inline email; OCR background architecture remains separate.
## WP-01b-3 approval and implementation record

Owner instruction: Approved `WP-01b-3`. D-017 A/D-018 B/D-023 B implemented as internal token model/lifecycle, approved additive migration and20 new tests. Full47-test account suite passed, system/drift checks passed, local schema/constraints inspected. No new decisions, dependencies, HTTP/email/UI/provider calls. See ADR-009, IMPLEMENTATION_PLAN.md and TESTING_AND_EVALUATION.md. No next package approved. D-022 generic signup and D-024 inline delivery remain approved unimplemented directions; exact HTTP/delivery/provider contracts await review.
## D-025 - Registration, verification and resend HTTP contract

Status: approved. Owner instruction: `D-025 Approved`. Relevant DL-01 plus approved owner-added public/verified registration; D-014/D-015/D-016/D-017/D-018/D-022/D-023/D-024. Proposed contract approved including204 confirmation; no implementation package approval.

Recommended concrete contract (approve as proposed or request changes): three POST endpoints under /api/v1/auth/, all explicitly CSRF-protected even anonymous, JSON/no-store/server request IDs/error envelope, no account/token/privilege leakage or automatic login. Existing session/auth routes unchanged.

POST register: required email/password, optional first_name/last_name/timezone, existing approved limits/normalization/password validators; reject unknown/client privilege/verification fields. New user active/unverified; existing address never overwritten or automatically resent. Normal accepted valid requests for new/existing address return identical202 message: "If registration can proceed, check your email for verification instructions. If you already have an account, sign in or request another verification email." Registration5/hour/REMOTE_ADDR already approved. Concurrent duplicate creates converge to same acknowledgement via unique constraints/transaction handling. Invalid fields400 validation_error.

POST verification/resend: email only, normalized/validated; normal accepted requests return202 fixed message: "If this account is eligible, check your email for verification instructions." Only active/unverified accounts may issue/send; missing/verified/inactive/cooldown cases return same202, no account-specific Retry-After. Approved issuance60-second cooldown and resend5/hour/REMOTE_ADDR remain; IP throttle429 with Retry-After uses existing local limitations. No token returned. Individual send failure still generic202 under D-024 A; global503 preflight/details await delivery contract, so no guarantee of timing/failure indistinguishability.

POST verification/confirm: token JSON field, valid one-use proof returns204 empty body; invalid/missing/malformed/expired/used/revoked/already-verified token400 invalid_verification_link. Malformed JSON remains400 parse_error; unknown fields400 validation_error. No login or suspension change. Verification GET never mutates or consumes (confirmation page separate D-026); no new confirm-specific IP throttle in this proposal. Wrong HTTP method405, missing/invalid CSRF403 csrf_failed. Possession can confirm associated user even when caller has no session; no user identity in success body.

Tradeoffs: explicit separate endpoints and minimal responses are easy to test and fit existing service boundaries; generic resend gives less specific feedback but avoids account-specific cooldown/status disclosures. Adds serializers/views/orchestration and regression tests, no dependency/provider cost by contract alone. Expected response time for register/resend still depends on approved inline provider call.204 confirm minimizes representation, frontend must render its own success message; a viable alternative is200 {status:verified}, with same privacy/state rules. URL/payload/status changes later require coordinated frontend/API updates; token schema unchanged. Provider pins/timeouts/diagnostics/bootstrap/integration remain excluded, not silently approved. Owner approved D-025 as proposed, including204 empty confirmation response; no additional rationale inferred.

## D-026 - Verification-link token transport

Status: approved. Owner instruction: `D-026 A`. Relevant DL-01/D-018 explicit confirmation and secret/log boundary; fragment transport approved, no UI/package implementation approval. Email opens frontend /verify-email, shows explicit confirmation button, no GET/automatic token consumption, no automatic login.

A recommended: /verify-email#token=<secret>. URI fragment is processed by browser, not sent as part of initial HTTP request. React later reads it into temporary memory and immediately removes fragment from address/history entry, never localStorage/sessionStorage/analytics/logs, sends token only in JSON POST to D-025 confirm after explicit user action and CSRF bootstrap. Reload after removal loses in-memory token; user reopens original email link. Initial fragment can still be exposed through browser/email access; not universal secret protection. Provider already receives approved message/link. Exact component/state/effect/layout will be explained/reviewed before UI implementation.

B: /verify-email?token=<secret>. Easier familiar query parsing, but token travels with GET URL and can enter server/proxy access logs. Requires explicit URL redaction across dev/proxy/server and a no-referrer policy, plus same immediate URL removal/in-memory-only/explicit POST rules. No permission to log secrets. Retrofitting log protection adds work; changing URL format later can break existing unexpired email links unless compatibility/reissue handled.

Both no new service cost/dependency and similar expected runtime performance; A minor browser handling work, less server logging exposure, compatible with approved React frontend. B more request-log configuration/testing. No route/UI implementation now. Owner selected A fragment transport; no additional rationale inferred. Source checked: https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment (fragment is not sent to server with URI request).
## D-027 - Authorization for Gmail sender administration and bootstrap

Status: approved. Owner instruction: `D-027 A`. Relevant DL-01 and D-020 B owner-only sender-connect page/endpoints. Active verified superusers selected; no permission implementation/package or account provisioning yet.

What/why: identify who may connect/replace the application-wide Gmail sender. Ordinary logged-in users must never administer sender credentials. Login alone or is_staff alone is insufficient. Existing VerifiedAccountBackend already enforces active/verified eligibility; sender-admin permission adds an explicit further check to all status/connect/callback/disconnect operations as applicable. OAuth state/session binding still required separately; no token disclosure to browser. Exact routes/response capabilities/UI remain later contract review.

A recommended for current owner-operated app: require active verified session and is_superuser. All trusted superusers may administer the sender, not literally only one named person. Existing model supports flag; no new schema/dependency. A later package would include explicit owner-run interactive createsuperuser provisioning; current manager deliberately trusts administrative provisioning and sets verified timestamp, avoiding Gmail-verification bootstrap cycle. Ordinary registration cannot set privilege/verification fields. Do not create account, accept secrets in chat or invoke provisioning before package approval.

B: require active verified session and exact User UUID configured as EMAIL_SENDER_OWNER_ID in backend environment. Only that one configured account may administer sender; other superusers do not automatically gain this access. Initial trusted owner can still be provisioned through explicit administrative command; UUID configured afterward, no ordinary verification bypass. Needs config validation, setup/transfer instructions, restart on owner change and allowlist permission tests. No new schema/dependency; UUID is identity configuration, not an authentication secret.

A simpler standard-role authorization, easier setup/maintenance, but broadens sender access to every future superuser. B tighter single-owner boundary, more configuration and potential lockout if UUID wrong/account unavailable; role/ownership transfer requires environment change. Neither provider cost/expected material performance difference; both need cross-user/anonymous/suspended tests. Changing later is inexpensive before sender UI clients/setup depend on policy, then requires coordinated config/permission/docs changes. Owner selected A: all active verified superusers; no additional rationale inferred. Bootstrap/permission implementation still needs package approval.
## WP-01b-4 approval and implementation record

Owner instruction: Approved `WP-01b-4`. Implemented D-027 A CanManageEmailSender and11 new synthetic permission/CLI tests.58 total account tests passed, check/no-drift passed, no live accounts created. Existing createsuperuser/UserManager reused unchanged. No new schema, dependency, API/UI/provider change or real bootstrap execution. Next package requires separate approval; remaining Gmail/provider/delivery decisions unresolved.

## Owner administrator provisioning confirmation

Owner instruction: "Super user created successfully" followed by "Proceed Further". Owner-run provisioning is now confirmed. Read-only aggregate query returned account_count:1 and eligible_sender_admin_count:1, filtered by is_superuser/is_active and non-null email_verified_at. No identity/password/hash displayed. This supersedes earlier current-state statements that provisioning was unperformed, without changing historical package test results. No real login or Gmail delivery verified; no new implementation package approved.

## D-028 - Gmail integration Python dependencies

Status: approved. Owner instruction: "D-028 A (but all libraries, must be in a venv)". Relevant DL-01 and owner-added verified registration, D-008 B pip-tools, D-019 B Gmail, D-020 B Web OAuth, D-021 B encryption. Option A pins approved with the additional virtual-environment requirement for all Python dependencies, including existing runtime libraries and dependency tooling. No installation package approved yet.

A recommended: google-auth==2.61.0 for credentials/refresh, google-auth-oauthlib==1.5.0 for OAuth consent/token exchange, requests==2.34.2 for bounded HTTP requests to Gmail's documented REST send endpoint, cryptography==50.0.2 for Fernet credential encryption. Python email/base64 standard library constructs the message. Authentication protocol/encryption use maintained libraries, while our service owns the small send request and safe error mapping. Keep D-008 exact direct pins and pip-tools hash lock for transitive dependencies; no automatic floating upgrades.

B: same four direct pins plus google-api-python-client==2.201.0, using Google's generated API client for Gmail send. More dependencies and transport configuration; less hand-written API request construction and easier expansion to other Gmail methods, which are not currently required/authorized. Retry defaults must still be explicitly disabled/controlled to respect D-024 ambiguity handling. Neither option changes Gmail scope, provider budget or data exposure. Package license cost is zero; no performance benchmark exists. A smaller dependency surface/lock and explicit timeout/retry ownership; B broader client abstraction/maintenance overhead. Switching adapters later should be inexpensive behind the sender service and does not change token/user schema.

Public PyPI JSON metadata checked for all five versions and Python constraints; direct constraints allow Python3.13 and the proposed combination. This is metadata review, not successful resolution/build/runtime verification. Future approved package must compile the lock, build, run pip check and regression tests; pause for material incompatibility rather than silently choose versions. Sources: https://pypi.org/project/google-auth/ ; https://pypi.org/project/google-auth-oauthlib/ ; https://pypi.org/project/requests/ ; https://pypi.org/project/cryptography/ ; https://pypi.org/project/google-api-python-client/ ; https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send . Owner choice pending: A or B. No approval/rationale inferred.

## D-029 - Credential-file safety and encryption-key recovery

Status: approved. Owner instruction: "D-029 A". Relevant DL-01, D-020 B and D-021 B. Common storage safeguards and option A single-key Fernet/reconnection recovery approved; no additional rationale inferred. No implementation package approved yet. A refresh credential can obtain future access tokens; encryption must be reversible, unlike verification-link hashing.

Common proposed design: one application sender, versioned minimal encrypted JSON containing refresh credential and granted scopes, no persisted access token. Dedicated backend-only named volume mounted at /var/lib/docinsight/sender; credentials.enc and a separate stable lock file. Separate backend environment key GMAIL_CREDENTIAL_ENCRYPTION_KEY, never Django SECRET_KEY or frontend environment; OAuth client JSON ignored and mounted read-only separately. Directory0700/file0600 inside Linux container; same-directory encrypted temporary file, flush/fsync then atomic replacement, cleanup on failure. Standard-library fcntl advisory lock serializes cooperating readers/writers across backend processes; stable lock survives credential replacement. Provider work must never hold a database lock; refresh/reconnect generation handling and bounded lock acquisition reviewed with OAuth/delivery contracts. Missing/wrong key, corruption or unsupported format fail closed with safe errors and preserve existing file, no plaintext fallback or silent overwrite. Tests must exercise concurrency, tamper/wrong-key and interrupted replacement using synthetic credentials. This protects stored data but not a compromised backend/host with access to both file and key. No database credential model; no Google call by storage itself.

A recommended: cryptography Fernet authenticated encryption (confidentiality plus detection of tampering), one generated key. Document owner-controlled private backup of the key separately from encrypted-volume backup; never place either in repository/docs. Routine key change uses planned sender reconnection under the new key, explicitly authorized when performed; loss of old key also requires reconnection. No automatic rotation/backup service. Suitable for one local sender, less code/testing and no service fee. Rotation interrupts sending until reconnection. Backups/restores/deletions are not authorized merely by this proposal.

B: same storage safeguards with MultiFernet key ring, plus an explicit owner-operated re-encryption command and rotation tests/runbook. New key encrypts, temporarily retained old key decrypts existing file until successful migration; remove old key only after verified rotation. More configuration/implementation/secret handling, less need to reconnect solely for planned rotation. Losing all decrypting keys still requires reconnect. No extra library/service cost or expected meaningful single-sender throughput difference; runtime performance unmeasured. A can evolve to B without changing user/token schema, but coordination is required to preserve access to existing encrypted file. Rotation command must not print secrets. Source: https://cryptography.io/en/latest/fernet/ . Owner choice pending: A or B. Endpoint/state/credential payload validation and refresh/disconnect race contract remain separate next decisions; no package approval inferred.

Approval reconciliation: the option descriptions above retain their original proposal wording. Owner selected D-028 A with all Python libraries in virtual environments, and D-029 A; earlier "choice pending" text is superseded by these explicit instructions. Current Dockerfile installs existing libraries into container-wide Python; it does not yet satisfy the new venv condition. Proposed WP-01b-5 addresses all runtime libraries and isolated pip-tools use before Gmail services. No host installation, code change or dependency installation performed in this decision-recording turn.

## WP-01b-5 approval

Owner instruction: Approved `WP-01b-5`. Authorizes the proposed runtime/tooling venv, approved dependency installation/lock, backend rebuild and checks/documentation. Credential storage/OAuth/email/UI remain excluded. Initial tooling download failed TLS certificate verification; retry uses an exported Windows trusted public CA bundle mounted read-only, without disabling TLS verification. A subsequent PowerShell quoting error in a diagnostic command was fixed within package scope. No architecture/provider change.

## D-028 runtime installation amendment

Status: approved; supersedes only the runtime-venv condition, not D-028 A dependency pins or D-029 A. Owner wrote "Install the new one like the previous managed". Asked explicitly whether this means installing into Docker's main Python environment without a venv, replacing the earlier venv requirement. Owner answered "Yup I men, yes, if there is no harm in it". Explained that container-wide installation is reasonable for this dedicated backend image: Docker separates it from Windows and exact/hash-locked packages control the install; no claim of protection from malicious packages or a compromised container. Restore previous runtime layout, retain isolated temporary pip-tools compiler environment and complete approved WP-01b-5 lock/build/regressions. No additional package approval required for this owner-directed amendment within the active package. No host-global installation or provider behavior authorized.

## WP-01b-5 implementation record

Verified after owner runtime-layout amendment. Approved four libraries installed with hash lock (20 distributions); original Django/DRF/psycopg pins retained. Compiler toolchain/venv check and resolution passed; backend image build/recreate, runtime versions/imports/locations, synthetic Fernet roundtrip, pip check, Django check/no-drift and58 account tests passed. Runtime /usr/local Python with UID10001, optional build CA mount absent at runtime. Postcheck one user/eligible administrator, zero verification tokens,10 tables, test DB absent; all services healthy. No migration/product API/frontend/provider change, no next package approved. D-029 storage and OAuth/delivery remain unimplemented. Actual command/failure evidence in TESTING_AND_EVALUATION.md.

## D-030 - Credential record and protection against stale operations

Status: approved. Owner instruction: `D-030 A`. Relevant DL-01 and owner-added verified registration; specification section10 secret handling; D-019 B/D-020 B/D-021 B/D-029 A. Owner selected common record/limits and optionA short locks/generation-checked writes with encrypted empty marker. No additional rationale inferred. Implementation/package approval remains separate; WP-01b-6 not approved yet.

Problem: a request reads the current Gmail credential and waits for Google. Meanwhile an administrator reconnects or disconnects the sender. The old request must not overwrite the newer state or restore a disconnected sender. Encryption/atomic replacement alone do not establish which operation is current. Provider endpoint/auth/state semantics remain separate review.

Common proposed record: versioned encrypted JSON, exactly one sender; credential contains refresh_token (nonempty string up to8192 characters), client_id (nonempty string up to512) and scopes (only approved gmail.send scope at this stage). No access token, OAuth client secret, recipient, document content or arbitrary provider endpoint stored. Bind reads/writes to caller's expected OAuth client_id to detect configuration mismatch, not to infer sender email identity. Validate schema/types/unknown fields/sizes after authenticated decryption; cap encrypted file at64KiB before reading/decrypting fully. Missing key, wrong key, tamper/corruption, unknown version or mismatch fail safely without overwriting. Two-second monotonic deadline for local file-lock acquisition, safe busy error on contention; exact future HTTP mapping pending. Caller authorization is enforced by future endpoints, not by this trusted internal file service.

A recommended: short file locks plus an opaque generation UUID, changed on every successful write. Caller reads credential/generation, releases lock before Google, then may replace/clear only if the current generation matches its expected value. Conflicts return a safe stale-state error; do not retry by overwriting latest. Store envelope is schema_version1, generation UUID and credential object or null. Disconnect persists an encrypted empty marker with a fresh generation rather than simply removing the file; this prevents an old "no credential existed" request from restoring it. Initial absent file is generationNone; a cleared store has a real generation. Creation/replacement/clear all compare-and-update under the same stable lock file. Missing/corrupt existing data must not be treated as an empty initial store. Refresh/consent adapters must honor returned conflicts; their APIs/network behavior not implemented by this choice. Manual file removal/old backup restore bypasses history and is not routine disconnect/recovery.

B: serialize the entire credential operation, including future Google refresh/authorization exchange, while holding the file lock. No generation comparison required; local disconnect waits for old operations, then clears state. Store exposes a scoped lock/operation interface; one encrypted credential record, no generation/empty-marker protocol needed. Simpler sequencing but slow/failed network work holds up other cooperating sender operations; bounded provider timeouts still need review. No database lock around provider calls under either option. Consistent lock use is mandatory for all cooperating processes; the Linux standard-library fcntl interface does not enforce business policy by itself.

Recommendation A: slightly more state validation/tests, clearer stale-write handling without holding a file lock across unpredictable network latency. B less initial protocol code, more blocking coupling between storage and future Google adapters. Neither adds dependencies/provider fees, changes user/token database schema or relaxes superuser/CSRF/OAuth-state boundaries. A may improve concurrency of local operations but no measured performance claim; B may increase lock-busy responses during slow requests. Reversing after live credentials exist needs reviewed file-format conversion and coordinated callers; before real connection it is inexpensive. Exact provider timeout, token freshness/in-memory access caching, API errors, sender identity checks and frontend remain separate decisions. Lock/key/network failure must never expose credentials. Owner choice needed: D-030 A or B, or requested changes to common record/limits.

Primary references reviewed: https://cryptography.io/en/50.0.2/fernet/ (authenticated encryption); https://docs.python.org/3.13/library/fcntl.html (Unix file-lock interface); https://docs.python.org/3.13/library/os.html#os.replace (atomic replacement when successful). Generation coordination is our proposed application design, not a guarantee provided by these libraries. No code/volume/key/provider action approved by this proposal.

Approval reconciliation: owner subsequently chose `D-030 A`; earlier alternatives/recommendation wording is proposal history. Common validation/record/limits and optionA design now approved, unimplemented. B not selected. No package approval inferred. Next obtain explicit WP-01b-6 approval for the finalized scope in IMPLEMENTATION_PLAN.md; no new unresolved decision inside that package.

## WP-01b-6 approval

Owner instruction: Approve `WP-01b-6`. Authorizes finalized credential-store service/private empty volume/config/synthetic verification/docs under D-021 B/D-029 A/D-030 A. No Google setup, real key/credential provisioning, OAuth/send/HTTP/UI, dependency changes or migration authorized. No prior sender volume found; live administrator count1/eligible1, test DB absent. Implementation in progress; results recorded on completion.

## WP-01b-6 completion

Status: verified. Owner instruction: Approve `WP-01b-6`. This subsequent package approval supersedes earlier pending-package statements in D-030/proposal history. D-021 B/D-029 A/D-030 A are implemented for internal storage; their selected designs did not change.

SenderCredentialStore strict Fernet file/read/replace/clear, generation checks/empty marker, private backend-only empty volume and lazy configuration implemented. Focused27/full85 tests and build/Compose/system/pip/no-drift/permissions checks passed. Test fixture and diagnostic initialization failures/fixes are recorded in TESTING_AND_EVALUATION.md. No real key/credential/Google/schema/HTTP/frontend changes. Live administrator preserved. See ADR-010 and components/gmail-sender-store.md.

No next package approved. Next owner review: protected OAuth endpoint/state/provider setup decisions in a small batch, followed by a separate package proposal.

## D-031 — OAuth connection-attempt persistence

Status: approved. Owner instruction: `D-031 B, D-032 A`. D-031 B selected dedicated attempt model/service; no implementation/package approval. Relevant DL-01, specification sections7/9/10, owner-added real verification and D-020 B/D-027 A/D-030 A.

Decide where to keep the temporary proof linking a sender-connect request with Google's callback. A callback is Google's return request after consent; state is an unpredictable value round-tripped through that flow, checked against the initiating administrator and browser session. Provider credentials remain in the approved encrypted file under either option.

A: use existing database-backed Django session storage, with explicit concurrency coordination and careful session-save integration. Avoids a new application model/migration, but ordinary session dictionary read/pop is not sufficient for concurrent single-use claims. Correct locking must prevent stale session saves restoring consumed state; this adds coupling to session middleware and more subtle concurrency tests.

B recommended: dedicated OAuthConnectionAttempt model in accounts plus a small lifecycle service. Keep only temporary attempt metadata/state digest/session binding/expiry and captured credential-store generation; no OAuth client secret, Google code or access/refresh token. Claim under a short database transaction, then release locks before provider work. More explicit schema/migration/tests, independent of session dictionary persistence and clearer race behavior.

Both need administrator/session revalidation and safe failures. No additional dependency/provider fee; B adds a small DB operation per rare connection attempt, no measured performance claim. A may initially take fewer files but safe concurrency narrows that saving. B is easier to maintain/test independently. Both reversible before real OAuth use; changing later requires retiring pending attempts. These are application design alternatives, not a Google requirement to use a dedicated table.

Owner choice needed: D-031 A or B. Approval selects persistence architecture only; exact fields, relationships/deletion rules/constraints and package still require review. Session-based DocInsight login and encrypted refresh-token file remain as already approved.

## D-032 — OAuth attempt expiry, replacement and reuse

Status: approved. Owner instruction: `D-031 B, D-032 A`. D-032 A and common ten-minute/session-bound/single-use policy selected; no package approval. Relevant DL-01, specification sections7/10, D-020 B/D-027 A/D-030 A.

Common proposed policy: cryptographically random32-byte state, persist only digest; bind attempt to initiating active verified superuser and exact browser login session. Ten-minute server expiry (now >= expiry invalid); recheck current permission/session at callback; one successful atomic claim before any code exchange. A provider error/timeout/process failure after claim requires starting a new attempt, not replay or automatic exchange retry. Invalid/mismatched callers do not consume another person's valid attempt. Snapshot credential-store generation at initiation; future publication must use that generation, preserving existing stale-write safeguards. Details of provider transport/PKCE/callback HTTP/log redaction remain separate review.

A recommended: one pending attempt per administrator across sessions. Starting again invalidates that administrator's earlier pending attempt. Simplest user instruction: complete the latest Connect attempt; other administrators are handled independently, with store generations resolving publication conflicts.

B: allow multiple pending attempts for the same administrator, each bound to its originating session and state. Different tabs/sessions may finish independently; each claim still single-use, and store publication still conditional. Requires a separately approved outstanding-attempt cap and more concurrent behavior/status tests; no unbounded attempt creation approved.

A fewer lifecycle cases, lower implementation/review effort and easier explanation, but an older tab stops working. B more convenient for parallel tabs, more storage/lifecycle complexity and user-visible publication conflicts. Neither adds provider fees or promises performance improvement; expired/failure attempts require reconnect under both. Policy changes are inexpensive before OAuth use; afterward retire or consistently honor old attempts.

Owner choice needed: D-032 A or B, or requested changes to common policy. Exact schema/API/errors/cleanup/provider calls remain unresolved and excluded from approval.

Primary references reviewed: https://developers.google.com/identity/protocols/oauth2/web-server (state/callback/offline authorization); https://docs.djangoproject.com/en/5.2/topics/http/sessions/ (session persistence). Ten-minute TTL, persistence alternatives and atomic-claim policy are our proposals, not provider-prescribed settings.

## D-031/D-032 approval reconciliation

Owner instruction: `D-031 B, D-032 A`. Dedicated OAuthConnectionAttempt table/service and common policy plus one pending attempt per administrator approved. Earlier alternatives/choice-needed wording is proposal history. No additional owner rationale inferred. Exact schema/retention/deletion/constraints and WP-01b-7 remain unapproved. See ADR-011.

## D-033 — OAuth attempt schema and retention

Status: approved. Owner instruction: `D-033 A; Approved WP-01b-7`. Common schema/service and A retained history/PROTECT selected; WP-01b-7 implementation authorized. Relevant DL-01 support, specification sections6/7/9/10, approved D-031 B/D-032 A/D-027 A/D-030 A.

Problem: define the actual temporary authorization model, relationships, lifecycle constraints and service boundaries before adding a migration. Model stores metadata, service coordinates rules; no HTTP views/serializers/tasks/provider calls in this slice.

Common proposed model in accounts/models.py:

| Field | Type/rule |
| --- | --- |
| id | UUID primary key, uuid4 |
| user | Required FK to AUTH_USER_MODEL; deletion differs by A/B below; related_name oauth_connection_attempts |
| state_digest | Unique CharField64; SHA256 hex of64-character hex state from32 random bytes; raw state returned to trusted caller in memory only |
| session_digest | CharField64; SHA256 of exact initiating database session key; no stored raw cookie/session key; no FK to django_session |
| client_id | Required CharField512, nonempty; snapshot of configured client, checked again on claim |
| expected_generation | Nullable UUIDField; None denotes initially absent sender file, actual UUID includes encrypted cleared state |
| created_at / expires_at | Aware UTC DateTimeFields; creation sampled after lock acquisition, expiry creation+10minutes |
| claimed_at / superseded_at | Nullable aware UTC DateTimeFields, default None; claim means authorization attempt accepted, not connected or delivered |

Database constraints: unique state_digest; partial unique user where claimed_at and superseded_at both null; expires_at > created_at; not both claimed/superseded; claimed_at if present is >=created_at and <expires_at; superseded_at if present is >=created_at. Index user/created_at for history; digest lookup unique index and default FK index. Exact digest format/client bounds/aware timestamps/input UUIDs validated by model/service; ORM save/bulk writes do not imply full_clean. No plaintext tokens, Google code/client secret, email body or provider response stored.

Lifecycle: one pending row (including expired but unmarked rows) occupies unique slot; start supersedes it before insertion, atomically. Claim leaves row with claimed_at set and cannot be replayed. New start invalidates only prior pending attempts, not work already claimed. Post-claim generation comparisons still guard publication; no cancellation guarantee for in-flight network operations is implied.

Internal service proposal in accounts/oauth_attempts.py:
- create_oauth_attempt(user_id, session_key, client_id, expected_generation): returns raw state plus attempt metadata to trusted caller with secret hidden from repr.
- claim_oauth_attempt(raw_state, user_id, session_key, client_id): returns safe immutable attempt context including captured generation/client ID; never credential/file/network work.
- Validate exact live django_session row, expiry, signed stored user/backend/password-auth hash against freshly loaded active/verified/superuser account. Do not accept an arbitrary user ID/session string merely because supplied by internal caller. No new session/login or session mutations.
- Consistent lock order User then Session then Attempt. Sample time after locks. Invalid/mismatched inputs do not consume/supersede another person's attempt. Missing/expired/logged-out/changed sessions or revoked roles fail safely.
- Own short outermost committed transactions; reject nested transaction use so returned claim cannot be rolled back after a future external exchange. No database/file locks across external work. Future caller obtains SenderState before create; this package accepts/validates generation but does not call/configure real store.
- Invalid/expired/replayed/mismatched claim uses one static internal invalid-attempt error without state/session/provider details. Permission and input errors likewise safe; HTTP mappings not part of this proposal.

A recommended: retain attempt rows with user FK PROTECT, matching existing verification-token history. Retain minimal metadata for lifecycle inspection; no automatic cleanup yet. User ORM deletion blocked until separately approved cleanup removes retained rows. Existing verification-token history independently can block deletion too. History is not a full audit trail and does not prove Google authorization/token exchange/sender success. Storage grows per rare admin connection; retention duration/cleanup needs later review.

B: same lifecycle/schema, user FK CASCADE. Keep rows while account exists but delete them alongside that user through Django ORM; easier eventual disposal of ephemeral metadata, less retained history. Does not add account deletion endpoint or bypass existing token-history PROTECT. No automatic time-based cleanup under either option.

Tradeoffs: A adds deletion coordination and growing metadata storage, retains troubleshooting context; B simpler attempt disposal with loss of account-linked history. Same service complexity/provider cost, no significant measured performance difference. Both use existing dependencies/PostgreSQL. Field/constraint decisions become more expensive to reverse after migrations/callers/data exist; FK policy can be migrated later only after reviewing deletion consequences. Recommendation A for consistency with current explicit cleanup boundaries, not a compliance mandate.

Owner choice needed: D-033 A or B (including common schema/service contract), or changes requested. Independently approve WP-01b-7 only after D-033 resolved.

Primary implementation references reviewed: https://docs.djangoproject.com/en/5.2/topics/db/transactions/ (outermost durable atomic blocks); https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update (row locks); https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.on_delete (PROTECT/CASCADE). Schema/service proposal is our design, not mandated by those sources.

## WP-01b-7 approval

Owner instruction: `D-033 A; Approved WP-01b-7`. D-033 A common schema/service and retained-history PROTECT approved, along with internal attempt package. No owner rationale/date inferred. Precheck:1 account/eligible administrator,0 verification tokens,10 tables; dedicated test DB absent and sender volume empty. Implementation in progress; no Google/config/key/HTTP/frontend/dependency work authorized.

## WP-01b-7 completion

Status: verified. Owner instruction: `D-033 A; Approved WP-01b-7`. Implements D-031 B/D-032 A/D-033 A without changing their approved rules. Earlier pending-schema/package statements are history superseded by this explicit approval and result.

OAuthConnectionAttempt, create_oauth_attempt/claim_oauth_attempt, committed transaction boundary/live-session revalidation, retained PROTECT history and27 synthetic tests implemented. Reviewed accounts.0003 creates only the new table/constraints/indexes; applied successfully. Focused27 tests passed on first run3.718s; full112 passed on first run22.435s. Django/no-drift/schema checks passed.

Postcheck1 account/eligible admin,0 verification tokens,0 OAuth attempts,11 tables, no test DB; sender volume empty/key unset; all3 services healthy. No provider/network/HTTP/frontend/dependency/config/key changes. No next package approved. Actual interfaces and limits: components/gmail-oauth-attempts.md; ADR-011 updated. Next review OAuth API/transport/provider decisions, including PKCE/callback log handling, before separately approved integration.

WP-01b-7 final-review verification: malformed timestamp handling hardened within approved model validation; intermediate regression had1 error, fixed. Final112 tests passed25.630s/no-drift passed. No decision changed; failure/fix recorded in TESTING_AND_EVALUATION.md.

## D-034 — Google callback responsibility and browser transport

Status: approved. Owner instruction: `D-034 A, D-035 A`. D-034 A direct Django callback direction selected; exact HTTP contract and package unapproved. Relevant DL-01 support, specification sections7/9/10, D-007 sessions, D-020 B Web OAuth and D-031/D-032/D-033 attempt lifecycle.

What/why: decide whether Google's browser return goes directly to Django or first reaches a React callback page. Google web-server flow returns short-lived authorization code/state or denial in query parameters. Existing runserver/default proxy diagnostics are not an approved callback-redaction solution; no real callback should be enabled before request/error logging is verified safe.

Common proposed boundaries: Connect initiation uses an administrator-only CSRF-protected POST. Callback validates current administrator/session and claims state once before backend-only exchange. No Google tokens/client secret returned to React. Both options need strict input limits/duplicates handling, no-store/no-referrer, safe errors, callback query redaction in every configured server/proxy/error path and fixed allowlisted result navigation. No untrusted next/redirect URL. Ordinary DocInsight auth remains sessions, not JWT/Google login. Exact route/payload/status/error and fixed result-page contracts follow choice; not approved by this direction alone.

A recommended: Google returns to a Django callback endpoint exposed under the same frontend origin via /api proxy. Django validates/claims/exchanges, then redirects to a fixed clean result/settings URL without code/state. React receives only a safe outcome/status. Future log work covers Django development request logger plus Vite proxy/error diagnostics; production reverse-proxy logging still separately reviewed before deployment. No result UI is currently present; it needs its own approved implementation scope.

B: Google returns to a dedicated React callback route. React reads code/state into transient memory, removes URL query from current history, then POSTs to Django with CSRF/session. Django still validates/claims/exchanges. Additional callback component/effect/API and reload/error state handling; code exposed to application JavaScript transiently and initial frontend URL still requires log/referrer safeguards. No localStorage/sessionStorage, provider token in browser or browser-side exchange.

Tradeoffs: A fewer moving parts and no React code handling, standard server-owned exchange; backend callback is a protocol-specific state-protected GET, unlike ordinary CSRF-header-protected POST APIs. B familiar JSON mutation contract/CSRF relay but more browser secret handling, failure states and implementation/review effort. Both need React outcome UI eventually, same-origin deployment and safe logging; neither adds dependencies/provider fees or a measured latency benefit. A easier maintenance/reasoning here. Changing after Google client setup requires redirect-URI and client/UI coordination, so decide before setup.

Owner choice needed: D-034 A or B. Approval selects responsibility/transport direction only. Exact endpoints, response/errors, redirect URL, provider limits, setup, real calls and package remain separate review.

## D-035 — PKCE for authorization-code exchange

Status: approved. Owner instruction: `D-034 A, D-035 A`. D-035 A S256/encrypted temporary verifier direction selected; exact schema/service/package unapproved. Relevant DL-01 support, specification section10, D-020 Web OAuth and attempt lifecycle D-031/D-032/D-033.

PKCE (Proof Key for Code Exchange) adds a fresh temporary backend secret called a verifier for each attempt. Authorization sends its S256 hash-derived challenge; code exchange must present the verifier. It complements state/session and confidential-client secret, does not establish Google sender identity or replace callback redaction. RFC9700 recommends PKCE for confidential clients; installed google-auth-oauthlib family exposes code_verifier support. Actual approved pinned1.5.0 behavior/provider compatibility will be checked before integration; no live token exchange has occurred.

A recommended: use S256 PKCE alongside current state/session checks and Web OAuth client secret. Generate verifier independently per attempt; keep it recoverable backend-only across redirect/restart. Proposed persistence: a nullable bounded encrypted verifier field on OAuthConnectionAttempt, using existing separately configured Fernet key (never Django SECRET_KEY), hidden from repr/HTTP/logs. Clear encrypted verifier on committed claim/supersession; claim returns plaintext to trusted adapter in memory only. Expiry alone does not run cleanup; expired pending ciphertext remains unusable and is removed on replacement/future approved cleanup. Claim must decrypt successfully before committing/clearing; malformed/wrong/missing key fails closed without consuming another valid attempt. No plaintext verifier in DB/session/browser. Model currently stores only metadata; this is an explicit new schema/service approval, not a claim PKCE is already built.

B: use Google's confidential Web OAuth authorization-code flow with existing state/session/client-secret validation and no PKCE. No temporary verifier/schema extension. Fewer fields/encryption paths/tests; lacks the additional code-exchange binding recommended by current OAuth security guidance. Does not remove state/CSRF/private storage/logging obligations. Future PKCE addition requires coordinating outstanding attempts and migration/callers. No claim B violates a universal confidential-client PKCE MUST.

Tradeoffs: A additional migration/encryption/lifecycle tests and key dependency for creating/claiming attempts; better defense against code misuse/injection, not universal prevention of token theft. Existing cryptography dependency/key-management boundary can be reused, no new provider fee/library needed. B faster initial exchange integration, simpler lifecycle but less defense. Performance impact unmeasured. A moderate reversible extension now; after active attempts exist, changes must retire/reject incompatible attempts deliberately. Missing key must leave sender unconfigured without breaking existing session API.

Owner choice needed: D-035 A or B. A approves PKCE/encrypted temporary verifier direction; exact field/constraints/migration, key helper/interfaces and bounded validation/cleanup contract must be presented in the next reviewable package before implementation. No real key, schema change or Google operation authorized by this proposal.

Primary references checked:
- https://developers.google.com/identity/protocols/oauth2/web-server (query callback and clean server redirect)
- https://www.rfc-editor.org/rfc/rfc9700.html (confidential-client PKCE recommendation)
- https://googleapis.dev/python/google-auth-oauthlib/latest/reference/google_auth_oauthlib.flow.html (Flow/code_verifier interface; current docs not proof of installed pinned implementation)
- https://developers.google.com/identity/openid-connect/reference (PKCE metadata vocabulary)

Encrypted-verifier persistence and callback architecture are our application proposals, not provider requirements. No additional Gmail/OIDC scope selected; sender identity/least-privilege scope and Google setup remain explicit later review.

## D-034/D-035 approval reconciliation

Owner instruction: `D-034 A, D-035 A`. Direct Django callback under frontend origin, clean fixed result navigation and S256 PKCE with backend-only encrypted temporary verifier selected. No additional rationale/date inferred. Earlier alternative/choice-needed wording is proposal history. No exact endpoint, verifier schema/migration, implementation package, real key or Google setup/call approved. See ADR-012; next D-036 and WP-01b-8 proposed below.

## D-036 — Exact PKCE schema and internal service lifecycle

Status: approved. Owner instruction: `D-036 B; Approved WP-01b-8`. Selected B including the common design; implemented and verified in WP-01b-8. Relevant DL-01 support, specification sections6/9/10, approved D-029 A encryption/D-033 A history/D-035 A PKCE.

Common design: add OAuthConnectionAttempt.encrypted_pkce_verifier as nullable CharField(max_length=1024, blank=True, default=None, editable=False). It contains ASCII Fernet ciphertext only, using GMAIL_CREDENTIAL_ENCRYPTION_KEY; never Django SECRET_KEY. No new key generation/provider/configuration in this package. Missing/malformed key safely leaves OAuth attempts unconfigured without blocking existing login/session API startup. Existing sender credential file is unchanged.

Generate independent32 random bytes per attempt, unpadded base64url verifier43 characters. Challenge is unpadded base64url(SHA256(ASCII(verifier))), method always S256, no plain fallback. Internal helpers validate verifier43-128 allowed RFC7636 characters; generated verifier fixed43. Version1 encrypted JSON envelope contains attempt_id, state_digest and verifier; strict keys/types/version/canonical UUID and expected ID/digest match. Binding prevents swapping otherwise valid ciphertext between attempt rows. Cap ciphertext at1024 ASCII characters before decryption and validate bounded decrypted record; no plaintext verifier/session/provider data logged or returned to browser. Encryption uses maintained Fernet, not a custom cipher.

Planned small oauth_pkce.py helper module owns generation/S256 transform and context-bound encryption/decryption/safe errors, depends on cryptography plus standard library, no database/file/network. Existing oauth_attempts.py keeps authorization/locks/transactions. No new abstraction framework or model-provider adapter.

Keep existing create_oauth_attempt/claim_oauth_attempt arguments. IssuedOAuthAttempt gains code_challenge and code_challenge_method='S256' but never plaintext verifier. ClaimedOAuthAttempt gains code_verifier with repr=False; only trusted backend future exchange code may access it, never generic serialization/HTTP/logs. Issued state still sensitive and repr-hidden. Helper loads configured key lazily; tests inject synthetic settings, no real .env edit.

Start generates/encrypts new verifier and supersedes previous pending row atomically, clearing old ciphertext in same update. Failed creation/encryption rolls back supersession; valid authorized supersession invalidates only that administrator's prior pending attempt. Claim first checks user/session/state/expiry/client as today, then decrypts/verifies bound record, saves claimed_at and clears ciphertext in same committed transaction, returning verifier afterward in memory only. Wrong/missing key, corruption, missing verifier or context mismatch fails closed without claim/clear; no state-only legacy fallback. Failed save rolls back both claim and clearing. Expired pending ciphertext remains until authorized replacement or future separately approved cleanup; expiry never silently deletes history. Retain PROTECT/history and existing locks/generation context; no actual provider work or cancellation guarantee.

A: nullable field; enforce pending presence and terminal clearing in model/service/tests only. Historical pending NULL rows remain structurally allowed but unclaimable until replaced. Simpler migration/backward metadata compatibility; direct/bulk DB writes can leave inconsistent secret lifecycle.

B recommended: same nullable field plus DB check: pending (claimed_at/superseded_at both NULL) requires non-NULL nonempty encrypted verifier; claimed/superseded rows require NULL ciphertext. Model/service still validate actual encryption/bounds/context, which DB cannot prove. Stronger protection against bypass writes; fixtures/alternate writers must supply valid lifecycle shape. More constraint/migration tests, little additional runtime work, no measured performance claim.

Migration safety for B: precheck current rows; last verified live attempts0, not assumed current. If any legacy pending row exists, pause before migration and ask owner how to handle it; do not expire/supersede/delete/backfill/reset automatically. Existing terminal rows accept new NULL field. Generate/review expected0004 additive field/constraint only. No destructive migration authorized. A/B reversal later requires checking existing rows before constraint changes.

Tradeoffs: A easier legacy compatibility and fewer DB constraints, weaker bypass protection; B clearer invariant at storage boundary, coordinated migration/fixtures. Both existing libraries/one reused key, no provider fees, no automated key rotation/retention and no measured performance benefit. Field/interface changes affect internal callers before Google integration; inexpensive now, more coordination once outstanding attempts/provider adapters exist. Recommendation B: reinforce the explicit pending/terminal protocol without adding another table/service.

Original proposal requested D-036 choice and separate package approval. Resolved by actual instruction `D-036 B; Approved WP-01b-8`; symbols and behavior are now implemented/verified. Alternatives above are retained as decision history.

References reviewed: https://www.rfc-editor.org/rfc/rfc7636.html (verifier/S256/base64url); https://cryptography.io/en/50.0.2/fernet/ (authenticated recoverable encryption). Our envelope/field/constraints/key reuse are application design choices, not prescribed by PKCE. Google library/provider compatibility and real exchange remain separate integration checks.

## WP-01b-8 approval and completion

Owner instruction: `D-036 B; Approved WP-01b-8`. D-036 B approved; WP-01b-8 verified. Fresh aggregate precheck: users1, eligible administrators1, OAuth attempts0/pending0, test database0. Implement encrypted S256 lifecycle and DB shape constraint only; no provider or HTTP integration. Focused38/full123 passed; additive migration0004 applied; no provider/HTTP integration. Next action: review verified result, then separately decide/propose WP-01b-9.
