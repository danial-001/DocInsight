# Interview guide

Optional checkpoint questions and their answers are maintained in [UNDERSTANDING_CHECKPOINTS.md](UNDERSTANDING_CHECKPOINTS.md). CP-01 covers the foundation, CP-02 through CP-04 the custom user, and CP-05 through CP-10 sessions, verification tokens, sender permission, dependencies, generations and uncertain writes. Add future checkpoints and answers there as part of the corresponding package/explanation.

## Current defensible account

DocInsight has a local framework/account foundation and verified session authentication API; document product behavior remains unimplemented. The owner selected the full P0 specification MVP and is making architecture choices before implementation. There are112 passing account tests covering model/session/token lifecycle, sender permission, synthetic trusted CLI provisioning, encrypted storage and committed OAuth attempt lifecycle, but no real signup/email or OCR/RAG application flow or evaluation metrics yet. Do not describe the proposed Django/React/pgvector pipeline as built, or use the specification's suggested CV wording as an accomplished claim.

## Intended explanations to develop as code lands

- Why a source page, extraction revision, chunk, answer evidence record, and displayed citation are separate concepts.
- How owner-scoped access covers metadata, private bytes, retrieval, and citation resolution.
- How OCR errors are exposed and corrected without silently rewriting original evidence.
- How index publication avoids mixing revisions or accepting stale workers.
- Why lexical and vector retrieval are combined, and how the baseline comparison controls extraction and generation settings.
- How unsupported questions abstain and why citation structure does not prove factual support.
- What tradeoffs the owner selected for provider cost/privacy, jobs, data model, and deployment.

For each implemented package, add actual file paths and symbols, end-to-end flows, observed failures and limits, test evidence, and the owner's role. Likely interview questions should have answers grounded in code and measurements, not the aspirational specification.

## WP-01a defensible explanation

Implemented local Django/React/PostgreSQL foundation with Compose, pip hash locks and npm lock. Owner chose architecture/version strategy and approved the package. Explain: Node runs Vite/TypeScript tooling, Python runs Django, database persists in a named volume; Django uses service DNS db while pgAdmin uses the host port. App is static so no hooks/effects/server cache yet. Command checks passed; browser check blocked. At this historical WP-01a checkpoint no OCR/RAG/auth or measured retrieval claim was defensible; later authentication results are recorded below. See components/development-foundation.md for actual paths.

Understanding checkpoint: explain why changing the database host port does not change Django's internal db:5432 address.

## WP-01b-1 interview explanation

Actual User extends AbstractBaseUser and PermissionsMixin under owner-selected D-011 B. UUID primary key; full-address lowercase policy; exact and Lower(email) unique indexes; manager validates and hashes, model stores data. Validation catches ordinary mistakes; database uniqueness catches bypass/concurrent conflicts. email_verified_at and is_active separate ownership verification from suspension. Trusted superuser provisioning is explicit, ordinary accounts start unverified.13 tests pass, local migration applied. At the WP-01b-1 checkpoint no login or email verification flow was implemented; WP-01b-2 now implements login, while email verification remains unimplemented; source isolation/citation/RAG claims remain unsupported. Explain why a custom user is established before other foreign keys, why a valid verification timestamp must not reactivate suspension, and why save/bulk writes do not replace full validation.

## WP-01b-2: Defensible authentication explanation

Owner selected sessions/CSRF, eight-hour expiry, generic403 codes, verified-active gates and local throttle; approved the small package with Approved `WP-01B-2`. Implemented account API under apps/accounts, shared response handling under config, Django database session migration.27 account tests passed, including real CSRF enforcement and two synthetic client identities. No document isolation/email/UI claims yet.

Explain the flow: fetch CSRF token -> submit credentials with token/cookies -> validate through serializer -> service calls verified backend and Django login -> session key/CSRF rotate and absolute expiry is recorded -> safe user/fresh token returned -> later session requests recheck verification/suspension -> logout flushes session. Models store data; serializers validate/represent; views handle HTTP; services coordinate business rules. No task or React hook needed for this backend package.

Likely questions: Why CSRF with session cookies? Browsers attach cookies automatically; unsafe requests need proof of permitted origin/token. Why explicit login CSRF? Default DRF session enforcement only covers authenticated sessions. Why no JWT? Owner chose same-origin browser sessions; JWT is not necessary for this flow and neither approach grants document ownership. How is fixed expiry enforced? An absolute deadline survives session reads/writes. Why extra rotation on relogin? Django normally retains the same key for the same already-authenticated user, while our contract rotates every successful login. Why separate verified and active? Email proof must not lift suspension. Is rate limiting production-ready? No: process-local, non-atomic and proxy-grouped; public deployment needs separate review.

Optional understanding checkpoint: explain the different jobs of the session cookie, CSRF token and Google sender refresh token. Only the first two exist in the API; Gmail credentials remain planned.
## WP-01b-3: Defensible verification-token explanation

Owner chose issuance history (D-023 B), one-hour links (D-018 B), separate verified/suspended state (D-017 A), then approved WP-01b-3. Implemented model in accounts/models.py, additive migration0002 and internal services in verification.py.47 account tests passed, including20 token checks and4 independent-connection PostgreSQL races. No email/registration UI or real delivery claim.

Explain: generate32 random bytes as64-hex secret; SHA256 digest goes to database, secret stays in memory for future sender. Resend after60 seconds revokes old row and issues another; confirmation hashes supplied token, locks/rechecks expiry/state, consumes once and marks that user verified. History makes used/revoked distinguishable but does not prove delivery. PROTECT blocks implicit user/history deletion until explicit cleanup policy is designed.

Likely questions: Why hash rather than encrypt links? Only comparison is needed, no recovery of old links. Why lock User before token? There is a stable row even before first issuance, and consistent order coordinates all operations for the account. Is partial uniqueness enough? It prevents two outstanding rows but not full single-use/User verification/cooldown behavior; services and transactions handle those. Why check time after lock acquisition? A token can expire while waiting. What if a write fails? Atomic rollback preserves old valid token or prevents half-consumed verification. Why send after commit? An email must not contain a token later rolled back. Is this delivered email verification? No, only internal lifecycle; Gmail/API/UI remain pending.

Optional understanding checkpoint: explain why an expired-but-unrevoked row still occupies the outstanding-token slot, and how resend safely replaces it.
## WP-01b-4: Sender administration and trusted bootstrap

Owner chose D-027 A and approved WP-01b-4. CanManageEmailSender in accounts/permissions.py requires authenticated active verified superuser; staff alone does not qualify. Model flags store state, backend validates session identity, permission decides allowed sender access, CSRF separately guards unsafe browser requests. Permission tested through test-only route; no working Gmail connection feature claimed.58 account tests passed including5 sender permission/6 CLI tests.

Explain trusted bootstrap: Gmail cannot send verification before connected, so explicit owner-run createsuperuser command uses trusted manager to create active verified admin with hashed/validated password. This is administrative trust, not delivered email ownership proof. Ordinary signup cannot choose these flags. Existing built-in command reused; owner later confirmed setup, aggregate inspection found one eligible administrator. Automated tests simulate terminal input in an isolated DB. Manager rejects invalid passwords even when Django bypass prompt answered yes; duplicate email does not reset/promote existing account.

Likely questions: Why not is_staff? It marks admin-site access, not chosen sender authority. Why check flags each request? Removing superuser/eligibility must affect existing sessions. Does CSRF grant permission? No; valid token does not authorize ordinary/staff users. Why not build a provisioning service? Built-in command already delegates to validated manager; extra abstraction adds no needed responsibility. What is unfinished? Sender endpoints/OAuth/provider credentials/UI remain pending. Every future superuser receives sender authority by explicit owner choice.

Optional checkpoint: explain why a verified staff user is denied while an active verified superuser is permitted, and why the latter still needs CSRF for mutations.

## WP-01b-5: Dependency reproducibility and container isolation

Owner chose maintained Google authentication libraries plus requests and cryptography, approved exact pins/package and then selected direct container-wide runtime installation after initially requesting a venv. Our Dockerfile installs hash-locked requirements at build time; Windows Python is untouched. The compiler runs pip-tools in a separate temporary container venv. This separates build tooling from the runtime while keeping the backend image's established package layout. Hashes constrain accepted artifacts; they do not prove a dependency is harmless. Versions were resolved and imports/dependency consistency checked, not chosen because newest necessarily means best.

Likely questions: Is a venv mandatory inside Docker? No, a dedicated image can isolate the runtime; a venv would add a separate package prefix and can be useful for other workflows. How are downloads verified? TLS plus --require-hashes; a missing container CA was addressed using a trusted public certificate bundle, not disabling verification. Why no full Google API client? Only a small Gmail send surface is planned; direct requests gives explicit timeout/retry ownership, while Google libraries handle OAuth. Does installation mean Gmail works? No; credentials, consent/state, protected storage, adapters and real send checks remain unfinished. Source interfaces: backend/requirements.in/.txt, backend/Dockerfile and scripts/Compile-BackendRequirements.ps1.

Optional checkpoint: explain the difference between Docker isolation, a Python venv and a hash-locked requirements file.

## WP-01b-6 — explain the actual credential store

Actual code: accounts/sender_store.py defines SenderCredentialStore, SenderCredential and SenderState; tests/test_sender_store.py has27 synthetic checks. Store read decrypts/validates a snapshot under a short stable lock. After future network work, replace accepts only the generation read earlier; clear writes encrypted empty state with a fresh generation. This stops cooperating older operations from restoring disconnected credentials, including operations that originally saw no file.

Fernet provides authenticated recoverable encryption; generation comparisons provide operation ordering. Neither proves Google sender identity, successful delivery or protection from a compromised backend. File permissions0700/0600 and backend-only volume restrict local exposure; key is separate environment configuration and currently unset. No real credentials stored.

Atomic replacement avoids partial published bytes. Before replacement, failed writes preserve old data; a directory-sync failure afterward is uncertain and requires rereading. See [component](components/gmail-sender-store.md), [ADR-010](decisions/ADR-010-sender-credential-store.md) and [CP-09/10 with answers](UNDERSTANDING_CHECKPOINTS.md).85 total tests passed, including real process locking checks; no OAuth/delivery or performance claim.

## WP-01b-7 — explain the implemented OAuth attempt lifecycle

OAuthConnectionAttempt in accounts/models.py stores temporary proof hashes/session binding/client ID/generation/timestamps with retained PROTECT history. create_oauth_attempt in accounts/oauth_attempts.py verifies the current administrator and live signed DB login session, supersedes prior pending state and commits a ten-minute proof. claim_oauth_attempt accepts it once and commits before return. ClaimedOAuthAttempt is context for a future provider adapter, not evidence Gmail is connected.

User→Session→Attempt row locks serialize competing operations; the outermost transaction guard prevents a later outer rollback from making a claimed callback reusable after external work. Logout winning the race blocks claim; logout after claim does not undo it. Password/role/session changes checked at claim, no promise of authorization throughout future network latency.

Owner chose dedicated table/latest-pending policy/retained history after alternatives review. Tradeoffs: more explicit model/tests and history/deletion coordination; old tabs fail when a newer pending attempt starts. No new dependency/provider fee or performance claim.27 tests including4 real PostgreSQL races and full112 regressions passed. See [component](components/gmail-oauth-attempts.md), [ADR-011](decisions/ADR-011-oauth-connection-attempts.md) and [CP-11/12 answers](UNDERSTANDING_CHECKPOINTS.md). HTTP/Google/setup/PKCE/UI remain unimplemented.

## WP-01b-8: explain actual PKCE implementation

Owner chose D-036 B and approved the small package. accounts/oauth_pkce.py creates a random verifier and S256 challenge, encrypts a strict versioned envelope bound to attempt UUID/state digest using the separate configured Fernet key. accounts/oauth_attempts.py owns authorization/locks/commit; claim returns verifier after atomically clearing ciphertext. Model/check prevents pending rows without ciphertext and terminal rows retaining it. DB shape does not prove authentic encryption; helper validation handles that.

Evidence: RFC7636 example, malformed/key/context failures, rollback and PostgreSQL concurrency tests;38 focused/123 full accounts checks passed. No provider call occurred. Portfolio claim can describe implemented backend PKCE infrastructure, never working Gmail integration or completed document assistant. Clearing is logical, not erasure from backups/memory; key reuse and no automated retention/rotation are limitations. See CP-13/14 in UNDERSTANDING_CHECKPOINTS.md for optional questions and answers.
