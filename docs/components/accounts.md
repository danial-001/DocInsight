# Accounts component

## Purpose, scope and decisions

WP-01b-1 supplies custom account persistence before other domain relationships. D-007, D-010 B, D-011 B, D-013 field details, D-016 A and D-017 A apply. Owner approved package with `Approved WP-01b-1`, including additive migrations and trusted-superuser behavior. DL-01 is partially implemented; WP-01b-2 adds login/session behavior below. Object/file isolation remains unimplemented.

## Actual interfaces

| File / symbol | Responsibility |
| --- | --- |
| backend/apps/accounts/models.py / User | AbstractBaseUser/PermissionsMixin schema; UUID/email/profile/status/verification, database uniqueness |
| backend/apps/accounts/managers.py / UserManager | normalize_email, create_user, create_superuser; input validation and password hashing before save |
| backend/apps/accounts/validators.py / validate_timezone | Reject unknown IANA timezone names and filesystem paths |
| backend/apps/accounts/validators.py / validate_password_length | Reject raw passwords longer than 128 before hashing |
| backend/apps/accounts/migrations/0001_initial.py | Initial user table, permission/group links and Lower(email) unique index |
| backend/apps/accounts/tests/test_models.py / UserModelTests | 13 database/validation/security-contract tests |
| backend/config/settings.py | AUTH_USER_MODEL, six registered apps, Django auth/contenttypes and password validators |

The six apps have AppConfig shells. accounts alone defines a model. Other domains have no models/services yet. WP-01b-1 introduced no HTTP interfaces; WP-01b-2 adds serializers/views/services/session authentication below. No tasks or React hooks exist.

## Creation flow

create_user(email,password=None,**fields) rejects privileged flags, normalizes full email with trim/lowercase, constructs User and runs full_clean excluding not-yet-set password. Provided password is capped at128, checked using Django minimum12/similarity/common/numeric validators, hashed with set_password and persisted. Password None sets an unusable password, so it cannot authenticate. Manager raises ValidationError/ValueError for invalid inputs; PostgreSQL can raise IntegrityError if concurrent/bypassing writes conflict.

create_superuser is explicitly trusted administrative provisioning: requires active/staff/superuser true and a provided valid password, sets email_verified_at to now unless supplied, then uses the same validation/hash flow. Ordinary create_user never silently marks email verified. Trusted management code may explicitly supply the timestamp; no browser can invoke this manager directly.

User.clean and save canonicalize email. Model full_clean must be called when validating direct model inputs; save does not automatically perform every validator. Bulk updates bypass model normalization/validation. The Lower(email) unique index still rejects case-only duplicates through bypass paths; arbitrary whitespace canonicalization is a manager/model write rule, not a DB check. UUID is the User primary key; Django's built-in permission/group metadata use Django's own IDs.

## State and authorization

is_active controls suspension; email_verified_at independently records verification. is_email_verified is a derived property, not another stored field. A verification timestamp does not reactivate a suspended user. Times use aware UTC, timezone is a display preference. Groups/user_permissions are many-to-many links supplied by PermissionsMixin.

WP-01b-1 supplied no login gate. WP-01b-2 now uses VerifiedAccountBackend for credential and existing-session eligibility; standard IsAuthenticated denies anonymous/ineligible requests. The default Django ModelBackend alone would not enforce email verification. No private-file or cross-user resource isolation claim exists yet. No admin UI, account-deletion workflow, seed or provider implemented. Internal token model/services added under WP-01b-3 below; user deletion now protected when token history exists.

## Verification and limitations

13 tests passed on a newly created separate test_docinsight database, removed afterward by Django. Migration generation/plan reviewed; no drift; system checks passed; local database inspected empty before approved migrations. Eight tables resulted, zero users, no auth_user table; exact and case-insensitive email uniqueness indexes confirmed. Initial test fixture passwordpassword was not in Django's common-password list; replaced with known common password and rerun passed without changing policy.

Example: synthetic mixed-case email and valid password create an unverified UUID account with hash; a case-only duplicate fails. Marking verification on a suspended fixture preserves suspension. These are tests, not a complete signup demonstration.

## WP-01b-2: Session authentication API

Owner instruction: Approved `WP-01B-2`. Relevant DL-01, D-007/D-011/D-012/D-013/D-016/D-017. This adds HTTP authentication, not registration or document ownership enforcement. No dependency additions, tasks or frontend hooks.

### Interfaces, ownership and dependencies

| Location / public symbols | Owns / inputs and outputs |
| --- | --- |
| authentication.py / VerifiedAccountBackend | Extends installed Django ModelBackend; checks active plus verified for password authentication and get_user session resolution; inherits password hashing/timing safeguards |
| authentication.py / AccountSessionAuthentication | Extends DRF SessionAuthentication; maps CSRF denial to approved csrf_failed code, preserves standard403 anonymous behavior |
| serializers.py / LoginSerializer | Required email max254, canonical trim/lowercase; required string password max128 without trimming, write-only; validation errors never echo password |
| serializers.py / UserSerializer | Read-only id/email/first_name/last_name/timezone representation; never password/hash/privilege flags |
| services.py / login_account | Validated credentials to Django authenticate/login; generic failure for ineligible accounts; rotates retained session key on same-user relogin; sets absolute eight-hour expiry; returns User |
| services.py / logout_account | Django logout flushes session, no account deletion |
| views.py / CsrfView, LoginView, MeView, LogoutView | HTTP input/output through serializers/services; explicit csrf_protect on login/logout dispatch (even anonymous); only login has LoginThrottle |
| throttles.py / LoginThrottle | Local10/minute login attempts keyed by REMOTE_ADDR only; inherits DRF429/Retry-After behavior |
| urls.py | Four /api/v1/auth routes; no trailing slash |
| backend/config/middleware.py / RequestIDMiddleware | Generates UUID before downstream processing, attaches X-Request-ID and auth-path no-store; ignores supplied ID |
| backend/config/exceptions.py / error_body, api_exception_handler, csrf_failure, InvalidCredentials | Stable JSON error envelope, safe framework/credential/CSRF errors; unexpected API errors500 without diagnostics |
| backend/config/settings.py | Sessions app/middleware ordering, verified backend, DRF defaults, cache, session/cookie policies |
| tests/test_auth_api.py / AuthAPITests |14 HTTP tests with synthetic users and enforce_csrf_checks=True; test-only failure/permission/mutation routes not production interfaces |

Models own stored identity/constraints. Serializers validate/represent. Views handle HTTP. Services coordinate login/session business rules. Built-in Django database sessions own persistence. Standard IsAuthenticated is reused; no custom permissions wrapper or extra abstraction is needed. No async tasks introduced.

### Example data flow

1. Browser GET csrf receives a masked token and cookie. API client retains cookies.
2. POST login sends JSON email/password, CSRF cookie and X-CSRFToken. Explicit anonymous CSRF enforcement precedes view validation/throttle. Serializer caps password before backend hash work.
3. Service authenticates through VerifiedAccountBackend. Wrong, unknown, unverified, suspended and unusable-password users fail generically. Successful Django login rotates CSRF; the service ensures session key rotation even on same-user relogin, then stores an absolute expiry timestamp.
4. Response contains safe user plus fresh csrf_token. Database session stores signed serialized identity/backend/auth-hash and expiry, not a plaintext password. Cookie identifies the session; it is not a JWT. CSRF token is not a substitute for login.
5. GET me loads session/user, rechecks active/verified and returns own profile. Separate client sessions retain separate identities. This does not establish future collection/document isolation.
6. POST logout requires current CSRF and flushes session. Repeat anonymous logout with valid CSRF returns204. Suspended users can still log out.

### Errors, security and limits

API_CONTRACT.md owns exact payload/status descriptions. No-store applies to all implemented auth paths including errors. Local HttpOnly host-only SameSite=Lax session cookie has Secure disabled for DEBUG local HTTP; DEBUG false enables Secure but does not constitute configured production deployment. CSRF cookie follows local/secure setting. Login deadline is fixed eight hours, session reads and later writes do not extend it. Expired database rows may remain until Django clearsessions maintenance; no scheduling added.

Django session authentication alone would not enforce anonymous login CSRF, hence csrf_protect is explicit. SessionAuthentication CSRF remains for future protected unsafe requests; tests exercise it using a test-only mutation view. Account verification remains separate from suspension and is rechecked on session resolution. Generic login failures hide eligibility in response contents; no timing-side-channel equivalence is claimed.

Local throttle resets on restart, is non-atomic and may group Vite proxy users. Not brute-force protection. Credentials never returned/logged by application code; diagnostic tracing and hosted operational logging are not built. Unknown routing-level URLs use Django's ordinary404 rather than the DRF envelope. No registration/verification HTTP/mail/OAuth/admin/seed/UI implemented; WP-01b-3 internal token lifecycle is documented below. No real accounts provisioned.

### Actual verification

27 account tests passed (13 model,14 API) in a newly migrated/destroyed test DB. Tests cover safe representation, anonymous/verified/suspended/unusable users, independent clients, expiry/no renewal, initial and repeated-login rotation, logout replay, explicit anonymous and authenticated CSRF, origin rejection, password validation-before-authentication, request IDs/no-store, cookie attributes, throttle key/recovery and safe Django/DRF/unexpected errors. Tests use synthetic verification timestamps; no email delivery is claimed. System check/drift check passed; sessions0001 plan reviewed/applied. Proxy smoke passed for csrf200, anonymous me403, login validation400 and logout204. No browser-render or real-user login demo yet.
## WP-01b-3: Internal verification-token lifecycle

Owner instruction: Approved `WP-01b-3`. Relevant DL-01 verified-account foundation and owner-added verification scope; D-017 A/D-018 B/D-023 B. Purpose: preserve link issuance history and enforce expiry/revocation/single use before connecting HTTP signup and real Gmail delivery. No serializers/views/tasks/hooks added in this package.

### Actual interfaces and responsibilities

| File / symbol | Responsibility / input / output |
| --- | --- |
| backend/apps/accounts/models.py / EmailVerificationToken | Digest/lifecycle persistence and approved constraints; DATA_MODEL.md owns field details |
| migrations/0002_emailverificationtoken.py | Additive table/index/check/FK migration; no existing data deletion/rewrite |
| verification.py / issue_verification_token(user_id) | Trusted existing user UUID -> raw token string in memory; None for already verified user; VerificationCooldown with retry_after seconds during60-second window; missing user raises User.DoesNotExist |
| verification.py / consume_verification_token(raw_token) | Raw64-hex string -> verified User; malformed/unknown/expired/used/revoked/already-verified all raise InvalidVerificationLink with code invalid_verification_link and generic message |
| verification.py / TOKEN_LIFETIME, ISSUANCE_COOLDOWN | Approved one-hour lifetime and60-second cooldown constants |
| verification.py / _token_digest | Private SHA256 of ASCII token text; never an authentication/session credential |
| tests/test_verification.py / VerificationTests |16 lifecycle/schema/rollback tests with synthetic users; no email fixture/provider |
| tests/test_verification.py / VerificationConcurrencyTests |4 real PostgreSQL races on independent connections with bounded synchronization/DB timeouts |

Dependencies: existing Django ORM/User/PostgreSQL; standard-library secrets, hashlib, re, math and timedelta. No extra packages, HTTP permissions or delivery adapter. Domain exceptions have safe static messages; raw secret never included. Caller must not expose/log raw token or errors with local variable dumps. No token HTTP endpoint exists.

### Issuance flow and transaction boundary

Service enters transaction.atomic and locks User before reading timestamp/token history. Already verified means no changes/None. Otherwise latest issuance controls cooldown; retry_after rounds remaining seconds up. After cooldown, secrets.token_hex(32) creates secret; previous outstanding row (including expired) is revoked, then a new unique digest record is created with one-hour expiry. Return raw token only to trusted calling code. Retain old row, no deletion. If insert fails, transaction rolls back prior revocation. Issuing for an inactive account does not change suspension.

The decorator may run inside a larger caller transaction. Raw token return does not mean the outer transaction committed; future inline sender must wait for outermost commit before Gmail calls. Raw token remains only in memory; never use digest as link token. This package performs no external operation while holding locks, sends no email and does not create accounts. Duplicate secret/digest integrity failures propagate and roll back; no automatic provider retry implied.

### Consumption flow and concurrency

Reject malformed input before lookup; derive digest and discover owner without taking a token lock. Lock User first, then re-read/lock matching token. Sample time after lock wait. Recheck verified account, expiry (now >= expires_at invalid), consumed/revoked state; only then mark consumed and set User.email_verified_at atomically. Never touch is_active, password, profile or session. If User save fails, token consumption rolls back too.

Both mutation paths follow User-first locking. For the same account, two resends serialize: first issues, second sees cooldown. Two confirmations serialize: first verifies, second sees already verified/used and fails. Resend versus confirmation may validly end in either (a) confirmation wins, no reissue; or (b) resend wins, old link revoked and confirmation fails. Tests assert only these consistent states. Unrelated accounts have separate row locks. Direct ORM/admin scripts must not bypass these service rules; DB constraints alone do not implement single-use/cooldown or automatically verify User.

### Authorization, failure and limitations

These are internal trusted functions, not browser interfaces. No cross-user lookup endpoint or token listing exists. Consume verifies the user attached to that exact token; a different synthetic account stays unverified in tests. Future HTTP wrapper must enforce CSRF, generic signup/resend acknowledgements, local request limits and safe errors. Account eligibility/possession is not proof of inbox delivery or document authorization.

Expired/used/revoked records remain stored. No retention/deletion service approved; PROTECT intentionally blocks implicit history deletion. No mail diagnostic state, queued job or recoverable secret persistence. D-024 A requires future inline email after commit, with actual limits/failure diagnostics still to review. No signup/confirmation UI or frontend hooks, admin/seed, Gmail setup/provider call, private document isolation or full MVP completion claim.

### Example and actual verification

A synthetic pending user receives token1 from issue_verification_token in a test. Immediate resend raises cooldown without mutation. At60 seconds token2 is issued and token1 record revoked. token1 fails; token2 sets verified timestamp once, leaving a suspended account inactive. No session created. These are internal lifecycle tests, not sent verification emails.

Full47 account tests passed:13 model,14 existing API,16 lifecycle/schema tests and4 PostgreSQL concurrency tests. Database created/migrated/destroyed separately. System check and no-drift check passed; additive migration reviewed/applied; local constraints inspected; zero live users/token records. See TESTING_AND_EVALUATION.md for commands. Frontend/provider checks not applicable to this internal package; previous browser gate remains unverified.
## WP-01b-4: Sender-admin permission and trusted CLI provisioning checks

Owner instruction: Approved `WP-01b-4`. D-027 A grants sender administration to every authenticated active verified superuser. Relevant DL-01 and owner-added D-020 B. Ordinary/staff-only users must not administer application sender credentials. No Gmail endpoint/UI/provider exists yet; this package supplies the reusable guard and verifies existing provisioning command.

### Actual symbols and ownership

- backend/apps/accounts/permissions.py / CanManageEmailSender(BasePermission): request.user -> boolean; requires is_authenticated, is_active, is_email_verified and is_superuser. No DB writes, credential handling or OAuth logic. Depends on existing User and DRF permission lifecycle; session backend loads fresh user on each request. No is_staff shortcut or single-owner UUID configuration.
- tests/test_sender_permissions.py / SenderPermissionTests:5 tests, test-only SenderPermissionProbe view at /permission-probe. No production route added, no provider simulated. Tests independently check guard matrix and real database-backed session/CSRF behavior; force_login is a test-only session setup, not a production login bypass.
- tests/test_admin_provisioning.py / AdminProvisioningTests:6 tests of Django's installed createsuperuser command with captured output, synthetic inputs/environment and mocked hidden password prompts/TTY. Not real terminal or real email verification evidence. Existing UserManager.create_superuser remains unchanged; no custom command added.

### Request and setup flow

Future sender views must attach CanManageEmailSender and retain session authentication/CSRF plus separately approved OAuth state/session binding. Guard alone is not a complete OAuth security implementation. In current test-only view, anonymous/ineligible sessions yield403 authentication_required; verified ordinary/staff users yield403 permission_denied; active verified superusers pass. Allowed unsafe requests still need CSRF (403 csrf_failed otherwise). Removing superuser status denies next request without logging out; suspension/verification removal invalidates identity through existing backend. Guard checks eligibility itself as defense for other trusted authentication contexts.

Trusted setup uses existing interactive command from local PowerShell:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Keep TTY, no -T. Owner chooses email/password privately at prompts; do not paste into chat or CLI args. Password entry hidden by Django/getpass. Manager normalizes email, validates/hashes password, enforces active/staff/superuser true and explicitly sets verified timestamp for trusted administrative provisioning. This bootstraps login before Gmail connection; timestamp is not proof of email inbox ownership. Ordinary signup must never accept those privileged/verification fields (approved D-025, still unimplemented). Duplicate exact/case-equivalent addresses rejected without resetting/promoting existing user. Weak/missing/overlong credentials rejected; even answering Django's interactive validation-bypass prompt yes cannot override manager policy. Non-TTY interactive invocation skips creation, hence setup requires TTY. No real command was executed to create an application account; owner-run setup remains unperformed.

### Verification and limits

First58-test account run passed: previous47 plus5 permission and6 CLI integration tests. Permission tests cover anonymous/ordinary/staff/pending/suspended/two allowed superusers, direct guard eligibility, existing session role/status revocation, required CSRF and CSRF not granting authorization. Command tests cover interactive valid hashed/trusted normalized account, validation bypass rejection, weak/overlong/missing password, duplicate preservation and non-TTY skip. Database tests use isolated Django-owned test DB, destroyed afterward. System check/no migration drift passed; no migration/new dependency/manager change. Postcheck live DB retains ten tables and zero users/tokens.

No production sender route means authorization is currently verified through test-only route, not a working Gmail connection feature. No actual owner account, admin UI, seed, signup/email/OAuth, provider call or frontend introduced. Real terminal setup is documented, not claimed completed. Every future superuser gains sender access under chosen policy; intentional trust boundary. Full document/file/citation isolation and MVP still incomplete. API_CONTRACT.md owns endpoint/error status details; no existing response fields changed.