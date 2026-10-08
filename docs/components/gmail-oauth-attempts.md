# Gmail OAuth connection attempts

## Purpose and ownership

WP-01b-7 implements D-031 B/D-032 A/D-033 A under owner instruction `D-033 A; Approved WP-01b-7`. Supports DL-01 and specification sections6/7/9/10; does not complete authentication/resource isolation or Gmail connection.

An attempt links a future Google callback to the administrator and exact login session that initiated it. It expires and can be claimed once. Existing session authentication identifies the user; existing sender-store generation protects later credential publication. Neither replaces attempt validation. No Google authorization/code/token exchange occurs in this component.

The model stores metadata and database constraints. The service validates identity/input and coordinates transactions. No serializer, view, task or React hook is added. Future protected views must enforce CSRF/permission and the separately approved OAuth callback contract; internal checks do not create a public endpoint.

## Actual code

| File/symbol | Responsibility |
| --- | --- |
| [models.py](../../backend/apps/accounts/models.py): OAuthConnectionAttempt | Required User PROTECT relationship, hashes/context/timestamps, validation and constraints |
| [0003_oauthconnectionattempt.py](../../backend/apps/accounts/migrations/0003_oauthconnectionattempt.py) | Additive table/index/constraint migration |
| [oauth_attempts.py](../../backend/apps/accounts/oauth_attempts.py): create_oauth_attempt | Validate current identity, supersede pending attempt and commit new proof |
| oauth_attempts.py: claim_oauth_attempt | Validate/bind/check expiry and commit one accepted claim |
| oauth_attempts.py: IssuedOAuthAttempt / ClaimedOAuthAttempt | Frozen trusted internal return values; raw state hidden from issuance repr |
| [test_oauth_attempts.py](../../backend/apps/accounts/tests/test_oauth_attempts.py) |27 synthetic checks including4 actual PostgreSQL races |

Dependencies: existing Django/PostgreSQL/custom User/database sessions; Python secrets/hashlib/UUID/dataclasses. No new package, provider, cache or file-store operation.

## Model and constraints

OAuthConnectionAttempt fields: UUID id; required user FK with PROTECT/related_name oauth_connection_attempts; unique state_digest CharField64; session_digest CharField64; client_id CharField512; nullable expected_generation UUID; awareUTC created_at/expires_at and nullable claimed_at/superseded_at.

State is32 random bytes encoded as64 lowercase hex characters, persisted only as SHA256 of its ASCII representation. Session digest is SHA256 of the exact32-character Django database-session key. The digest is not a session authentication credential. Client ID is required nonempty bounded UTF-8; it identifies configured OAuth client, not Google mailbox. None generation means no sender file at snapshot; a cleared file has a UUID.

Database enforces unique state digest, one user row with claimed_at/superseded_at both null, expiry after creation, not both terminal timestamps, claim within [creation,expiry), and supersession at/after creation. Index user/created_at supports history; unique digest and standard FK indexes also exist. An expired unmarked row still occupies the pending unique slot until superseded. Model full_clean validates digest syntax, field types/lengths and aware timestamps; service constructs approved values. Direct/bulk ORM writes do not call full_clean; DB constraints do not independently validate digest format or exact ten-minute duration.

History is retained without automated cleanup. PROTECT blocks ORM user deletion while attempt rows remain; existing verification-token history can independently block deletion. No account-deletion endpoint or cleanup policy added. This metadata is not a complete audit log or evidence of Google consent/delivery.

## Public internal interfaces

`create_oauth_attempt(user_id, session_key, client_id, expected_generation)` requires UUID user ID, actual live session key, bounded configured client ID and UUID-or-None generation. Returns IssuedOAuthAttempt(id, state, expires_at) after commit. Raw state is sensitive transient memory: future code must not log, serialize generically, dump locals or persist it. Hiding repr does not prevent deliberate dataclass serialization from exposing it.

`claim_oauth_attempt(raw_state, user_id, session_key, client_id)` requires the issued state and same session/admin/client context. Returns ClaimedOAuthAttempt(id, user_id, client_id, expected_generation) after commit. No credential/token/state/session key in this result. The caller must later publish using captured generation, not read a fresh generation to bypass conflict.

No HTTP mapping of domain errors is approved. Static exceptions:

| Error/code | Meaning |
| --- | --- |
| InvalidOAuthAttempt / invalid_oauth_attempt | Missing/ineligible user/session, invalid proof, mismatch, replay, supersession or expiry |
| OAuthAttemptInputError / oauth_attempt_invalid_input | Invalid client ID or generation input |
| OAuthAttemptTransactionError / oauth_attempt_transaction_required | Caller has an active transaction or disabled autocommit |

Domain messages do not echo state/session/provider details. Unexpected database failures are not converted into a successful result; future HTTP integration still needs safe mapping/log policy. No automatic database/provider retry occurs.

## Data flow and authorization

1. Future authorized caller obtains SenderState outside any DB transaction and passes its generation plus current configured client ID and login identity. This package does not call the store or configure real keys.
2. Service rejects nested/manual transactions and invalid input. It owns an outermost durable atomic block, including an explicit check that also rejects Django TestCase wrapping.
3. Lock User, then exact Session, then Attempt where applicable. Reload account eligibility: active, verified and superuser.
4. Check live session expiry and decode its signed data. User ID, configured VerifiedAccountBackend and password authentication hash must match the current user; corrupt/missing/non-object data fails safely. Password changes, logout/session deletion, rotation and role removal invalidate subsequent claims. No session is created, refreshed, deleted or changed by this service.
5. Start samples time after locks, checks session expiry, supersedes this user's prior pending row and inserts a ten-minute attempt. An insertion failure rolls back supersession. Other administrators remain independent.
6. Claim locks the user's matching state row, samples time after lock waits, checks pending/expiry/session digest/client ID/current session expiry and saves claimed_at. Invalid/mismatched callers do not consume another valid attempt.
7. Exiting the transaction commits before result is returned. Future provider work happens afterward without database/file locks. A later provider error/crash cannot undo the claim: start a new attempt.

No raw Google code/token/message exists in this flow. Captured generation is not a distributed transaction between PostgreSQL and files. Future store publication must perform its own CAS; mismatch fails instead of overwriting newer credentials.

## Example and concurrency limits

Synthetic administrator starts attemptA in session1. Starting attemptB in session2 supersedes A. A callback fails; B can claim once in session2. Two callbacks racing for B produce exactly one claim. If logout wins the race, claim fails; if claim commits first, logout does not retroactively undo it.

New start replaces pending attempts only. Already claimed work may proceed; this package does not cancel it or guarantee account/session eligibility throughout later network latency. Later publication/permission/disconnect decisions remain reviewable. Different administrators may claim their own attempts, while store generations arbitrate competing future publications. No exactly-once Google call or delivery guarantee.

Row locks coordinate cooperating database operations. Tests bound statement/lock waits to avoid hanging; this package adds no new production lock-timeout or durable rate-limit policy. Host compromise, direct DB modifications or logging trusted secrets are outside the component's protection.

## Verification and remaining integration

Focused27 tests passed on first run, including real signed-session content, one synthetic password login/logout through Django, role/session/password invalidation, strict input/model validation, expiry boundary, hash-only persistence/repr, rollback, independent commit visibility, nested/manual transaction rejection, PROTECT/DB constraints, and four independent-connection races: duplicate claim, duplicate first start, start versus claim, logout versus claim.

Most fixtures build synthetic signed DB sessions; they are not Google consent. No provider mock or real provider was used. Tests create/migrate/destroy a separate Django test DB. Actual full regression/migration/postcheck outcomes are recorded in [TESTING_AND_EVALUATION.md](../TESTING_AND_EVALUATION.md).

Unimplemented: HTTP/CSRF/callback transport/log redaction, PKCE/provider setup and Google exchange/identity checking, real sender connection, credential publication, disconnect/revocation, email delivery and frontend. These need separate decisions/packages. Checkpoints CP-11/12 in [UNDERSTANDING_CHECKPOINTS.md](../UNDERSTANDING_CHECKPOINTS.md) distinguish session, state, generation and successful connection.

Final review also verifies malformed timestamp types produce ValidationError rather than DateTimeField conversion TypeError. OAuthConnectionAttempt.clean_fields checks unsupported types before Django conversion; clean checks awareness. An intermediate regression exposed integer timestamp failure and was corrected; final112 tests passed25.630s and no-drift passed. This changed validation methods only, not schema or protocol.

## WP-01b-8: implemented encrypted PKCE lifecycle

This section supersedes earlier metadata-only/no-PKCE descriptions. Approved D-036 B under `D-036 B; Approved WP-01b-8`; DL-01 support, not completed Gmail integration.

### Ownership and interfaces

- models.py: OAuthConnectionAttempt.encrypted_pkce_verifier is nullable noneditable CharField(1024). accounts_oauth_pkce_shape requires pending nonempty ciphertext, terminal NULL. Database proves lifecycle shape, not authentic encryption. Migration0004 adds only column/check; existing constraints/indexes/PROTECT remain.
- oauth_pkce.py is a small stateless crypto helper module. generate_verifier() returns base64url of32 independent random bytes, fixed43 characters. code_challenge(verifier) validates RFC7636 length43–128/allowed characters and returns S256; no plain fallback.
- encrypt_verifier(verifier, attempt_id, state_digest) returns ASCII Fernet ciphertext. decrypt_verifier(ciphertext, attempt_id, state_digest) returns raw verifier only after validation. Inputs are trusted backend values; functions perform no DB/file/network work.
- Envelope has exactly schema_version=1 (integer, not bool), canonical attempt UUID string, lowercase state digest and validated verifier. Bound to expected row ID/digest; prevents cross-row ciphertext swaps. Reject duplicate/extra/missing keys, invalid types/version/UTF8/JSON, oversized payloads. Ciphertext at most1024 ASCII characters before decryption; plaintext at most512 bytes. Fernet authenticates bytes; envelope validation authenticates application context.
- Lazy GMAIL_CREDENTIAL_ENCRYPTION_KEY only; no SECRET_KEY fallback. OAuthPKCEConfigurationError (oauth_pkce_unconfigured) reports missing/malformed key with static text. InvalidOAuthPKCE (invalid_oauth_pkce) reports corrupt/wrong-key/context-invalid proof with static text. No HTTP mapping approved yet. Import/startup does not load key; existing account API remains usable unconfigured.
- create_oauth_attempt/claim_oauth_attempt signatures unchanged. IssuedOAuthAttempt adds code_challenge/code_challenge_method=S256, never verifier; state remains repr-hidden. ClaimedOAuthAttempt adds code_verifier with repr=False. repr hiding does not make generic dataclass serialization safe: never serialize these results into HTTP/logs.

### Flow and failures

Start authenticates/locks current User and exact Session, supersedes/clears that user's previous pending row, generates independent state/verifier, encrypts bound envelope and inserts new pending attempt in one durable transaction. Configuration/encryption/insert failure rolls everything back, including prior ciphertext clearing. Other administrators are unaffected.

Claim checks identity/session/state/client/expiry before decrypting. After successful bound decryption, saves claimed_at and NULL ciphertext together; verifier returned only after commit. Wrong configuration/corruption leaves claim/ciphertext unchanged. Failed save rolls back both. Superseded/claimed attempts cannot return verifier again. Expired pending ciphertext remains until authorized replacement or separately approved cleanup.

Example: create returns state/challenge; future authorization will send challenge/S256. Later valid claim returns original verifier to future backend exchange code and removes row ciphertext. No authorization request or exchange occurs in current code.

### Verification and limitations

tests/test_oauth_pkce.py has7 helper tests including RFC7636 known S256 example, formats, roundtrip, strict records, context swaps/key failures/bounds. tests/test_oauth_attempts.py has31 lifecycle/concurrency tests, including four independent PostgreSQL races, row-swap failure, authorization-before-decrypt, constraint bypass, rollback preservation and one verifier winner. Focused38 and full123 accounts tests passed; migration/schema checked live. See TESTING_AND_EVALUATION.md for commands/results.

Logical clearing is not secure erasure from WAL/backups/memory. Shared key compromise exposes both encrypted stores. No key provisioning/rotation or cleanup added. No Google calls, callback endpoints, browser routing, source/file/citation behavior implemented here; claimed is not connected Gmail. Future publication still checks sender generation and approved permissions; locks are released before network work. Real key remains unset, sender volume unchanged/empty.
