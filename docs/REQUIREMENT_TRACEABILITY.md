# Requirement traceability

`Planned` means the requirement is in the approved specification-MVP target; it does not mean its design or implementation is approved. `Implemented` and `verified` must be recorded separately. DL-01 has a verified account-persistence foundation; no full product requirement is complete.

| ID | Requirement and intended package | Implementation files | Meaningful check | Current status |
| --- | --- | --- | --- | --- |
| DL-01 | Authenticate and isolate users; WP-01b-1, WP-01b-2, WP-01b-3, WP-01b-4, WP-01b-6, WP-01b-7, WP-04, WP-06 | backend/apps/accounts/models.py, managers.py, validators.py, authentication.py, serializers.py, services.py, verification.py, permissions.py, sender_store.py, oauth_attempts.py, migrations/0003_oauthconnectionattempt.py, migrations/0002_emailverificationtoken.py, views.py, urls.py, throttles.py, tests/; backend/config/settings.py, middleware.py, exceptions.py | 112 account tests passed (85 prior +27 OAuth-attempt checks, including4 new PostgreSQL races); prior proxy smoke passed; resource/file/citation isolation unrun | Account/session, internal token lifecycle, sender permission/CLI, internal store and committed OAuth attempt lifecycle implemented/verified; registration/email delivery and full DL-01 incomplete |
| DL-02 | Create, rename, archive collections; WP-01b, WP-06 | None | Owner-scoped CRUD; archived write rejection | Planned; not implemented; unrun |
| DL-03 | Validate file signature, bytes, pages, readability; WP-01b, WP-02 | None | Valid text/scan/image plus oversized, encrypted, malformed files | Planned; not implemented; unrun |
| DL-04 | Asynchronous extraction/OCR and observable jobs; WP-02 | None | Scanned document, progress, failure, no duplicated text | Planned; not implemented; unrun |
| DL-05 | Preview/correct extraction and reindex; WP-03, WP-05 | None | Correction creates revision; new retrieval uses it | Planned; not implemented; unrun |
| DL-06 | Source-aware parent–child chunks; WP-03 | None | Child-parent and valid page-span invariants | Planned; not implemented; unrun |
| DL-07 | Collection-scoped retrieval; WP-04 | None | Cross-collection and cross-user evidence exclusion | Planned; not implemented; unrun |
| DL-08 | Cited answers with known evidence IDs; WP-04 | None | Reject unknown IDs; unsupported-question abstention; semantic support review | Planned; not implemented; unrun |
| DL-09 | Open original page and stored evidence; WP-04, WP-06 | None | Citation resolves to authorized page and exact excerpt | Planned; not implemented; unrun |
| DL-10 | Follow-up questions with bounded history; WP-05 | None | Explicit and ambiguous references; sources still required | Planned; not implemented; unrun |
| DL-11 | Retry without duplicate active chunks; WP-03, WP-05 | None | Failed embedding retry; superseded worker race | Planned; not implemented; unrun |
| DL-12 | Delete and immediately exclude documents; WP-05 | None | Retrieval/generation/deletion race and cleanup | Planned; not implemented; unrun |
| DL-13 | Record answer feedback; WP-05 | None | Owner-scoped verdict create/update and validation | Planned; not implemented; unrun |
| DL-14 | Bound provider use; WP-04, WP-05 | None | Server-side file/question/token limits and quota rejection | Planned; not implemented; unrun |

Additional P0 acceptance: text and scanned PDF end-to-end; approximately 50 labelled questions including at least 15 held out; reproducible baseline versus advanced retrieval on identical extraction and generation settings; actual latency, cost, evidence and abstention metrics; responsive and accessible primary states; reproducible seed and startup commands. These remain planned and unrun. Update the table with actual symbols, checks, and separate implementation/verification status after each package.

## Foundation traceability

WP-01a adds compose.yaml, backend/config/, backend/manage.py, frontend/src/ and dependency locks as shared technical groundwork. Command verification recorded in TESTING_AND_EVALUATION.md; browser gate blocked. Foundation startup alone completes no DL requirement. Subsequent WP-01b-1/2/3/4 partially implement and verify DL-01 as recorded above; remaining domain isolation/files/retrieval/citations are unimplemented.

WP-01b-5 supports DL-01 and the owner-added verified-registration direction with approved Google/encryption libraries in backend/requirements.in/.txt, Dockerfile verified hash installation and scripts/Compile-BackendRequirements.ps1 isolated lock tooling. Implemented and verified:20 runtime version/location checks, imports/synthetic Fernet roundtrip, pip/Django/no-drift checks,58 account regressions and aggregate administrator preservation. Runtime venv condition explicitly superseded by owner; container-wide runtime retained. Adds no new functional endpoint, full requirement completion or Gmail/provider integration. D-029 storage and all OAuth/send acceptance remain unimplemented/unrun.

## WP-01b-6 support evidence

D-021 B/D-029 A/D-030 A implemented and verified in sender_store.py, tests/test_sender_store.py, settings.py, Dockerfile and compose.yaml.27 synthetic checks plus full85 regressions; private empty backend-only volume verified. Earlier WP-01b-5 notes that storage was unimplemented describe that checkpoint and are superseded here.

This supports DL-01/owner-added verification and specification section10 secret handling. No complete DL requirement added: production Gmail authorization and document/user/file/citation isolation remain incomplete/unrun.

## WP-01b-7 support evidence

D-031 B/D-032 A/D-033 A implemented in accounts/models.py, oauth_attempts.py, migrations/0003_oauthconnectionattempt.py and tests/test_oauth_attempts.py.27 checks (23 lifecycle/model/session +4 PostgreSQL concurrency) and full112 regressions passed. Additive schema applied/inspected; current administrator preserved,0 real attempt records, no test DB after suite. Internal proof/session isolation supports DL-01, not complete document/file/citation isolation. No full DL requirement newly complete; no P0 deferral.

## WP-01b-8 traceability update

| Requirement | Package/status | Actual implementation | Verified checks | Remaining |
| --- | --- | --- | --- | --- |
| DL-01 authentication/isolation support; spec6/9/10 security | WP-01b-8 implemented and verified | accounts/models.py OAuthConnectionAttempt.encrypted_pkce_verifier/check; migration0004; oauth_pkce.py helpers; oauth_attempts.py create/claim/results | 38 focused tests;123 full accounts tests; migration/schema/check/drift | Gmail HTTP/provider/UI and collection/document/file/citation isolation |

0/14 DL requirements fully complete. No P0 deferral. PKCE verifies local proof lifecycle, not provider account identity or successful delivery. DL-02–DL-14 implementation/verification statuses unchanged.
