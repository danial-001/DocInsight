# Understanding checkpoints and answers

Optional reference for learning and interview preparation, not a compulsory test. Backfilled from earlier package checkpoints in INTERVIEW_GUIDE.md and the accompanying user-model explanation prompts. Questions are restated for readability; they are not claimed to be verbatim conversation transcripts. Answers describe current code and explicitly label planned behavior. The implementation status and verification record remain in CURRENT_STATE.md and TESTING_AND_EVALUATION.md.

For each future checkpoint, add a stable CP ID, package/topic, question, plain-English answer, relevant code/document references and any implementation limits. Revise answers when an approved decision changes; do not leave superseded designs presented as current behavior. Keep full answers here and link from package/interview notes to avoid duplication.

## CP-01 — Database ports inside and outside Docker

**Package:** WP-01a. **Question:** Why does changing the database host port not change Django's internal `db:5432` address?

**Answer:** Docker exposes one port to Windows while PostgreSQL listens on another port inside its container. Our mapping is `127.0.0.1:55432` on Windows to port `5432` in the database container. Desktop pgAdmin connects through the Windows address. Django runs on the Compose network, where the service name `db` identifies PostgreSQL directly, so it connects to `db:5432`.

Changing the published Windows port avoids conflicts with other local applications without changing PostgreSQL's listening port or Django's internal connection address.

**Example:** pgAdmin uses `127.0.0.1:55432`; Django uses `db:5432`. Both reach the same database.

**References:** [compose.yaml](../compose.yaml), [development foundation](components/development-foundation.md).

## CP-02 — Defining a custom user early

**Package:** WP-01b-1 explanation prompt. **Question:** Why establish the custom user model before the first migrations and other models' user relationships?

**Answer:** Other tables need to know which user table their relationships reference. DocInsight uses `accounts.User`, configured through `AUTH_USER_MODEL`, rather than Django's default user. We selected UUID identity, email-based login and verification/profile fields as part of that model.

Defining it before the initial migrations lets Django build consistent relationships from the start. Switching later can require changing foreign keys, migration dependencies and existing data; it is more involved than changing one setting. Code should reference the configured user through `settings.AUTH_USER_MODEL` or `get_user_model()` where appropriate.

**Current status:** The custom model and its initial migration exist. This does not mean collections or document ownership are implemented.

**References:** [User](../backend/apps/accounts/models.py), [settings](../backend/config/settings.py), [account component](components/accounts.md).

## CP-03 — Verification and suspension are separate

**Package:** WP-01b-1 explanation prompt. **Question:** Why must an email-verification timestamp not reactivate a suspended account?

**Answer:** Email verification and suspension answer different questions. `email_verified_at` records verification state; `is_active` controls whether the account is allowed to operate. A suspended person may still possess their email link. Using that link must not reverse an administrative suspension.

`consume_verification_token()` sets the verification timestamp but leaves `is_active` unchanged. `VerifiedAccountBackend` requires both active and verified state for login and existing-session identity resolution. Trusted administrator provisioning deliberately sets verification state; that is administrative trust, not proof that a verification email was delivered.

**Example:** A suspended, unverified account successfully consumes its valid token. It becomes verified but remains suspended and cannot log in.

**References:** [verification service](../backend/apps/accounts/verification.py), [authentication backend](../backend/apps/accounts/authentication.py), [account tests](../backend/apps/accounts/tests/).

## CP-04 — Validation versus saving and constraints

**Package:** WP-01b-1 explanation prompt. **Question:** Why do `save()` and bulk writes not replace full validation?

**Answer:** Django's model `save()` does not automatically run `full_clean()`. Our `User.save()` normalizes email, but it does not run every field, password or business-rule validator. `QuerySet.update()` and bulk operations can also bypass model methods. A direct write should not be assumed to follow the manager's validation path.

`UserManager` validates approved account-creation inputs and hashes passwords. Database constraints provide another layer: email uniqueness still rejects conflicting writes even if application validation is bypassed or two requests race. Constraints do not enforce every application rule; for example, lowercase uniqueness does not itself implement our whitespace-trimming policy.

**Example:** Two requests can both find an email unused before either saves. Database uniqueness still prevents both accounts from being committed with the same normalized address.

**References:** [User.save and constraints](../backend/apps/accounts/models.py), [UserManager](../backend/apps/accounts/managers.py), [model tests](../backend/apps/accounts/tests/test_models.py).

## CP-05 — Session cookie, CSRF token and Gmail refresh token

**Package:** WP-01b-2. **Question:** What different jobs do these three credentials perform?

| Credential | Purpose | Where it belongs | Current status |
| --- | --- | --- | --- |
| Session cookie | Identifies the browser's Django login session | Browser cookie; session data in PostgreSQL | Implemented |
| CSRF token | Helps reject forged unsafe browser requests that exploit automatically attached cookies | CSRF cookie plus matching request token, checked by Django | Implemented |
| Gmail sender refresh token | Lets the backend obtain short-lived Google access tokens to send application email | Backend-only encrypted credential storage | Approved design; storage/OAuth/send unimplemented |

**Answer:** The session cookie answers which login session a request belongs to. Browsers attach cookies automatically, which is why a session cookie alone does not protect against CSRF. For unsafe requests, Django also checks the CSRF token and applicable Origin/Referer rules. Our login and logout endpoints explicitly enforce CSRF even for anonymous requests. Successful login rotates the session key and CSRF token.

A valid CSRF token does not log someone in or grant permission. Authentication and authorization are still required where applicable. Likewise, a Gmail refresh token would authorize backend access to the dedicated Google sender; it would not authenticate an ordinary DocInsight user. It must never be sent to the frontend. This is not JWT-based user authentication.

**Example:** An ordinary verified user with a valid session and CSRF token is still denied sender administration by `CanManageEmailSender`.

**References:** [account request flow](components/accounts.md), [login service](../backend/apps/accounts/services.py), [views](../backend/apps/accounts/views.py), [Gmail design](decisions/ADR-008-gmail-oauth-sender.md).

## CP-06 — Replacing an expired verification token

**Package:** WP-01b-3. **Question:** Why does an expired but unrevoked token still occupy the outstanding-token slot, and how does resend replace it safely?

**Answer:** The database's partial unique constraint allows only one token per user with both `consumed_at` and `revoked_at` unset. Its condition does not check the expiry timestamp. Time passing does not update the row, so an expired row can still count as outstanding for uniqueness. Expiry is checked separately when a token is consumed; outstanding does not necessarily mean usable.

`issue_verification_token()` opens a transaction and locks the User row. After checking verification state and the 60-second issuance cooldown, it revokes any outstanding token, including an expired one, then creates the replacement. This frees the unique slot while retaining issuance history. If insertion fails, the transaction rolls back the revocation too. The old token's original expiry still applies after rollback.

The User lock serializes cooperating operations for the same account, including the first issuance when no token row exists. Concurrent resends cannot both publish different outstanding tokens through this service; the second sees the updated cooldown. Future email delivery must wait for the outermost transaction to commit so it cannot send a link that is subsequently rolled back.

**Current status:** Internal lifecycle and PostgreSQL race tests are implemented. A public resend endpoint and real email delivery are not.

**References:** [EmailVerificationToken constraints](../backend/apps/accounts/models.py), [issue_verification_token](../backend/apps/accounts/verification.py), [verification tests](../backend/apps/accounts/tests/test_verification.py).

## CP-07 — Sender permission and CSRF

**Package:** WP-01b-4. **Question:** Why is a verified staff user denied while an active verified superuser is permitted, and why does the latter still need CSRF for mutations?

**Answer:** The owner approved active, verified superusers as sender administrators. Django's `is_staff` flag conventionally controls admin-site access; it is not the chosen sender-management permission. `CanManageEmailSender` explicitly checks authentication, active state, verification and `is_superuser`. Staff status alone is insufficient. Every eligible superuser qualifies under this policy, not only one named owner.

Permission decides whether the caller may perform the action. CSRF separately helps establish that an unsafe cookie-authenticated browser request is legitimate rather than forged by another site. A superuser session does not remove that requirement, and a valid CSRF token does not give an ordinary user superuser privileges.

**Current status:** Permission behavior is verified through a test-only protected route, including role/status changes affecting subsequent requests. There are no production Gmail sender endpoints yet. Future OAuth endpoints also need their separately reviewed state/session protections; CSRF and this permission do not replace them.

**References:** [CanManageEmailSender](../backend/apps/accounts/permissions.py), [sender permission tests](../backend/apps/accounts/tests/test_sender_permissions.py), [D-027 and approved directions](DECISION_LOG.md).

## CP-08 — Docker, a venv and a hash lock

**Package:** WP-01b-5. **Question:** What is the difference between Docker isolation, a Python venv and a hash-locked requirements file?

| Mechanism | Problem it solves | DocInsight usage |
| --- | --- | --- |
| Docker isolation | Separates application runtime/process/filesystem environments from the host, subject to configured mounts and access | Backend Python and its libraries run in a dedicated container, separate from Windows Python |
| Python venv | Gives Python packages a separate installation directory using an existing Python interpreter and standard library | Temporary compiler uses `/opt/lock-venv`; backend runtime has no additional venv |
| Hash-locked requirements | Records exact direct/indirect dependency versions and accepted package-file hashes | `requirements.txt` is generated with pip-tools and installed using `--require-hashes` |

**Answer:** Docker controls the runtime environment. A venv controls the Python package installation environment; it does not isolate operating-system dependencies or processes like Docker does. A hash lock controls which dependency versions and package artifacts installation accepts; it does not provide runtime isolation.

The owner initially requested a runtime venv, then explicitly selected the previous direct container-wide installation. Our runtime packages therefore live under `/usr/local/lib/python3.13/site-packages`. This is reasonable for the dedicated backend image; it does not install packages into Windows Python. Temporary compiler tooling remains isolated from the runtime.

**Flow:** Temporary compiler container/venv runs pip-tools → writes the hash lock → Docker build installs approved packages into container Python → backend runs as non-root app UID10001.

Hash checks detect unexpected downloaded artifacts relative to the lock; they do not prove a package is harmless. Docker isolation is not an absolute security boundary. TLS verification remains enabled, and this machine used a trusted public CA bundle for dependency downloads. Installing Gmail libraries does not implement OAuth or email delivery.

**Interview answer:** “Docker separates our runtime from Windows. A venv separates Python package installations. Our requirements lock pins direct and indirect dependency versions and verifies package hashes during the image build.”

**References:** [Dockerfile](../backend/Dockerfile), [direct requirements](../backend/requirements.in), [hash lock](../backend/requirements.txt), [compiler helper](../scripts/Compile-BackendRequirements.ps1), [foundation component](components/development-foundation.md), [installation amendment](DECISION_LOG.md).

## CP-09 — Encryption and stale credential writes

**Package:** WP-01b-6; implemented and verified under D-029 A/D-030 A. **Question:** Why does encrypted storage still need protection against an older request saving after a disconnect or reconnect?

**Answer:** Encryption protects stored content from reading/tampering without the key; it does not decide which legitimate operation is newest. An earlier request can read a credential, wait on Google, then finish after an administrator has changed the sender. Its old write must not replace that newer state.

Owner selected `D-030 A`: every persisted state has a generation UUID. A caller may save only if the state still has the generation it originally read. The internal clear operation leaves an encrypted empty record with a new generation, so earlier requests cannot restore credentials. Short file locks protect each comparison/write while network work happens outside the lock. The alternative holding the lock through the whole operation was not selected. SenderCredentialStore.read/replace/clear implement this protocol; provider adapters and actual disconnect remain future work.

Refresh credentials need reversible encryption because the backend must recover and use them. Verification links use hashes because our service only compares a submitted secret's digest and never needs to recover the original. These are different purposes.

**Current limits:** Store/generation behavior is implemented/tested, including stale updates after clear from absent and populated states. Disconnect route, OAuth refresh and delivery remain unimplemented. Clear does not revoke Google tokens; manual deletion/old backups bypass generation history.

**References:** [D-029/D-030](DECISION_LOG.md), [WP-01b-6 proposal](IMPLEMENTATION_PLAN.md), [existing hashed verification service](../backend/apps/accounts/verification.py).

## CP-10 — A failed save can still change state

**Package:** WP-01b-6. **Question:** Why can a failed save still have published the new credential, and what should its caller do?

**Answer:** Saving writes encrypted temporary bytes, syncs them, atomically replaces the old file, then syncs the directory. An error before replacement preserves the old record. If replacement succeeds but directory sync fails, the new state may already be visible while durability after host failure is uncertain.

SenderStoreWriteUncertain reports this case. Reread actual state before deciding the next action; do not assume rollback or blindly retry with an old generation. An injected failure test confirms the new generation is readable and the old one conflicts. This local persistence result says nothing about a Google request/email delivery.

**References:** [store](../backend/apps/accounts/sender_store.py), [tests](../backend/apps/accounts/tests/test_sender_store.py), [component/error contract](components/gmail-sender-store.md).

## CP-11 — Session, OAuth state and credential generation

**Package:** WP-01b-7; D-031 B/D-032 A/D-033 A implemented and verified.

**Question:** Why does connecting Gmail need OAuth state if DocInsight already has a session cookie and credential generations?

**Answer:** The session cookie identifies the logged-in DocInsight account. OAuth state links Google's return request to the specific connection attempt started in that browser; a logged-in browser alone does not establish that relationship. The credential generation separately checks whether sender configuration changed while an operation was away doing network work.

Example: an administrator starts Connect, returns from Google, and the backend checks session, permission, attempt state and expiry before claiming it once. A later credential save must still compare the captured store generation. This prevents stale publication even after a valid callback. create_oauth_attempt/claim_oauth_attempt now implement proof/session handling; store generations already exist. HTTP callback and provider exchange remain future integration. None of these checks alone proves the selected Google mailbox is the intended sender.

**References:** [decisions](DECISION_LOG.md), [existing session authentication](../backend/apps/accounts/authentication.py), [implemented store](../backend/apps/accounts/sender_store.py), [Google web-server OAuth guide](https://developers.google.com/identity/protocols/oauth2/web-server).

## CP-12 — Claiming an attempt does not mean Gmail is connected

**Package:** WP-01b-7; committed attempt lifecycle implemented and verified.
**Question:** What does claimed_at prove, and why must the claim be committed before exchanging Google's code?

**Answer:** claimed_at records that DocInsight accepted that attempt once after its administrator/session/state/expiry checks. It does not record successful Google consent, token exchange, credential storage or message delivery.

If an inner transaction marked the attempt claimed but a later outer transaction rolled back, a callback could become usable again after external work had already happened. claim_oauth_attempt therefore owns an outermost committed transaction before returning the claim, rejecting nested/manual transactions. Future provider failures do not unclaim it; start again. Two concurrent callbacks compete for one claim.

A later connection save must still compare the captured credential-store generation. A new Connect start supersedes earlier pending attempts; already claimed external work is not automatically cancelled.

**References:** [D-033 and approved directions](DECISION_LOG.md), [WP-01b-7 proposal](IMPLEMENTATION_PLAN.md), [Django transaction boundaries](https://docs.djangoproject.com/en/5.2/topics/db/transactions/). OAuthConnectionAttempt.claimed_at and create_oauth_attempt/claim_oauth_attempt exist in accounts/models.py and accounts/oauth_attempts.py. Independent-connection visibility, rollback/nesting and duplicate callback tests passed; no real Google exchange occurred.

WP-01b-7 implementation references for CP-11/12: [attempt service](../backend/apps/accounts/oauth_attempts.py), [model](../backend/apps/accounts/models.py), [27 verification checks](../backend/apps/accounts/tests/test_oauth_attempts.py), [component flow/limits](components/gmail-oauth-attempts.md).

## CP-13 — OAuth state and PKCE protect different steps

**Topic:** D-035 A/D-036 B; WP-01b-8 implemented and verified. Direct Django callback D-034 A remains an approved direction only.

**Question:** If state already binds a callback to my session, what does PKCE add, and why does its verifier need encryption instead of only a hash?

**Answer:** State checks whether the return matches an attempt started by this administrator/session. PKCE additionally binds the later code exchange to a fresh per-attempt verifier known to the backend. Authorization will carry its S256 challenge; exchange must present the original verifier. A challenge/hash cannot recover that original value.

The browser returns in a later request, potentially after backend restart. OAuthConnectionAttempt.encrypted_pkce_verifier now retains the verifier reversibly encrypted with the separate configured Fernet key. oauth_pkce.generate_verifier/code_challenge/encrypt_verifier/decrypt_verifier implement the local proof. Issuance returns challenge/S256, never verifier; a valid committed claim returns repr-hidden verifier to trusted backend code. No raw verifier in DB/session/browser/logs; never generically serialize the claim dataclass.

State, PKCE, sender generation and Gmail identity solve different problems. Tests verify local crypto/lifecycle, not a real exchange or intended mailbox. Actual callback must redact code/state query values across server/proxy/error logs before real integration; a later clean redirect does not erase earlier logs.

**References:** [helper](../backend/apps/accounts/oauth_pkce.py), [service](../backend/apps/accounts/oauth_attempts.py), [component](components/gmail-oauth-attempts.md), [RFC7636](https://www.rfc-editor.org/rfc/rfc7636.html).

## CP-14 — Retained history and clearing a verifier

**Topic:** D-036 B; WP-01b-8 implemented and verified.

**Question:** If attempt history is retained, why clear its encrypted verifier when claimed or superseded?

**Answer:** History needs identity/context/timestamps to explain lifecycle, not an exchange secret after its one allowed use. claim_oauth_attempt marks claim and clears ciphertext together, returning the decrypted verifier only after commit. create_oauth_attempt also clears old pending ciphertext during supersession. Failed transactions roll back both timestamp and clearing; invalid identity or corrupt proof cannot consume the attempt.

Pending attempts need recoverable ciphertext. Expiry rejects claim but runs no cleanup job; ciphertext remains until authorized replacement or future approved cleanup. accounts_oauth_pkce_shape requires pending nonempty ciphertext and terminal NULL; the helper proves actual encryption/context validity. Database NULL is logical removal, not secure erasure from WAL/backups/memory.

**References:** [model](../backend/apps/accounts/models.py), [service](../backend/apps/accounts/oauth_attempts.py), [helper tests](../backend/apps/accounts/tests/test_oauth_pkce.py), [lifecycle/race tests](../backend/apps/accounts/tests/test_oauth_attempts.py). Focused38/full123 tests passed; no Google exchange occurred.
