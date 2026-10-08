# Gmail sender credential store

## Purpose, scope and decisions

WP-01b-6 implements the local credential-storage component needed by the eventual Gmail sender. Relevant DL-01 support and owner-added verified registration; D-021 B private encrypted volume, D-028 A libraries, D-029 A single Fernet key/file safeguards, D-030 A generation-checked short writes. Owner instruction: Approve `WP-01b-6`. No complete Gmail feature or full DL-01 is claimed.

Refresh credentials must be recoverable so a future Google adapter can use them. SHA256 verification-link digests cannot serve this purpose. Fernet supplies authenticated encryption; our service supplies record validation, private file access, locking, generation comparisons and atomic persistence. No unnecessary provider abstraction, database model, serializer/view/task or React hook is introduced.

## Actual locations and interfaces

| Location / symbol | Inputs → outputs and ownership |
| --- | --- |
| backend/apps/accounts/sender_store.py / SenderCredential | Validated refresh_token/client_id/scopes → frozen credential; repr excludes refresh secret |
| SenderState | generation UUID or None, credential or None → frozen local snapshot; repr excludes credential |
| SenderCredentialStore(directory, encryption_key, client_id=...) | Absolute trusted directory, separate Fernet key and expected OAuth client ID → trusted storage instance; does not authenticate a user |
| SenderCredentialStore.from_settings(client_id=...) | Optional Django store directory/key plus caller's expected client ID → instance, or safe unconfigured error |
| read() | No request/user input → current decrypted SenderState; absent file returns generationNone/credentialNone |
| replace(credential, expected_generation=...) | Validated credential plus UUID/None from earlier read → new state, or conflict if stored generation changed |
| clear(expected_generation=...) | Expected UUID/None → encrypted empty state with fresh generation; no Google revocation or file deletion |
| _locked / _read_locked / _write_locked | Private filesystem coordination, validation/decryption and encrypted atomic publication; callers do not access these for provider operations |
| backend/config/settings.py | Optional GMAIL_CREDENTIAL_STORE_DIR/key; blank key allowed at Django startup, store construction fails explicitly |
| backend/Dockerfile / compose.yaml | App-owned0700 directory → backend-only named sender_credentials volume at /var/lib/docinsight/sender |
| tests/test_sender_store.py / SenderStoreTests, SenderStoreProcessTests | Synthetic temporary directories/keys →24 storage checks and3 independent-process checks; no real provider or runtime volume fixture |

All code paths are backend-only. Future endpoints must authorize using CanManageEmailSender plus approved session/CSRF and OAuth state rules. Passing a client ID is configuration binding, not proof of sender email identity. No endpoint currently calls this store.

## Stored data and configuration

credentials.enc holds Fernet-encrypted UTF8 JSON with exactly schema_version1, canonical generation UUID and credential object or null. Credential keys are exactly refresh_token (1–8192 characters), client_id (1–512) and scopes (one gmail.send scope). Invalid Unicode, wrong types/fields/version, duplicate JSON keys and malformed/deep JSON fail safely. Encrypted file capped at64KiB before decryption; resulting encrypted writes are also capped. No access token, OAuth client secret, arbitrary endpoint, document, recipient or account password stored. API/error/repr output must never expose refresh credentials or keys; never dump local variables or serialize returned objects to HTTP.

GMAIL_CREDENTIAL_ENCRYPTION_KEY is distinct from DJANGO_SECRET_KEY. Missing/invalid key raises SenderStoreUnconfigured before file operations. .env.example documents only an empty value; real .env was not modified and no real key generated. Docker's environment and private volume are not secret protection against a compromised host/backend with access to both.

Single-key recovery: privately retain the real key separately from encrypted-volume backup once real setup is approved; never put either in repository, chat or logs. Lost key requires separately approved Gmail reconnection/recovery. Changing key alone does not decrypt old records; service refuses to overwrite unreadable data. No automatic deletion/reset/rotation/backup service. Restoring older files or manually removing credentials.enc bypasses generation history and must not be treated as routine disconnect. Real recovery procedures must be reviewed before acting on credentials.

## Data flow and concurrency

1. Validate configuration. Create missing private directory only if its parent exists; reject existing symlink/nonprivate/wrong-owner directory without repairing it.
2. Open stable credentials.lock with0600 mode, no symlink following; validate regular file/owner/permissions/link count. Use exclusive nonblocking flock with a two-second monotonic acquisition deadline. Close releases the lock; never unlink/replace the lock file.
3. Under lock, read at most64KiB+1, validating owner0600/regular file/single link. Missing record is distinct from corrupt/empty ciphertext. Decrypt/validate record and compare client ID.
4. Mutations compare expected_generation with the current value. A mismatch raises SenderStoreConflict without altering credential bytes. A valid mutation allocates a new UUID, including clear on an initially absent file.
5. Encrypt in memory. Write only ciphertext to a random same-directory0600 temporary file, flush/fsync, then os.replace the credential file. Fsync the directory after replacement. File replacement and generation comparison occur under the same lock.
6. Release lock and return snapshot. Future Google work must occur outside these short operations, then conditionally save using the original generation. Do not blindly reread and overwrite after a conflict.

**Synthetic example:** requestA reads generation1, administrator clears to generation2 with credentialNone, requestA attempts replace(expected_generation=1) and receives conflict. Another initial request that read generationNone also cannot restore credentials after a clear publishes a real UUID. Concurrent creators reading generationNone have one successful writer and one conflict.

## Errors and failure limits

| Exception / code | Meaning and caller behavior |
| --- | --- |
| SenderStoreUnconfigured / sender_store_unconfigured | Missing/invalid key or invalid directory/client configuration; do not silently use Django key |
| SenderStoreInvalidInput / sender_store_invalid_input | Invalid trusted mutation input; correct caller validation |
| SenderStoreInvalidRecord / sender_store_invalid_record | Wrong decrypting key, tamper, malformed/oversized/unsupported record; preserve bytes, investigate/recover explicitly |
| SenderStoreClientMismatch / sender_store_client_mismatch | Configured OAuth client differs; do not overwrite existing connection |
| SenderStoreConflict / sender_store_conflict | Generation changed; abandon stale update and reconsider current state |
| SenderStoreBusy / sender_store_busy | Could not acquire lock within two seconds; no credential mutation |
| SenderStoreError / sender_store_unavailable | Unsafe filesystem state or I/O failure; no raw exception/path/credential details exposed |
| SenderStoreWriteUncertain / sender_store_write_uncertain | Replacement succeeded but directory sync failed; state may already have changed, reread before any next action |

These are internal errors, not approved HTTP response mappings. Futures adapters must handle them; no automatic provider retry follows a storage exception.

Before replacement, injected write/fsync/replace failure preserves old credential bytes and attempts to remove the temporary ciphertext. Cleanup failure may leave encrypted temporary data; it never contains plaintext. After replacement, do not claim rollback on directory-sync failure. Successful local fsync is not a guarantee against every host/filesystem/power failure. Tests inject failures rather than crashing the machine. flock coordinates cooperating processes on the approved local Linux volume; this is not a distributed multi-host store or native Windows service.

## Verification and current limits

Focused27-test run initially failed one test's16 invalid-data subcases because its fixture reread the prior deliberately invalid record. Fixed fixture initialization, retaining fail-closed behavior; rerun27 passed. Includes encryption/persistence/repr/traceback checks, schema/size/client/key rejection, symlink/FIFO/hardlink/permission checks, pre/post replacement failure handling and3 real spawned-process checks for one writer, stale updates after clear and bounded lock contention. Full-suite/current environment outcomes are recorded in TESTING_AND_EVALUATION.md.

Runtime volume inspection confirmed UID10001/mode0700, mounted only in backend and empty before/after missing-key inspection. No real key/credential or production credentials.enc was created. Blank configuration leaves existing session API available. Google consent/token validity/revocation, sender identity, network trust/delivery and browser UI remain unimplemented/unverified. Empty local state is not proof of Google revocation, and populated local state would not prove a usable Google token or inbox delivery.

Completion evidence: focused27 tests passed6.662s; full85 account tests passed25.640s. Django/pip/no-drift/quiet Compose/build/backend-recreate/mount checks passed. Postcheck preserved1 account/eligible admin,0 tokens,10 tables and no test DB; all3 services healthy, runtime sender volume empty. These durations are test execution only.
