# Architecture

## Actual state

The local framework/database and accounts model foundation are implemented; session authentication endpoints are implemented under WP-01b-2; other product endpoints/domain models remain unimplemented. The owner approved Django/DRF for the API, React/TypeScript/Vite for the browser, pinned dependency lockfiles, Docker Compose for local development, and a custom email-based user with same-origin sessions/CSRF (D-005 through D-007). The remaining service, data, provider, and deployment design is undecided.

## Candidate design from the specification

The source document additionally proposes PostgreSQL with pgvector, private file storage, and a Redis/Celery worker. Its intended flow is upload → extract/OCR → review/correct → index → retrieve → generate → validate citations → inspect sources. Those remaining technologies and service boundaries await owner decisions; this section is a reference to the candidate, not an implementation claim.

## Invariants for design review

- Authenticate and scope every collection, document, file, question, job, answer, and citation to the owner.
- Store source page and extraction revision identity through indexing and answering.
- Publish only complete indexes for the intended revision; prevent superseded or deleted work from becoming active.
- Keep files private and model credentials server-side.
- Distinguish structural citation validation from whether the evidence supports the answer.

Before implementing a component, document its responsibility, interfaces, inputs/outputs, dependencies, failure cases, authorization, and verification. Update this file to describe the actual approved architecture and explain deviations from the original specification.

## Implemented WP-01a foundation

Actual code now includes Compose db/backend/frontend, Django config and React/Vite placeholder. PostgreSQL17/pgvector0.8.6 approved under D-009. No worker/storage/provider/domain application yet. Local browser→Vite; /api proxy→Django; Django→internal db:5432. See components/development-foundation.md. Previous “no architecture implemented” describes pre-WP-01a history; current state is the foundation above.

## Actual accounts architecture

apps/accounts is implemented as a persistence component, with models/User, managers/UserManager and supporting validators. All six AppConfigs registered; other five contain no models. AUTH_USER_MODEL configured before initial migrations. Auth/contenttypes/sessions enabled; session middleware/storage and HTTP auth flows implemented in WP-01b-2. Admin interface remains unimplemented. See components/accounts.md for actual data flow, validation boundaries and authorization limitations.

## Implemented session request flow (WP-01b-2)

Browser -> Vite /api proxy -> RequestIDMiddleware -> Django session/CSRF/auth middleware -> DRF view -> serializer -> account service -> verified authentication backend -> PostgreSQL session. GET me uses standard IsAuthenticated and verified backend session lookup; no custom permission abstraction. Login/logout explicitly enforce CSRF for anonymous requests. Eight-hour absolute deadline, same-user relogin key rotation, local login throttle and safe error envelope implemented. See API_CONTRACT.md and components/accounts.md for ownership/interfaces/limits. No worker/provider/frontend authentication flow yet.
## Internal verification lifecycle (WP-01b-3)

accounts/models.EmailVerificationToken stores issuance digests/lifecycle history; accounts/verification.issue_verification_token and consume_verification_token own transactional rules. User-first row locks coordinate resend/confirmation; database checks and partial uniqueness defend stored state. No HTTP/provider task/UI entry point added. Trusted caller receives raw token only in memory and must wait for outermost commit before future inline Google send under D-024 A. Token generation/hash use standard library, no provider/dependency change. accounts component and DATA_MODEL.md own flow/schema details.47 account tests passed including4 PostgreSQL races; no email completion claim.
## Sender permission foundation (WP-01b-4)

accounts/permissions.CanManageEmailSender checks authenticated/active/verified/superuser identity for future sender administration. Existing verified session backend supplies fresh identity; DRF CSRF still protects mutations. No production sender/OAuth route or permission capability added to user responses. Existing built-in createsuperuser and UserManager handle trusted bootstrap, tested with synthetic input only; no custom command or real account.58 account tests passed. Provider credentials/storage/API/UI remain unimplemented and require review; this guard does not replace OAuth state/session binding.

## Dependency foundation update (WP-01b-5)

Approved Google authentication/OAuth, requests and cryptography libraries now installed with20-distribution hash lock in dedicated backend image /usr/local Python. Owner explicitly selected this established runtime layout after superseding initial venv condition. Separate disposable compiler container uses /opt/lock-venv; Windows Python untouched. Optional public CA build mount solves this machine's container download trust without disabling verification or persisting the bundle. See components/development-foundation.md/ADR-005 for actual interfaces, limitations and verified checks. No Google adapter, protected credential file, OAuth endpoint or email delivery implemented by installing libraries. Owner-run administrator is now confirmed (one eligible account); prior no-account text is the historical WP-01b-4 snapshot.

## Implemented internal sender store — WP-01b-6

[SenderCredentialStore](components/gmail-sender-store.md) owns filesystem record validation, encryption, private permissions, short process locks and conditional atomic persistence. It accepts a separate Fernet key/directory/expected client ID; read returns SenderState, replace/clear require expected_generation. Credential secrets remain trusted backend inputs/outputs, never public serializer data.

No model, serializer, view, task or provider adapter added. Future authorized OAuth/delivery services depend on this store, release local locks before network work and honor generation conflicts. Clear persists an encrypted empty marker, not Google revocation. Post-replacement sync failures report uncertainty. The backend-only volume is currently empty/key unset; lazy factory does not block session API startup. Earlier unimplemented-storage statements are superseded by this verified slice; OAuth/delivery remain unimplemented.

## Internal OAuth attempt lifecycle — WP-01b-7 verified

OAuthConnectionAttempt model owns digest/context/lifecycle persistence and constraints; accounts/oauth_attempts.py services coordinate current account/live signed database-session checks and User→Session→Attempt locking. create returns transient state after commit; claim returns ID/client/generation context after a single committed claim. Explicit outermost transaction guard rejects nested/manual transactions; future Google calls run after return with no DB/file locks.

Ten-minute expiry, latest pending attempt per admin and PROTECT history implemented. New starts do not cancel already claimed work. Future publication still uses sender-store generation CAS; DB metadata and file store do not form a distributed transaction. No new view/serializer/task/hook/provider adapter. [Component](components/gmail-oauth-attempts.md) documents public internal interfaces and security boundaries; HTTP/CSRF/PKCE/callback transport/provider configuration remain later integration.

## WP-01b-8 verified PKCE ownership

accounts/oauth_pkce.py owns generation, S256 transformation and bounded context-bound Fernet envelope validation, without DB/file/network work. accounts/oauth_attempts.py retains session authorization, User→Session→Attempt locks and durable transaction coordination. Model/DB enforce ciphertext pending/terminal shape. Existing separate key reused lazily, sender file untouched; no new dependency/abstraction/provider adapter. Direct Django callback D-034 remains approved direction, not implementation. See components/gmail-oauth-attempts.md and ADR-012.
