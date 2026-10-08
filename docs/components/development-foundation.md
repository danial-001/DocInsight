# Development foundation

WP-01a provides local framework startup before domain migrations. D-005–D-009/ADR-002–ADR-006 apply; no DL requirement is completed.

## Components and interfaces

| Location / symbol | Responsibility and inputs/outputs |
| --- | --- |
| compose.yaml | .env configuration → database, backend and frontend; local ports, named volumes and startup health ordering |
| scripts/Initialize-LocalEnvironment.ps1 / New-LocalSecret | Missing .env → random local secret/password; existing file preserved |
| backend/Dockerfile; requirements.in/.txt | Exact direct pins and hash-locked transitive packages → Python/Django runtime |
| backend/requirements-tools.in/.txt | pip-tools 7.6.1 toolchain lock; separate from application dependencies |
| backend/manage.py / main | Management arguments → Django configured through config.settings |
| backend/config/settings.py / DATABASES | Required secret/PostgreSQL URL → validated application configuration |
| backend/config/asgi.py, wsgi.py / application | Django ASGI/WSGI server entry points |
| backend/config/urls.py / urlpatterns | Empty domain route registry; DEBUG default welcome page |
| frontend/package.json, package-lock.json, Dockerfile | Locked packages → Node/npm/TypeScript/Vite toolchain |
| frontend/vite.config.js | Development HTTP server and future /api proxy to backend:8000 |
| frontend/src/main.tsx | index.html root → React StrictMode/App mount; missing root throws |
| frontend/src/App.tsx / App; styles.css | Static under-construction notice and layout |
| frontend/src/vite-env.d.ts; tsconfig.json | Vite CSS declarations and strict TypeScript checks |

No domain models, serializers, views, services or tasks exist. Their future responsibilities are data/constraints, API validation/representation, HTTP handling, business-rule coordination and asynchronous execution respectively; designs need approval.

## Flow, state and dependencies

Compose starts PostgreSQL, waits for pg_isready, starts Django and waits for a listening socket, then starts Vite. Socket health proves listening, not business behavior. Frontend health proves HTTP readiness. Django uses internal db:5432; desktop pgAdmin uses the published host port. Database bytes persist in a named volume.

Vite serves index.html and React modules. main.tsx mounts App. App has no hooks, effects, polling, fetching or cache because it has no changing local or server state. Node runs the frontend tooling; the browser runs built JavaScript. Production serving is a separate decision.

## Authorization and failures

Ports bind only loopback. No private files or providers exist. User isolation is unimplemented. .env is excluded from source and Docker contexts; secrets reach only the backend/database. Missing secret or invalid database URL prevents startup. Exact image tags are used, without immutable digest pinning.

Port conflicts require changing DB_HOST_PORT while preserving other applications; current host port is 55432. Downloads can fail; Python resolution recovered from one timeout. TypeScript initially rejected CSS imports; vite-env.d.ts fixed it and rerun passed. See ../TESTING_AND_EVALUATION.md for actual checks. Browser execution is blocked by missing sandboxPolicy tool metadata; HTTP/build success does not prove visual rendering.

Example: initialize environment → Compose start → SELECT 1 succeeds → Vite serves placeholder. No simulated document-answering flow or implemented RAG is claimed.

## WP-01b-1 update

Accounts persistence now exists; earlier statements about absence of models describe WP-01a only. See accounts.md for actual User/manager/validators/migration. Frontend remains a static placeholder with no hooks or server state. No account HTTP flow or email provider exists.

## Python dependency installation (WP-01b-5)

Owner approved D-028 A and Approved `WP-01b-5`, then explicitly selected the previous container-wide runtime layout after clarification, superseding the runtime-venv condition. Docker isolates application dependencies from Windows; no runtime venv is required for this dedicated backend image. This package adds libraries and reproducible compiler tooling, not authentication/API behavior.

backend/Dockerfile uses the pinned Python3.13.15 image. requirements.txt supplies exact package versions and accepted artifact hashes; python -m pip installs them into container Python's /usr/local/lib/python3.13/site-packages at image build time. Existing Compose server, health check and management commands use /usr/local/bin/python. app UID10001 reads/executes root-owned packages, rather than installing on server startup. Packages are outside /app so the source bind mount cannot hide them; rebuilding the image reproduces them. No Python packages are installed on Windows. Container isolation is not protection from malicious dependencies or a compromised host.

scripts/Compile-BackendRequirements.ps1 accepts optional CertificateBundlePath and mounts backend as /work in a disposable pinned-Python container. It creates /opt/lock-venv, installs hash-locked requirements-tools.txt (pip-tools7.6.1 and dependencies), checks tooling dependencies/isolation and compiles requirements.in into requirements.txt. It owns dependency resolution only, not server startup, secrets, migrations or provider calls. Existing lock versions are retained where compatible; direct changes require approved pins. Failure exits nonzero and the resulting lock must be inspected before building. Docker removes the tooling container on exit; its venv is temporary and does not pollute the app venv or Windows.

Approved new packages: google-auth2.61.0 (Google credentials/refresh), google-auth-oauthlib1.5.0 (OAuth flow), requests2.34.2 (HTTP), cryptography50.0.2 (future Fernet store). Importing/installing them does not configure Gmail or send email. Storage, OAuth and email adapters remain unimplemented.

TLS: this machine's first container download failed certificate verification. A public CA bundle exported from Windows trusted Root stores is supplied read-only to the tooling container via PIP_CERT. Backend Dockerfile optionally accepts BuildKit secret pip_ca_bundle, exporting PIP_CERT only during installation; the certificate bundle is not copied into the image or repository. TLS verification remains enabled; no trusted-host/insecure fallback. On networks with ordinary container-trusted certificates the optional bundle is unnecessary. Future Gmail HTTPS trust is separate operational work and not verified by pip download success.

Verification interfaces: python/sys.prefix/sys.base_prefix and import locations show container-wide runtime package origin; tooling site/config output shows isolated compiler venv. pip check verifies declared dependency consistency; Django system/drift/regression checks verify existing behavior after rebuild. Download/CA errors, incompatible resolutions, missing wheels or unreadable packages prevent build/startup or fail these checks. No new product behavior requires an implementation-mirroring unit test; actual command evidence belongs in TESTING_AND_EVALUATION.md.

## WP-01b-6 volume addition

Compose now mounts sender_credentials only into backend at /var/lib/docinsight/sender. Dockerfile initializes ownership UID10001/mode0700. Actual mount/permission checks passed; volume remains empty and real key unset. No dependency/runtime Python layout change. Storage interfaces, limits and recovery belong in [gmail-sender-store.md](gmail-sender-store.md).
