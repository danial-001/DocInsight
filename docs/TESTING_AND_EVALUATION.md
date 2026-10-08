# Testing and evaluation

## Actual results

WP-01a command checks have run as recorded below. Account model and authentication API tests have passed (see WP-01b-1/2 records below). No document/retrieval evaluation, performance measurements or provider calls have run. No accuracy, latency, cost, or improvement figures exist. WP-00 documentation checks are recorded in `DEVELOPMENT_LOG.md`.

## Planned verification

Prioritize cross-user API and private-file access; citation-to-page and evidence-ID resolution; unsupported questions; extraction correction/revision behavior; retry without duplicate indexes; superseded jobs and deletion races; file limits; and frontend loading, empty, failure, keyboard, and responsive states. Tests should exercise observable contracts and failure paths rather than mirror implementation details.

The specification proposes about 50 checked questions across meeting notes, manuals, policies, and study material, with at least 15 held out. Include scans, paraphrases, exact names, multi-section questions, and no-answer cases. Label expected pages and answers manually. Compare fixed-size vector-only retrieval with the selected advanced pipeline using the same extraction, revision, corpus, and generation settings. Record recall@5, supported factual blocks, citation precision, abstention correctness, latency, and cost per query. Measure OCR quality separately on transcribed page samples.

Evaluation design, corpus licensing, metrics, and model/provider budget still require approval. A structurally valid citation is not a semantic-support pass. Report blocked and unrun checks explicitly and never invent results.

## WP-01a actual command verification

Approved by “Approved: D-009 A and WP-01a”. Results recorded from actual runs:

| Check | Result |
| --- | --- |
| Python pip-tools compile with hashes; npm package-lock resolution | Passed; approved pins resolved; one PyPI timeout retried successfully |
| docker compose config --quiet | Passed |
| docker compose build frontend / backend | Both passed |
| docker compose up -d --wait --wait-timeout 180; compose ps | Passed on DB host port 55432; all three healthy |
| backend python manage.py check | No issues |
| backend python -m pip check | No broken requirements |
| Django connection cursor SELECT 1 | Returned 1 |
| Public table count query | Returned 0; no migrations |
| pg_available_extensions query for vector | default_version 0.8.6; installed_version empty |
| frontend npm run build | Initial CSS declaration failure; fixed; rerun typecheck and Vite build passed |
| Invoke-WebRequest frontend/root/App module and backend | HTTP 200; frontend root present |
| Initializer run with existing .env; compare file hashes | File preserved |
| Browser DOM/render/console smoke check | Blocked: execution tool failed twice before code ran, missing sandboxPolicy metadata |
| Desktop pgAdmin, responsive/keyboard UI, production deployment | Unrun |

WP-01a remains in progress until browser acceptance is verified or changed by owner. No cross-user, citation, OCR, revision, job or provider behavior exists to test yet. No evaluation/latency/cost metrics exist. Ports 5432 and 5433 failed before successful 55432 startup; another project owns 5433. No existing containers or volumes were deleted.

## WP-01b-1 verification record

Owner approved `Approved WP-01b-1`. PostgreSQL public-table query returned zero rows before implementation. Generated/reviewed accounts0001 migration and migration plan. Django system check passed. First run of13 tests failed because passwordpassword was not in common-password list; corrected fixture only. Rerun `docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity 1`:13 tests, OK, separate test database created/migrated/destroyed. `makemigrations --check --dry-run`: No changes detected. `migrate --noinput`: all accounts/auth/contenttype migrations OK. Postmigration system check passed. Table query returned8 expected tables, zero accounts, no auth_user. Index query confirmed accounts_user_email_key and accounts_user_email_ci_unique.

No login, registration, CSRF/session, throttle, admin, seed, email delivery or cross-user resource tests apply yet; those features unimplemented. WP-01a browser smoke gate still blocked/unrun. No performance/provider metrics.

## WP-01b-2 verification record

Owner instruction: Approved `WP-01B-2`. Docker engine initially unavailable; started Docker Desktop with approval, then existing Compose services became healthy. No architectural substitution or new dependency.

| Command/check actually run | Result |
| --- | --- |
| docker compose ps (before startup) | Failed: Docker engine unavailable; escalated retry also unavailable |
| Start-Process Docker Desktop (hidden); docker compose up -d --wait --wait-timeout180 | Succeeded; db/backend/frontend healthy |
| Pre-migration schema/test-database query |8 expected tables; test_docinsight absent |
| docker compose exec -T backend python manage.py check | No issues |
| docker compose exec -T backend python manage.py migrate --plan | Only sessions.0001_initial/Create model Session pending |
| docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity2 | Initial26 tests passed; dedicated test DB migrated/destroyed |
| Error-handler review and added regression; same suite --verbosity1 |27 passed; Django Http404/PermissionDenied and unexpected-error responses safe |
| Same-user repeated-login rotation fix; same suite --verbosity1 | Final27 passed; extended existing rotation test covers every successful login |
| docker compose exec -T backend python manage.py migrate --noinput | sessions.0001_initial applied OK; no destructive migrations |
| docker compose exec -T backend python manage.py makemigrations --check --dry-run | No changes detected |
| Windows HttpClient with CookieContainer through127.0.0.1:5173/api/v1/auth | csrf200; anonymous me403; login validation400; valid-CSRF anonymous logout204; tokens/passwords not printed |
| Post-migration schema/count query |9 tables including django_session, zero users/sessions, no auth_user; test DB absent |

Final suite:13 model tests and14 API tests. Synthetic users and explicit verification timestamps exist only in the test DB. No real email or registration simulated as delivered. No successful live login with a provisioned user: positive login covered by API tests. No cross-user resource/private-file/citation, OCR, job, evaluation, UI/responsive or provider checks run. WP-01a browser gate remains unverified. No latency/accuracy/cost metrics.
## WP-01b-3 verification record

Owner instruction: Approved `WP-01b-3`. Actual checks:

| Command/check | Result |
| --- | --- |
| docker compose ps initially | Failed: Docker Desktop Linux engine unavailable |
| Start-Process Docker Desktop (hidden, approved); docker compose up -d --wait --wait-timeout180 | Existing services started and healthy |
| Pre-migration table/history/test-DB inspection |9 expected tables, accounts0001/auth/contenttypes/sessions history; test_docinsight absent |
| docker compose exec -T backend python manage.py makemigrations accounts --name emailverificationtoken | Generated accounts0002, Create model EmailVerificationToken only |
| Read generated migration; docker compose exec -T backend python manage.py migrate --plan | Reviewed; only accounts0002/Create model EmailVerificationToken pending |
| docker compose exec -T backend python manage.py check | No issues |
| docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity2 |47 tests passed on first run, no assertion failures; fresh separate test DB migrated and destroyed |
| docker compose exec -T backend python manage.py migrate --noinput | accounts.0002_emailverificationtoken applied OK |
| docker compose exec -T backend python manage.py makemigrations --check --dry-run | No changes detected |
| Postmigration table/constraint/count/test-DB inspection |10 tables; digest unique, lifecycle checks, user FK, partial outstanding uniqueness, user/created index confirmed; zero users/tokens; test DB absent |

47 total:13 model,14 session API,16 token lifecycle/schema,4 PostgreSQL concurrency. Independent worker connections confirmed distinct pg_backend_pid values; bounded barrier waits/future deadlines and statement/lock timeouts prevent indefinite test waits. Concurrent tests cover first issuance, resend, confirmation and resend-vs-confirmation outcomes. No benchmark, throughput or exhaustive concurrency proof claimed.

Lifecycle checks cover hash-only storage, cooldown boundaries, expiry boundary/pre-expiry, generic invalid errors/no mutation, used/revoked/latest-only links, verified/inactive states, no automatic sessions, rollback of revocation/consumption/outer issuance, digest format/uniqueness, expired-row outstanding constraint, invalid timestamps/conflicting states and protected user deletion. Synthetic database failures exercise rollback, not a fake email integration. No email delivery simulated or attempted; no real accounts created. No new dependencies.

No HTTP registration/verify/resend, browser/UI, Gmail/provider, document/citation isolation, OCR/job/evaluation checks this package. Earlier WP-01a browser gate still unverified. Earlier proxy smoke remains WP-01b-2 evidence, not newly rerun. No accuracy/latency/cost metrics or full-MVP acceptance claimed.
## WP-01b-4 verification record

Owner instruction: Approved `WP-01b-4`. Actual checks:

| Check/command | Result |
| --- | --- |
| docker compose ps | Existing db/backend/frontend healthy; no startup change needed |
| Installed createsuperuser Command.handle source inspection | Confirmed TTY/password prompt, noninteractive handling and manager delegation; reused built-in command |
| Pretest account/table/test-DB query | Zero live users,10 tables, test_docinsight absent |
| docker compose exec -T backend python manage.py check | No issues |
| docker compose exec -T backend python manage.py makemigrations --check --dry-run | No changes detected; no migrations generated/applied |
| docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity2 |58 tests passed on first run; dedicated test DB created/migrated/destroyed; no assertion failures |
| Posttest query | Zero live users/tokens,10 unchanged tables, test DB absent |

58 total =13 account model +14 session API +20 token lifecycle/concurrency +5 sender permission +6 trusted CLI provisioning. All previous account/token regression checks passed. New tests use actual installed Django command with synthetic password/TTY input; not actual owner account creation. Test-only protected view uses real session backend and CSRF checks, not a Gmail provider or production sender endpoint. No actual interactive terminal setup/browser/provider/send tests run; no real credentials logged. No manager change, new dependencies or product routes. Earlier WP-01a browser gate remains unverified; prior proxy smoke not rerun. No new document/evaluation/latency/cost metrics.

## WP-01b-5 verification record

Owner: Approved `WP-01b-5`, then explicitly confirmed returning to the previous container-wide runtime installation without a venv. That supersedes only the original runtime-venv acceptance condition; compiler tooling remains isolated. Actual checks:

| Command/check | Actual result |
| --- | --- |
| docker compose ps; aggregate precheck | All3 services healthy;1 user/eligible administrator; test_docinsight absent |
| ./scripts/Compile-BackendRequirements.ps1, first attempt | Failed SSL certificate validation; original lock/backend unchanged |
| Retry with -CertificateBundlePath pointing to Windows trusted public root bundle | Locked tooling installed and pip check passed; failed diagnostic python -c due to PowerShell/native quoting; no application lock generated by this attempt |
| Third compiler attempt after diagnostic fix | Exit0; isolated /opt/lock-venv site path and include-system-site-packages=false; tooling pip check passed; runtime hash lock generated; warning only about future pip-tools8 strip-extras default |
| Lock inspection |20 distributions; approved four new direct pins present; existing Django5.2.17/DRF3.18.1/psycopg3.3.6/asgiref3.12.1/sqlparse0.6.0 retained; tools lock unchanged. Generated comment header normalized to helper command, not old no-index header; future helper sets CUSTOM_COMPILE_COMMAND |
| docker build --secret id=pip_ca_bundle,src=<temporary-public-CA-bundle> --tag docinsight-backend ./backend | Exit0; hash-verified wheels installed; no disabled certificate verification; ordinary build-time pip root warning, runtime runs as non-root |
| docker compose up -d --no-deps --wait --wait-timeout180 backend | Recreated only backend; healthy; existing db/frontend preserved |
| docker compose exec -T backend python -c <metadata/import/location assertions and synthetic Fernet check> | All20 locked versions match, all distributions located in /usr/local/lib/python3.13/site-packages; seven direct package imports pass; synthetic encrypt/decrypt roundtrip passes without logging key/plaintext; /usr/local/bin/python, prefix/base both /usr/local; /run/secrets/pip_ca_bundle absent |
| docker compose exec -T backend python -m pip check | No broken requirements found |
| docker compose exec -T backend python manage.py check | No issues |
| docker compose exec -T backend python manage.py makemigrations --check --dry-run | No changes detected; no migration generated/applied |
| Pretest query then docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity2 | Confirmed test DB absent,58 tests passed first regression run with new dependencies;16.936s; fresh dedicated test DB created/migrated/destroyed |
| Aggregate postcheck and docker compose ps | Runtime UID10001;1 user and1 eligible administrator,0 verification tokens,10 tables; test DB absent; all3 services healthy |

No new product tests were added because this package changes dependency installation/tooling only; existing behavior checks are meaningful regression coverage. No application venv is claimed. CA bundle remained outside source/image and certificate verification stayed enabled; Google runtime HTTPS trust remains untested. No Google/OAuth/send or paid provider call, real owner login, new browser/proxy check, document/citation isolation, OCR or evaluation. Prior browser gate remains blocked.58 tests do not demonstrate complete DL-01/full MVP, Gmail delivery or measured application latency/quality/cost.

## WP-01b-6 — actual credential-store verification

Only synthetic keys/refresh strings in temporary directories; no Google, paid call, real credential/key provisioning or runtime store record. Commands ran inside Linux backend where file locking is supported.

| Command/check | Actual outcome |
| --- | --- |
| docker compose ps; volume inventory; aggregate DB precheck (separate commands) | All3 healthy; no preexisting sender volume;1 user/eligible admin; test DB absent |
| docker compose exec -T backend python manage.py test apps.accounts.tests.test_sender_store --noinput --verbosity 2 | First run:27 tests,16 subcase errors in one invalid-data test. Fixture incorrectly reread deliberately invalid prior data. Fixed fixture initialization without weakening fail-closed service. Second run:27 passed6.662s; no DB needed |
| docker compose config --quiet | Passed; resolved config/secrets not printed |
| docker build --tag docinsight-backend --secret "id=pip_ca_bundle,src=<existing-temporary-public-CA-PEM>" ./backend | Passed; existing dependency layers cached, TLS verification enabled |
| docker compose up -d --no-deps --wait --wait-timeout 180 backend | Passed; backend alone recreated; new docinsight_sender_credentials volume created; old DB/frontend preserved |
| Standalone Django-initialized Python diagnostic and docker inspect mount summaries | First diagnostic lacked DJANGO_SETTINGS_MODULE and failed; corrected initialization passed. UID10001/private directory0700/empty volume confirmed. Key unset; factory safely unconfigured; volume still empty. Sender volume mounted only in backend |
| docker compose exec -T backend python manage.py check | Passed; no issues |
| docker compose exec -T backend python manage.py makemigrations --check --dry-run | Passed; no changes |
| docker compose exec -T backend python -m pip check | Passed; no broken requirements |
| Test DB safety precheck, then docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity 2 |85 passed25.640s;58 prior +27 new. Fresh dedicated test DB created/migrated/destroyed |
| Aggregate DB, volume-empty and health postcheck |1 account/1 eligible admin,0 verification tokens,10 tables, test DB absent; sender volume empty; all3 services healthy |

New tests cover encryption/persistence, safe representations/errors, strict schema/scope/client/size/key validation, permissions/symlinks/FIFO/hardlinks, stable locking, conditional generations/empty markers, failed writes/cleanup and post-replacement uncertainty. Three spawned-process checks verify one winning writer, stale updates rejected after clear, and bounded lock contention/recovery. Existing four real PostgreSQL race checks also passed.

Test durations are not latency/performance benchmarks. No machine crash/power-loss test, real Google consent/token/sender/delivery, owner login, browser acceptance, uploaded private-file isolation, citation support/resolution or retrieval evaluation performed. Browser gate remains blocked/unverified;85 tests do not establish full MVP acceptance.

## WP-01b-7 — actual OAuth attempt verification

Owner instruction: `D-033 A; Approved WP-01b-7`. All attempt/session fixtures synthetic; no Google provider/mock, real owner login or OAuth network request.

| Command/check | Actual outcome |
| --- | --- |
| Aggregate DB/test-DB/credential-volume precheck |1 account/1 eligible administrator,0 verification tokens,10 tables; test_docinsight absent, sender volume empty |
| docker compose exec -T backend python manage.py makemigrations accounts --name oauthconnectionattempt | Generated0003_oauthconnectionattempt.py; inspected single CreateModel with approved fields/FK/constraints/index |
| docker compose exec -T backend python manage.py migrate --plan | Only accounts.0003 Create model OAuthConnectionAttempt pending |
| docker compose exec -T backend python manage.py test apps.accounts.tests.test_oauth_attempts --noinput --verbosity 2 |27 passed on first run,3.718s. Separate DB created/migrated/destroyed |
| docker compose exec -T backend python manage.py migrate --noinput | accounts.0003 applied successfully; no existing data rewrite |
| docker compose exec -T backend python manage.py check | Passed; no issues |
| docker compose exec -T backend python manage.py makemigrations --check --dry-run | Passed; no changes |
| docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity 1 |112 passed on first run,22.435s;85 previous +27 new; separate DB created/migrated/destroyed |
| Aggregate state/migration/constraint inspection |1 account/eligible admin,0 verification tokens,0 OAuth attempts,11 tables; test DB absent; migration applied; primary key/digest uniqueness/User FK and named pending/time/terminal constraints/history index present |
| Volume/key diagnostic and docker compose ps | Sender volume empty, real key unset; all3 services healthy |

23 lifecycle/model/session tests cover hashed-only state/session storage, hidden issuance repr, UUID/None/client context, ten-minute boundary, role/status/backend/hash/session mismatch, corruption, logout/rotation/password changes, independent admins, replacement across sessions, rollback, committed visibility from another connection, nested/manual transaction rejection and PROTECT/DB constraints. One synthetic password login uses Django Client; most sessions are constructed with Django's signed DB session engine.

Four actual PostgreSQL race tests use independent connections/PIDs, bounded Barrier synchronization and test-only statement/lock deadlines: duplicate callbacks, duplicate first starts, start-versus-claim and logout-versus-claim. Existing4 token PostgreSQL races and3 file-store spawned-process checks also passed in full suite. Logout after a committed claim does not retroactively cancel it.

The initial focused/regression runs passed. During final review, additional malformed timestamp subcases exposed Django DateTimeField raising TypeError during clean_fields for integer input. The intermediate full rerun had1 error in112 tests (22.107s); added pre-conversion type validation in OAuthConnectionAttempt.clean_fields, preserving ordinary ValidationError behavior. Final verification recorded below. An initial repository read guessed a nonexistent test_session_api.py path; corrected inspection to actual test_auth_api.py, no runtime failure. No optional rebuild/pip/browser checks rerun: bind-mounted source updated and dependencies/config/frontend unchanged. Earlier browser gate remains blocked. No full-MVP private document/citation/retrieval/evaluation/provider acceptance performed. Test durations are not performance metrics.

Final code verification: docker compose exec -T backend python manage.py test apps.accounts --noinput --verbosity 1 passed all112 tests25.630s after the timestamp conversion fix; test DB destroyed and process exit0. Final makemigrations --check --dry-run reported no changes. No new migration or approved-design change. All27 attempt checks are included in this final run.

## WP-01b-8 actual verification

Approval: `D-036 B; Approved WP-01b-8`. Precheck aggregate users1/eligible_admins1/attempts0/pending0/test_docinsight0. Synthetic users/keys/signed sessions only; no real account credentials or provider calls.

Commands executed in Docker backend (manage.py):

| Command | Actual result |
| --- | --- |
| makemigrations accounts --name oauth_pkce_verifier | Generated0004; reviewed additive field/check only |
| test apps.accounts.tests.test_oauth_pkce apps.accounts.tests.test_oauth_attempts --noinput | 38 passed6.560s, first run |
| migrate --plan | Only0004 field/check pending |
| migrate --noinput | accounts.0004_oauth_pkce_verifier OK |
| test apps.accounts --noinput | 123 passed31.292s;112 prior plus11 new; no failure |
| check | No issues |
| makemigrations --check --dry-run | No changes detected |

Django created/migrated/destroyed separate test DB for each suite. Helper cases: RFC7636 known S256 example, random verifier/allowed lengths, encryption roundtrip, strict version/types/keys/duplicates/UTF8/JSON/bounds, wrong key/context swap, malformed configuration. Lifecycle cases: authorization before decryption, row swaps/corruption/key failures preserve claim, failed insert/save preserve original ciphertext, expiry, supersession clearing, DB bypass shape failures. Existing four independent PostgreSQL attempt races now check PKCE lifecycle; competing claims return one verifier. Prior auth/token/store regressions included. Full suite runs with real runtime key unset outside synthetic fixtures, exercising existing account API availability.

Read-only live diagnostic confirmed varchar(1024) nullable field, actual PostgreSQL check definition and migration recorded once; users1/admin1/tokens0/attempts0; sender directory empty/key unset. No data rewrites or test identities retained in live DB. Test durations are not latency benchmarks. No Google consent/exchange/send, real owner login, browser or document access/citation evaluation run. These remain unimplemented/unverified, not passed.

Final postcheck: db/backend/frontend all healthy; test_docinsight absent (count0). Documentation relative Markdown links checked successfully. No process remains running from verification.

