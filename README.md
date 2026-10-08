# DocInsight

Learning reference: [optional checkpoint questions and answers](docs/UNDERSTANDING_CHECKPOINTS.md).

A planned private document workspace: upload, review extraction, ask questions, inspect cited sources. Target: full P0 [specification MVP](DocInsight_SRS_Architecture.md); no P0 deferrals.

**Current:** Local account/session API, internal verification-token lifecycle, sender-admin permission and encrypted credential-store and OAuth-attempt lifecycle services implemented; 112 account tests passed. Sender permission currently verified through test-only routes; Gmail endpoints are not implemented. Frontend remains an under-construction screen; registration, email delivery, uploads, OCR, retrieval and citations unimplemented. Command checks passed; browser check blocked. See [current state](docs/CURRENT_STATE.md).

## Local setup (PowerShell)

Start Docker Desktop, then from repository root:

```powershell
./scripts/Initialize-LocalEnvironment.ps1
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
```

Initializer creates ignored .env with random local secrets and preserves an existing file. Do not commit/share it. .env.example has dummy values. Builds need network. If port 5432 is occupied, edit DB_HOST_PORT in .env; this machine uses **55432**. Django always connects internally to db:5432.

- Frontend: http://127.0.0.1:5173
- Authentication API: http://127.0.0.1:5173/api/v1/auth/csrf (also backend8000); see [API contract](docs/API_CONTRACT.md). Backend root has no product page.
- Desktop pgAdmin 4: host 127.0.0.1, port matching DB_HOST_PORT (currently 55432), database/user docinsight, password from local POSTGRES_PASSWORD. Connection owner-confirmed; GUI not agent-tested.

User schema implemented under approved WP-01b-1. After startup run `docker compose exec -T backend python manage.py migrate --noinput` for the approved account/session/verification-token/OAuth-attempt schema; local database is already migrated. pgvector available but not enabled.

```powershell
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity 1
docker compose exec -T backend python -m pip check
docker compose exec -T frontend npm run build
docker compose stop
```

Stop preserves data; do not remove volumes for routine fixes. Changing the environment password after database creation does not update the stored password. Development servers use DEBUG/local HTTP; production deployment is unconfigured.

Python image runs Django. Node supplies npm/TypeScript/Vite. PostgreSQL supplies database and pgvector extension availability. [Foundation documentation](docs/components/development-foundation.md) explains components. Approved direct pins are in requirements.in/package.json; full resolutions in requirements.txt/package-lock.json. Images use exact version tags, not immutable digest pins.

### Python dependency workflow

WP-01b-5 keeps Python application packages in the backend container's main Python environment, as the owner selected after revising the initial venv requirement. Nothing is installed into Windows Python. Dependency compilation uses a separate temporary container venv, not host-global pip:

```powershell
./scripts/Compile-BackendRequirements.ps1
docker compose build backend
docker compose up -d --no-deps --wait --wait-timeout 180 backend
```

Only compile dependency changes within approved scope. The helper uses the existing hash-locked pip-tools toolchain and writes backend/requirements.txt. If your network's CA is missing from the container, pass a trusted public PEM bundle via `-CertificateBundlePath`; for image builds use `docker build --secret "id=pip_ca_bundle,src=<public-ca-bundle.pem>" --tag docinsight-backend ./backend`. The bundle stays outside source/image, and TLS verification remains enabled. See foundation documentation and the verification record for this machine's results. Gmail dependencies alone do not provide email delivery.

WP-01b-5 verified:20 locked runtime distributions/import locations checked, dependency and Django checks passed,58 account regressions passed again, existing administrator preserved. No Gmail/OAuth/send integration implemented yet.

See [plan](docs/IMPLEMENTATION_PLAN.md), [decisions](docs/DECISION_LOG.md), [verification](docs/TESTING_AND_EVALUATION.md) and [handoff](docs/HANDOFF.md). No quality, performance or cost claims exist.

## Trusted administrator setup (owner-run)

WP-01b-4 verified the existing Django command with synthetic test inputs. No real administrator has been created by the agent. When ready, run this yourself from your local PowerShell terminal after starting the backend and applying approved migrations:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Keep interactive TTY (do not add -T). Enter your chosen email and password at the terminal prompts; password entry is hidden. Use the approved password policy (12-128 characters, not common/numeric or similar to account details). Do not put passwords in command arguments, chat, source or logs. This explicitly trusted command creates an active verified superuser, permitting initial login before Gmail is connected. It does not verify email ownership through Google or send a verification email. Duplicate addresses are rejected; no existing password/status is silently reset or promoted. Our manager still rejects invalid passwords even if Django's bypass prompt is answered yes.

D-027 A grants future sender administration to every active verified superuser; staff-only/ordinary accounts do not qualify. Permission code exists, but Connect Gmail endpoints/UI and Django admin UI remain unimplemented. Owner subsequently confirmed successful setup; aggregate inspection found one account and one active verified superuser. This does not demonstrate real login or Gmail connection. Do not rerun setup to replace the existing account.

## Sender credential storage

WP-01b-6 verified internal Fernet storage with generation-checked writes and encrypted empty markers on clear. Persistent sender_credentials volume is backend-only, directory0700/files0600. Currently empty, with GMAIL_CREDENTIAL_ENCRYPTION_KEY unset; no real key/Google credentials created. Session API stays available while store is unconfigured.

See [interfaces and recovery limits](docs/components/gmail-sender-store.md). OAuth connection/endpoints and email delivery need separate approved packages.

## OAuth connection-attempt lifecycle

WP-01b-7 verified an internal model/service for ten-minute, session-bound connection attempts accepted once. A new start supersedes your prior pending attempt; claimed history is retained with PROTECT. Only hashes/context are stored, never Google codes/tokens. The additive accounts.0003 migration is applied locally;112 account tests passed.

This does not connect Gmail: protected endpoints, Google exchange/setup and UI remain unimplemented. See [attempt interfaces and boundaries](docs/components/gmail-oauth-attempts.md).

## Latest verified slice: internal PKCE (WP-01b-8)

Encrypted attempt-bound S256 verifier lifecycle and database pending/terminal constraint implemented;123 account tests pass. This is local backend infrastructure, not a working Gmail connection. No OAuth callback/provider exchange, registration delivery, document pipeline or product UI yet. Full P0 MVP remains incomplete (0/14 DL fully complete). See docs/CURRENT_STATE.md for authoritative status and docs/UNDERSTANDING_CHECKPOINTS.md for explanations with answers.
