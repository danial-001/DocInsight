# ADR-011: OAuth connection-attempt persistence and policy

**Status:** approved; implemented and verified under WP-01b-7.
**Decisions:** D-031 B, D-032 A, D-033 A.
**Owner instruction:** `D-031 B, D-032 A`. No date or additional rationale inferred.

## Context and alternatives

Future Google callback must correspond to an attempt by the currently eligible administrator in the initiating login session, expire and be accepted once. Existing session cookie identifies the account; existing sender-store generation handles stale publication, not callback legitimacy.

D-031 A coordinated existing database sessions; B dedicated attempt model/service. Owner selected B. A avoids application table but safe concurrent claims require session-save integration. B adds explicit schema/migration/tests and independent lifecycle coordination. No new provider/dependency/cost; no measured performance benefit.

D-032 common policy: random32-byte state/digest-only persistence, ten-minute expiry, current administrator/exact session binding, one atomic claim before provider exchange and captured credential-store generation. A one pending attempt per administrator across sessions; B multiple pending attempts with reviewed cap. Owner selected A: new start supersedes earlier pending state, other admins independent. A simpler lifecycle but older tabs fail; B more parallel-tab convenience and complexity.

## Consequences and boundaries

Attempt metadata belongs to accounts; refresh credentials remain in approved private encrypted file, no Google tokens in attempt table/session. Future network work runs after a committed claim outside locks. Failure after claim requires new start, not replay. Attempt validity does not prove sender identity, Google consent, refresh-token validity or delivery. A previously claimed operation is no longer pending; cancellation of its external work is not promised.

Changing persistence later requires retiring/migrating pending attempts. Owner subsequently instructed `D-033 A; Approved WP-01b-7`, approving detailed fields/constraints, PROTECT history, live-session service validation and outermost committed transactions. These are now implemented; no cleanup automation added. PKCE/provider transport/endpoints/log redaction/real setup/UI remain later review.

## References and implementation status

Implemented accounts/models.py: OAuthConnectionAttempt; accounts/oauth_attempts.py: create_oauth_attempt/claim_oauth_attempt and immutable results/errors; migrations/0003_oauthconnectionattempt.py; tests/test_oauth_attempts.py. Details: ../components/gmail-oauth-attempts.md.27 new tests include4 PostgreSQL races; full112 regressions, migration/system/no-drift/schema/postchecks passed. Live history remains empty; no real Google flow. CP-11/12 in UNDERSTANDING_CHECKPOINTS.md explain distinctions and metadata limits.

Sources: https://developers.google.com/identity/protocols/oauth2/web-server ; https://docs.djangoproject.com/en/5.2/topics/http/sessions/ . Our chosen storage/TTL/lifecycle are application design choices.


## WP-01b-8 extension

D-036 B now adds encrypted PKCE lifecycle and DB shape enforcement to the existing attempt protocol. See ADR-012 and components/gmail-oauth-attempts.md for actual helper/interfaces and verification. Prior metadata-only descriptions are historical; existing authorization, lock ordering, commit, generation and retained history decisions remain.
