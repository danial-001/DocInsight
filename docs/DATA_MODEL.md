# Data model

## Implemented account schema

WP-01b-1: `backend/apps/accounts/models.py: User` extends AbstractBaseUser and PermissionsMixin. Initial migration `backend/apps/accounts/migrations/0001_initial.py` applied after owner approval and empty-schema inspection.

| Field | Type / rule |
| --- | --- |
| id | UUID primary key, uuid4 |
| email | required EmailField254, normalized trim/lowercase; unique plus Lower(email) uniqueness |
| first_name / last_name | optional CharField150, empty default |
| timezone | CharField64, UTC default, IANA validator |
| date_joined | DateTimeField, aware UTC defaultnow |
| email_verified_at | nullable DateTimeField, None default |
| is_active / is_staff | boolean true / false defaults |
| password / last_login | inherited hash storage / nullable login timestamp |
| is_superuser / groups / user_permissions | PermissionsMixin flag and many-to-many auth metadata links |

No account deletion feature is implemented. Django manages join-table/auth-metadata relations using its built-in behavior; future collection/document ownership and deletion policy remain unapproved. User's migration depends on auth0012; AUTH_USER_MODEL is set before migration so default auth_user is not created.

Observed local schema: accounts_user, accounts_user_groups, accounts_user_user_permissions, auth_group, auth_group_permissions, auth_permission, django_content_type, django_migrations. Zero users seeded. pgvector0.8.6 available, not enabled. WP-01b-2 applied built-in sessions.0001_initial, adding django_session as the ninth table. It stores a primary session_key (CharField40), signed serialized session_data (TextField) and indexed expire_date (DateTimeField); no User foreign key. User identity/auth backend/password-auth hash live in signed session data. Expiry is enforced on lookup; expired rows can remain until Django clearsessions maintenance is run. No cleanup schedule added or deployment approved. Zero users/sessions observed after API smoke.

## Candidate domain entities

Collection, Document, IngestionJob, ExtractionRevision, Page, ParentChunk, ChildChunk, ChunkPageSpan, Conversation, Message, AnswerRun, AnswerEvidence, Citation and Feedback remain specification candidates. No models or migrations for these exist. Resolve cross-table ownership/revision invariants, provenance/deletion, active publication, retries, span corrections and embedding dimension before implementation. Independent foreign keys do not establish matching ownership.

See components/accounts.md for manager/validation behavior and TESTING_AND_EVALUATION.md for actual checks.

## Implemented verification-token schema (WP-01b-3)

Owner instruction: Approved `WP-01b-3`; D-017 A, D-018 B and D-023 B. EmailVerificationToken in backend/apps/accounts/models.py; additive accounts.0002_emailverificationtoken applied. Table accounts_emailverificationtoken is the tenth local table; zero users/token records observed. No real accounts provisioned.

| Field | Type / rule |
| --- | --- |
| id | UUID primary key, uuid4 |
| user | Required ForeignKey to AUTH_USER_MODEL, PROTECT; related_name email_verification_tokens |
| token_digest | Unique CharField64, lower-case SHA256 hex; RegexValidator enforces format in full_clean; service always constructs valid digest |
| created_at | AwareUTC DateTimeField, default now; issuance service supplies sampled time after user lock |
| expires_at | Required awareUTC DateTimeField; service uses issuance+one hour |
| consumed_at / revoked_at | Nullable DateTimeField, default None |

Database checks: accounts_token_expiry_after_creation (expires_at > created_at); accounts_token_not_used_and_revoked (at least one of consumed_at/revoked_at null). Partial unique index accounts_token_one_outstanding allows one row per user with both null. An expired row still occupies this slot until explicitly revoked; the service revokes it before replacement. Index accounts_token_user_created on user/created_at, plus Django-generated FK/digest indexes. Introspection confirmed check/unique/FK/index definitions. Digest format and timestamp awareness are model/service rules, not additional DB format/timezone checks; direct/bulk ORM writes bypass full_clean. DB constraints still protect uniqueness and lifecycle invariants as tested.

Raw token is64 lower-case hex characters encoding32 random bytes, hashed as SHA256 of its ASCII representation. Stored digest is not the secret link value. No raw token, message body, delivery status, recipient payload or provider credentials stored here. created_at denotes issuance, not delivery. No cleanup/retention schedule or account deletion endpoint added. User.delete through ORM raises ProtectedError when any token history remains; explicit future deletion/cleanup policy still needs review.

## Proposed OAuthConnectionAttempt — D-033, not implemented

D-031 B/D-032 A approve a dedicated attempt table and lifecycle policy only. Detailed fields/constraints/FK alternatives are in [D-033](DECISION_LOG.md); WP-01b-7 remains proposed. No model/migration/table added. Refresh credentials continue to belong in encrypted file, not this metadata table. Current observed schema remains ten tables from WP-01b-6.

## Implemented OAuthConnectionAttempt — WP-01b-7

Owner instruction: `D-033 A; Approved WP-01b-7`. The preceding proposed note is superseded: accounts.0003_oauthconnectionattempt applied, adding accounts_oauthconnectionattempt as eleventh local table;0 live attempts and existing1 administrator preserved.

Fields: UUID id; required User FK PROTECT with oauth_connection_attempts relation; unique state_digest CharField64; session_digest CharField64; client_id CharField512; nullable expected_generation UUID; awareUTC created_at/expires_at; nullable claimed_at/superseded_at. No FK to session, no raw state/session key/provider credentials. History remains when session expires/deletes; PROTECT blocks user ORM deletion pending explicit future cleanup.

Inspected database: primary key, state-digest unique index, user FK, user/created_at index and named constraints accounts_oauth_one_pending, accounts_oauth_expiry_after, accounts_oauth_one_terminal, accounts_oauth_claim_in_window, accounts_oauth_superseded_after present. Expiry/pending/terminal timestamps and uniqueness enforced in DB; digest format/UTF-8/aware inputs/exact10-minute duration are model/service rules. save/bulk writes do not call full_clean.

[Component](components/gmail-oauth-attempts.md) owns full interfaces/flow/error/limitations. Claimed means accepted once, not Google-connected. No account cleanup or provider state model added.

## Proposed PKCE extension — D-036, not implemented

D-035 A approves encrypted temporary verifier direction only. D-036 proposes nullable bounded encrypted_pkce_verifier field and service lifecycle, with A service-only shape checks or B recommended DB pending/terminal shape constraint. Existing attempt model/migration0003 unchanged. Last verified11 tables/0 attempts is historical evidence, not a fresh migration precheck. No key/schema operation authorized until D-036 and WP-01b-8 approvals.

## WP-01b-8 verified schema extension

OAuthConnectionAttempt.encrypted_pkce_verifier: CharField(max_length=1024, null=True, blank=True, default=None, editable=False). ASCII Fernet ciphertext validated by internal helpers. Database accounts_oauth_pkce_shape enforces pending non-NULL/nonempty and claimed/superseded NULL; cannot prove cryptographic validity. Existing history/PROTECT/time/pending constraints unchanged. accounts.0004_oauth_pkce_verifier applied after attempts0/pending0 precheck; additive column/check only, schema remains11 tables. No legacy rows invalidated, accounts preserved. Future migrations encountering legacy pending data must receive an explicit handling decision. See components/gmail-oauth-attempts.md for lifecycle.
