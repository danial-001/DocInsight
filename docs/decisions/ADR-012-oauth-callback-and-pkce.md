# ADR-012: Backend OAuth callback and PKCE

**Status:** approved. Local PKCE implemented/verified under D-036 B/WP-01b-8; direct callback remains direction only.
**Decisions:** D-034 A, D-035 A, D-036 B.
**Owner instruction:** `D-034 A, D-035 A`. No date/additional rationale inferred.

## Context and alternatives

D-034 A direct Django callback under same frontend origin versus B React code/state relay to backend. Owner selected A. Backend validates/claims/exchanges then redirects to a fixed clean result URL. Initiation remains administrator/session/CSRF-protected POST; callback uses session/state/permission checks. No client secret/provider token in React. Exact endpoints/results/errors/URLs/log handlers/UI unapproved.

A reduces browser code handling and component/error-state work; B provides JSON POST relay with more transient browser secret handling. Both need no-store/no-referrer and tested callback query redaction in all configured server/proxy/error paths before real integration. Local backend/proxy log safety is not currently verified. Changing callback later requires registered redirect-URI/client coordination. No fee or measured performance difference.

D-035 A S256 PKCE with temporary encrypted backend verifier versus B confidential code flow/state/client secret without PKCE. Owner selected A. Fresh verifier challenge binds code exchange; supplements existing state/session and sender generation. Extra schema/encryption/tests/key dependency, stronger exchange binding; B simpler but lacks additional recommended defense. No new library/provider fee or measured performance claim.

## Consequences and scope

Temporary verifier must survive redirect/restart reversibly encrypted using existing separate Fernet key, never Django SECRET_KEY. WP-01b-8 implements encrypted_pkce_verifier and accounts_oauth_pkce_shape, context-bound envelope/helpers and challenge/claim result extensions under D-036 B. On claim/supersession, ciphertext is cleared; raw verifier only trusted in-memory future exchange. Expiry is enforced without automatic history cleanup. No plaintext verifier in DB/session/browser/log.

Callback ownership/PKCE directions do not approve endpoints, schema, migration, package, real key, Google setup/consent/exchange/send, scopes or deployment. Existing provider/storage/attempt decisions remain; no implemented behavior superseded yet. Dedicated Gmail sender identity, scope, network budgets and error contracts still need review.

## References/status

[DECISION_LOG.md](../DECISION_LOG.md): D-034/D-035 approval and D-036 proposal; [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md): WP-01b-8 proposal. Existing [attempt service](../../backend/apps/accounts/oauth_attempts.py) now integrates [PKCE helpers](../../backend/apps/accounts/oauth_pkce.py); [store](../../backend/apps/accounts/sender_store.py) remains unchanged. CP-13/14 explain implemented local behavior/limits.

Primary references: https://developers.google.com/identity/protocols/oauth2/web-server ; https://www.rfc-editor.org/rfc/rfc9700.html ; https://www.rfc-editor.org/rfc/rfc7636.html ; https://cryptography.io/en/50.0.2/fernet/ . Protocol guidance supports choices, not exact application storage design.

## Implementation and verification

Owner instruction: `D-036 B; Approved WP-01b-8`. Selected common exact design plus DB shape check. Migration0004 adds only nullable encrypted field/check, no legacy pending rows found. New oauth_pkce.py owns generation/S256/strict bounded context-bound Fernet validation; oauth_attempts.py owns authorization/locks/atomic clearing/commit. Helper and lifecycle tests:38 focused/123 full account tests passed, Django/no-drift/schema checks passed. Real key unset; no callback/provider integration. Existing directions do not authorize next package. See component, TESTING_AND_EVALUATION.md and CURRENT_STATE.md for exact state/resume point.
