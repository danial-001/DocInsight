# API contract

## Implemented: WP-01b-2 authentication

Owner instruction: Approved `WP-01B-2`. Relevant DL-01, D-007/D-011/D-012/D-013/D-016/D-017. Routes have no trailing slash. Same-origin browser requests use session cookies and CSRF; Vite proxies /api locally. No JWT or Google login. Login/register UI does not exist.

| Method/path | Input / authorization | Success |
| --- | --- | --- |
| GET /api/v1/auth/csrf | Anonymous allowed | 200 `{ "csrf_token": "<masked token>" }`; sets CSRF cookie |
| POST /api/v1/auth/login | JSON email/password; CSRF cookie and X-CSRFToken required even when anonymous | 200 `{ "user": { "id": "<uuid>", "email": "user@example.com", "first_name": "", "last_name": "", "timezone": "UTC" }, "csrf_token": "<fresh masked token>" }` |
| GET /api/v1/auth/me | Verified active session required | 200 `{ "user": { ...same safe fields... } }` |
| POST /api/v1/auth/logout | CSRF required; anonymous/suspended allowed | 204 empty body, session invalidated; repeat with valid CSRF also 204 |

Email is trimmed and lowercased. Login requires valid email max254 and a nonempty string password max128 (not whitespace-trimmed). Invalid input returns 400 validation_error; unknown/wrong/unusable-password/unverified/inactive accounts share 400 invalid_credentials. Password strength validators apply at creation, not retroactively at login. Use the fresh token after login because both session key and CSRF secret rotate. No automatic login through verification exists.

## Session, CSRF and error rules

Django database sessions use django_session. Absolute eight-hour deadline set on login, no sliding renewal, persistent cookie. Host-only HttpOnly SameSite=Lax session cookie; Secure disabled only in current DEBUG local HTTP configuration, enabled with DEBUG false. CSRF cookie is host-only, SameSite=Lax and follows the same Secure setting; it is not an authentication credential. No hosted deployment is configured. Authentication backend rechecks is_active and email_verified_at when resolving sessions, so suspension or verification removal blocks /me.

Every auth-path response has Cache-Control: no-store and server-generated UUID X-Request-ID. Caller-provided request IDs are ignored. Errors use:

```json
{"error":{"code":"authentication_required","message":"Please log in to continue.","field_errors":{},"request_id":"<server UUID matching X-Request-ID>"}}
```

| Status/code | Meaning |
| --- | --- |
| 400 validation_error | Field errors in field_errors; no password echoed |
| 400 invalid_credentials | Generic credential/account eligibility failure |
| 400 parse_error | Malformed JSON; safe generic diagnostic |
| 403 authentication_required | Missing, expired or ineligible session; owner-approved D-012 variation from spec401 |
| 403 csrf_failed | Missing/invalid token or disallowed origin |
| 403 permission_denied | Authenticated permission denial |
| 404 not_found | Resource absent in an API view |
| 405 method_not_allowed | Unsupported method |
| 415 unsupported_media_type | Unsupported request content type |
| 429 rate_limited | Login10/minute/REMOTE_ADDR, with Retry-After |
| 500 internal_error | Safe unexpected API error; exception details not returned |

Login throttle uses process-local LocMemCache, ignores X-Forwarded-For, resets on restart and is non-atomic. Local proxy traffic can share an address. This is basic request limiting, not durable brute-force protection. CSRF runs before anonymous login/logout parsing and throttling. Responses are JSON for implemented API routes; routing-level unknown URLs outside these views still use Django's ordinary 404 handling.

## Implementation and checks

backend/apps/accounts/urls.py, views.py (CsrfView/LoginView/MeView/LogoutView), serializers.py (LoginSerializer/UserSerializer), services.py (login_account/logout_account), authentication.py (VerifiedAccountBackend/AccountSessionAuthentication), throttles.py (LoginThrottle); backend/config/settings.py, urls.py, middleware.py and exceptions.py.

27 account tests passed (13 model,14 API), including CSRF enforcement, expiry/rotation, logout replay, safe failures, throttling and two independent profile sessions. Local Vite proxy smoke passed for CSRF, anonymous /me, login validation and anonymous logout. No browser UI or complete domain isolation verified.

## Remaining contract reviews

Registration/verification/resend HTTP payloads and delivery failure semantics; owner-only Gmail authorization/bootstrap and connect APIs; collection/file ownership and private streaming; upload/jobs/retry; revision/correction; question/evidence/citation; pagination, quotas and deletion remain unimplemented and require package/design review. D-018 through D-024 approve verification/provider/registration directions; WP-01b-3 implements internal token model/services only, not these unresolved HTTP/provider contracts.
## WP-01b-3 internal lifecycle (not HTTP)

EmailVerificationToken and issue_verification_token(user_id)/consume_verification_token(raw_token) now exist in accounts/models.py and verification.py.47 account tests passed, including20 token tests. These functions are trusted backend interfaces, not registered routes. Existing four session endpoints unchanged. No registration/verification/resend endpoint, confirmation page or email delivery exists. See components/accounts.md for return values/errors/transaction contract and DATA_MODEL.md for constraints. Raw token must not become an HTTP response/log or queued payload; future sender passes it only in the approved verification message. Future HTTP layer must enforce approved CSRF/generic acknowledgements/throttles; no such layer is silently implied here.
## Approved, unimplemented registration contract (D-025/D-026)

Owner instructions: `D-025 Approved`, `D-026 A`. POST /api/v1/auth/register (email/password, optional names/timezone) and POST /api/v1/auth/verification/resend (email) return generic202 under approved rules; POST /api/v1/auth/verification/confirm (token) returns204 success,400 invalid_verification_link for invalid proof. All explicitly CSRF-protected, no-store and shared request/error IDs; no automatic login. See D-025 for exact messages, validation, limits and eligibility; delivery-wide503 preflight/limits/diagnostics remain unresolved. These routes do not exist yet.

Email link format approved: /verify-email#token=<secret>. Future React page reads token into temporary memory, immediately removes fragment from current history entry, does not store/log it or automatically consume it. Explicit confirmation button obtains CSRF and posts token as JSON. Refresh after URL removal requires reopening email link. Component/layout/hooks and package not approved yet. Sender administration permissions pending D-027; no added privileges in current /me representation.
## Sender-admin authorization foundation (WP-01b-4)

CanManageEmailSender in accounts/permissions.py implements D-027 A. It is not yet attached to a production sender endpoint because no such route exists. Test-only protected view verified real session permissions/CSRF;58 account tests passed. Future sender operations require active verified superuser identity plus CSRF for mutations and separately reviewed OAuth state/callback protection. Existing /me/login user representation unchanged; no admin flags or capability field added. D-025 register/verify/resend and D-026 link transport remain approved, unimplemented contracts. No fake provider substitutes for real delivery.

## WP-01b-6 internal boundary — no HTTP additions

SenderCredentialStore.read/replace/clear are trusted backend Python interfaces, documented in [store component](components/gmail-sender-store.md). SenderCredential/SenderState must not be serialized into HTTP responses. Domain failures have safe internal codes; HTTP mappings are not approved by this package.

Existing csrf/login/me/logout routes are unchanged. No sender status/connect/callback/disconnect route or OAuth state/session contract implemented. Future protected services must enforce CanManageEmailSender and appropriate CSRF/OAuth state checks before invoking storage. A usable local record would not establish sender identity or Google token validity.

## WP-01b-7 — internal OAuth attempt interfaces, no routes

create_oauth_attempt(user_id, session_key, client_id, expected_generation) and claim_oauth_attempt(raw_state, user_id, session_key, client_id) implemented in accounts/oauth_attempts.py. IssuedOAuthAttempt contains transient raw state and must never be generically serialized/logged; ClaimedOAuthAttempt returns only ID/user/client/generation context. See [component](components/gmail-oauth-attempts.md) for exact inputs and errors.

Internal codes invalid_oauth_attempt, oauth_attempt_invalid_input and oauth_attempt_transaction_required are not approved HTTP mappings. Existing four session routes unchanged. No production sender route, CSRF/callback HTTP handling or Google exchange added. Future protected view must provide actual current identity/client configuration, enforce approved CSRF/OAuth protocol, invoke service outside outer transactions, then perform provider work after commit.

## WP-01b-8 internal result extension (verified; no HTTP addition)

create_oauth_attempt inputs unchanged; IssuedOAuthAttempt adds code_challenge and code_challenge_method=S256, never plaintext verifier. claim_oauth_attempt inputs unchanged; ClaimedOAuthAttempt adds repr-hidden code_verifier for trusted backend future exchange only. Never generically serialize either secret-bearing dataclass to HTTP/logs. OAuthPKCEConfigurationError and InvalidOAuthPKCE are static internal exceptions; HTTP mapping/callback contracts unapproved. Existing four session endpoints unchanged. See components/gmail-oauth-attempts.md for exact helper interfaces and errors.
