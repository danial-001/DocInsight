# Handoff

## Resume boundary

Read AGENTS.md, CURRENT_STATE.md, DECISION_LOG.md, ADR-004/005/007/008/009/010/011/012, the specification and relevant components; reconcile code before resuming. Full P0 MVP, no deferrals/deadline; owner makes decisions. No subagents. Preserve optional checkpoint questions with answers in UNDERSTANDING_CHECKPOINTS.md.

Latest owner instruction: `D-036 B; Approved WP-01b-8`. D-036 B approved; WP-01b-8 verified. No active process/package or next implementation approval. Exact next action: review result, then propose a small batch of exact OAuth HTTP/callback/log/provider configuration decisions and a separate WP-01b-9 scope. No key generation, Google setup/consent/exchange/send or public deployment authorized.

## Actual implementation

backend/apps/accounts/models.py: OAuthConnectionAttempt adds encrypted_pkce_verifier varchar(1024), nullable, noneditable; accounts_oauth_pkce_shape requires pending nonempty ciphertext and terminal NULL. Migration0004_oauth_pkce_verifier applied after precheck found attempts0/pending0; additive only. Preserve history and PROTECT.

backend/apps/accounts/oauth_pkce.py: generate_verifier, code_challenge, encrypt_verifier, decrypt_verifier; strict bounded version1 envelope bound to attempt UUID/state digest. Lazy separate GMAIL_CREDENTIAL_ENCRYPTION_KEY; static OAuthPKCEConfigurationError/InvalidOAuthPKCE. No SECRET_KEY fallback, DB/file/network I/O or new dependencies.

backend/apps/accounts/oauth_attempts.py: same create/claim input signatures; issuance gains challenge/method=S256, never verifier. Claim gains repr-hidden code_verifier. Existing administrator/session/User→Session→Attempt locks and durable outermost commit preserved. Creation supersedes/clears old pending ciphertext; claim validates context then decrypts and claims/clears atomically. Failed configuration/insert/save rolls back; expiry leaves pending ciphertext until authorized replacement. No actual callback/provider adapter yet. Sensitive dataclasses must never be generically serialized into HTTP/logs.

Prior foundations: session csrf/login/me/logout APIs; custom User, internal verification token lifecycle; CanManageEmailSender; SenderCredentialStore generation CAS/locking/atomic file persistence. See component docs and decisions. Signup/verification delivery, collections and document/RAG features absent; DL-01 partial, no DL fully complete. Frontend still placeholder.

## Verification and state

Focused38 tests passed6.560s; full123 passed31.292s, including four attempt PostgreSQL races, existing token races and storage process checks. No failures in this package. Django check/no migration drift passed. Test DB created/migrated/destroyed. Model/constraint/migration inspected live; schema11 tables unchanged. Test durations are not performance claims.

Pre/post aggregate account_count1/eligible_admin1, tokens0/attempts0. Preserve owner's existing account; never recreate/reset/promote or print identity/password. Sender directory empty; real key remains unset. Real owner login and Google consent/inbox not tested. Tests use synthetic keys/users/sessions, not a simulated provider. No paid/provider/network/browser call.

## Environment and commands

Windows PowerShell; workspace D:\Projects - Danial Wajahat\DocInsight, 24GB RAM/Docker Desktop. Git initialized on dev; initial project commit 09c5e1d. Loopback frontend5173/backend8000/database55432→5432; another project's5433 preserved. pgAdmin owner-confirmed. PostgreSQL17/pgvector0.8.6 available, extension not enabled. Backend source mounted at /app; no image rebuild needed for WP8.

Python3.13.15 container runtime /usr/local (owner amended initial venv condition); no host Python installation. Runtime requirements20 hash-locked distributions unchanged, including approved Google libraries/cryptography. Compiler temporary venv only. Never read/print/overwrite .env or real credentials. Private sender volume docinsight_sender_credentials mounted only to backend at /var/lib/docinsight/sender, UID10001/mode0700. Key loaded lazily, no startup requirement for account API.

```powershell
docker compose up -d --wait --wait-timeout 180
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py test apps.accounts --noinput
docker compose exec -T backend python manage.py makemigrations --check --dry-run
```

Before noninteractive tests confirm test_docinsight absent or known Django-owned. Only approved additive migrations; no volume deletion/reset. Stop preserves volumes. Real superuser already owner-created; do not rerun createsuperuser.

Earlier build TLS trust required temporary trusted public Root CA bundle at TEMP/docinsight-build-ca.pem (outside repository), mounted read-only to compiler and BuildKit secret; TLS verification remained enabled. Runtime Google HTTPS trust untested. If future approved dependency work needs it:

```powershell
./scripts/Compile-BackendRequirements.ps1 -CertificateBundlePath (Join-Path $env:TEMP 'docinsight-build-ca.pem')
$caBundlePath = Join-Path $env:TEMP 'docinsight-build-ca.pem'
docker build --secret "id=pip_ca_bundle,src=$caBundlePath" --tag docinsight-backend ./backend
docker compose up -d --no-deps --wait --wait-timeout 180 backend
```

No need to repeat those builds now. Obtain trusted public PEM if absent; never disable TLS or export private keys. Browser acceptance from WP01a remains blocked by missing sandboxPolicy metadata, unrelated to this internal package.

## Integration risks for next proposal

D-034 A direct backend callback approved direction, not implemented. Exact routes/CSRF/result/error transport, fixed clean redirect, no-store/no-referrer, callback query redaction across proxy/server/error logs must be decided/tested before real integration. Google client configuration, dedicated sender identity/scope validation, timeouts and publication rechecks also require owner choice. D-019 B $0 paid budget remains.

State/session proof, PKCE proof, credential generation and Gmail identity solve separate problems. Do not infer provider success from claim or cryptographic checks. Committed claim cannot be revived after network failure; later save uses generation CAS. Pending replacement does not cancel already claimed work. Ciphertext clearing does not erase backups/memory; retained history has no cleanup automation. Future document access/source/citation tests remain required; no P0 deferrals.

Final postcheck: db/backend/frontend all healthy; test_docinsight absent (count0). Documentation relative Markdown links checked successfully. No process remains running from verification.


## Git publication request and resume point

Owner requested all project code pushed to git@github.com:danial-001/DocInsight.git, branch dev, using danial-001. Local repository initialized on dev; origin configured. Repository-local commit author uses danial-001 <danial-001@users.noreply.github.com>; global identity untouched. Existing .env excluded, dependencies/build caches excluded; staged filenames and common credential patterns checked without reading real secrets. Initial project commit prepared including implementation through WP-01b-8 and documentation.

SSH identity resolved after owner requested checking another user: existing github-personal alias/key id_ed25519_danial001 successfully authenticates as danial-001. Remote read-only inspection advertised no refs. Repository-local core.sshCommand selects this existing key with IdentitiesOnly=yes; origin retains requested git@github.com:danial-001/DocInsight.git URL. Global SSH/Git settings untouched. Push of dev completed using danial-001. Remote/local commit a1e8ac9 matched on verification, upstream origin/dev configured and working tree clean before this publication-result documentation commit. Git commands may need process-local safe.directory for this workspace because Windows ownership differs; Git metadata writes require escalation in this environment. No global safe.directory exception added.

Exact next application action: review WP-01b-8 and propose the small decision batch/scope for WP-01b-9; wait for owner choices and package approval. Git publication completed; use git log -1 for the latest documentation commit. Application next-package approvals remain unchanged. Use git log -1 for actual initial commit hash after commit creation; never invent a hash in docs.
