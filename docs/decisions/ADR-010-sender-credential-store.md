# ADR-010: Encrypted sender store and stale-write protection

**Status:** approved; implemented and verified under WP-01b-6.  
**Decisions:** D-021 B, D-029 A, D-030 A.  
**Owner instructions:** `D-021 B`, `D-029 A`, `D-030 A`; package: Approve `WP-01b-6`.

## Context and alternatives

One application Gmail sender needs recoverable refresh credentials kept out of source/frontend/PostgreSQL. D-021 B selected encrypted private backend file on a persistent Docker volume instead of encrypted database storage. D-029 A selected single-key Fernet and explicit reconnect-based recovery instead of MultiFernet rotation tooling. Approved common safeguards include permissions, stable locking, atomic replacement, separate key and fail-closed validation.

Encryption does not prevent a valid but stale request from overwriting a newer connection. D-030 offered A: short locked generation compare-and-update, or B: hold lock across the entire future provider operation. Owner selected A; no additional rationale inferred. Recommendation was to avoid coupling file-lock duration to unpredictable Google latency while explicitly rejecting stale writes.

## Chosen design and consequences

One encrypted schema_version1 record contains generation UUID and credential or null. Credentials contain only refresh token, expected-client-bound ID and approved send scope. No access token/client secret/provider endpoint. Every successful mutation generates a new marker. Initial absence is generationNone, whereas local clear persists a generation-bearing empty marker. All mutations require expected_generation; stale updates conflict, never blindly overwrite. Provider work occurs outside local operations; future adapters must use the same protocol.

Private0700 directory and0600 regular owned files, no symlink following/hardlinks, stable Linux flock with two-second acquisition deadline,64KiB cap, encrypted same-directory temporary write/fsync/atomic replace/directory fsync. Wrong key/malformed records/client mismatch fail without reset. Pre-publication failure preserves old bytes; post-replacement directory-sync failure reports uncertainty instead of claiming rollback. No database model/migration or new dependency.

More validation/state tests than whole-operation locking; less lock coupling to provider calls. No provider fees or measured performance claim. Single key is operationally simple but loss requires explicit reconnection/recovery. File formats/callers must be coordinated before changing protocol on real data. Advisory locks/local Linux volume are not a distributed store or protection from a compromised backend/host. Manual deletion/old backups bypass generation history; no such operation is authorized by this ADR.

## Implementation and evidence

backend/apps/accounts/sender_store.py: SenderCredential, SenderState, SenderCredentialStore and safe domain errors; tests/test_sender_store.py:27 synthetic checks including3 spawned-process cases. Dockerfile initializes app-owned private directory; Compose mounts sender_credentials only in backend. settings expose optional directory/key; .env.example stays blank, real .env/key untouched. Detailed interfaces/limits in components/gmail-sender-store.md; actual results/failures in TESTING_AND_EVALUATION.md.

No HTTP sender routes, real Google credentials/consent/refresh/send, provider retry policy or UI implemented here. Missing key means explicitly unconfigured store while existing account API starts. Approved future directions remain D-019/D-020/D-024; exact OAuth/delivery/API contracts still need owner review.
