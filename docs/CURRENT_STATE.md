# Current state

## Working and verified

Full P0 specification MVP target; no deferrals or fixed deadline. WP-00 and WP-01b-1 through WP-01b-8 verified. WP-01a command gate passed; original browser acceptance remains blocked/unverified.

Latest owner instruction: `D-036 B; Approved WP-01b-8`. D-036 B approved and implemented. No active package or running process; no next implementation approved.

- Custom UUID/email User, six Django app shells; session csrf/login/me/logout APIs, eight-hour sessions, CSRF, safe errors/request IDs/local login limit.
- Internal hashed verification tokens: one-hour expiry, 60-second cooldown, single use, revocation, rollback and User-first locking. No signup/verify/resend HTTP or delivery yet.
- CanManageEmailSender requires active verified superuser. Permission verified through test-only route; no production sender route.
- SenderCredentialStore implements Fernet read/replace/clear, generation compare-and-swap, private locking and atomic file persistence. Private backend-only directory remains empty, real key unset.
- OAuthConnectionAttempt and create_oauth_attempt/claim_oauth_attempt: ten-minute expiry, state/session digests, exact live authenticated administrator session, latest pending attempt, committed single claim, client/generation context, PROTECT history.
- WP-01b-8 adds encrypted_pkce_verifier, accounts_oauth_pkce_shape, and oauth_pkce.py. Independent random 43-character verifier, S256 challenge, versioned context-bound Fernet envelope. Pending requires ciphertext; claimed/superseded requires NULL. Claim/supersession clear ciphertext atomically; failures preserve prior state. Claim returns repr-hidden verifier only after commit. Issuance never returns verifier.
- Migration accounts.0004_oauth_pkce_verifier reviewed/applied; additive field and constraint only, 11 tables unchanged. Fresh precheck found no legacy pending attempts.

## Last verification

Focused 38 PKCE/attempt tests passed in 6.560s. Full accounts suite: 123 passed in 31.292s (112 prior plus 11 new), including PostgreSQL races and existing file-store process checks. No failing test run in WP-01b-8. Django check and migration drift check passed. Separate Django test database created/migrated/destroyed. Durations are test execution, not performance metrics.

Live aggregate postcheck: one account/eligible administrator, zero verification tokens/OAuth attempts; new varchar(1024) nullable field/check and migration confirmed. Sender directory empty; real encryption key unconfigured. Existing account regressions pass with runtime key unset. No real owner login or provider success claimed. Final service/test database postcheck recorded in TESTING_AND_EVALUATION.md.

## Incomplete and limits

No Gmail OAuth HTTP callback, authorization URL/exchange/refresh/send, signup/verification HTTP, sender/frontend/admin UI, demo seed or cleanup. D-034 direct Django callback is an approved direction only. All document collections/upload/private-file/OCR/job/index/retrieval/answer/citation/evaluation behavior remains unimplemented. DL-01 partial; 0/14 DL requirements complete. User file isolation and citation integrity await their implementation/verification packages.

Claimed does not mean Gmail connected. Future network work occurs after locks release and must honor captured sender generation and separately approved publication rules. New start supersedes only pending work; logout cannot undo a committed claim. Services reject nested/manual transactions. No transaction around provider work.

Verifier clearing is logical removal, not secure erasure from memory/WAL/backups. Expired pending ciphertext remains until authorized replacement or future cleanup. History PROTECT blocks ORM user deletion; no retention automation. Shared encryption key exposes both stores if compromised; no rotation automation. Store clear does not revoke Google tokens. Local login limit is nonpersistent/non-atomic.

## Environment and blockers

Windows/PowerShell, 24GB RAM, Docker Desktop. Loopback frontend5173/backend8000/DB55432; other project's5433 preserved. Git initialized on dev; initial commit preparation in this session. Backend source bind-mounted, no rebuild needed for this package. pgvector0.8.6 available/not enabled; pgAdmin owner-confirmed. No dependencies/config/.env/frontend/routes/provider changes in WP-01b-8.

Runtime Python is /usr/local in container under owner amendment; hash-locked 20 distributions unchanged. Temporary pip-tools compiler uses a venv. Earlier image build used trusted public CA BuildKit secret with TLS verification enabled; future Google runtime trust untested. Original browser gate blocked by missing sandboxPolicy metadata; no browser needed for internal-only package.

## Exact next action

Review WP-01b-8 result and CP-13/14 questions with answers. Next proposed package WP-01b-9: protected OAuth HTTP/provider integration, to be narrowed after a small batch of decisions on exact initiation/callback/result/error/log-redaction contract and Google configuration/sender identity/network failures. Prepare proposal only; wait for decisions and separate package approval. No real key generation, Google setup/consent/calls, paid spend, deployment or publication approved beyond the explicitly requested GitHub code push.

Final postcheck: db/backend/frontend all healthy; test_docinsight absent (count0). Documentation relative Markdown links checked successfully. No process remains running from verification.


## Git publication request and resume point

Owner requested all project code pushed to git@github.com:danial-001/DocInsight.git, branch dev, using danial-001. Local repository initialized on dev; origin configured. Repository-local commit author uses danial-001 <danial-001@users.noreply.github.com>; global identity untouched. Existing .env excluded, dependencies/build caches excluded; staged filenames and common credential patterns checked without reading real secrets. Initial project commit prepared including implementation through WP-01b-8 and documentation.

Push pending: SSH authenticates as danialwajahat-lab, not requested danial-001. Await owner's SSH configuration for danial-001 or explicit instruction to use the currently authenticated account. No push attempted with mismatched account. Remote read-only inspection advertised no refs. Git commands may need process-local safe.directory for this workspace because Windows ownership differs; Git metadata writes require escalation in this environment. No global safe.directory exception added.

Exact next action: resolve SSH identity, inspect remote refs again, push dev without force, verify remote commit matches local HEAD and upstream/clean status. Application next-package approvals remain unchanged. Use git log -1 for actual initial commit hash after commit creation; never invent a hash in docs.
