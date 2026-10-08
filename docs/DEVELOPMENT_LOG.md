# Development log

## WP-00 — Documentation baseline

The owner approved the documentation structure and documentation-only package with `1. Approved`. Created `AGENTS.md`, `README.md`, and the requested `docs/` structure. Recorded the owner's full-specification-MVP scope choice and flexible delivery cadence. No application code, dependency, migration, provider call, deployment, or Git operation was part of this package.

Repository inspection before the package found only `DocInsight_SRS_Architecture.md`; the directory was not a Git repository. Significant specification ambiguities and integration risks are recorded in `SPEC_REVIEW.md`.

**Verification run:** `rg --files -g '*.md'` found the specification and 18 requested/new Markdown files. A PowerShell required-path check found 18 of 18 expected files and no missing path. A DL-row check found exactly one traceability row for each DL-01 through DL-14. A content search confirmed the documents distinguish proposed architecture and unimplemented behavior from approved scope. No product tests apply yet.

**Read-only environment inspection for the next proposal:** Node reported `v24.16.0`, npm `11.13.0`, and the Docker CLI `29.3.1`. `psql` and `tesseract` were unavailable on PATH. The Docker daemon did not answer; its config was also inaccessible to this process. The Python launcher was present, but `py --version` could not start its registered Python because access was denied. A hardware query was denied, so RAM and CPU remain unknown. No dependencies were installed or services started.

Next proposed work is a small decision batch for WP-01. WP-01 itself remains proposed and needs explicit approval before implementation.

## Foundation decisions after WP-00

The owner selected D-005 A (Django/DRF and React/TypeScript/Vite, with pinned lockfiles) and D-006 A (local Docker Compose runtime). D-007 remains proposed because the owner asked whether JWT is required. ADR-002 and ADR-003 record the approved choices and their limits. No product files were changed or services started. The standard DRF session-authentication 403 response versus the specification's proposed 401 response was added to the API-contract review list.

The owner subsequently selected D-007 A, a custom email-based user with same-origin sessions/CSRF, and reported 24 GB RAM with Docker Desktop available to open. ADR-004 records the choice. A read-only `docker info` check still could not connect to the daemon. No auth code or migration was created.

Read-only package and upstream release checks prepared proposed D-008 foundation versions and D-009 PostgreSQL/pgvector versions. The proposed smaller WP-01a verifies framework and database startup before domain migrations. No package was installed, container was started, or schema was created.

The owner approved D-008 B: pip-tools and pip requirements files. ADR-005 records the instruction. D-009 and WP-01a remain proposed; the owner asked about pgAdmin 4 access to the PostgreSQL container. Documentation updates only; no integration has been tested.

## WP-01a — Framework/database foundation

Owner approved D-009 A and WP-01a with “Approved: D-009 A and WP-01a”. Created Compose/Docker framework shells, pip hash locks/tool lock, npm lock, environment initializer and React construction notice. No migrations, auth/domain APIs, providers or deployment. Approved direct versions resolved without substitutions.

Both image builds and all command checks in TESTING_AND_EVALUATION.md passed after fixing the Vite CSS declaration. Local DB uses 55432 after port conflicts; existing project containers preserved. All three containers healthy. Browser check attempted twice but tool failed before code execution, missing sandboxPolicy metadata; package remains in progress. Updated README, component guide, current state/handoff, plan, decisions, architecture, traceability and interview notes. Next exact action: browser smoke check within WP-01a, then owner review and next package proposal.

## Latest WP-01a continuation

Owner instructed “Proceed further”. Retried browser bootstrap; tool again failed before code execution with missing sandboxPolicy metadata. `docker compose ps` passed and all three containers remain healthy. No visual acceptance result claimed. Next: owner may verify the construction page manually, or retain browser gate pending tool recovery. Read-only planning for WP-01b is permitted; no WP-01b code is approved.

## WP-01b-1 — User model and app shells

Owner instruction `Approved WP-01b-1` authorized six app shells, approved custom-user schema, tests and additive initial migrations/trusted superuser creation. Implemented User/UserManager/validators, AUTH_USER_MODEL, password configuration, migration and13 tests. Inspected empty local schema, reviewed migration and applied; no default auth_user created. Tests/drift/system/schema checks passed (details TESTING_AND_EVALUATION.md). Initial common-password fixture assumption failed, fixed fixture then rerun passed. No accounts seeded/provider calls/API/UI changes. Model timezone field shadows import name within class scope, handled with django_timezone alias. Accounts component/current-state/handoff/data-model/plan/traceability/testing/README/architecture/interview docs updated. Next: owner review, token/provider decisions and auth API package proposal.

## WP-01b-2 - Session authentication API

Owner instruction: Approved `WP-01B-2`. Added csrf/login/me/logout endpoints, verified-active authentication backend and session CSRF adapter, serializers/services/views, approved local login throttle, request IDs and safe error handling. Enabled built-in database sessions and applied reviewed sessions0001 additive migration. No dependencies, frontend, email/provider, admin or seed added.

Docker Desktop was stopped; approved start restored existing services. Initial26 tests passed. Review identified handling needed for Django permission/not-found exceptions and same-user relogin rotation; ordinary scope fixes plus regression coverage applied. Final27 account tests passed, system/drift checks passed, proxy HTTP smoke passed. No failures concealed; no test assertion failures occurred in this package. Zero local accounts/sessions observed. Details TESTING_AND_EVALUATION.md.

Updated README, implementation plan, package approval record, API contract, architecture, data model, account component, traceability, verification, interview guide, current state and handoff. Owner decisions D-018 through D-021 remain approved directions, not implemented verification/Gmail. Next owner review, then registration/verification schema/API proposal. No next package approved. WP-01a browser gate still blocked.
## WP-01b-3 - Verification-token persistence and lifecycle

Owner instruction: Approved `WP-01b-3`. Implemented approved EmailVerificationToken model/digest validation/constraints and additive migration0002; issue/consume services with User-first locks, one-hour expiry,60-second issuance cooldown, revocation/history, safe domain errors and suspension preservation. Returned raw token only to trusted caller in memory; no HTTP/provider/UI/dependency changes. Outer transaction commit must precede future delivery.

Docker engine initially unavailable; approved Docker Desktop start restored existing containers. Inspected expected9-table schema and absent test DB before migration/tests. First47-test account run passed, including20 new token tests (4 real PostgreSQL concurrency tests); no assertion failures. Reviewed only additive token migration, applied successfully, system/drift checks passed; postmigration10 tables/constraints confirmed, zero users/tokens and test DB absent. No provider calls, account provisioning, paid spend or Git/deployment operations.

Updated model/component/architecture/API-internal notes, ADR-009, traceability, verification, plan, decisions, README/interview, current state and handoff. Next owner review, then precise registration/verify/resend/delivery/Gmail contracts and small approved package. Real email still required; this internal slice is not completed registration or MVP. No next implementation package approved.
## WP-01b-4 - Sender-admin permission and trusted bootstrap checks

Owner instruction: Approved `WP-01b-4`. Added CanManageEmailSender requiring authenticated/active/verified/superuser,5 permission tests and6 Django createsuperuser integration tests. Reused installed command and existing manager unchanged; no custom provisioning abstraction. Documented owner-run interactive terminal setup; no real account created. Permission currently exercised through test-only probe, no sender endpoints/UI implemented.

Existing containers healthy. Precheck zero users/10 tables and absent test DB. First58-test account run passed, system/no-drift checks passed; postcheck zero users/tokens,10 tables and test DB absent. Confirmed validation bypass cannot override manager policy, exact/case duplicates preserve existing account, role revocation effective next request and CSRF remains necessary. No new dependencies/migrations/provider calls/paid spend/Git/deployment.

## Continuation - owner provisioning and Gmail proposals

Owner reported "Super user created successfully". Aggregate read-only query confirmed one account and one active verified superuser; no credentials inspected/displayed. Real login not tested. Updated current state, handoff and README; historical58-test result unchanged, tests not rerun for this documentation continuation. Proposed D-028 dependency bundle and D-029 file/key safety choices after public package metadata/documentation review. No installation/product code/provider call or next package approval.

## Continuation - D-028/D-029 approval and venv condition

Owner wrote "D-028 A (but all libraries, must be in a venv)" and "D-029 A". Recorded both approved; inspected Dockerfile and found existing runtime dependencies installed container-wide. Proposed WP-01b-5 to put all Python runtime dependencies in /opt/venv and pip-tools in an isolated tooling venv, then install/verify approved pins. Full specification reread; no product code, dependency installation or tests run this turn. Package approval pending; updated plan/current state/handoff with precise resume point.

## WP-01b-5 - partial progress, runtime choice awaiting clarification

Owner instruction: Approved `WP-01b-5`. Precheck existing services healthy, one live user/eligible sender administrator, test_docinsight absent. Edited Dockerfile for runtime venv and optional CA build mount, added approved direct requirements and container-based Compile-BackendRequirements.ps1. First compiler failed TLS trust; used Windows public trusted-root bundle mounted read-only with verification enabled. Second attempt failed a native-shell diagnostic quoting issue after successful tooling installation; fixed within scope. Third completed exit0: isolated pip-tools toolchain pip check passed, include-system-site-packages=false, application hash lock generated with all approved direct versions and original foundation versions retained.

Owner subsequently wrote "Install the new one like the previous managed". Asked whether this means same pip/hash workflow inside venv or superseding venv with original container-wide installation. Runtime rebuild held pending answer; existing backend unchanged. No runtime installation/import checks, Django/regression tests or migration run yet. Foundation/README explanations describe written changes, not verified deployment. Current state/handoff preserve exact resume point. No provider calls or application feature completion claimed.

## WP-01b-5 - completed after runtime-layout clarification

Owner answered "Yup I men, yes, if there is no harm in it" to explicit no-runtime-venv clarification. Recorded that only the runtime-venv condition is superseded; restored original container Python layout and retained isolated compiler. Approved libraries/hash lock installed; backend image built with temporary trusted public CA mount, only backend recreated.20 version/location assertions/seven imports/synthetic Fernet roundtrip passed; pip check and Django system/no-drift passed.58 account regressions passed first run with new dependencies; test DB created/migrated/destroyed. Postcheck UID10001, one live user/eligible administrator, zero tokens,10 tables, test DB absent, all services healthy. No model/migration/HTTP/frontend/provider change.

Updated foundation component, README, ADR-005/008, decision log, plan, traceability, verification, current state, handoff and interview guide. Corrected misplaced WP-01b-4 plan tail during documentation review. Current/next actions reconciled; no runtime clarification or compiler left pending. Next prepare credential-store scope under approved D-029 A and obtain its separate package approval; no new product work authorized by this completion.

## Learning documentation - checkpoint answers

Owner explicitly requested past optional checkpoint questions with answers in an .md file and the same practice for future work. Added UNDERSTANDING_CHECKPOINTS.md with8 entries recovered from INTERVIEW_GUIDE.md: five explicit checkpoints plus three related user-model explanation prompts. Answers grounded in inspected models, verification/login services, existing component docs and current approved directions; Gmail storage/OAuth/send labelled unimplemented. No invented past quotations or new architecture choices. Added maintenance rule to AGENTS.md and references in README/interview guide; current state/handoff preserve practice and unchanged engineering resume point. Documentation-only; no packages installed, runtime tests rerun or product behavior changed.

## Next-scope review - D-030 and WP-01b-6 proposed

Owner asked to proceed; inspected current code/settings/Compose and approved Gmail/file decisions. No sender store, private sender volume or key config exists yet. Prepared D-030 record/stale-operation options (generation-checked short writes recommended versus holding lock through whole operation) and dependent WP-01b-6 scope with synthetic failure/concurrency verification. Reviewed primary Fernet50.0.2 and Python3.13 filesystem/locking documentation; existing encrypted-file direction unchanged. Added CP-09 question/answer explicitly labelled proposed; updated current state/handoff. No implementation/package approval inferred, code/install/provider call or tests run. Await owner choice then separate package approval.

## D-030 A approval and finalized WP-01b-6 proposal

Owner instruction: `D-030 A`. Recorded common credential record/validation/limits and generation-checked short-write/empty-marker design approved; no rationale invented. Finalized WP-01b-6 for separate package approval, no unresolved choices inside scope; later OAuth/provider/API/UI explicitly excluded. Updated CP-09 answer/current state/handoff. Documentation only, no implementation, volume/key setup or runtime tests performed. Await owner package approval.

Updated README, accounts component, API/architecture notes, ADR-008, project brief, traceability/testing, implementation/decision/development logs, interview guide, current state and handoff. Next owner review and concrete Gmail dependency/storage/OAuth/API/delivery proposal. No next package approved; all P0 targets retained.

## WP-01b-6 — encrypted sender storage completed

Owner instruction: Approve `WP-01b-6`. Implemented SenderCredentialStore/read/replace/clear and safe record/errors,27 synthetic tests, lazy settings, private image directory and backend-only persistent volume. No locks cover provider work; every mutation checks expected generation, and clear retains a generation-bearing empty marker.

First focused run exposed fixture rereading intentionally corrupt data; corrected fixture, then27 passed. Hardened invalid Unicode/deep JSON handling. Post-replacement directory-sync failure explicitly reports uncertainty rather than claiming rollback. Full85 regressions passed; build/Compose/Django/pip/no-drift/mount/permissions checks passed. Standalone inspection initially lacked Django settings initialization; diagnostic corrected. Detailed commands/failures in TESTING_AND_EVALUATION.md.

New runtime volume is UID10001/mode0700 and empty, with real encryption key unset. Existing1 account/eligible admin preserved;0 tokens,10 tables, no test DB after suite. No Google/provider calls, migrations, dependency-lock/frontend/routes changes or real secret provisioning.

Updated component/ADR, README, architecture/API notes, traceability, plan/decision/development/testing logs, current state/handoff, interview guide and checkpoints CP-09/10. Next: owner review, then propose OAuth contract/setup decisions and separately approved package; no active package.

## D-031/D-032 owner choices and next proposal

Actual owner instruction: `D-031 B, D-032 A`. Recorded as approved dedicated attempt model and latest-pending-per-admin policy/common expiry/session/claim rules. Added ADR-011; detailed D-033 schema/retention/service and WP-01b-7 proposed, awaiting decisions/package approval.

Updated decision log, plan, proposed data-model note, checkpoints CP-11/12, current state/handoff. No product/config/dependency/migration/provider operation or runtime test this documentation turn;85-test WP-01b-6 evidence remains last verification. Resume with D-033 choice and separate WP-01b-7 approval.

## WP-01b-7 — internal attempt lifecycle completed

Actual owner instruction: `D-033 A; Approved WP-01b-7`. Implemented OAuthConnectionAttempt with PROTECT history/digest/context/time constraints, create_oauth_attempt/claim_oauth_attempt, immutable transient results/static errors and27 synthetic tests. Current signed DB session/user/backend/password-auth hash revalidated; lock order User→Session→Attempt; short outermost committed transactions, no external work.

Reviewed/generated/applied additive0003 table. Focused27 tests passed on first run3.718s, full112 passed on first run22.435s; Django/no-drift and schema/postchecks passed. Four new PostgreSQL races plus existing token/storage races passed. No ordinary implementation failures required a design change.

Postcheck preserved1 administrator,0 tokens/attempts,11 tables; test DB absent; all3 services healthy; encrypted sender volume still empty/key unset. No dependencies/config/frontend/HTTP/provider/key changes or image rebuild needed for bind-mounted development source.

Updated component/ADR/data model/architecture/API/traceability/plan/testing/decision/current-state/handoff/interview/README/checkpoints. CP-11/12 now reference implemented symbols and retain limits. Next owner review, then small-batch OAuth API/transport/PKCE/log/provider decisions before separate integration package; no next implementation approved.

Final review amendment within WP-01b-7: added malformed timestamp cases and safe pre-conversion type validation in model.clean_fields. Intermediate112-test rerun had1 TypeError on integer superseded_at input; corrected using normal ValidationError. Final112 passed25.630s and no-drift passed; no schema or architectural change. Initial passing counts above are historical, final result is authoritative.

## Next integration decision review — no implementation

After owner "Proceed further", inspected current instructions/state/handoff/approved attempts/store and routing/proxy middleware. Checked primary Google callback guidance, OAuth RFC9700 and official Flow docs. Proposed D-034 callback ownership/transport and D-035 PKCE; no owner choice inferred.

Added decisions/next-package outline/CP-13 question-answer; updated current state/handoff. No code/config/migration/dependency/provider or test operation. Latest verified code remains WP-01b-7/112 tests. Await choices, then detailed package approval.

## D-034/D-035 choices recorded — next package proposed

Owner instruction: `D-034 A, D-035 A`. Approved direct Django callback and encrypted S256 verifier directions; recorded ADR-012. Proposed exact D-036 schema/service/lifecycle and WP-01b-8 internal verifier package. No implementation inferred. Updated decision/plan/data-model/checkpoint/current-state/handoff docs; CP-13/14 answers maintained.

Read current code/approved boundaries and primary RFC7636/Fernet references. No product/dependency/config/migration/key/provider/test action. Last runtime evidence112 tests. Await D-036 choice and separate WP-01b-8 approval; callback/API/log/provider setup still later scope.

## WP-01b-8 completed

Owner instruction `D-036 B; Approved WP-01b-8`; common design plus DB shape constraint approved. Precheck users1/admin1/attempts0/pending0/testDB0; no legacy data decision needed. Added small crypto helper, encrypted model field/check, migration0004 and lifecycle integration. New tests use synthetic keys only; no real key/dependency/config/provider/HTTP/frontend changes. Source bind mount, no rebuild needed.

Focused38 passed6.560s; full123 passed31.292s, no failures in this package. Migration plan reviewed/applied, Django/no-drift/schema checks passed; live account preserved and sender directory empty/key unset. Additional assertions strengthened rollback preservation before full run. Documentation and CP-13/14 updated. No architectural deviations. Next: review result and separately decide/propose protected OAuth integration WP-01b-9; no next implementation approved.

Git publication requested to danial-001/DocInsight on dev. Initialized local repository, configured repository-local username/noreply email, excluded .env and reviewed staged files/common credential patterns. Push awaits SSH identity resolution: current account danialwajahat-lab differs from requested danial-001. No application changes or tests rerun for Git setup.

