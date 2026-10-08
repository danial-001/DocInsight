# ADR-009: Verification-token history and concurrency

**Status:** approved; token model/internal lifecycle implemented and verified  
**Decisions:** D-017 A, D-018 B, D-023 B  
**Owner instructions:** `D-017 A`, `D-018 B`, `D-023 B`

## Context and alternatives

Real verified registration is approved. A replaceable current token record (D-023 A) uses fewer rows but loses issuance history. Separate issuance records (B) retain used/revoked states and need additional constraints and eventual retention review. The owner selected B; no further owner rationale inferred.

## Approved schema and rules

Proposed EmailVerificationToken belongs in accounts: UUID id; required User ForeignKey with PROTECT; unique lower-case64-hex SHA256 token_digest; awareUTC created_at/expires_at; nullable consumed_at/revoked_at. Expiry follows creation; consumed and revoked cannot both be set. Partial unique constraint permits at most one unconsumed/unrevoked record per user, including an expired record until explicitly revoked. Index user/created_at supports latest issuance checks.

Generate32 random bytes, store only digest, expire after one hour, allow one successful use. Resend after60-second issuance cooldown revokes earlier outstanding link. Serialize issuance/consumption with consistent User-first locking in short transactions; no provider calls under locks. Verification sets email_verified_at without changing is_active or automatically logging in. Issuance history does not establish delivery.

## Consequences and limits

More rows support investigation; retention/deletion policy is not approved. PROTECT prevents implicit user/token-history deletion pending an explicit cleanup design. Hashes cannot reconstruct the original link. Raw token may be passed in memory to trusted delivery code, never stored or logged. D-024 A approves future inline sending after database commit; no delivery code exists. HTTP contracts, Gmail integration/diagnostics and UI remain separate review items.

## Implementation and verification

Owner instruction: Approved `WP-01b-3`. Implemented EmailVerificationToken in backend/apps/accounts/models.py, migration0002_emailverificationtoken.py, internal issue/consume services in verification.py and20 tests in tests/test_verification.py. Full47-test account suite passed, including4 PostgreSQL concurrency tests; system/drift checks passed; reviewed additive migration applied; constraints inspected. No HTTP/provider/UI implementation. See IMPLEMENTATION_PLAN.md, TESTING_AND_EVALUATION.md and CURRENT_STATE.md.
